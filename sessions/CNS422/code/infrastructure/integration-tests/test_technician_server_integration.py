"""
Integration tests for Technician Tracking MCP Server.

These tests run against a live technician server that should already be running.
Start the server first with: python -m mcp_servers.technician_server.server
"""

import asyncio
import json
import pytest
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from testing_framework.base_test_classes import BaseMCPStandaloneTest


class TestTechnicianServerStandalone(BaseMCPStandaloneTest):
    """Test technician server standalone connection."""

    @property
    def server_name(self) -> str:
        return "Technician Tracking Server"

    @property
    def server_port(self) -> int:
        return 8003

    @property
    def server_module_path(self) -> str:
        return "mcp_servers.technician_server.server"

    @property
    def expected_tools(self) -> set:
        return {
            "get_technician_status",
            "get_technician_location",
            "list_available_technicians",
            "update_technician_status",
            "get_technician_route",
            "notify_status_change"
        }

    @pytest.mark.asyncio
    async def test_standalone_connection(self) -> bool:
        """Test standalone connection with pytest-asyncio decorator."""
        return await super().test_standalone_connection()

    async def _test_standalone_tool_calls(self, session):
        """Test tool calls in standalone mode."""
        print(f"\n🔧 Testing {self.server_name} tool calls...")

        try:
            # Test basic technician status
            print("  📋 Testing get_technician_status...")
            result = await session.call_tool("get_technician_status", {"technician_id": "TECH001"})
            print(f"     Response: {result.content[0].text[:100]}...")

            # Test technician location
            print("  📍 Testing get_technician_location...")
            result = await session.call_tool("get_technician_location", {"technician_id": "TECH001"})
            location_data = json.loads(result.content[0].text)
            if "error" not in location_data:
                print(f"     Location: {location_data.get('current_location', {}).get('latitude', 'Unknown')}, {location_data.get('current_location', {}).get('longitude', 'Unknown')}")
            else:
                print(f"     Note: {location_data['error']}")

            # Test available technicians
            print("  🔍 Testing list_available_technicians...")
            future_time = (datetime.now() + timedelta(hours=2)).isoformat()
            result = await session.call_tool("list_available_technicians", {
                "area": "downtown",
                "datetime_str": future_time,
                "specialties": ["refrigerator"]
            })
            available_data = json.loads(result.content[0].text)
            print(f"     Found {available_data.get('total_found', 0)} available technicians")

            # Test route calculation
            print("  🗺️ Testing get_technician_route...")
            result = await session.call_tool("get_technician_route", {
                "technician_id": "TECH001",
                "destination": [41.9000, -87.6000]
            })
            route_data = json.loads(result.content[0].text)
            if "error" not in route_data:
                print(f"     Route distance: {route_data.get('distance_miles', 'Unknown')} miles")
                print(f"     Travel time: {route_data.get('estimated_travel_time_minutes', 'Unknown')} minutes")
            else:
                print(f"     Note: {route_data['error']}")

            print("  ✓ All tool calls completed successfully")

        except Exception as e:
            print(f"  ✗ Tool call error: {e}")


# Test runner function for manual execution
def test_technician_server_standalone():
    """Run standalone client test."""
    test_class = TestTechnicianServerStandalone()

    print("Running Technician Server Standalone Test...")
    print("Make sure the technician server is running on port 8003")
    print("Start with: python -m mcp_servers.technician_server.server")

    try:
        result = asyncio.run(test_class.test_standalone_connection())
        if result:
            print("✓ Standalone test passed")
        else:
            print("✗ Standalone test failed")
            assert False, "Standalone test failed"
    except Exception as e:
        print(f"✗ Standalone test error: {e}")
        assert False, f"Standalone test error: {e}"


if __name__ == "__main__":
    print("🧪 Technician Tracking MCP Server Integration Test")
    print("=" * 60)

    print("\n📝 Prerequisites:")
    print("1. Start the technician server: python -m mcp_servers.technician_server.server")
    print("2. Server should be running on http://localhost:8003")
    print("3. Run this test: python test_technician_server_integration.py")

    test_technician_server_standalone()
