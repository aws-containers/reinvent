#!/usr/bin/env python3
"""
Utility script to delete existing Gateway Targets.
Useful for testing and cleanup operations.

Usage:
    uv run python delete_gateway_targets.py [prefix] [--target-name TARGET_NAME]

If no prefix is provided, it will use the default 'reinvent' prefix.
This will delete Gateway Targets from the gateway with the name pattern:
{prefix}-AppMod-Insurance

Use --target-name to delete a specific target, otherwise all targets will be deleted.
"""

import sys
import boto3
from src.utils import get_current_region
from botocore.exceptions import ClientError

def find_gateway_by_name(gateway_client, gateway_name):
    """Find gateway ID by name"""
    try:
        list_response = gateway_client.list_gateways(maxResults=100)
        for gateway in list_response.get('items', []):
            if gateway.get('name') == gateway_name:
                return gateway['gatewayId']
        return None
    except Exception as e:
        print(f"Error listing gateways: {e}")
        return None

def list_gateway_targets(gateway_client, gateway_id):
    """List all targets for a gateway"""
    try:
        list_response = gateway_client.list_gateway_targets(
            gatewayIdentifier=gateway_id,
            maxResults=100
        )
        return list_response.get('items', [])
    except Exception as e:
        print(f"Error listing gateway targets: {e}")
        return []

def delete_gateway_target(gateway_client, gateway_id, target_id, target_name, max_retries=3):
    """Delete a specific gateway target with retry logic for throttling"""
    import time

    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                wait_time = 2 ** attempt  # Exponential backoff: 2, 4, 8 seconds
                print(f"⏳ Retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries + 1})")
                time.sleep(wait_time)

            print(f"Deleting gateway target: {target_name} (ID: {target_id})")
            gateway_client.delete_gateway_target(
                gatewayIdentifier=gateway_id,
                targetId=target_id
            )
            print(f"✅ Successfully deleted target: {target_name}")
            return True

        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException' and attempt < max_retries:
                print(f"⚠️  Throttling detected for target {target_name}, will retry...")
                continue
            else:
                print(f"❌ Error deleting target {target_name}: {e}")
                return False

    return False

def delete_gateway_targets(prefix="reinvent", specific_target_name=None):
    """Delete Gateway Targets for the given prefix"""

    GATEWAY_NAME = f'{prefix}-AppMod-Insurance'
    region = get_current_region()

    print(f"🗑️  Deleting Gateway Targets")
    print(f"   Prefix: {prefix}")
    print(f"   Gateway name: {GATEWAY_NAME}")
    print(f"   Region: {region}")
    if specific_target_name:
        print(f"   Target filter: {specific_target_name}")
    else:
        print(f"   Target filter: ALL targets")
    print("-" * 50)

    gateway_client = boto3.client('bedrock-agentcore-control', region_name=region)

    # Step 1: Find the gateway
    print("🔍 Step 1: Finding gateway...")
    gateway_id = find_gateway_by_name(gateway_client, GATEWAY_NAME)

    if not gateway_id:
        print(f"❌ No gateway found with name: {GATEWAY_NAME}")
        print("Available gateways:")
        try:
            list_response = gateway_client.list_gateways(maxResults=100)
            gateways = list_response.get('items', [])
            if gateways:
                for gateway in gateways:
                    print(f"   - {gateway.get('name')} (ID: {gateway.get('gatewayId')})")
            else:
                print("   - No gateways found")
        except Exception as e:
            print(f"   Error listing gateways: {e}")
        return False

    print(f"✅ Found gateway with ID: {gateway_id}")

    # Step 2: List gateway targets
    print("\n🔍 Step 2: Listing gateway targets...")
    targets = list_gateway_targets(gateway_client, gateway_id)

    if not targets:
        print("ℹ️  No targets found in gateway")
        return True

    print(f"Found {len(targets)} targets:")
    for target in targets:
        target_name = target.get('name', 'Unknown')
        target_id = target.get('targetId', 'Unknown')
        print(f"   - {target_name} (ID: {target_id})")

    # Step 3: Filter targets if specific name provided
    targets_to_delete = []
    if specific_target_name:
        for target in targets:
            if target.get('name') == specific_target_name:
                targets_to_delete.append(target)

        if not targets_to_delete:
            print(f"⚠️  No target found with name: {specific_target_name}")
            return False
    else:
        targets_to_delete = targets

    # Step 4: Delete targets
    print(f"\n🗑️  Step 3: Deleting {len(targets_to_delete)} target(s)...")
    deleted_count = 0
    failed_count = 0

    for i, target in enumerate(targets_to_delete):
        target_name = target.get('name', 'Unknown')
        target_id = target.get('targetId', 'Unknown')

        # Add delay between deletions to prevent throttling (except for first target)
        if i > 0:
            import time
            print("⏳ Waiting 3 seconds to avoid throttling...")
            time.sleep(3)

        if delete_gateway_target(gateway_client, gateway_id, target_id, target_name):
            deleted_count += 1
        else:
            failed_count += 1

    # Summary
    print(f"\n📊 Summary:")
    print(f"   ✅ Successfully deleted: {deleted_count} targets")
    if failed_count > 0:
        print(f"   ❌ Failed to delete: {failed_count} targets")

    print(f"\n🎉 Gateway targets cleanup completed")
    return failed_count == 0

def main():
    # Parse command line arguments
    prefix = "reinvent"
    specific_target_name = None

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--target-name" and i + 1 < len(sys.argv):
            specific_target_name = sys.argv[i + 1]
            i += 2
        elif not arg.startswith('--'):
            prefix = arg
            i += 1
        else:
            i += 1

    print(f"Using prefix: {prefix}")
    if specific_target_name:
        print(f"Targeting specific target: {specific_target_name}")

    try:
        success = delete_gateway_targets(prefix, specific_target_name)
        if success:
            print("\n✅ Gateway targets cleanup completed successfully")
        else:
            print("\n❌ Gateway targets cleanup failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error during cleanup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
