"""
Comprehensive test suite for Technician Tracking MCP Server.

This module tests all technician server functionality including:
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
from mcp_servers.technician_server.server import (
    list_all_technicians,
    get_technician_status,
    get_technician_location,
    list_available_technicians,
    update_technician_status,
    get_technician_route,
    notify_status_change,
    calculate_distance,
    calculate_eta,
    simulate_location_update,
    load_mock_data
)


class TestTechnicianServerEndpoints(BaseMCPEndpointTest):
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
    def expected_tools(self) -> set:
        return {
            "list_all_technicians",
            "get_technician_status",
            "get_technician_location",
            "list_available_technicians",
            "update_technician_status",
            "get_technician_route",
            "notify_status_change"
        }

    def setup_test_data(self):
        """Set up test data before each test."""
        # Mock technician data
        self.mock_technicians = {
            "TECH001": {
                "id": "TECH001",
                "name": "Alex Rodriguez",
                "specialties": ["refrigerator", "freezer", "ice_maker"],
                "current_location": [41.8781, -87.6298],  # Chicago
                "status": "available",
                "phone": "555-111-2222",
                "estimated_arrival": None,
                "current_appointment_id": None,
                "profile": {
                    "years_experience": 8,
                    "certification_level": "Master Technician",
                    "rating": 4.9
                }
            },
            "TECH002": {
                "id": "TECH002",
                "name": "Maria Santos",
                "specialties": ["washing_machine", "dryer", "dishwasher"],
                "current_location": [39.7392, -104.9903],  # Denver
                "status": "en_route",
                "phone": "555-333-4444",
                "estimated_arrival": (datetime.now() + timedelta(minutes=30)).isoformat(),
                "current_appointment_id": "APPT003",
                "profile": {
                    "years_experience": 6,
                    "certification_level": "Senior Technician",
                    "rating": 4.8
                }
            },
            "TECH003": {
                "id": "TECH003",
                "name": "Kevin Johnson",
                "specialties": ["dishwasher", "garbage_disposal", "water_heater"],
                "current_location": [30.2672, -97.7431],  # Austin
                "status": "on_site",
                "phone": "555-555-6666",
                "estimated_arrival": None,
                "current_appointment_id": "APPT005",
                "profile": {
                    "years_experience": 12,
                    "certification_level": "Master Technician",
                    "rating": 4.95
                }
            }
        }

    def _call_server_function(self, func, *args, **kwargs):
        """Helper to call server functions and format response for testing framework."""
        # Ensure test data is set up
        if not hasattr(self, 'mock_technicians'):
            self.setup_test_data()

        # Create fresh copies of the data for each test to avoid state pollution
        import copy
        fresh_technicians = copy.deepcopy(self.mock_technicians)

        # Patch the shared data function to return mock data
        with patch('mcp_servers.technician_server.server.get_technicians_data', return_value=fresh_technicians):

            result = func(*args, **kwargs)

            # Create a mock response object that matches what the framework expects
            class MockResponse:
                def __init__(self, text):
                    self.text = text

            return [MockResponse(result)]

    def test_get_technician_status_success(self):
        """Test successful technician status retrieval."""
        result = self._call_server_function(get_technician_status, "TECH001")
        response_data = self.assert_successful_response(result, ["technician_id", "name", "status", "specialties"])

        assert response_data["technician_id"] == "TECH001"
        assert response_data["name"] == "Alex Rodriguez"
        assert response_data["status"] == "available"
        assert "refrigerator" in response_data["specialties"]
        assert response_data["phone"] == "555-111-2222"
        assert response_data["current_appointment_id"] is None
        assert "last_updated" in response_data

    def test_get_technician_status_not_found(self):
        """Test technician status retrieval for non-existent technician."""
        result = self._call_server_function(get_technician_status, "TECH999")
        self.assert_error_response(result, "Technician not found")

    def test_get_technician_location_success(self):
        """Test successful technician location retrieval."""
        result = self._call_server_function(get_technician_location, "TECH001")
        response_data = self.assert_successful_response(result, ["technician_id", "name", "status", "current_location"])

        assert response_data["technician_id"] == "TECH001"
        assert response_data["name"] == "Alex Rodriguez"
        assert response_data["status"] == "available"
        assert "current_location" in response_data
        assert "latitude" in response_data["current_location"]
        assert "longitude" in response_data["current_location"]
        assert "last_location_update" in response_data

        # Verify location is near Chicago (within reasonable bounds)
        lat = response_data["current_location"]["latitude"]
        lon = response_data["current_location"]["longitude"]
        assert 41.0 < lat < 42.0  # Rough Chicago area bounds
        assert -88.0 < lon < -87.0

    def test_get_technician_location_en_route_with_eta(self):
        """Test technician location retrieval for en_route technician with ETA calculation."""
        result = self._call_server_function(get_technician_location, "TECH002")
        response_data = self.assert_successful_response(result, ["technician_id", "status"])

        assert response_data["technician_id"] == "TECH002"
        assert response_data["status"] == "en_route"
        assert "eta_minutes" in response_data
        assert isinstance(response_data["eta_minutes"], int)
        assert response_data["eta_minutes"] >= 0

    def test_get_technician_location_not_found(self):
        """Test technician location retrieval for non-existent technician."""
        result = self._call_server_function(get_technician_location, "TECH999")
        self.assert_error_response(result, "Technician not found")

    def test_list_available_technicians_success(self):
        """Test successful listing of available technicians."""
        future_time = (datetime.now() + timedelta(hours=2)).isoformat()

        result = self._call_server_function(
            list_available_technicians,
            "downtown",
            future_time,
            ["refrigerator"]
        )
        response_data = self.assert_successful_response(result, ["area", "required_specialties", "available_technicians"])

        assert response_data["area"] == "downtown"
        assert response_data["required_specialties"] == ["refrigerator"]
        assert "available_technicians" in response_data
        assert response_data["total_found"] >= 0

        # Should find TECH001 (available with refrigerator specialty)
        available_techs = response_data["available_technicians"]
        tech_ids = [tech["technician_id"] for tech in available_techs]
        assert "TECH001" in tech_ids

        # Verify technician details
        tech001 = next(tech for tech in available_techs if tech["technician_id"] == "TECH001")
        assert tech001["name"] == "Alex Rodriguez"
        assert "refrigerator" in tech001["specialties"]
        assert "distance_miles" in tech001
        assert "eta_minutes" in tech001
        assert "estimated_arrival" in tech001

    def test_list_available_technicians_no_matches(self):
        """Test listing available technicians with no matches."""
        future_time = (datetime.now() + timedelta(hours=2)).isoformat()

        result = self._call_server_function(
            list_available_technicians,
            "downtown",
            future_time,
            ["air_conditioner"]  # No technicians have this specialty
        )
        response_data = self.assert_successful_response(result, ["total_found", "available_technicians"])

        assert response_data["total_found"] == 0
        assert len(response_data["available_technicians"]) == 0

    def test_list_available_technicians_invalid_datetime(self):
        """Test listing available technicians with invalid datetime."""
        result = self._call_server_function(
            list_available_technicians,
            "downtown",
            "invalid-datetime",
            ["refrigerator"]
        )
        response_data = self.assert_successful_response(result, ["error"])
        assert "Invalid datetime format" in response_data["error"]

    def test_update_technician_status_success(self):
        """Test successful technician status update."""
        result = self._call_server_function(
            update_technician_status,
            "TECH001",
            "en_route",
            [41.8800, -87.6300],  # New location
            "APPT123"
        )
        response_data = self.assert_successful_response(result, ["success", "technician_id", "old_status", "new_status"])

        assert response_data["success"] is True
        assert response_data["technician_id"] == "TECH001"
        assert response_data["old_status"] == "available"
        assert response_data["new_status"] == "en_route"
        assert response_data["current_appointment_id"] == "APPT123"
        assert "updated_at" in response_data
        assert "estimated_arrival" in response_data

    def test_update_technician_status_to_available_clears_appointment(self):
        """Test that updating status to available clears appointment assignment."""
        result = self._call_server_function(update_technician_status, "TECH001", "available")
        response_data = self.assert_successful_response(result, ["success", "new_status"])

        assert response_data["success"] is True
        assert response_data["new_status"] == "available"
        assert response_data["current_appointment_id"] is None

    def test_update_technician_status_invalid_status(self):
        """Test technician status update with invalid status."""
        result = self._call_server_function(update_technician_status, "TECH001", "invalid_status")
        response_data = self.assert_successful_response(result, ["error"])
        assert "Invalid status" in response_data["error"]
        assert "provided_status" in response_data

    def test_update_technician_status_not_found(self):
        """Test technician status update for non-existent technician."""
        result = self._call_server_function(update_technician_status, "TECH999", "available")
        self.assert_error_response(result, "Technician not found")

    def test_get_technician_route_success(self):
        """Test successful route calculation."""
        destination = [41.9000, -87.6000]  # Destination in Chicago area

        result = self._call_server_function(get_technician_route, "TECH001", destination)
        response_data = self.assert_successful_response(result, ["technician_id", "technician_name", "origin", "destination"])

        assert response_data["technician_id"] == "TECH001"
        assert response_data["technician_name"] == "Alex Rodriguez"
        assert "origin" in response_data
        assert "destination" in response_data
        assert "distance_miles" in response_data
        assert "estimated_travel_time_minutes" in response_data
        assert "estimated_arrival" in response_data
        assert "traffic_conditions" in response_data
        assert "route_waypoints" in response_data
        assert "calculated_at" in response_data

        # Verify origin matches technician's current location
        origin = response_data["origin"]
        tech_location = self.mock_technicians["TECH001"]["current_location"]
        assert origin["latitude"] == tech_location[0]
        assert origin["longitude"] == tech_location[1]

        # Verify destination matches input
        dest = response_data["destination"]
        assert dest["latitude"] == destination[0]
        assert dest["longitude"] == destination[1]

    def test_get_technician_route_invalid_destination(self):
        """Test route calculation with invalid destination."""
        result = self._call_server_function(get_technician_route, "TECH001", [41.9000])  # Missing longitude
        response_data = self.assert_successful_response(result, ["error"])
        assert "Invalid destination" in response_data["error"]

    def test_get_technician_route_not_found(self):
        """Test route calculation for non-existent technician."""
        result = self._call_server_function(get_technician_route, "TECH999", [41.9000, -87.6000])
        self.assert_error_response(result, "Technician not found")

    def test_notify_status_change_success(self):
        """Test successful status change notification."""
        result = self._call_server_function(notify_status_change, "TECH002", "APPT003")
        response_data = self.assert_successful_response(result, ["success", "appointment_id", "technician_id", "technician_name"])

        assert response_data["success"] is True
        assert response_data["appointment_id"] == "APPT003"
        assert response_data["technician_id"] == "TECH002"
        assert response_data["technician_name"] == "Maria Santos"
        assert response_data["current_status"] == "en_route"
        assert "message" in response_data
        assert "timestamp" in response_data

        # Should include location for en_route technician
        assert "current_location" in response_data

    def test_notify_status_change_custom_message(self):
        """Test status change notification with custom message."""
        custom_message = "Custom status update message"

        result = self._call_server_function(notify_status_change, "TECH001", "APPT123", custom_message)
        response_data = self.assert_successful_response(result, ["success", "message"])

        assert response_data["success"] is True
        assert response_data["message"] == custom_message

    def test_notify_status_change_not_found(self):
        """Test status change notification for non-existent technician."""
        result = self._call_server_function(notify_status_change, "TECH999", "APPT123")
        self.assert_error_response(result, "Technician not found")

    def test_calculate_distance(self):
        """Test distance calculation between two points."""
        # Test distance between Chicago and Milwaukee (approximately 90 miles)
        chicago_lat, chicago_lon = 41.8781, -87.6298
        milwaukee_lat, milwaukee_lon = 43.0389, -87.9065

        distance = calculate_distance(chicago_lat, chicago_lon, milwaukee_lat, milwaukee_lon)

        # Should be approximately 90 miles (allow some tolerance)
        assert 80 < distance < 100

    def test_calculate_eta(self):
        """Test ETA calculation."""
        # Test with 10 miles and no traffic
        eta = calculate_eta(10.0, 1.0)

        # Should be around 24 minutes (10 miles / 25 mph * 60 min/hr)
        # Allow for randomness (±5 minutes)
        assert 15 < eta < 35

        # Test with heavy traffic
        eta_heavy = calculate_eta(10.0, 1.5)

        # Should be longer than no traffic case
        assert eta_heavy > eta

    def test_simulate_location_update_available(self):
        """Test location simulation for available technician."""
        technician = {
            "current_location": [41.8781, -87.6298],
            "status": "available"
        }

        new_lat, new_lon = simulate_location_update(technician)

        # Should be near original location (within 0.02 degrees)
        assert abs(new_lat - 41.8781) < 0.02
        assert abs(new_lon - (-87.6298)) < 0.02

    def test_simulate_location_update_en_route(self):
        """Test location simulation for en_route technician."""
        technician = {
            "current_location": [41.8781, -87.6298],
            "status": "en_route"
        }
        destination = (41.9000, -87.6000)

        new_lat, new_lon = simulate_location_update(technician, destination)

        # Should move towards destination
        # New location should be between current and destination
        assert min(41.8781, 41.9000) <= new_lat <= max(41.8781, 41.9000)
        assert min(-87.6298, -87.6000) <= new_lon <= max(-87.6298, -87.6000)

    def test_load_mock_data_error_handling(self):
        """Test load_mock_data error handling."""
        # Test file not found
        with patch('builtins.open', side_effect=FileNotFoundError):
            load_mock_data()
            # Should handle gracefully

        # Test invalid JSON
        with patch('builtins.open', mock_open(read_data='invalid json')):
            load_mock_data()
            # Should handle gracefully

    def test_technician_filtering_by_specialty(self):
        """Test that technician filtering by specialty works correctly."""
        future_time = (datetime.now() + timedelta(hours=2)).isoformat()

        # Test filtering for washing machine specialty
        result = self._call_server_function(
            list_available_technicians,
            "downtown",
            future_time,
            ["washing_machine"]
        )
        response_data = self.assert_successful_response(result, ["available_technicians"])

        # Should not find TECH001 (only has refrigerator specialty)
        # TECH002 has washing_machine but is en_route (not available)
        # So should find no available technicians
        tech_ids = [tech["technician_id"] for tech in response_data["available_technicians"]]
        assert "TECH001" not in tech_ids  # Wrong specialty
        assert "TECH002" not in tech_ids  # Right specialty but not available


class TestTechnicianServerIntegration(BaseMCPIntegrationTest):
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
    def expected_tools(self) -> set:
        return {
            "list_all_technicians",
            "get_technician_status",
            "get_technician_location",
            "list_available_technicians",
            "update_technician_status",
            "get_technician_route",
            "notify_status_change"
        }

    @pytest.mark.asyncio
    async def test_mcp_client_connection(self) -> bool:
        """Test MCP client connection with pytest-asyncio decorator."""
        return await super().test_mcp_client_connection()

    async def _test_tool_calls(self, session) -> bool:
        """Test specific tool calls for technician server."""
        print("\n🔧 Testing technician server tool calls...")

        try:
            # Test get_technician_status
            print("  Testing get_technician_status...")
            result = await session.call_tool("get_technician_status", {"technician_id": "TECH001"})
            response_data = json.loads(result.content[0].text)
            assert "technician_id" in response_data
            print("  ✓ get_technician_status works")

            # Test get_technician_location
            print("  Testing get_technician_location...")
            result = await session.call_tool("get_technician_location", {"technician_id": "TECH001"})
            response_data = json.loads(result.content[0].text)
            assert "current_location" in response_data
            print("  ✓ get_technician_location works")

            # Test list_available_technicians
            print("  Testing list_available_technicians...")
            future_time = (datetime.now() + timedelta(hours=2)).isoformat()
            result = await session.call_tool("list_available_technicians", {
                "area": "downtown",
                "datetime_str": future_time,
                "specialties": ["refrigerator"]
            })
            response_data = json.loads(result.content[0].text)
            assert "available_technicians" in response_data
            print("  ✓ list_available_technicians works")

            print("✓ All technician server tool calls successful")
            return True

        except Exception as e:
            print(f"✗ Tool call failed: {e}")
            return False


# Test runner functions
def test_technician_server_endpoints():
    """Run all endpoint tests."""
    test_class = TestTechnicianServerEndpoints()
    test_class.setup_test_data()

    print("Running Technician Server Endpoint Tests...")

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


def test_technician_server_integration():
    """Run MCP integration test."""
    test_class = TestTechnicianServerIntegration()

    print("Running Technician Server MCP Integration Test...")

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
    print("🧪 Technician Tracking MCP Server Test Suite")
    print("=" * 50)

    # Run endpoint tests
    test_technician_server_endpoints()

    # Run integration tests
    test_technician_server_integration()

    # Note: Standalone tests are now in integration-tests directory
    print("\n📝 To run standalone/integration tests:")
    print("1. Start the technician server: python -m mcp_servers.technician_server.server")
    print("2. Run: cd integration-tests && pytest test_technician_server_integration.py -v")
