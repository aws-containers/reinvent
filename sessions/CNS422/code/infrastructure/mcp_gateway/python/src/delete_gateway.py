#!/usr/bin/env python3
"""
Utility script to delete an existing MCP gateway.
This script will first delete all gateway targets, then delete the gateway itself.

Usage:
    uv run delete-gateway [gateway_id]

If no gateway_id is provided, it will attempt to find and delete
the gateway with the default name pattern.
"""

import sys
import boto3
import time
from botocore.exceptions import ClientError

# Try relative import first, fall back to absolute import
try:
    from . import utils
except ImportError:
    import utils

def find_gateway_by_name(gateway_client, gateway_name):
    """Find gateway ID by name"""
    try:
        list_response = gateway_client.list_gateways(maxResults=100)
        for gateway in list_response.get('items', []):
            if gateway.get('name') == gateway_name:
                return gateway['gatewayId']
        return None
    except Exception as e:
        print(f"❌ Error listing gateways: {e}")
        return None

def delete_gateway_with_logging(gateway_client, gateway_id):
    """Delete gateway with detailed logging"""
    try:
        print(f"🗑️  Starting gateway deletion process...")
        print(f"   Gateway ID: {gateway_id}")
        print("--------------------------------------------------")

        # Step 1: List and delete all gateway targets
        print("🔍 Step 1: Listing gateway targets...")
        try:
            list_response = gateway_client.list_gateway_targets(
                gatewayIdentifier=gateway_id,
                maxResults=100
            )

            targets = list_response.get('items', [])
            if not targets:
                print("✅ No targets found for this gateway")
            else:
                print(f"Found {len(targets)} target(s) to delete:")
                for target in targets:
                    target_id = target.get('targetId')
                    target_name = target.get('name', 'Unknown')
                    print(f"   - {target_name} (ID: {target_id})")

                print(f"\n🗑️  Step 2: Deleting {len(targets)} target(s)...")
                for i, target in enumerate(targets, 1):
                    target_id = target.get('targetId')
                    target_name = target.get('name', 'Unknown')

                    try:
                        print(f"Deleting target {i}/{len(targets)}: {target_name} (ID: {target_id})")
                        gateway_client.delete_gateway_target(
                            gatewayIdentifier=gateway_id,
                            targetId=target_id
                        )
                        print(f"✅ Successfully deleted target: {target_name}")

                        # Add delay between deletions to avoid throttling
                        if i < len(targets):  # Don't wait after the last deletion
                            print("⏳ Waiting 5 seconds to avoid throttling...")
                            time.sleep(5)

                    except ClientError as e:
                        error_code = e.response['Error']['Code']
                        if error_code == 'ResourceNotFoundException':
                            print(f"⚠️  Target {target_name} not found (may have been deleted already)")
                        else:
                            print(f"❌ Error deleting target {target_name}: {e}")
                            raise

                print("✅ All targets deleted successfully")
                print("⏳ Waiting 10 seconds for target deletions to propagate...")
                time.sleep(10)

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                print("⚠️  Gateway not found (may have been deleted already)")
                return True
            else:
                print(f"❌ Error listing gateway targets: {e}")
                raise

        # Step 3: Delete the gateway itself
        print(f"\n🗑️  Step 3: Deleting gateway...")
        try:
            gateway_client.delete_gateway(gatewayIdentifier=gateway_id)
            print(f"✅ Successfully deleted gateway: {gateway_id}")

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                print("⚠️  Gateway not found (may have been deleted already)")
            else:
                print(f"❌ Error deleting gateway: {e}")
                raise

        print("\n🎉 Gateway deletion completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Gateway deletion failed: {e}")
        return False

def main():
    print("🚀 Starting MCP Gateway deletion...")

    gateway_client = boto3.client('bedrock-agentcore-control')

    # Get current region for logging
    region = utils.get_current_region()
    print(f"📍 Region: {region}")

    # Check if gateway ID was provided as argument
    if len(sys.argv) > 1:
        gateway_id = sys.argv[1]
        print(f"🎯 Using provided gateway ID: {gateway_id}")
    else:
        # Try to find gateway by default name
        gateway_name = "reinvent-AppMod-Insurance"
        print(f"🔍 Looking for gateway with name: {gateway_name}")
        gateway_id = find_gateway_by_name(gateway_client, gateway_name)

        if not gateway_id:
            print(f"❌ No gateway found with name: {gateway_name}")
            print("Usage: uv run delete-gateway [gateway_id]")
            sys.exit(1)

        print(f"✅ Found gateway with ID: {gateway_id}")

    # Delete the gateway with detailed logging
    success = delete_gateway_with_logging(gateway_client, gateway_id)

    if success:
        print("✅ Gateway deletion completed successfully")
        sys.exit(0)
    else:
        print("❌ Gateway deletion failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
