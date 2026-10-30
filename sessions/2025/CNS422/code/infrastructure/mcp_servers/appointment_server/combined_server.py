"""
Combined MCP + REST Server for Appointment Management

This server runs both MCP and REST interfaces on the same port (8002).
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
    title="Appointment Management Server - Combined MCP + REST",
    description="Combined server providing both MCP and REST interfaces for appointment management",
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
        "service": "appointment-management-combined-server",
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
        "service": "Appointment Management Server",
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
            "list_appointments": "/api/appointments/{customer_id}",
            "create_appointment": "/api/appointments",
            "update_appointment": "/api/appointments/{appointment_id}",
            "cancel_appointment": "/api/appointments/{appointment_id}",
            "available_slots": "/api/appointments/available-slots",
            "reschedule_appointment": "/api/appointments/{appointment_id}/reschedule",
            "appointment_details": "/api/appointments/{appointment_id}/details"
        }
    }

# MCP Server integration
mcp_server = None

async def setup_mcp_server():
    """Set up the MCP server component"""
    global mcp_server
    try:
        # Create MCP server instance
        mcp_server = FastMCP("appointment-management-server")

        # Add MCP resources
        @mcp_server.resource("appointment://schedules")
        def appointment_schedules() -> str:
            return "Appointment scheduling data"

        @mcp_server.resource("appointment://availability")
        def appointment_availability() -> str:
            return "Availability data"

        @mcp_server.resource("appointment://status")
        def appointment_status() -> str:
            return "Status tracking data"

        # Add MCP tools (delegate to the main functions)
        @mcp_server.tool()
        def list_appointments(customer_id: str, status_filter: str = "all") -> str:
            return mcp_server_module.list_appointments(customer_id, status_filter)

        @mcp_server.tool()
        def create_appointment(
            customer_id: str,
            technician_id: str,
            appliance_type: str,
            issue_description: str,
            scheduled_datetime: str,
            estimated_duration: int = 90,
            claim_id: str = None
        ) -> str:
            return mcp_server_module.create_appointment(
                customer_id, technician_id, appliance_type, issue_description,
                scheduled_datetime, estimated_duration, claim_id
            )

        @mcp_server.tool()
        def update_appointment(appointment_id: str, updates: str) -> str:
            return mcp_server_module.update_appointment(appointment_id, updates)

        @mcp_server.tool()
        def cancel_appointment(appointment_id: str, reason: str = "Customer request") -> str:
            return mcp_server_module.cancel_appointment(appointment_id, reason)

        @mcp_server.tool()
        def get_available_slots(
            date_range_start: str,
            date_range_end: str,
            appliance_type: str,
            duration_minutes: int = 90
        ) -> str:
            return mcp_server_module.get_available_slots(
                date_range_start, date_range_end, appliance_type, duration_minutes
            )

        @mcp_server.tool()
        def reschedule_appointment(appointment_id: str, new_datetime: str) -> str:
            return mcp_server_module.reschedule_appointment(appointment_id, new_datetime)

        @mcp_server.tool()
        def get_appointment_details(appointment_id: str) -> str:
            return mcp_server_module.get_appointment_details(appointment_id)

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
    logger.info("Starting Appointment Management Combined Server...")

    # Run the combined server
    uvicorn.run(
        app,  # Use the app object directly instead of string import
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )

if __name__ == "__main__":
    main()
