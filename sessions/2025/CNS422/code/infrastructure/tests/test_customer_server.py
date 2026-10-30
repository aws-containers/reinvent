"""
Comprehensive test suite for Customer Information MCP Server.

This module tests all customer server functionality including:
- Endpoint testing (direct function calls)
- MCP client integration testing
- Standalone client testing
"""

import asyncio
import json
import pytest
import sys
from datetime import datetime
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
from mcp_servers.customer_server.server import (
    list_all_customers,
    list_all_claims,
    get_customer_profile,
    get_policy_details,
    create_claim,
    get_claim_history,
    get_claim_details,
    update_claim_status,
    check_appliance_coverage,
    load_mock_data
)


class TestCustomerServerEndpoints(BaseMCPEndpointTest):
    """Test customer server endpoints directly."""

    @property
    def server_name(self) -> str:
        return "Customer Information Server"

    @property
    def server_port(self) -> int:
        return 8001

    @property
    def server_module_path(self) -> str:
        return "mcp_servers.customer_server.server"

    @property
    def expected_tools(self) -> set:
        return {
            "list_all_customers",
            "list_all_claims",
            "get_customer_profile",
            "get_policy_details",
            "create_claim",
            "get_claim_history",
            "get_claim_details",
            "update_claim_status",
            "check_appliance_coverage"
        }

    def setup_test_data(self):
        """Set up test data before each test."""
        # Mock customer data
        self.mock_customers = {
            "CUST001": {
                "id": "CUST001",
                "name": "John Doe",
                "email": "john.doe@email.com",
                "phone": "555-123-4567",
                "address": "123 Main St, City, State 12345",
                "policy_number": "POL-2024-001",
                "covered_appliances": ["refrigerator", "washing_machine", "dishwasher"],
                "created_at": "2023-01-15T10:30:00",
                "policy_details": {
                    "coverage_type": "Premium Home Appliance Protection",
                    "deductible": 50,
                    "annual_limit": 5000,
                    "policy_start": "2023-01-15T00:00:00",
                    "policy_end": "2025-01-15T00:00:00",
                    "monthly_premium": 29.99
                }
            },
            "CUST002": {
                "id": "CUST002",
                "name": "Jane Smith",
                "email": "jane.smith@email.com",
                "phone": "555-987-6543",
                "address": "456 Oak Ave, City, State 12345",
                "policy_number": "POL-2024-002",
                "covered_appliances": ["refrigerator", "oven"],
                "created_at": "2023-02-20T14:15:00",
                "policy_details": {
                    "coverage_type": "Basic Home Appliance Protection",
                    "deductible": 100,
                    "annual_limit": 2000,
                    "policy_start": "2023-02-20T00:00:00",
                    "policy_end": "2025-02-20T00:00:00",
                    "monthly_premium": 15.99
                }
            }
        }

        # Mock claims data
        self.mock_claims = {
            "CLAIM001": {
                "id": "CLAIM001",
                "customer_id": "CUST001",
                "appliance_type": "refrigerator",
                "issue_description": "Refrigerator not cooling properly",
                "status": "approved",
                "urgency_level": "high",
                "created_at": "2024-01-15T10:30:00",
                "approved_at": "2024-01-15T11:00:00",
                "completed_at": None,
                "appointment_id": "APPT001",
                "estimated_cost": 250.0,
                "notes": "Emergency repair needed"
            },
            "CLAIM002": {
                "id": "CLAIM002",
                "customer_id": "CUST001",
                "appliance_type": "washing_machine",
                "issue_description": "Washing machine making loud noises",
                "status": "completed",
                "urgency_level": "medium",
                "created_at": "2024-01-10T09:00:00",
                "approved_at": "2024-01-10T10:00:00",
                "completed_at": "2024-01-12T15:30:00",
                "appointment_id": "APPT002",
                "estimated_cost": 150.0,
                "notes": "Repair completed successfully"
            }
        }

    def _call_server_function(self, func, *args, **kwargs):
        """Helper to call server functions and format response for testing framework."""
        # Ensure test data is set up
        if not hasattr(self, 'mock_customers'):
            self.setup_test_data()

        # Create fresh copies of the data for each test to avoid state pollution
        import copy
        fresh_customers = copy.deepcopy(self.mock_customers)
        fresh_claims = copy.deepcopy(self.mock_claims)

        # Patch the shared data functions with mock data
        with patch('mcp_servers.customer_server.server.get_customers_data', return_value=fresh_customers), \
             patch('mcp_servers.customer_server.server.get_claims_data', return_value=fresh_claims):

            result = func(*args, **kwargs)

            # Create a mock response object that matches what the framework expects
            class MockResponse:
                def __init__(self, text):
                    self.text = text

            return [MockResponse(result)]

    def test_get_customer_profile_success(self):
        """Test successful customer profile retrieval."""
        result = self._call_server_function(get_customer_profile, "CUST001")
        response_data = self.assert_successful_response(result, ["id", "name", "email", "phone", "policy_number"])

        assert response_data["id"] == "CUST001"
        assert response_data["name"] == "John Doe"
        assert response_data["email"] == "john.doe@email.com"
        assert response_data["phone"] == "555-123-4567"
        assert response_data["policy_number"] == "POL-2024-001"
        assert "refrigerator" in response_data["covered_appliances"]
        assert "policy_details" not in response_data  # Should not include policy details

    def test_get_customer_profile_not_found(self):
        """Test customer profile retrieval for non-existent customer."""
        result = self._call_server_function(get_customer_profile, "CUST999")
        self.assert_error_response(result, "Customer not found")

    def test_get_policy_details_success(self):
        """Test successful policy details retrieval."""
        result = self._call_server_function(get_policy_details, "CUST001")
        response_data = self.assert_successful_response(result, ["customer_id", "policy_number", "covered_appliances", "policy_details"])

        assert response_data["customer_id"] == "CUST001"
        assert response_data["policy_number"] == "POL-2024-001"
        assert "covered_appliances" in response_data
        assert "policy_details" in response_data
        assert response_data["policy_details"]["coverage_type"] == "Premium Home Appliance Protection"
        assert response_data["policy_details"]["deductible"] == 50
        assert response_data["active"] is True

    def test_get_policy_details_not_found(self):
        """Test policy details retrieval for non-existent customer."""
        result = self._call_server_function(get_policy_details, "CUST999")
        self.assert_error_response(result, "Customer not found")

    def test_create_claim_success(self):
        """Test successful claim creation."""
        result = self._call_server_function(
            create_claim,
            "CUST001",
            "dishwasher",
            "Dishwasher not draining water",
            "medium"
        )
        response_data = self.assert_successful_response(result, ["success", "claim_id", "status", "message"])

        assert response_data["success"] is True
        assert "claim_id" in response_data
        assert response_data["status"] == "submitted"
        assert response_data["message"] == "Claim created successfully"

    def test_create_claim_customer_not_found(self):
        """Test claim creation for non-existent customer."""
        result = self._call_server_function(
            create_claim,
            "CUST999",
            "refrigerator",
            "Not working",
            "high"
        )
        self.assert_error_response(result, "Customer not found")

    def test_create_claim_appliance_not_covered(self):
        """Test claim creation for non-covered appliance."""
        result = self._call_server_function(
            create_claim,
            "CUST001",
            "air_conditioner",
            "AC not cooling",
            "high"
        )
        response_data = self.assert_successful_response(result, ["error"])
        assert response_data["error"] == "Appliance not covered under policy"
        assert response_data["appliance_type"] == "air_conditioner"
        assert "covered_appliances" in response_data

    def test_get_claim_history_success(self):
        """Test successful claim history retrieval."""
        result = self._call_server_function(get_claim_history, "CUST001", "all")
        response_data = self.assert_successful_response(result, ["customer_id", "total_claims", "status_filter", "claims"])

        assert response_data["customer_id"] == "CUST001"
        assert response_data["total_claims"] == 2
        assert response_data["status_filter"] == "all"
        assert len(response_data["claims"]) == 2

        # Claims should be sorted by creation date (newest first)
        claims = response_data["claims"]
        assert claims[0]["id"] == "CLAIM001"  # More recent
        assert claims[1]["id"] == "CLAIM002"  # Older

    def test_get_claim_history_with_status_filter(self):
        """Test claim history retrieval with status filter."""
        result = self._call_server_function(get_claim_history, "CUST001", "active")
        response_data = self.assert_successful_response(result, ["customer_id", "status_filter", "total_claims", "claims"])

        assert response_data["customer_id"] == "CUST001"
        assert response_data["status_filter"] == "active"
        assert response_data["total_claims"] == 1  # Only approved claim
        assert response_data["claims"][0]["status"] == "approved"

    def test_get_claim_history_customer_not_found(self):
        """Test claim history retrieval for non-existent customer."""
        result = self._call_server_function(get_claim_history, "CUST999", "all")
        self.assert_error_response(result, "Customer not found")

    def test_get_claim_details_success(self):
        """Test successful claim details retrieval."""
        result = self._call_server_function(get_claim_details, "CLAIM001")
        response_data = self.assert_successful_response(result, ["id", "customer_id", "appliance_type", "status", "urgency_level"])

        assert response_data["id"] == "CLAIM001"
        assert response_data["customer_id"] == "CUST001"
        assert response_data["appliance_type"] == "refrigerator"
        assert response_data["status"] == "approved"
        assert response_data["urgency_level"] == "high"

    def test_get_claim_details_not_found(self):
        """Test claim details retrieval for non-existent claim."""
        result = self._call_server_function(get_claim_details, "CLAIM999")
        self.assert_error_response(result, "Claim not found")

    def test_update_claim_status_success(self):
        """Test successful claim status update."""
        result = self._call_server_function(update_claim_status, "CLAIM001", "completed", "Repair finished")
        response_data = self.assert_successful_response(result, ["success", "claim_id", "old_status", "new_status"])

        assert response_data["success"] is True
        assert response_data["claim_id"] == "CLAIM001"
        assert response_data["old_status"] == "approved"
        assert response_data["new_status"] == "completed"

    def test_update_claim_status_not_found(self):
        """Test claim status update for non-existent claim."""
        result = self._call_server_function(update_claim_status, "CLAIM999", "completed")
        self.assert_error_response(result, "Claim not found")

    def test_check_appliance_coverage_covered(self):
        """Test appliance coverage check for covered appliance."""
        result = self._call_server_function(check_appliance_coverage, "CUST001", "refrigerator")
        response_data = self.assert_successful_response(result, ["customer_id", "appliance_type", "is_covered"])

        assert response_data["customer_id"] == "CUST001"
        assert response_data["appliance_type"] == "refrigerator"
        assert response_data["is_covered"] is True
        assert "policy_info" in response_data
        assert response_data["policy_info"]["coverage_type"] == "Premium Home Appliance Protection"

    def test_check_appliance_coverage_not_covered(self):
        """Test appliance coverage check for non-covered appliance."""
        result = self._call_server_function(check_appliance_coverage, "CUST001", "air_conditioner")
        response_data = self.assert_successful_response(result, ["customer_id", "appliance_type", "is_covered"])

        assert response_data["customer_id"] == "CUST001"
        assert response_data["appliance_type"] == "air_conditioner"
        assert response_data["is_covered"] is False
        assert "policy_info" not in response_data

    def test_check_appliance_coverage_customer_not_found(self):
        """Test appliance coverage check for non-existent customer."""
        result = self._call_server_function(check_appliance_coverage, "CUST999", "refrigerator")
        self.assert_error_response(result, "Customer not found")

    def test_case_insensitive_appliance_matching(self):
        """Test that appliance matching is case insensitive."""
        # Test coverage check with different case
        result = self._call_server_function(check_appliance_coverage, "CUST001", "REFRIGERATOR")
        response_data = self.assert_successful_response(result, ["is_covered"])
        assert response_data["is_covered"] is True

        # Test claim creation with different case
        result = self._call_server_function(create_claim, "CUST001", "WASHING_MACHINE", "Issue", "low")
        response_data = self.assert_successful_response(result, ["success"])
        assert response_data["success"] is True

    def test_load_mock_data_error_handling(self):
        """Test load_mock_data error handling without affecting global state."""
        # This test verifies that load_mock_data handles errors gracefully
        # We test this by checking the function behavior in isolation

        # Test file not found
        with patch('builtins.open', side_effect=FileNotFoundError):
            load_mock_data()
            # Should handle gracefully

        # Test invalid JSON
        with patch('builtins.open', mock_open(read_data='invalid json')):
            load_mock_data()
            # Should handle gracefully

    def test_claim_id_generation(self):
        """Test that claim IDs are generated correctly."""
        result = self._call_server_function(create_claim, "CUST001", "dishwasher", "Test issue", "low")
        response_data = self.assert_successful_response(result, ["success", "claim_id"])

        # Verify the response is successful
        assert response_data["success"] is True
        assert "claim_id" in response_data
        # Claim ID should follow the pattern CLAIMXXX
        assert response_data["claim_id"].startswith("CLAIM")

    def test_claim_timestamps(self):
        """Test that claim timestamps are set correctly."""
        result = self._call_server_function(create_claim, "CUST001", "dishwasher", "Test issue", "low")
        response_data = self.assert_successful_response(result, ["success", "claim"])

        # Verify the response is successful
        assert response_data["success"] is True
        claim = response_data["claim"]
        assert "created_at" in claim
        assert claim["approved_at"] is None
        assert claim["completed_at"] is None


class TestCustomerServerIntegration(BaseMCPIntegrationTest):
    """Test customer server through MCP protocol."""

    @property
    def server_name(self) -> str:
        return "Customer Information Server"

    @property
    def server_port(self) -> int:
        return 8001

    @property
    def server_module_path(self) -> str:
        return "mcp_servers.customer_server.server"

    @property
    def expected_tools(self) -> set:
        return {
            "list_all_customers",
            "list_all_claims",
            "get_customer_profile",
            "get_policy_details",
            "create_claim",
            "get_claim_history",
            "get_claim_details",
            "update_claim_status",
            "check_appliance_coverage"
        }

    @pytest.mark.asyncio
    async def test_mcp_client_connection(self) -> bool:
        """Test MCP client connection with pytest-asyncio decorator."""
        return await super().test_mcp_client_connection()

    async def _test_tool_calls(self, session) -> bool:
        """Test specific tool calls for customer server."""
        print("\n🔧 Testing customer server tool calls...")

        try:
            # Test get_customer_profile
            print("  Testing get_customer_profile...")
            result = await session.call_tool("get_customer_profile", {"customer_id": "CUST001"})
            response_data = json.loads(result.content[0].text)
            assert "id" in response_data
            print("  ✓ get_customer_profile works")

            # Test get_policy_details
            print("  Testing get_policy_details...")
            result = await session.call_tool("get_policy_details", {"customer_id": "CUST001"})
            response_data = json.loads(result.content[0].text)
            assert "policy_details" in response_data
            print("  ✓ get_policy_details works")

            # Test check_appliance_coverage
            print("  Testing check_appliance_coverage...")
            result = await session.call_tool("check_appliance_coverage", {
                "customer_id": "CUST001",
                "appliance_type": "refrigerator"
            })
            response_data = json.loads(result.content[0].text)
            assert "is_covered" in response_data
            print("  ✓ check_appliance_coverage works")

            print("✓ All customer server tool calls successful")
            return True

        except Exception as e:
            print(f"✗ Tool call failed: {e}")
            return False


# Test runner functions
def test_customer_server_endpoints():
    """Run all endpoint tests."""
    test_class = TestCustomerServerEndpoints()
    test_class.setup_test_data()

    print("Running Customer Server Endpoint Tests...")

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


def test_customer_server_integration():
    """Run MCP integration test."""
    test_class = TestCustomerServerIntegration()

    print("Running Customer Server MCP Integration Test...")

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
    print("🧪 Customer Information MCP Server Test Suite")
    print("=" * 50)

    # Run endpoint tests
    test_customer_server_endpoints()

    # Run integration tests
    test_customer_server_integration()

    # Note: Standalone tests are now in integration-tests directory
    print("\n📝 To run standalone/integration tests:")
    print("1. Start the customer server: python -m mcp_servers.customer_server.server")
    print("2. Run: cd integration-tests && pytest test_customer_server_integration.py -v")
