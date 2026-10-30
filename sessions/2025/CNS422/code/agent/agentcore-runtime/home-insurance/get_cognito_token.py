#!/usr/bin/env python3
"""
Get AWS Cognito access token using client credentials flow.
"""

import base64
import os
import requests


def get_cognito_access_token(client_id: str, client_secret: str, cognito_domain: str) -> dict:
    """
    Get access token from AWS Cognito using client credentials.

    Args:
        client_id: Cognito app client ID
        client_secret: Cognito app client secret
        cognito_domain: Cognito domain (e.g., https://your-domain.auth.region.amazoncognito.com)

    Returns:
        dict with access_token, token_type, expires_in
    """
    # Create Basic Auth header
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_credentials}"
    }

    data = {
        "grant_type": "client_credentials"
    }

    token_url = f"{cognito_domain}/oauth2/token"

    response = requests.post(token_url, headers=headers, data=data)
    response.raise_for_status()

    return response.json()


if __name__ == "__main__":
    # Get credentials from environment variables
    CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
    CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")

    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ Error: COGNITO_CLIENT_ID and COGNITO_CLIENT_SECRET environment variables must be set")
        exit(1)

    # Cognito domain for reinvent-agentcore-gateway-pool
    COGNITO_DOMAIN = os.getenv("COGNITO_DOMAIN", "https://us-west-2x6guupcf1.auth.us-west-2.amazoncognito.com")

    try:
        token_data = get_cognito_access_token(CLIENT_ID, CLIENT_SECRET, COGNITO_DOMAIN)

        print("\n✅ Successfully obtained access token!")
        print(f"\nAccess Token: {token_data['access_token']}")
        print(f"Token Type: {token_data['token_type']}")
        print(f"Expires In: {token_data['expires_in']} seconds")

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ Error: {e}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
