#!/usr/bin/env python3
"""
Simple connection test for MCP Gateway
This script tests the basic connectivity without running the full setup
"""

import argparse
import requests
import json

# Try relative import first, fall back to absolute import
try:
    from . import setup
except ImportError:
    import setup


def test_gateway_connection(prefix="reinvent"):
    """Test basic gateway connectivity"""
    print(f"Testing MCP Gateway connection with prefix: {prefix}")

    try:
        # Get existing resources (don't create new ones)
        print("Retrieving existing gateway credentials...")

        # Get Cognito resources
        user_pool_id, client_id, client_secret, cognito_discovery_url, token_url = setup.get_or_create_cognito(prefix)

        # Get gateway info
        gateway_client = setup.boto3.client('bedrock-agentcore-control')
        gateway_name = f'{prefix}-AppMod-Insurance'

        # Find existing gateway
        list_response = gateway_client.list_gateways(maxResults=100)
        gateway_url = None

        for gateway in list_response.get('items', []):
            if gateway.get('name') == gateway_name:
                gateway_id = gateway['gatewayId']
                gateway_details = gateway_client.get_gateway(gatewayIdentifier=gateway_id)
                gateway_url = gateway_details.get('gatewayUrl')
                break

        if not gateway_url:
            print(f"❌ Gateway '{gateway_name}' not found. Run setup first.")
            return False

        print(f"✅ Found gateway: {gateway_url}")
        print(f"✅ Token URL: {token_url}")
        print(f"✅ Client ID: {client_id}")

        # Test token retrieval
        print("Testing token retrieval...")
        response = requests.post(
            token_url,
            data=f"grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}",
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ Successfully retrieved access token")
            print(f"   Token type: {token_data.get('token_type', 'N/A')}")
            print(f"   Expires in: {token_data.get('expires_in', 'N/A')} seconds")
            return True
        else:
            print(f"❌ Failed to retrieve token: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


def main():
    """Main function for connection test"""
    parser = argparse.ArgumentParser(description='Test MCP Gateway connection')
    parser.add_argument(
        '--prefix',
        type=str,
        default='reinvent',
        help='Resource prefix to use (default: reinvent)'
    )
    args = parser.parse_args()

    success = test_gateway_connection(args.prefix)

    if success:
        print("\n🎉 MCP Gateway connection test PASSED!")
        exit(0)
    else:
        print("\n💥 MCP Gateway connection test FAILED!")
        exit(1)


if __name__ == "__main__":
    main()
