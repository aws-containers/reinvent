"""
Comprehensive test suite for Appointment Management MCP Server.

This module tests all appointment server functionality including:
- Endpoint testing (direct function calls)
- MCP client integration testing
- Standalone client testing
"""

import asyncio
import json
import pytest
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, mock_open

# Add parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from testing_framework.base_test_classes import (
    BaseMCPEndpointTest,
    BaseMCPIntegrationTest,
    BaseMCPStandaloneTest
)

# Import server functions
from mcp_servers.appointment_server.server import (
    list_appointments,
    create_appointment,
    update_appointment,
    cancel_appointment,
    get_available_slots,
    reschedule_appointment,
    get_appointment_details
)


class TestAppointmentServerEndpoints(BaseMCPEndpointTest):
    """Test appointment server endpoints directly."""

    @property
    def server_name(self) -> str:
        return "Appointment Management Server"

    @property
    def server_port(self) -> int:
        return 8002

    @property
    def server_module_path(self) -> str:
        return "mcp_servers.appointment_server.server.main"

    @property
    def expected_tools(self) -> set:
        return {
            "list_all_appointments",
            "list_appointments",
            "create_appointment",
            "update_appointment",
            "cancel_appointment",
            "get_available_slots",
            "reschedule_appointment",
            "get_appointment_details"
        }

    def setup_test_data(self):
        """Set up test data before each test."""
        # Mock appointment data
        self.mock_appointments = {
            "APPT001": {
                "id": "APPT001",
                "customer_id": "CUST001",
                "technician_id": "TECH001",
                "appliance_type": "refrigerator",
                "issue_description": "Refrigerator not cooling properly",
                "scheduled_datetime": "2025-09-05T08:00:00",
                "status": "scheduled",
                "estimated_duration": 120,
                "created_at": "2025-09-04T06:00:00",
                "notes": "Customer mentioned strange noises",
                "claim_id": "CLAIM001",
                "service_details": {
                    "priority": "high",
                    "parts_needed": ["compressor_relay"],
                    "estimated_cost": 285.5,
                    "warranty_covered": True
                }
            },
            "APPT002": {
                "id": "APPT002",
                "customer_id": "CUST002",
                "technician_id": "TECH002",
                "appliance_type": "washing_machine",
                "issue_description": "Washing machine not draining water",
                "scheduled_datetime": "2025-09-06T09:00:00",
                "status": "confirmed",
                "estimated_duration": 90,
                "created_at": "2025-09-05T07:00:00",
                "notes": "Customer reported error code E03",
                "claim_id": "CLAIM002",
                "service_details": {
                    "priority": "medium",
                    "parts_needed": ["drain_pump"],
                    "estimated_cost": 165.75,
                    "warranty_covered": True
                }
            }
        }

        # Mock technician data
        self.mock_technicians = {
            "TECH001": {
                "id": "TECH001",
                "name": "Alex Rodriguez",
                "specialties": ["refrigerator", "freezer", "ice_maker"],
                "current_location": [41.8781, -87.6298],
                "status": "available",
                "phone": "555-111-2222",
                "profile": {
                    "years_experience": 8,
                    "rating": 4.9,
                    "completed_jobs": 1247
                }
            },
            "TECH002": {
                "id": "TECH002",
                "name": "Maria Santos",
                "specialties": ["washing_machine", "dryer", "dishwasher"],
                "current_location": [39.7392, -104.9903],
                "status": "available",
                "phone": "555-333-4444",
                "profile": {
                    "years_experience": 6,
                    "rating": 4.8,
                    "completed_jobs": 892
                }
            }
        }

    def _call_server_function(self, func, *args, **kwargs):
        """Helper to call server functions and format response for testing framework."""
        # Ensure test data is set up
        if not hasattr(self, 'mock_appointments'):
            self.setup_test_data()

        # Create fresh copies of the data for each test to avoid state pollution
        import copy
        fresh_appointments = copy.deepcopy(self.mock_appointments)
        fresh_technicians = copy.deepcopy(self.mock_technicians)

        # Patch the shared data variables with mock data
        with patch('mcp_servers.appointment_server.shared_data._appointments_data', fresh_appointments), \
             patch('mcp_servers.appointment_server.shared_data._technicians_data', fresh_technicians):

            result = func(*args, **kwargs)

            # Create a mock response object that matches what the framework expects
            class MockResponse:
                def __init__(self, text):
                    self.text = text

            return [MockResponse(result)]

    def test_list_all_appointments_success(self):
        """Test successful listing of all appointments."""
        from mcp_servers.appointment_server.server import list_all_appointments
        result = self._call_server_function(list_all_appointments)
        response_data = self.assert_successful_response(result, ["total_appointments", "appointments"])

        assert response_data["total_appointments"] == 2
        assert len(response_data["appointments"]) == 2

    def test_list_all_appointments_with_status_filter(self):
        """Test listing all appointments with status filter."""
        from mcp_servers.appointment_server.server import list_all_appointments
        result = self._call_server_function(list_all_appointments, "scheduled")
        response_data = self.assert_successful_response(result)

        assert response_data["status_filter"] == "scheduled"
        assert all(appt["status"] == "scheduled" for appt in response_data["appointments"])

    def test_list_appointments_success(self):
        """Test successful appointment listing."""
        result = self._call_server_function(list_appointments, "CUST001")
        response_data = self.assert_successful_response(result, ["customer_id", "total_appointments", "appointments"])

        assert response_data["customer_id"] == "CUST001"
        assert response_data["total_appointments"] == 1
        assert len(response_data["appointments"]) == 1
        assert response_data["appointments"][0]["id"] == "APPT001"

    def test_list_appointments_with_status_filter(self):
        """Test appointment listing with status filter."""
        result = self._call_server_function(list_appointments, "CUST002", "confirmed")
        response_data = self.assert_successful_response(result)

        assert response_data["status_filter"] == "confirmed"
        assert response_data["total_appointments"] == 1
        assert response_data["appointments"][0]["status"] == "confirmed"

    def test_list_appointments_no_results(self):
        """Test appointment listing for customer with no appointments."""
        result = self._call_server_function(list_appointments, "CUST999")
        response_data = self.assert_successful_response(result)

        assert response_data["customer_id"] == "CUST999"
        assert response_data["total_appointments"] == 0
        assert response_data["appointments"] == []

    def test_create_appointment_success(self):
        """Test successful appointment creation."""
        future_datetime = (datetime.now() + timedelta(days=1)).isoformat()

        result = self._call_server_function(
            create_appointment,
            customer_id="CUST003",
            technician_id="TECH001",
            appliance_type="refrigerator",
            issue_description="Ice maker not working",
            scheduled_datetime=future_datetime,
            estimated_duration=60,
            claim_id="CLAIM003"
        )

        response_data = self.assert_successful_response(result, ["success", "appointment_id", "appointment"])

        assert response_data["success"] is True
        assert response_data["appointment"]["customer_id"] == "CUST003"
        assert response_data["appointment"]["technician_id"] == "TECH001"
        assert response_data["appointment"]["appliance_type"] == "refrigerator"
        assert response_data["appointment"]["status"] == "scheduled"

    def test_create_appointment_invalid_technician(self):
        """Test appointment creation with invalid technician."""
        future_datetime = (datetime.now() + timedelta(days=1)).isoformat()

        result = self._call_server_function(
            create_appointment,
            customer_id="CUST003",
            technician_id="TECH999",
            appliance_type="refrigerator",
            issue_description="Ice maker not working",
            scheduled_datetime=future_datetime
        )

        self.assert_error_response(result, "Technician not found")

    def test_create_appointment_wrong_specialty(self):
        """Test appointment creation with technician who doesn't handle appliance type."""
        future_datetime = (datetime.now() + timedelta(days=1)).isoformat()

        result = self._call_server_function(
            create_appointment,
            customer_id="CUST003",
            technician_id="TECH001",  # Specializes in refrigerator
            appliance_type="washing_machine",  # Not their specialty
            issue_description="Machine not working",
            scheduled_datetime=future_datetime
        )

        self.assert_error_response(result, "Technician does not specialize in this appliance type")

    def test_create_appointment_invalid_datetime(self):
        """Test appointment creation with invalid datetime format."""
        result = self._call_server_function(
            create_appointment,
            customer_id="CUST003",
            technician_id="TECH001",
            appliance_type="refrigerator",
            issue_description="Ice maker not working",
            scheduled_datetime="invalid-datetime"
        )

        response_data = self.assert_successful_response(result, ["error"])
        assert "Invalid datetime format" in response_data["error"]

    def test_update_appointment_success(self):
        """Test successful appointment update."""
        updates = json.dumps({
            "status": "confirmed",
            "notes": "Customer confirmed availability"
        })

        result = self._call_server_function(update_appointment, "APPT001", updates)
        response_data = self.assert_successful_response(result, ["success", "appointment_id", "updated_appointment"])

        assert response_data["success"] is True
        assert response_data["updated_appointment"]["status"] == "confirmed"
        assert "Customer confirmed availability" in response_data["updated_appointment"]["notes"]

    def test_update_appointment_not_found(self):
        """Test updating non-existent appointment."""
        updates = json.dumps({"status": "confirmed"})

        result = self._call_server_function(update_appointment, "APPT999", updates)
        self.assert_error_response(result, "Appointment not found")

    def test_update_appointment_invalid_json(self):
        """Test updating appointment with invalid JSON."""
        result = self._call_server_function(update_appointment, "APPT001", "invalid-json")
        self.assert_error_response(result, "Invalid JSON format for updates")

    def test_cancel_appointment_success(self):
        """Test successful appointment cancellation."""
        result = self._call_server_function(cancel_appointment, "APPT001", "Customer no longer needs service")
        response_data = self.assert_successful_response(result, ["success", "appointment_id", "new_status"])

        assert response_data["success"] is True
        assert response_data["new_status"] == "cancelled"
        assert response_data["cancellation_reason"] == "Customer no longer needs service"

    def test_cancel_appointment_not_found(self):
        """Test cancelling non-existent appointment."""
        result = self._call_server_function(cancel_appointment, "APPT999")
        self.assert_error_response(result, "Appointment not found")

    def test_get_appointment_details_success(self):
        """Test getting appointment details."""
        result = self._call_server_function(get_appointment_details, "APPT001")
        response_data = self.assert_successful_response(result, ["id", "customer_id", "technician_details"])

        assert response_data["id"] == "APPT001"
        assert response_data["customer_id"] == "CUST001"
        assert response_data["technician_details"]["name"] == "Alex Rodriguez"
        assert response_data["technician_details"]["phone"] == "555-111-2222"

    def test_get_appointment_details_not_found(self):
        """Test getting details for non-existent appointment."""
        result = self._call_server_function(get_appointment_details, "APPT999")
        self.assert_error_response(result, "Appointment not found")

    def test_get_available_slots_success(self):
        """Test getting available time slots."""
        start_date = (datetime.now() + timedelta(days=1)).isoformat()
        end_date = (datetime.now() + timedelta(days=2)).isoformat()

        result = self._call_server_function(
            get_available_slots,
            date_range_start=start_date,
            date_range_end=end_date,
            appliance_type="refrigerator",
            duration_minutes=90
        )

        response_data = self.assert_successful_response(result, ["appliance_type", "available_slots", "qualified_technicians"])

        assert response_data["appliance_type"] == "refrigerator"
        assert response_data["qualified_technicians"] >= 1
        assert isinstance(response_data["available_slots"], list)

    def test_get_available_slots_no_qualified_technicians(self):
        """Test getting available slots for unsupported appliance type."""
        start_date = (datetime.now() + timedelta(days=1)).isoformat()
        end_date = (datetime.now() + timedelta(days=2)).isoformat()

        result = self._call_server_function(
            get_available_slots,
            date_range_start=start_date,
            date_range_end=end_date,
            appliance_type="unsupported_appliance",
            duration_minutes=90
        )

        self.assert_error_response(result, "No technicians available for this appliance type")

    def test_reschedule_appointment_success(self):
        """Test successful appointment rescheduling."""
        new_datetime = (datetime.now() + timedelta(days=2)).isoformat()

        result = self._call_server_function(reschedule_appointment, "APPT001", new_datetime)
        response_data = self.assert_successful_response(result, ["success", "appointment_id", "new_datetime"])

        assert response_data["success"] is True
        assert response_data["appointment_id"] == "APPT001"
        assert response_data["new_datetime"] == new_datetime

    def test_reschedule_appointment_not_found(self):
        """Test rescheduling non-existent appointment."""
        new_datetime = (datetime.now() + timedelta(days=2)).isoformat()

        result = self._call_server_function(reschedule_appointment, "APPT999", new_datetime)
        self.assert_error_response(result, "Appointment not found")


class TestAppointmentServerIntegration(BaseMCPIntegrationTest):
    """Test appointment server through MCP protocol."""

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
            "list_all_appointments",
            "list_appointments",
            "create_appointment",
            "update_appointment",
            "cancel_appointment",
            "get_available_slots",
            "reschedule_appointment",
            "get_appointment_details"
        }

    @pytest.mark.asyncio
    async def test_mcp_client_connection(self) -> bool:
        """Test MCP client connection with pytest-asyncio decorator."""
        return await super().test_mcp_client_connection()

    async def _test_tool_calls(self, session) -> bool:
        """Test specific tool calls for appointment server."""
        print("\n🔧 Testing appointment server tool calls...")

        try:
            # Test list_appointments
            print("  Testing list_appointments...")
            result = await session.call_tool("list_appointments", {"customer_id": "CUST001"})
            response_data = json.loads(result.content[0].text)
            assert "appointments" in response_data
            print("  ✓ list_appointments works")

            # Test get_available_slots
            print("  Testing get_available_slots...")
            start_date = (datetime.now() + timedelta(days=1)).isoformat()
            end_date = (datetime.now() + timedelta(days=2)).isoformat()

            result = await session.call_tool("get_available_slots", {
                "date_range_start": start_date,
                "date_range_end": end_date,
                "appliance_type": "refrigerator"
            })
            response_data = json.loads(result.content[0].text)
            assert "available_slots" in response_data
            print("  ✓ get_available_slots works")

            # Test get_appointment_details
            print("  Testing get_appointment_details...")
            result = await session.call_tool("get_appointment_details", {"appointment_id": "APPT001"})
            response_data = json.loads(result.content[0].text)
            assert "id" in response_data
            print("  ✓ get_appointment_details works")

            print("✓ All appointment server tool calls successful")
            return True

        except Exception as e:
            print(f"✗ Tool call failed: {e}")
            return False



# Test runner functions
def test_appointment_server_endpoints():
    """Run all endpoint tests."""
    test_class = TestAppointmentServerEndpoints()
    test_class.setup_test_data()

    print("Running Appointment Server Endpoint Tests...")

    # Run all test methods
    test_methods = [method for method in dir(test_class) if method.startswith('test_')]

    for method_name in test_methods:
        try:
            print(f"  Running {method_name}...")
            method = getattr(test_class, method_name)
            method()
            print(f"  ✓ {method_name} passed")
        except Exception as e:
            print(f"  ✗ {method_name} failed: {e}")
            raise


def test_appointment_server_integration():
    """Run MCP integration test."""
    test_class = TestAppointmentServerIntegration()

    print("Running Appointment Server MCP Integration Test...")

    try:
        result = asyncio.run(test_class.test_mcp_client_connection())
        if result:
            print("✓ MCP Integration test passed")
        else:
            print("✗ MCP Integration test failed")
            assert False, "MCP Integration test failed"
    except Exception as e:
        print(f"✗ MCP Integration test error: {e}")
        assert False, f"MCP Integration test error: {e}"





if __name__ == "__main__":
    print("🧪 Appointment Management MCP Server Test Suite")
    print("=" * 50)

    # Run endpoint tests
    test_appointment_server_endpoints()

    # Run integration tests
    test_appointment_server_integration()

    # Note: Standalone tests are now in integration-tests directory
    print("\n📝 To run standalone/integration tests:")
    print("1. Start the appointment server: python -m mcp_servers.appointment_server.server")
    print("2. Run: cd integration-tests && pytest test_appointment_server_integration.py -v")
