# Try relative import first, fall back to absolute import
try:
    from . import utils
except ImportError:
    import utils

import os
import boto3
import requests
import time
import argparse
from pprint import pprint
from botocore.exceptions import ClientError
from bedrock_agentcore.services.identity import IdentityClient

# Where is our EKS REST API domain
REST_API_DOMAIN = os.getenv("DOMAIN_NAME")
if not REST_API_DOMAIN:
    raise ValueError("DOMAIN_NAME environment variable must be set")


# Create an S3 client
session = boto3.session.Session()
sts_client = session.client('sts')

# Retrieve AWS account ID and region
ACCOUNT_ID = sts_client.get_caller_identity()["Account"]
REGION = utils.get_current_region()


#    scopeString = f"{RESOURCE_SERVER_ID}/gateway:read {RESOURCE_SERVER_ID}/gateway:write"

def get_or_create_agentcore_gateway_role(prefix="reinvent"):
    agentcore_gateway_iam_role = utils.create_agentcore_gateway_role(f'{prefix}-mcpgateway')
    print("Agentcore gateway role ARN: ", agentcore_gateway_iam_role['Role']['Arn'])
    return agentcore_gateway_iam_role


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

    return user_pool_id, client_id, client_secret, cognito_discovery_url, token_url, RESOURCE_SERVER_ID


def get_or_create_gateway(client_id, cognito_discovery_url, agentcore_gateway_iam_role, prefix="reinvent"):
    GATEWAY_NAME = f'{prefix}-AppMod-Insurance'
    gateway_client = boto3.client('bedrock-agentcore-control')

    # Check if gateway already exists
    try:
        list_response = gateway_client.list_gateways(maxResults=100)
        for gateway in list_response.get('items', []):
            if gateway.get('name') == GATEWAY_NAME:
                gatewayID = gateway['gatewayId']

                # Get detailed gateway information to retrieve the URL
                try:
                    gateway_details = gateway_client.get_gateway(gatewayIdentifier=gatewayID)
                    gatewayURL = gateway_details.get('gatewayUrl', 'URL_NOT_AVAILABLE')
                except ClientError as detail_error:
                    print(f"Warning: Could not get gateway details: {detail_error}")
                    gatewayURL = "URL_NOT_AVAILABLE"

                print(f"Gateway '{GATEWAY_NAME}' already exists with ID: {gatewayID}")
                print(f"Gateway URL: {gatewayURL}")
                return gatewayID, gatewayURL
    except ClientError as e:
        print(f"Error checking existing gateways: {e}")
        # Continue to create new gateway if listing fails

    # Create new gateway if it doesn't exist
    print(f"Creating new gateway: {GATEWAY_NAME}")
    auth_config = {
        "customJWTAuthorizer": {
            "allowedClients": [client_id],  # Client MUST match with the ClientId configured in Cognito. Example: 7rfbikfsm51j2fpaggacgng84g
            "discoveryUrl": cognito_discovery_url
        }
    }

    try:
        create_response = gateway_client.create_gateway(
            name=GATEWAY_NAME,
            roleArn=agentcore_gateway_iam_role['Role']['Arn'], # The IAM Role must have permissions to create/list/get/delete Gateway
            protocolType='MCP',
            authorizerType='CUSTOM_JWT',
            authorizerConfiguration=auth_config,
            description='AgentCore Gateway with OpenAPI target'
        )
        #pprint(create_response)
        # Retrieve the GatewayID used for GatewayTarget creation
        gatewayID = create_response["gatewayId"]
        gatewayURL = create_response["gatewayUrl"]
        print(f"Created new gateway with ID: {gatewayID}")
        print(f"Gateway URL: {gatewayURL}")
        return gatewayID, gatewayURL
    except ClientError as e:
        raise e

def get_or_create_gateway_target(credentialProviderARN, openapi_s3_uri, targetname, description, gatewayID):
    gateway_client = boto3.client('bedrock-agentcore-control')

    # Check if gateway target already exists
    try:
        list_response = gateway_client.list_gateway_targets(
            gatewayIdentifier=gatewayID,
            maxResults=100
        )
        for target in list_response.get('items', []):
            if target.get('name') == targetname:
                targetID = target['targetId']
                print(f"Gateway target '{targetname}' already exists with ID: {targetID}")
                return target
    except ClientError as e:
        print(f"Error checking existing gateway targets: {e}")
        # Continue to create new target if listing fails

    # Create new gateway target if it doesn't exist
    print(f"Creating new gateway target: {targetname}")

    # API Key credentials provider configuration
    api_key_credential_config = [
        {
            "credentialProviderType" : "API_KEY",
            "credentialProvider": {
                "apiKeyCredentialProvider": {
                        "credentialParameterName": "api_key_", # Replace this with the name of the api key name expected by the respective API provider. For passing token in the header, use "Authorization"
                        "providerArn": credentialProviderARN,
                        "credentialLocation":"QUERY_PARAMETER", # Location of api key. Possible values are "HEADER" and "QUERY_PARAMETER".
                        #"credentialPrefix": " " # Prefix for the token. Valid values are "Basic". Applies only for tokens.
                }
            }
        }
    ]
    # S3 Uri for OpenAPI spec file
    openapi_s3_target_config_appointment = {
        "mcp": {
            "openApiSchema": {
                "s3": {
                    "uri": openapi_s3_uri
                }
            }
        }
    }

    try:
        response = gateway_client.create_gateway_target(
            gatewayIdentifier=gatewayID,
            name=targetname,
            description=description,
            targetConfiguration=openapi_s3_target_config_appointment,
            credentialProviderConfigurations=api_key_credential_config)
        print(f"Created new gateway target '{targetname}' with ID: {response.get('targetId')}")
        time.sleep(3)
        return response
    except ClientError as e:
        raise e





def get_or_create_key_credential_provider(prefix="reinvent"):
    KEY_PROVIDER_NAME = f'{prefix}-AppMod-Insurance'
    acps = boto3.client(service_name="bedrock-agentcore-control")

    def find_existing_provider():
        """Helper function to find existing provider with pagination support"""
        try:
            # Try with pagination to ensure we get all providers
            paginator = acps.get_paginator('list_api_key_credential_providers')
            for page in paginator.paginate():
                for provider in page.get('items', []):
                    if provider.get('name') == KEY_PROVIDER_NAME:
                        time.sleep(3)
                        return provider['credentialProviderArn']
        except Exception as e:
            print(f"Error during paginated search: {e}")
            # Fallback to simple list
            try:
                list_response = acps.list_api_key_credential_providers(maxResults=100)
                for provider in list_response.get('items', []):
                    if provider.get('name') == KEY_PROVIDER_NAME:
                        return provider['credentialProviderArn']
            except Exception as fallback_e:
                print(f"Error in fallback search: {fallback_e}")
        return None

    # Check if credential provider already exists
    existing_arn = find_existing_provider()
    if existing_arn:
        print(f"Credential provider '{KEY_PROVIDER_NAME}' already exists with ARN: {existing_arn}")
        return existing_arn

    # Create new credential provider if it doesn't exist
    print(f"Creating new credential provider: {KEY_PROVIDER_NAME}")
    try:
        response = acps.create_api_key_credential_provider(
            name=KEY_PROVIDER_NAME,
            apiKey="111223334455",
        )

        #pprint(response)
        credentialProviderARN = response['credentialProviderArn']
        print(f"Created new credential provider with ARN: {credentialProviderARN}")
        return credentialProviderARN
    except ClientError as e:
        if e.response['Error']['Code'] == 'ValidationException' and 'already exists' in e.response['Error']['Message']:
            # Provider exists but wasn't found in list - try one more time with a delay
            print(f"Credential provider '{KEY_PROVIDER_NAME}' already exists but wasn't found in list. Retrying search...")
            time.sleep(2)  # Brief delay for eventual consistency
            existing_arn = find_existing_provider()
            if existing_arn:
                print(f"Found existing credential provider with ARN: {existing_arn}")
                return existing_arn
            else:
                print(f"Warning: Could not retrieve existing credential provider '{KEY_PROVIDER_NAME}' after retry")
                print("This may be due to eventual consistency or permissions issues.")
                print("Continuing with execution - the credential provider exists but ARN is unknown.")
                # Return a placeholder ARN since we know it exists but can't retrieve it
                # This allows the script to continue rather than failing
                boto_session = boto3.Session()
                region = boto_session.region_name or utils.get_current_region()
                account_id = boto3.client("sts").get_caller_identity()["Account"]
                placeholder_arn = f"arn:aws:bedrock-agentcore:{region}:{account_id}:credential-provider/{KEY_PROVIDER_NAME}"
                print(f"Using placeholder ARN: {placeholder_arn}")
                return placeholder_arn
        else:
            raise e

def upload_openapi_to_s3(bucket_name, url_path, object_key, api_url):
    """
    Download OpenAPI JSON from URL, modify it to add servers array, and upload to S3 bucket.

    Args:
        bucket_name: Name of the S3 bucket
        url_path: URL to download the OpenAPI JSON file from
        object_key: S3 object key (filename) for the uploaded file
        api_url: API URL to add to the servers array in the OpenAPI spec

    Returns:
        str: S3 URI of the uploaded file
    """
    import json

    s3_client = boto3.client('s3')

    try:
        # Download the JSON file from the URL
        print(f"📥 Downloading OpenAPI spec from: {url_path}")
        response = requests.get(url_path, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Parse and validate the JSON
        try:
            openapi_spec = response.json()
        except ValueError as e:
            raise ValueError(f"Downloaded content is not valid JSON: {e}")

        # Modify the OpenAPI spec to add the servers array
        print(f"🔧 Adding server URL to OpenAPI spec: {api_url}")
        openapi_spec["servers"] = [
            {
                "url": api_url
            }
        ]

        # Convert back to JSON string
        modified_json = json.dumps(openapi_spec, indent=2)

        # Check if bucket exists, create if it doesn't
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"✅ Bucket '{bucket_name}' already exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                print(f"🪣 Creating bucket '{bucket_name}'...")
                try:
                    if REGION == 'us-east-1':
                        # us-east-1 doesn't need LocationConstraint
                        s3_client.create_bucket(Bucket=bucket_name)
                    else:
                        s3_client.create_bucket(
                            Bucket=bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': REGION}
                        )
                    print(f"✅ Successfully created bucket '{bucket_name}'")
                except ClientError as create_error:
                    raise RuntimeError(f"Failed to create bucket '{bucket_name}': {create_error}")
            else:
                raise RuntimeError(f"Error checking bucket '{bucket_name}': {e}")

        # Upload the modified JSON to S3
        print(f"📤 Uploading modified OpenAPI spec to S3: s3://{bucket_name}/{object_key}")
        s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=modified_json.encode('utf-8'),
            ContentType='application/json',
            ServerSideEncryption='AES256'  # Enable server-side encryption
        )

        print(f"✅ Successfully uploaded modified OpenAPI spec to S3")
        return f's3://{bucket_name}/{object_key}'

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to download OpenAPI spec from {url_path}: {e}")
    except ClientError as e:
        raise RuntimeError(f"S3 operation failed: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error uploading to S3: {e}")

def get_or_create_identity_provider(prefix="reinvent", client_id=None, client_secret=None, token_endpoint=None, issuer=None, authorization_endpoint=None):
    IDENTITY_PROVIDER_NAME = f'{prefix}-cognito-gateway-provider'
    identity_client = IdentityClient(REGION)

    # Try to create the identity provider, if it already exists, just return success
    try:
        print(f"Creating identity provider '{IDENTITY_PROVIDER_NAME}'...")
        cognito_provider = identity_client.create_oauth2_credential_provider({
            "name": IDENTITY_PROVIDER_NAME,
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
        print(f"Identity provider created successfully")
    except ClientError as e:
        if 'already exists' in str(e):
            print(f"Identity provider '{IDENTITY_PROVIDER_NAME}' already exists")
        else:
            raise

    return IDENTITY_PROVIDER_NAME

def save_gateway_config_to_ssm(identity_provider_name, gateway_url, resource_server_id, prefix="reinvent"):
    """
    Save gateway configuration to SSM Parameter Store for easy retrieval by agents.

    Args:
        identity_provider_name: Name of the identity provider
        gateway_url: MCP Gateway URL
        resource_server_id: Cognito resource server ID
        prefix: Prefix for parameter names
    """
    ssm_client = boto3.client('ssm')

    parameters = {
        f'/{prefix}/gateway/identity_provider_name': identity_provider_name,
        f'/{prefix}/gateway/mcp_url': gateway_url,
        f'/{prefix}/gateway/resource_server_id': resource_server_id
    }

    print("\n📝 Saving gateway configuration to SSM Parameter Store...")

    for param_name, param_value in parameters.items():
        try:
            ssm_client.put_parameter(
                Name=param_name,
                Value=param_value,
                Type='String',
                Overwrite=True,
                Description=f'MCP Gateway configuration - {param_name.split("/")[-1]}'
            )
            print(f"✅ Saved parameter: {param_name}")
        except ClientError as e:
            print(f"❌ Error saving parameter {param_name}: {e}")
            raise

    print(f"✅ Successfully saved all gateway configuration to SSM Parameter Store\n")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Setup MCP Gateway with configurable REST API domain and environment')
    parser.add_argument(
        '--rest-api-domain',
        type=str,
        default=REST_API_DOMAIN,
        help=f'REST API domain to use (default: {REST_API_DOMAIN})'
    )
    parser.add_argument(
        '--rest-api-env',
        type=str,
        default=os.getenv('REST_API_ENV', 'development'),
        help='REST API environment to use (default: dev, can be set via REST_API_ENV environment variable)'
    )
    args = parser.parse_args()

    print("Starting to setup MCP Gateway\n")
    rest_api_domain = args.rest_api_domain
    rest_api_env = args.rest_api_env
    print(f"Using REST API domain: {rest_api_domain}")
    print(f"Using REST API environment: {rest_api_env}\n")


################################################################################################
# Part A: Create the MCP Gateway
# Description: Set up the core MCP Gateway infrastructure with IAM roles, Cognito
# authentication, and identity provider. This creates the secure foundation that
# enables AI agents to communicate with backend services through a unified gateway.
################################################################################################
    agentcore_gateway_iam_role = get_or_create_agentcore_gateway_role()
    user_pool_id, client_id, client_secret, cognito_discovery_url, token_url, resource_server_id = get_or_create_cognito()
    # create the MCP Gateway
    gatewayID, gatewayURL = get_or_create_gateway(
        client_id=client_id,
        cognito_discovery_url=cognito_discovery_url,
        agentcore_gateway_iam_role=agentcore_gateway_iam_role
    )
    # Create Outbound Identity Provider
    # authorization_endpoint is same as token_url but replacing the last /token with /authorize
    authorization_endpoint = token_url.replace("/token", "/authorize")
    #print(f"authorization_endpoint: {authorization_endpoint}")
    identity_provider_name = get_or_create_identity_provider(
        client_id=client_id,
        client_secret=client_secret,
        token_endpoint=token_url,
        issuer=f"https://cognito-idp.{REGION}.amazonaws.com/{user_pool_id}",
        authorization_endpoint=authorization_endpoint
    )
    # Save key information to SSM Parameter Store
    save_gateway_config_to_ssm(
        gateway_url=gatewayURL,
        identity_provider_name=identity_provider_name,
        resource_server_id=resource_server_id
    )


################################################################################################
# Part B: Create MCP Gateway Targets for All Services
# Description: Connect all backend services (Appointment, Customer, Technician) to
# the MCP Gateway by downloading their OpenAPI specs, uploading to S3, and creating
# gateway targets. This enables AI agents to interact with all services through MCP.
################################################################################################
    credentialProviderARN = get_or_create_key_credential_provider()
    bucket_name = f'agentcore-gateway-{ACCOUNT_ID}-{REGION}'

    # Define all services to connect
    services = [
        {
            "name": "appointment",
            "description": "Appointment Management - schedule, update, and query appointments"
        },
        {
            "name": "customer",
            "description": "Customer Information - access profiles, policies, and claims data"
        },
        {
            "name": "technician",
            "description": "Technician Tracking - track locations, status, and availability"
        }
    ]

    # Create gateway targets for all services
    for service in services:
        target_name = service["name"]
        print(f"\n🔗 Setting up gateway target for {target_name} service...")

        api_url = f'https://{target_name}-{rest_api_env}.{rest_api_domain}'
        openapi_s3_uri = upload_openapi_to_s3(
            bucket_name=bucket_name,
            url_path=f'{api_url}/openapi.json',
            object_key=f'{target_name}.json',
            api_url=api_url
        )

        get_or_create_gateway_target(
            credentialProviderARN=credentialProviderARN,
            openapi_s3_uri=openapi_s3_uri,
            targetname=target_name,
            description=f'AppMod {target_name}',
            gatewayID=gatewayID
        )
        print(f"✅ Gateway target for {target_name} service configured")

    print(f"Now you can build your Agent to use MCP Gateway as URL: {gatewayURL}")





if __name__ == "__main__":
    main()
