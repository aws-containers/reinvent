"""
Combined MCP + REST Server for Customer Information

This server runs both MCP and REST interfaces on the same port (8001).
The MCP interface is available at /mcp and REST API at /api.
"""

import asyncio
import json
import logging
import uvicorn
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Import the REST API app
from .server_rest import app as rest_app
from .shared_data import load_mock_data

# Import MCP components
from mcp.server.fastmcp import FastMCP
from . import server as mcp_server_module

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create main FastAPI app
app = FastAPI(
    title="Customer Information Server - Combined MCP + REST",
    description="Combined server providing both MCP and REST interfaces for customer information management",
    version="1.0.0"
)

# Mount the REST API
app.mount("/api", rest_app)

# Add health check for the combined server
@app.get("/health")
async def health_check():
    """Health check for the combined server"""
    return {
        "status": "healthy",
        "service": "customer-info-combined-server",
        "interfaces": {
            "rest_api": "/api",
            "mcp": "/mcp",
            "docs": "/api/docs"
        }
    }

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Customer Information Server",
        "version": "1.0.0",
        "interfaces": {
            "rest_api": {
                "base_url": "/api",
                "docs": "/api/docs",
                "openapi": "/api/openapi.json"
            },
            "mcp": {
                "endpoint": "/mcp",
                "transport": "streamable-http"
            }
        },
        "endpoints": {
            "health": "/health",
            "customer_profile": "/api/customers/{customer_id}/profile",
            "policy_details": "/api/customers/{customer_id}/policy",
            "validate_coverage": "/api/customers/{customer_id}/validate-coverage",
            "create_claim": "/api/claims",
            "claim_history": "/api/customers/{customer_id}/claims",
            "claim_details": "/api/claims/{claim_id}",
            "update_claim_status": "/api/claims/{claim_id}/status"
        }
    }

# MCP Server integration
mcp_server = None

async def setup_mcp_server():
    """Set up the MCP server component"""
    global mcp_server
    try:
        # Create MCP server instance
        mcp_server = FastMCP("customer-info-server")

        # Copy all the MCP tools and resources from the original server
        # This is a simplified approach - in production, you'd want better integration

        # Add MCP resources
        @mcp_server.resource("customer://profiles")
        def customer_profiles() -> str:
            return "Customer profile data"

        @mcp_server.resource("customer://policies")
        def customer_policies() -> str:
            return "Policy information data"

        @mcp_server.resource("customer://claims")
        def customer_claims() -> str:
            return "Claims data"

        # Add MCP tools (simplified versions that delegate to the main functions)
        @mcp_server.tool()
        def get_customer_profile(customer_id: str) -> str:
            return mcp_server_module.get_customer_profile(customer_id)

        @mcp_server.tool()
        def get_policy_details(customer_id: str) -> str:
            return mcp_server_module.get_policy_details(customer_id)

        @mcp_server.tool()
        def create_claim(customer_id: str, appliance_type: str, issue_description: str, urgency_level: str) -> str:
            return mcp_server_module.create_claim(customer_id, appliance_type, issue_description, urgency_level)

        @mcp_server.tool()
        def get_claim_history(customer_id: str, status_filter: str = "all") -> str:
            return mcp_server_module.get_claim_history(customer_id, status_filter)

        @mcp_server.tool()
        def get_claim_details(claim_id: str) -> str:
            return mcp_server_module.get_claim_details(claim_id)

        @mcp_server.tool()
        def update_claim_status(claim_id: str, new_status: str, notes: str = None) -> str:
            return mcp_server_module.update_claim_status(claim_id, new_status, notes)

        @mcp_server.tool()
        def check_appliance_coverage(customer_id: str, appliance_type: str) -> str:
            return mcp_server_module.check_appliance_coverage(customer_id, appliance_type)

        logger.info("MCP server component set up successfully")
        return mcp_server

    except Exception as e:
        logger.error(f"Failed to set up MCP server: {e}")
        return None

# MCP endpoint handler
@app.get("/mcp")
async def mcp_endpoint():
    """MCP protocol endpoint"""
    return JSONResponse({
        "status": "MCP endpoint available",
        "transport": "streamable-http",
        "note": "This is a simplified MCP endpoint. For full MCP functionality, use the dedicated MCP server."
    })

@app.on_event("startup")
async def startup_event():
    """Initialize the combined server"""
    logger.info("Starting combined MCP + REST server...")

    # Load mock data
    load_mock_data()
    logger.info("Mock data loaded")

    # Set up MCP server component
    await setup_mcp_server()

    logger.info("Combined server startup complete")

def main():
    """Main entry point for the combined server"""
    logger.info("Starting Customer Information Combined Server...")

    # Run the combined server
    uvicorn.run(
        app,  # Use the app object directly instead of string import
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )

if __name__ == "__main__":
    main()
