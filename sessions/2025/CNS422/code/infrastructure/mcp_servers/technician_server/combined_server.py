"""
Combined MCP + REST Server for Technician Tracking

This server runs both MCP and REST interfaces on the same port (8003).
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
    title="Technician Tracking Server - Combined MCP + REST",
    description="Combined server providing both MCP and REST interfaces for technician location and status management",
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
        "service": "technician-tracking-combined-server",
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
        "service": "Technician Tracking Server",
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
            "technician_status": "/api/technicians/{technician_id}/status",
            "technician_location": "/api/technicians/{technician_id}/location",
            "available_technicians": "/api/technicians/available",
            "update_status": "/api/technicians/{technician_id}/status",
            "get_route": "/api/technicians/{technician_id}/route",
            "notify_status": "/api/technicians/{technician_id}/notify"
        }
    }

# MCP Server integration
mcp_server = None

async def setup_mcp_server():
    """Set up the MCP server component"""
    global mcp_server
    try:
        # Create MCP server instance
        mcp_server = FastMCP("technician-tracking-server")

        # Add MCP resources
        @mcp_server.resource("technician://status")
        def technician_status() -> str:
            return "Technician status and availability data"

        @mcp_server.resource("technician://locations")
        def technician_locations() -> str:
            return "Real-time technician location tracking"

        @mcp_server.resource("technician://routes")
        def technician_routes() -> str:
            return "Technician routing and ETA information"

        # Add MCP tools (simplified versions that delegate to the main functions)
        @mcp_server.tool()
        def get_technician_status(technician_id: str) -> str:
            return mcp_server_module.get_technician_status(technician_id)

        @mcp_server.tool()
        def get_technician_location(technician_id: str) -> str:
            return mcp_server_module.get_technician_location(technician_id)

        @mcp_server.tool()
        def list_available_technicians(area: str, datetime_str: str, specialties: list) -> str:
            return mcp_server_module.list_available_technicians(area, datetime_str, specialties)

        @mcp_server.tool()
        def update_technician_status(technician_id: str, new_status: str, location: list = None, appointment_id: str = None) -> str:
            return mcp_server_module.update_technician_status(technician_id, new_status, location, appointment_id)

        @mcp_server.tool()
        def get_technician_route(technician_id: str, destination: list) -> str:
            return mcp_server_module.get_technician_route(technician_id, destination)

        @mcp_server.tool()
        def notify_status_change(technician_id: str, appointment_id: str, status_message: str = None) -> str:
            return mcp_server_module.notify_status_change(technician_id, appointment_id, status_message)

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
    logger.info("Starting Technician Tracking Combined Server...")

    # Run the combined server
    uvicorn.run(
        app,  # Use the app object directly instead of string import
        host="0.0.0.0",
        port=8003,
        log_level="info"
    )

if __name__ == "__main__":
    main()
