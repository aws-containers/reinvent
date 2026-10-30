#!/usr/bin/env python3
"""
Utility script to delete an existing API Key Credential Provider.
Useful for testing and cleanup operations.

Usage:
    uv run python delete_credential_provider.py [prefix] [--no-wait]

If no prefix is provided, it will use the default 'reinvent' prefix.
This will delete the API Key Credential Provider with the name pattern:
{prefix}-AppMod-Insurance

The script handles AWS API limitations and waits for SecretsManager cleanup.
Use --no-wait to skip SecretsManager cleanup verification.
"""

import sys
import boto3
import time
from src.utils import get_current_region
from botocore.exceptions import ClientError

def find_credential_provider_by_name(acps_client, provider_name):
    """Find credential provider ARN by name using pagination"""
    try:
        # Try with pagination to ensure we get all providers
        paginator = acps_client.get_paginator('list_api_key_credential_providers')
        for page in paginator.paginate():
            for provider in page.get('items', []):
                if provider.get('name') == provider_name:
                    return provider['credentialProviderArn']
    except Exception as e:
        print(f"Error during paginated search: {e}")
        # Fallback to simple list
        try:
            list_response = acps_client.list_api_key_credential_providers(maxResults=100)
            for provider in list_response.get('items', []):
                if provider.get('name') == provider_name:
                    return provider['credentialProviderArn']
        except Exception as fallback_e:
            print(f"Error in fallback search: {fallback_e}")
    return None

def check_secrets_manager_cleanup(provider_name, region, max_wait_time=60):
    """Check if SecretsManager secrets related to the provider are cleaned up"""
    secrets_client = boto3.client('secretsmanager', region_name=region)

    print(f"Checking SecretsManager cleanup for provider: {provider_name}")

    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        try:
            response = secrets_client.list_secrets(MaxResults=100)
            related_secrets = []

            for secret in response.get('SecretList', []):
                secret_name = secret.get('Name', '')
                # Check if secret is related to our provider
                if provider_name in secret_name or f'apikey/{provider_name}' in secret_name:
                    related_secrets.append(secret_name)

            if not related_secrets:
                print("✅ SecretsManager cleanup completed - no related secrets found")
                return True
            else:
                elapsed = int(time.time() - start_time)
                print(f"⏳ Found {len(related_secrets)} related secrets, waiting for cleanup... ({elapsed}s elapsed)")
                for secret_name in related_secrets:
                    print(f"   - {secret_name}")
                time.sleep(5)

        except Exception as e:
            print(f"Error checking SecretsManager: {e}")
            time.sleep(5)

    print(f"⚠️  SecretsManager cleanup verification timed out after {max_wait_time} seconds")
    return False

def attempt_delete_by_name(acps_client, provider_name):
    """Attempt to delete credential provider directly by name (handles API limitations)"""
    try:
        print(f"Attempting direct deletion of provider: {provider_name}")
        acps_client.delete_api_key_credential_provider(name=provider_name)
        print("✅ Direct deletion successful")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print("ℹ️  Provider not found (may already be deleted)")
            return True
        else:
            print(f"❌ Direct deletion failed: {e}")
            return False

def delete_credential_provider(prefix="reinvent", wait_for_cleanup=True):
    """Delete the API Key Credential Provider for the given prefix"""

    PROVIDER_NAME = f'{prefix}-AppMod-Insurance'
    region = get_current_region()

    print(f"🗑️  Deleting API Key Credential Provider")
    print(f"   Prefix: {prefix}")
    print(f"   Provider name: {PROVIDER_NAME}")
    print(f"   Region: {region}")
    print("-" * 50)

    acps = boto3.client(service_name="bedrock-agentcore-control", region_name=region)

    # Step 1: Try to find the credential provider (may not work due to API limitations)
    print("🔍 Step 1: Searching for credential provider...")
    provider_arn = find_credential_provider_by_name(acps, PROVIDER_NAME)

    if provider_arn:
        print(f"✅ Found credential provider with ARN: {provider_arn}")
    else:
        print("⚠️  Provider not found in list (this is expected due to API limitations)")
        print("   Available credential providers:")
        try:
            list_response = acps.list_api_key_credential_providers(maxResults=100)
            providers = list_response.get('items', [])
            if providers:
                for provider in providers:
                    print(f"     - {provider.get('name')} (ARN: {provider.get('credentialProviderArn')})")
            else:
                print("     - No providers found in list")
        except Exception as e:
            print(f"     Error listing providers: {e}")

    # Step 2: Attempt deletion (works even if not found in list)
    print("\n🗑️  Step 2: Attempting deletion...")
    deletion_success = attempt_delete_by_name(acps, PROVIDER_NAME)

    if not deletion_success:
        print("❌ Deletion failed")
        return False

    # Step 3: Wait for SecretsManager cleanup if requested
    if wait_for_cleanup:
        print("\n⏳ Step 3: Waiting for SecretsManager cleanup...")
        cleanup_success = check_secrets_manager_cleanup(PROVIDER_NAME, region, max_wait_time=60)

        if cleanup_success:
            print("✅ SecretsManager cleanup verified")
        else:
            print("⚠️  SecretsManager cleanup verification timed out")
            print("   This may cause conflicts when creating a new provider with the same name")
            print("   Consider waiting longer or using a different name")

    print("\n🎉 Credential provider deletion completed")
    return True

def main():
    # Check if prefix was provided as argument
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        prefix = sys.argv[1]
        print(f"Using provided prefix: {prefix}")
    else:
        prefix = "reinvent"
        print(f"Using default prefix: {prefix}")

    # Check for --no-wait flag
    wait_for_cleanup = "--no-wait" not in sys.argv
    if not wait_for_cleanup:
        print("⚡ Fast mode: Skipping SecretsManager cleanup verification")

    try:
        success = delete_credential_provider(prefix, wait_for_cleanup)
        if success:
            print("\n✅ Credential provider cleanup completed successfully")
            if wait_for_cleanup:
                print("   Safe to create a new provider with the same name")
        else:
            print("\n❌ Credential provider cleanup failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error during cleanup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
