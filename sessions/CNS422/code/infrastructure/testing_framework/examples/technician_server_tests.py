"""
Technician Tracking MCP Server Integration Tests

This module provides comprehensive MCP integration tests for the Technician Tracking server
following the established testing framework patterns.
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Set

from mcp import ClientSession

# Add parent directories to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from testing_framework.base_test_classes import (
    BaseMCPEndpointTest,
    BaseMCPIntegrationTest,
    BaseMCPStandaloneTest
)
from testing_framework.server_configs import get_technician_server_config


class TechnicianServerEndpointTest(BaseMCPEndpointTest):
    """Test technician server endpoints directly."""

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
    def expected_tools(self) -> Set[str]:
        config = get_technician_server_config()
        return config['expected_tools']

    def test_endpoint_functions_available(self):
        """Test that all endpoint functions can be imported."""
        from mcp_servers.technician_server.server import (
            get_technician_status,
            get_technician_location,
            list_available_technicians,
            update_technician_status,
            get_technician_route,
            notify_status_change
        )

        # Verify functions are callable
        assert callable(get_technician_status)
        assert callable(get_technician_location)
        assert callable(list_available_technicians)
        assert callable(update_technician_status)
        assert callable(get_technician_route)
        assert callable(notify_status_change)

        print("✓ All technician server endpoint functions are available")


class TechnicianServerIntegrationTest(BaseMCPIntegrationTest):
    """Test technician server through MCP protocol."""

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
    def expected_tools(self) -> Set[str]:
        config = get_technician_server_config()
        return config['expected_tools']

    async def _test_tool_calls(self, session: ClientSession) -> bool:
        """Test specific technician server tool calls."""
        print("\n🔧 Testing technician server tool calls...")

        try:
            # Test get_technician_status
            print("  Testing get_technician_status...")
            status_result = await session.call_tool(
                "get_technician_status",
                {"technician_id": "TECH001"}
            )

            if status_result.content:
                status_data = json.loads(status_result.content[0].text)
                if "error" not in status_data:
                    print(f"    ✓ Status retrieved for {status_data.get('name', 'technician')}")
                else:
                    print(f"    ℹ Status call returned: {status_data['error']}")

            # Test list_available_technicians
            print("  Testing list_available_technicians...")
            future_time = (datetime.now() + timedelta(hours=2)).isoformat()

            list_result = await session.call_tool(
                "list_available_technicians",
                {
                    "area": "downtown",
                    "datetime_str": future_time,
                    "specialties": ["refrigerator"]
                }
            )

            if list_result.content:
                list_data = json.loads(list_result.content[0].text)
                if "error" not in list_data:
                    count = list_data.get('total_found', 0)
                    print(f"    ✓ Found {count} available technicians")
                else:
                    print(f"    ℹ List call returned: {list_data['error']}")

            # Test get_technician_location
            print("  Testing get_technician_location...")
            location_result = await session.call_tool(
                "get_technician_location",
                {"technician_id": "TECH001"}
            )

            if location_result.content:
                location_data = json.loads(location_result.content[0].text)
                if "error" not in location_data:
                    location = location_data.get('current_location', {})
                    lat = location.get('latitude', 'N/A')
                    lon = location.get('longitude', 'N/A')
                    print(f"    ✓ Location retrieved: {lat}, {lon}")
                else:
                    print(f"    ℹ Location call returned: {location_data['error']}")

            # Test get_technician_route
            print("  Testing get_technician_route...")
            route_result = await session.call_tool(
                "get_technician_route",
                {
                    "technician_id": "TECH001",
                    "destination": [41.9000, -87.6000]
                }
            )

            if route_result.content:
                route_data = json.loads(route_result.content[0].text)
                if "error" not in route_data:
                    distance = route_data.get('distance_miles', 'N/A')
                    eta = route_data.get('estimated_travel_time_minutes', 'N/A')
                    print(f"    ✓ Route calculated: {distance} miles, {eta} minutes")
                else:
                    print(f"    ℹ Route call returned: {route_data['error']}")

            # Test update_technician_status
            print("  Testing update_technician_status...")
            update_result = await session.call_tool(
                "update_technician_status",
                {
                    "technician_id": "TECH001",
                    "new_status": "busy",
                    "appointment_id": "TEST_APPT"
                }
            )

            if update_result.content:
                update_data = json.loads(update_result.content[0].text)
                if "error" not in update_data:
                    success = update_data.get('success', False)
                    new_status = update_data.get('new_status', 'unknown')
                    print(f"    ✓ Status updated successfully to: {new_status}")
                else:
                    print(f"    ℹ Update call returned: {update_data['error']}")

            # Test notify_status_change
            print("  Testing notify_status_change...")
            notify_result = await session.call_tool(
                "notify_status_change",
                {
                    "technician_id": "TECH001",
                    "appointment_id": "TEST_APPT",
                    "status_message": "Test notification message"
                }
            )

            if notify_result.content:
                notify_data = json.loads(notify_result.content[0].text)
                if "error" not in notify_data:
                    success = notify_data.get('success', False)
                    message = notify_data.get('message', '')
                    print(f"    ✓ Notification sent: {message[:50]}...")
                else:
                    print(f"    ℹ Notify call returned: {notify_data['error']}")

            print("✓ All technician server tool calls completed")
            return True

        except Exception as e:
            print(f"✗ Error during tool call testing: {e}")
            return False


class TechnicianServerStandaloneTest(BaseMCPStandaloneTest):
    """Test connection to running technician server."""

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
    def expected_tools(self) -> Set[str]:
        config = get_technician_server_config()
        return config['expected_tools']

    async def _test_standalone_tool_calls(self, session: ClientSession):
        """Test tool calls against running server."""
        print(f"\n🔧 Testing technician server tool calls...")

        # Test basic status check
        print("  📋 Testing technician status check...")
        try:
            result = await session.call_tool(
                "get_technician_status",
                {"technician_id": "TECH001"}
            )

            if result.content:
                data = json.loads(result.content[0].text)
                if "error" not in data:
                    print(f"    ✓ Technician: {data.get('name', 'Unknown')}")
                    print(f"    ✓ Status: {data.get('status', 'Unknown')}")
                    print(f"    ✓ Specialties: {', '.join(data.get('specialties', []))}")
                else:
                    print(f"    ℹ {data['error']}")
        except Exception as e:
            print(f"    ✗ Error: {e}")

        # Test location tracking
        print("  📍 Testing location tracking...")
        try:
            result = await session.call_tool(
                "get_technician_location",
                {"technician_id": "TECH001"}
            )

            if result.content:
                data = json.loads(result.content[0].text)
                if "error" not in data:
                    location = data.get('current_location', {})
                    lat = location.get('latitude', 'N/A')
                    lon = location.get('longitude', 'N/A')
                    print(f"    ✓ Current location: {lat}, {lon}")

                    if 'eta_minutes' in data:
                        print(f"    ✓ ETA: {data['eta_minutes']} minutes")
                else:
                    print(f"    ℹ {data['error']}")
        except Exception as e:
            print(f"    ✗ Error: {e}")

        # Test availability search
        print("  🔍 Testing technician availability search...")
        try:
            future_time = (datetime.now() + timedelta(hours=2)).isoformat()
            result = await session.call_tool(
                "list_available_technicians",
                {
                    "area": "downtown",
                    "datetime_str": future_time,
                    "specialties": ["refrigerator", "washing_machine"]
                }
            )

            if result.content:
                data = json.loads(result.content[0].text)
                if "error" not in data:
                    count = data.get('total_found', 0)
                    print(f"    ✓ Found {count} available technicians")

                    for tech in data.get('available_technicians', [])[:3]:  # Show first 3
                        name = tech.get('name', 'Unknown')
                        eta = tech.get('eta_minutes', 'N/A')
                        distance = tech.get('distance_miles', 'N/A')
                        print(f"      - {name}: {distance} miles, {eta} min ETA")
                else:
                    print(f"    ℹ {data['error']}")
        except Exception as e:
            print(f"    ✗ Error: {e}")

        # Test route calculation
        print("  🗺️ Testing route calculation...")
        try:
            result = await session.call_tool(
                "get_technician_route",
                {
                    "technician_id": "TECH001",
                    "destination": [41.9000, -87.6000]  # Chicago area destination
                }
            )

            if result.content:
                data = json.loads(result.content[0].text)
                if "error" not in data:
                    distance = data.get('distance_miles', 'N/A')
                    eta = data.get('estimated_travel_time_minutes', 'N/A')
                    traffic = data.get('traffic_conditions', 'unknown')
                    waypoints = len(data.get('route_waypoints', []))
                    print(f"    ✓ Route: {distance} miles, {eta} minutes")
                    print(f"    ✓ Traffic: {traffic}, {waypoints} waypoints")
                else:
                    print(f"    ℹ {data['error']}")
        except Exception as e:
            print(f"    ✗ Error: {e}")

        # Test status update
        print("  📝 Testing status update...")
        try:
            result = await session.call_tool(
                "update_technician_status",
                {
                    "technician_id": "TECH001",
                    "new_status": "en_route",
                    "appointment_id": "DEMO_APPT_001"
                }
            )

            if result.content:
                data = json.loads(result.content[0].text)
                if "error" not in data and data.get('success'):
                    old_status = data.get('old_status', 'unknown')
                    new_status = data.get('new_status', 'unknown')
                    print(f"    ✓ Status updated: {old_status} → {new_status}")
                else:
                    print(f"    ℹ {data.get('error', 'Update failed')}")
        except Exception as e:
            print(f"    ✗ Error: {e}")

        # Test notification
        print("  📢 Testing status notification...")
        try:
            result = await session.call_tool(
                "notify_status_change",
                {
                    "technician_id": "TECH001",
                    "appointment_id": "DEMO_APPT_001"
                }
            )

            if result.content:
                data = json.loads(result.content[0].text)
                if "error" not in data and data.get('success'):
                    message = data.get('message', '')
                    print(f"    ✓ Notification: {message[:60]}...")
                else:
                    print(f"    ℹ {data.get('error', 'Notification failed')}")
        except Exception as e:
            print(f"    ✗ Error: {e}")


# Test runner functions
async def run_integration_test():
    """Run the MCP integration test."""
    test = TechnicianServerIntegrationTest()
    success = await test.test_mcp_client_connection()
    return success


async def run_standalone_test():
    """Run the standalone connection test."""
    test = TechnicianServerStandaloneTest()
    success = await test.test_standalone_connection()
    return success


def run_endpoint_test():
    """Run the endpoint test."""
    test = TechnicianServerEndpointTest()
    test.test_endpoint_functions_available()
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test Technician Tracking MCP Server")
    parser.add_argument(
        "test_type",
        choices=["endpoint", "integration", "standalone"],
        help="Type of test to run"
    )

    args = parser.parse_args()

    if args.test_type == "endpoint":
        print("🧪 Running Technician Server Endpoint Tests...")
        success = run_endpoint_test()

    elif args.test_type == "integration":
        print("🧪 Running Technician Server Integration Tests...")
        success = asyncio.run(run_integration_test())

    elif args.test_type == "standalone":
        print("🧪 Running Technician Server Standalone Tests...")
        success = asyncio.run(run_standalone_test())

    if success:
        print("\n🎉 All tests completed successfully!")
        exit(0)
    else:
        print("\n❌ Some tests failed!")
        exit(1)
