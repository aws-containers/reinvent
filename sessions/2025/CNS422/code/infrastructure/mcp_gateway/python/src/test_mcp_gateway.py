from strands import Agent
import logging
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
import os
import requests
import json
from bedrock_agentcore.identity.auth import requires_access_token

# Try relative import first, fall back to absolute import
try:
    from . import setup
except ImportError:
    import setup

def get_gateway_credentials(prefix="reinvent"):
    """Get or create the gateway credentials using setup.py functions"""
    print("Getting or creating gateway credentials...")

    # Get or create IAM role
    agentcore_gateway_iam_role = setup.get_or_create_agentcore_gateway_role(prefix)

    # Get or create Cognito resources
    user_pool_id, client_id, client_secret, cognito_discovery_url, token_url = setup.get_or_create_cognito(prefix)

    # Get or create gateway
    gateway_id, gateway_url = setup.get_or_create_gateway(
        client_id=client_id,
        cognito_discovery_url=cognito_discovery_url,
        agentcore_gateway_iam_role=agentcore_gateway_iam_role,
        prefix=prefix
    )

    return client_id, client_secret, token_url, gateway_url

def fetch_access_token(client_id, client_secret, token_url):
    response = requests.post(
        token_url,
        data=f"grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}",
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    return response.json()['access_token']


@requires_access_token(
    provider_name="reinvent-cognito-gateway-provider",
    auth_flow="M2M",
    scopes=["reinvent-agentcore-gateway-id/gateway:read", "reinvent-agentcore-gateway-id/gateway:write"],
)
def create_streamable_http_transport(mcp_url: str = "https://reinvent-appmod-insurance-e1qpbpfbkt.gateway.bedrock-agentcore.us-west-2.amazonaws.com/mcp", access_token: str = None):
       return streamablehttp_client(mcp_url, headers={"Authorization": f"Bearer {access_token}"})


def get_full_tools_list():
    """
    List tools w/ support for pagination
    """

    client = MCPClient(lambda: create_streamable_http_transport())
    client.start()
    more_tools = True
    tools = []
    pagination_token = None
    while more_tools:
        tmp_tools = client.list_tools_sync(pagination_token=pagination_token)
        tools.extend(tmp_tools)
        if tmp_tools.pagination_token is None:
            more_tools = False
        else:
            more_tools = True
            pagination_token = tmp_tools.pagination_token
    print(f"Found the following tools: {[tool.tool_name for tool in tools]}")



def run_agent(message="Hi, describe how can you help me based on the tools you have available")-> dict:

    # Get credentials from setup functions
    client_id, client_secret, token_url, gateway_url = get_gateway_credentials()

    print(f"Using Gateway URL: {gateway_url}")
    print(f"Using Token URL: {token_url}")
    print(f"Using Client ID: {client_id}")

    # Get access token and run agent
    access_token = fetch_access_token(client_id, client_secret, token_url)

    mcp_client = MCPClient(lambda: create_streamable_http_transport(gateway_url, access_token))
    with mcp_client:
        agent = Agent(
            model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            system_prompt="You are a helpful assistant. always say the tool you are using and the parameters your using with the tool",
            tools=mcp_client.list_tools_sync()
        )
        return agent(message)

def main():
    """Main function to test MCP Gateway"""

    # Test 0: List available tools
    print("\n=== Test 1: No prompt ===")
    get_full_tools_list()

    # # Test 1: List available tools
    # print("\n=== Test 1: Listing available tools ===")
    # run_agent("Hi, can you list all tools available to you")

    # # Test 2: Customer information query
    # print("\n=== Test 2: Customer information query ===")
    # run_agent("I am customer CUST001, tell me about my claims, status of the appointments with info of technician name and contact info, and corresponding claim ID")




if __name__ == "__main__":
    main()
