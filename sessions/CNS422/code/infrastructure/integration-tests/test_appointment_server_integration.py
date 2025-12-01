"""
Integration tests for Appointment Management MCP Server.

These tests run against a live appointment server that should already be running.
Start the server first with: python -m mcp_servers.appointment_server.server
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


class TestAppointmentServerStandalone(BaseMCPStandaloneTest):
    """Test appointment server standalone connection."""

    @property
    def server_name(self) -> str:
        return "Appointment Management Server"

    @property
    def server_port(self) -> int:
        return 8002

    @property
    def server_module_path(self) -> str:
        return "mcp_servers.appointment_server.server"

    @property
    def expected_tools(self) -> set:
        return {
            "list_appointments",
            "create_appointment",
            "update_appointment",
            "cancel_appointment",
            "get_available_slots",
            "reschedule_appointment",
            "get_appointment_details"
        }

    @pytest.mark.asyncio
    async def test_standalone_connection(self) -> bool:
        """Test standalone connection with pytest-asyncio decorator."""
        return await super().test_standalone_connection()

    async def _test_standalone_tool_calls(self, session):
        """Test tool calls in standalone mode."""
        print(f"\n🔧 Testing {self.server_name} tool calls...")

        try:
            # Test basic appointment listing
            print("  📋 Testing list_appointments...")
            result = await session.call_tool("list_appointments", {"customer_id": "CUST001"})
            print(f"     Response: {result.content[0].text[:100]}...")

            # Test available slots
            print("  📅 Testing get_available_slots...")
            start_date = (datetime.now() + timedelta(days=1)).isoformat()
            end_date = (datetime.now() + timedelta(days=2)).isoformat()

            result = await session.call_tool("get_available_slots", {
                "date_range_start": start_date,
                "date_range_end": end_date,
                "appliance_type": "refrigerator"
            })
            print(f"     Found slots: {len(json.loads(result.content[0].text).get('available_slots', []))}")

            # Test appointment details
            print("  📄 Testing get_appointment_details...")
            result = await session.call_tool("get_appointment_details", {"appointment_id": "APPT001"})
            appointment_data = json.loads(result.content[0].text)
            if "error" not in appointment_data:
                print(f"     Appointment: {appointment_data.get('id', 'Unknown')} - {appointment_data.get('appliance_type', 'Unknown')}")
            else:
                print(f"     Note: {appointment_data['error']}")

            print("  ✓ All tool calls completed successfully")

        except Exception as e:
            print(f"  ✗ Tool call error: {e}")


# Test runner function for manual execution
def test_appointment_server_standalone():
    """Run standalone client test."""
    test_class = TestAppointmentServerStandalone()

    print("Running Appointment Server Standalone Test...")
    print("Make sure the appointment server is running on port 8002")
    print("Start with: python -m mcp_servers.appointment_server.server")

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
    print("🧪 Appointment Management MCP Server Integration Test")
    print("=" * 60)

    print("\n📝 Prerequisites:")
    print("1. Start the appointment server: python -m mcp_servers.appointment_server.server")
    print("2. Server should be running on http://localhost:8002")
    print("3. Run this test: python test_appointment_server_integration.py")

    test_appointment_server_standalone()
