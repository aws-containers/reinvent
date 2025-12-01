# Try relative import first, fall back to absolute import
try:
    from . import utils
except ImportError:
    import utils

import boto3
from bedrock_agentcore.services.identity import IdentityClient
from bedrock_agentcore.identity.auth import requires_access_token

def get_or_create_cognito(prefix="reinvent"):
    USER_POOL_NAME = f'{prefix}-agentcore-gateway-pool'
    RESOURCE_SERVER_ID = f'{prefix}-agentcore-gateway-id'
    RESOURCE_SERVER_NAME = f'{prefix}-agentcore-gateway-name'
    CLIENT_NAME = f'{prefix}-agentcore-gateway-client'
    SCOPES = [
        {"ScopeName": "gateway:read", "ScopeDescription": "Read access"},
        {"ScopeName": "gateway:write", "ScopeDescription": "Write access"}
    ]

    cognito = boto3.client("cognito-idp")

    print("Creating or retrieving Cognito resources...")
    user_pool_id, domain, token_url, cognito_discovery_url = utils.get_or_create_user_pool(cognito, USER_POOL_NAME)
    print(f"User Pool ID: {user_pool_id}")
    print(f"Domain: {domain}")
    print(f"Token URL: {token_url}")
    print(f"Cognito Discovery URL: {cognito_discovery_url}")

    utils.get_or_create_resource_server(cognito, user_pool_id, RESOURCE_SERVER_ID, RESOURCE_SERVER_NAME, SCOPES)
    print("Resource server ensured.")

    client_id, client_secret = utils.get_or_create_m2m_client(cognito, user_pool_id, CLIENT_NAME, RESOURCE_SERVER_ID)
    print(f"Client ID: {client_id}")

    return user_pool_id, client_id, client_secret, cognito_discovery_url, token_url


def create_identity_provider(client_id, client_secret,token_endpoint,issuer,authorization_endpoint):
    region = "us-west-2"
    identity_client = IdentityClient(region)

    # Configure GitHub OAuth2 provider - On-Behalf-Of User
    cognito_provider = identity_client.create_oauth2_credential_provider({
        "name": "reinvent-cognito-gateway-provider",
        "credentialProviderVendor": "CognitoOauth2",
        "oauth2ProviderConfigInput": {
            "includedOauth2ProviderConfig": {
                "clientId": client_id,
                "clientSecret": client_secret,
                "tokenEndpoint": token_endpoint,
                "issuer": issuer,
                "authorizationEndpoint": authorization_endpoint
            }
        }
    })

def main():
    region = "us-west-2"
    user_pool_id, client_id, client_secret, cognito_discovery_url, token_url = get_or_create_cognito()
    # authorization_endpoint is same as token_url but replacing the last /token with /authorize
    authorization_endpoint = token_url.replace("/token", "/authorize")
    print(f"authorization_endpoint: {authorization_endpoint}")
    response = create_identity_provider(
        client_id=client_id,
        client_secret=client_secret,
        token_endpoint=token_url,
        issuer=f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}",
        authorization_endpoint=authorization_endpoint
    )
    print(f"response {response}")


def get_access_token():
    prefix="reinvent"
    RESOURCE_SERVER_ID = f'{prefix}-agentcore-gateway-id'

    @requires_access_token(
        provider_name="reinvent-cognito-gateway-provider",
        auth_flow="M2M",
        scopes=[f"{RESOURCE_SERVER_ID}/gateway:read", f"{RESOURCE_SERVER_ID}/gateway:write"],
    )
    def test_access_token(access_token):
        print(f"access_token: {access_token}")
    test_access_token()


if __name__ == "__main__":
    get_access_token()


# {
#   "authorization_endpoint": "https://us-west-2x6guupcf1.auth.us-west-2.amazoncognito.com/oauth2/authorize",
#   "end_session_endpoint": "https://us-west-2x6guupcf1.auth.us-west-2.amazoncognito.com/logout",
#   "id_token_signing_alg_values_supported": [
#     "RS256"
#   ],
#   "issuer": "https://cognito-idp.us-west-2.amazonaws.com/us-west-2_x6GUuPCf1",
#   "jwks_uri": "https://cognito-idp.us-west-2.amazonaws.com/us-west-2_x6GUuPCf1/.well-known/jwks.json",
#   "response_types_supported": [
#     "code",
#     "token"
#   ],
#   "revocation_endpoint": "https://us-west-2x6guupcf1.auth.us-west-2.amazoncognito.com/oauth2/revoke",
#   "scopes_supported": [
#     "openid",
#     "email",
#     "phone",
#     "profile"
#   ],
#   "subject_types_supported": [
#     "public"
#   ],
#   "token_endpoint": "https://us-west-2x6guupcf1.auth.us-west-2.amazoncognito.com/oauth2/token",
#   "token_endpoint_auth_methods_supported": [
#     "client_secret_basic",
#     "client_secret_post"
#   ],
#   "userinfo_endpoint": "https://us-west-2x6guupcf1.auth.us-west-2.amazoncognito.com/oauth2/userInfo"
# }
