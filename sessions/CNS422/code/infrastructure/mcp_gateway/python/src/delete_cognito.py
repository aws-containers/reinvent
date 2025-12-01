#!/usr/bin/env python3
"""
Utility script to delete Cognito resources (User Pool, Domain, Clients, Resource Server).
Useful for testing and cleanup operations.

Usage:
    uv run python delete_cognito.py [prefix]

If no prefix is provided, it will use the default 'reinvent' prefix.
This will delete:
- User Pool Client
- Resource Server
- User Pool Domain
- User Pool

Note: Resources are deleted in the correct order to handle dependencies.
"""

import sys
import boto3
import time
from src.utils import get_current_region
from botocore.exceptions import ClientError

def delete_cognito_resources(prefix="reinvent"):
    """Delete all Cognito resources for the given prefix"""

    USER_POOL_NAME = f'{prefix}-agentcore-gateway-pool'
    RESOURCE_SERVER_ID = f'{prefix}-agentcore-gateway-id'
    CLIENT_NAME = f'{prefix}-agentcore-gateway-client'

    region = get_current_region()
    cognito = boto3.client("cognito-idp", region_name=region)

    print(f"Deleting Cognito resources with prefix: {prefix}")
    print(f"Region: {region}")

    # First, find the user pool
    user_pool_id = None
    try:
        response = cognito.list_user_pools(MaxResults=60)
        for pool in response["UserPools"]:
            if pool["Name"] == USER_POOL_NAME:
                user_pool_id = pool["Id"]
                print(f"Found User Pool: {USER_POOL_NAME} (ID: {user_pool_id})")
                break

        if not user_pool_id:
            print(f"No User Pool found with name: {USER_POOL_NAME}")
            return

    except ClientError as e:
        print(f"Error listing user pools: {e}")
        return

    # Delete User Pool Client
    try:
        clients_response = cognito.list_user_pool_clients(UserPoolId=user_pool_id, MaxResults=60)
        for client in clients_response["UserPoolClients"]:
            if client["ClientName"] == CLIENT_NAME:
                print(f"Deleting User Pool Client: {CLIENT_NAME}")
                cognito.delete_user_pool_client(
                    UserPoolId=user_pool_id,
                    ClientId=client["ClientId"]
                )
                print("User Pool Client deleted successfully")
                break
    except ClientError as e:
        print(f"Error deleting user pool client: {e}")

    # Delete Resource Server
    try:
        print(f"Deleting Resource Server: {RESOURCE_SERVER_ID}")
        cognito.delete_resource_server(
            UserPoolId=user_pool_id,
            Identifier=RESOURCE_SERVER_ID
        )
        print("Resource Server deleted successfully")
    except ClientError as e:
        if e.response['Error']['Code'] != 'ResourceNotFoundException':
            print(f"Error deleting resource server: {e}")
        else:
            print("Resource Server not found (already deleted or doesn't exist)")

    # Delete User Pool Domain
    try:
        # Get domain name from user pool
        user_pool_response = cognito.describe_user_pool(UserPoolId=user_pool_id)
        domain = user_pool_response.get('UserPool', {}).get('Domain')

        if not domain:
            # Construct domain from user_pool_id if not found
            domain = user_pool_id.replace("_", "").lower()

        print(f"Deleting User Pool Domain: {domain}")
        cognito.delete_user_pool_domain(
            Domain=domain,
            UserPoolId=user_pool_id
        )
        print("User Pool Domain deleted successfully")

        # Wait a bit for domain deletion to propagate
        time.sleep(5)

    except ClientError as e:
        if e.response['Error']['Code'] != 'ResourceNotFoundException':
            print(f"Error deleting user pool domain: {e}")
        else:
            print("User Pool Domain not found (already deleted or doesn't exist)")

    # Delete User Pool (must be last)
    try:
        print(f"Deleting User Pool: {USER_POOL_NAME}")
        cognito.delete_user_pool(UserPoolId=user_pool_id)
        print("User Pool deleted successfully")
    except ClientError as e:
        print(f"Error deleting user pool: {e}")

    print("Cognito cleanup completed")

def main():
    # Check if prefix was provided as argument
    if len(sys.argv) > 1:
        prefix = sys.argv[1]
        print(f"Using provided prefix: {prefix}")
    else:
        prefix = "reinvent"
        print(f"Using default prefix: {prefix}")

    try:
        delete_cognito_resources(prefix)
    except Exception as e:
        print(f"Unexpected error during cleanup: {e}")

if __name__ == "__main__":
    main()
