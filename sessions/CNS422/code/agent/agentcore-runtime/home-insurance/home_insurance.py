
import logging
import os
from strands_tools.calculator import calculator
from strands import Agent
from strands.multiagent.a2a import A2AServer
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# From Gateway example
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
import requests
import json

import asyncio
import boto3
from contextlib import asynccontextmanager
from datetime import timedelta
import uuid

from bedrock_agentcore.runtime import BedrockAgentCoreContext
from bedrock_agentcore.identity.auth import requires_access_token

from context import AgentContext

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

agentcore_client = boto3.client("bedrock-agentcore")

# Model Configuration
MODEL_ID = os.getenv("MODEL_ID", "global.anthropic.claude-sonnet-4-20250514-v1:0")
# Other Options: "global.anthropic.claude-haiku-4-5-20251001-v1:0", "us.anthropic.claude-3-7-sonnet-20250219-v1:0", "global.anthropic.claude-sonnet-4-20250514-v1:0"
MODEL_REGION = os.getenv("MODEL_REGION","us-west-2")

################################################################################################
# Part A: Gateway Configuration Setup
# Description:
# Loads MCP Gateway configuration from AWS SSM Parameter Store or environment variables.
# This includes the identity provider name, resource server ID, and gateway URL needed
# for authentication and connection. These settings enable secure communication with the
# MCP Gateway, which acts as a bridge between our AI agent and the backend MCP servers.
################################################################################################
def get_gateway_config():
    """Retrieve gateway configuration from SSM Parameter Store or environment variables."""
    ssm_client = boto3.client('ssm')
    prefix = "reinvent"  # Match the prefix used in setup.py

    def get_param(param_name, env_var_name):
        """Get parameter from env var first, then SSM, with no fallback."""
        # Check environment variable first (for testing/override)
        env_value = os.getenv(env_var_name)
        if env_value:
            logger.info(f"Using {env_var_name} from environment variable")
            return env_value

        # Retrieve from SSM Parameter Store
        try:
            response = ssm_client.get_parameter(Name=f'/{prefix}/gateway/{param_name}')
            logger.info(f"Retrieved {param_name} from SSM Parameter Store")
            return response['Parameter']['Value']
        except Exception as e:
            logger.error(f"Failed to retrieve {param_name} from SSM: {e}")
            raise ValueError(f"Gateway configuration '{param_name}' not found in environment or SSM Parameter Store")

    return {
        'provider_name': get_param('identity_provider_name', 'GATEWAY_PROVIDER_NAME'),
        'resource_server_id': get_param('resource_server_id', 'GATEWAY_RESOURCE_SERVER_ID'),
        'mcp_url': get_param('mcp_url', 'GATEWAY_MCP_URL')
    }

# Load gateway configuration
gateway_config = get_gateway_config()
GATEWAY_PROVIDER_NAME = gateway_config['provider_name']
GATEWAY_RESOURCE_SERVER_ID = gateway_config['resource_server_id']
GATEWAY_MCP_URL = gateway_config['mcp_url']


# create variable boolean running_local to true if the env AGENTCORE_RUNTIME_URL is not set
running_local = os.environ.get("AGENTCORE_RUNTIME_URL") is None

# Use the complete runtime URL from environment variable, fallback to local
runtime_url = os.environ.get("AGENTCORE_RUNTIME_URL", "http://127.0.0.1:9000/")
host, port = "0.0.0.0", 9000
logger.info(f"Configuration loaded - Runtime URL: {runtime_url}")

# Initialization lock to prevent race conditions
initialization_lock = asyncio.Lock()

def get_gateway_url() -> str:
    """Lazy load gateway URL from SSM."""
    return GATEWAY_MCP_URL

################################################################################################
# Part B:  MCP Client with Authorization token injected
# Description:
# Creates an MCP client configured with the authorization token from Part A.
# This client establishes a secure connection to the MCP Gateway and enables
# the AI agent to discover and invoke tools from all connected MCP servers.
################################################################################################
@requires_access_token(
    provider_name=GATEWAY_PROVIDER_NAME,
    scopes=[f"{GATEWAY_RESOURCE_SERVER_ID}/gateway:read", f"{GATEWAY_RESOURCE_SERVER_ID}/gateway:write"],
    auth_flow="M2M",
    into="gateway_access_token"
)
def create_gateway_client(gateway_access_token: str) -> MCPClient:
    """Create and return a gateway MCP client with OAuth2 authentication."""
    url = get_gateway_url()

    logger.info("Gateway access token obtained successfully")
    return MCPClient(
        lambda: streamablehttp_client(
            url=url,
            headers={"Authorization": f"Bearer {gateway_access_token}"},
            timeout=timedelta(seconds=120),
        )
    )

bedrock_model = BedrockModel(
    model_id=MODEL_ID,
    region_name=MODEL_REGION,
)



# Lifespan context manager for shutdown cleanup
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

    # Shutdown: Stop gateway client if it was initialized
    logger.info("Shutting down...")
    gateway_client = AgentContext.get_gateway_client()
    if gateway_client:
        logger.info("Stopping gateway client...")
        gateway_client.stop()
        logger.info("Gateway client stopped successfully")

app = FastAPI(title="Agent A2A Server", lifespan=lifespan)


################################################################################################
# Part C: Create the AI Agent with A2A Server
# Description:
# Initializes the AI Agent using the MCP client from Part B to access backend tools.
# The agent uses Strands SDK with Bedrock models to orchestrate conversations and execute
# tools for customer service, appointment scheduling, and technician tracking. The A2A
# (Agent-to-Agent) server exposes the agent via HTTP, enabling integration with AgentCore
# runtime and communication with other agents or external systems.
################################################################################################
@app.middleware("http")
async def capture_session_id(request: Request, call_next):
    # Print all the headers one per line and sorted
    logger.info(f"Request headers: {request.headers}")
    sorted_headers = sorted(request.headers.items())
    for header_name, header_value in sorted_headers:
        logger.info(f"{header_name}: {header_value}")

    # Capture workload identity token if present
    if request.headers.get("x-amzn-bedrock-agentcore-runtime-workload-accesstoken"):
        token = request.headers.get(
            "x-amzn-bedrock-agentcore-runtime-workload-accesstoken"
        )
        # This is done for the AgentCore SDK be able to access the identity token
        BedrockAgentCoreContext.set_workload_access_token(token)
        logger.debug("Agent identity token captured from request headers")

    session_id = request.headers.get("x-amzn-bedrock-agentcore-runtime-session-id")
    host = request.headers.get("host")
    if not session_id and running_local:
        logger.info("No session ID found and running on local, generating a new one...")
        session_id = str(uuid.uuid4())

    # Set session ID in context for this request
    if session_id:
        AgentContext.set_session_id(session_id)

    # Check if this session has already been initialized
    agent = AgentContext.get_agent()

    #debug
    logger.info(f"Session ID: {session_id}")
    logger.info(f"Agent initialized: {agent is not None}")


    # Initialize agent components if we have a session ID and haven't initialized yet
    if session_id and agent is None:
        async with initialization_lock:
            # Double-check after acquiring lock (another request might have initialized)
            if AgentContext.get_agent():
                response = await call_next(request)
                return response

            AgentContext.set_session_id(session_id)
            logger.info(
                f"Initializing agent components for session: {session_id[:8]}..."
            )


            # Initialize and start gateway client (needs request context for access token)
            logger.info("Initializing gateway client...")
            gateway_client = create_gateway_client()
            gateway_client.start()
            AgentContext.set_gateway_client(gateway_client)
            logger.info("Gateway client started successfully")

            # Get gateway tools from MCP client
            gateway_tools = gateway_client.list_tools_sync()
            logger.info(f"Loaded {len(gateway_tools)} tools from gateway client")

            # Create strands agent with gateway tools
            strands_agent = Agent(
                name="Home Insurance Agent",
                description="Home Insurance Agent that help customers",
                system_prompt="you are a very polite Home Insurance Assitant that uses the tools available to help the customer with their request",
                model=bedrock_model,
                tools=gateway_tools
            )
            AgentContext.set_agent(strands_agent)
            logger.info(
                f"Strands Agent created with {len(gateway_tools)} tools"
            )

            # Create A2A server with the initialized agent
            a2a_server = A2AServer(
                agent=strands_agent,
                http_url=runtime_url,
                serve_at_root=True,
                host=host,
                port=port,
                version="1.0.0",
            )
            AgentContext.set_a2a_server(a2a_server)
            logger.info("A2A Server created successfully")

    response = await call_next(request)
    return response

@app.get("/ping")
def ping():
    """Health check endpoint with agent status."""
    return {"status": "healthy"}

# Conditional mount - only mount if a2a_server is initialized
@app.middleware("http")
async def mount_a2a_conditionally(request: Request, call_next):
    a2a_server = AgentContext.get_a2a_server()

    # If a2a_server exists and hasn't been mounted yet, log readiness
    if a2a_server is not None and not hasattr(app, "_a2a_mounted"):
        # Mark as mounted to avoid re-logging
        app._a2a_mounted = True
        logger.info("A2A server ready to handle requests")

    response = await call_next(request)
    return response


# Handle routing - check if a2a_server exists before forwarding
@app.api_route(
    "/{full_path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
)
async def proxy_to_a2a(request: Request):
    """Proxy requests to the A2A server once initialized."""
    a2a_server = AgentContext.get_a2a_server()

    if a2a_server is None:
        return JSONResponse(
            status_code=503,
            content={
                "error": "Agent not initialized",
                "message": "Waiting for session ID to initialize agent",
            },
        )

    # Forward request to a2a_server
    a2a_app = a2a_server.to_fastapi_app()
    return await a2a_app(request.scope, request.receive, request._send)


if __name__ == "__main__":
    uvicorn.run(app, host=host, port=port)
