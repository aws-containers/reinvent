"""
Example implementation of Customer Server tests using the MCP testing framework.

This demonstrates how to use the standardized testing framework to create
comprehensive tests for the Customer Information MCP Server.
"""

import json
import pytest
from typing import Dict, Any, Set
from unittest.mock import patch

# Import the testing framework
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from base_test_classes import BaseMCPEndpointTest, BaseMCPIntegrationTest, BaseMCPStandaloneTest
from test_helpers import TestDataManager
from server_configs import get_customer_server_config
from test_templates import create_server_test_suite

# Import server functions for direct testing
sys.path.append(str(Path(__file__).parent.parent.parent))
from mcp_servers.customer_server.server import (
    get_customer_profile,
    get_policy_details,
    create_claim,
    get_claim_history,
    get_claim_details,
    update_claim_status,
    check_appliance_coverage,
    customers_data,
    claims_data
)


class CustomerServerEndpointTest(BaseMCPEndpointTest):
    """Endpoint tests for Customer Information MCP Server."""

    @property
    def server_name(self) -> str:
        return "Customer Information Server"

    @property
    def server_port(self) -> int:
        return 8001

    @property
    def server_module_path(self) -> str:
        return "mcp_servers.customer_server.server.main"

    @property
    def expected_tools(self) -> Set[str]:
        return {
            "get_customer_profile",
            "get_policy_details",
            "create_claim",
            "get_claim_history",
            "get_claim_details",
            "update_claim_status",
            "check_appliance_coverage"
        }

    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Set up test data before each test."""
        # Clear existing data
        customers_data.clear()
        claims_data.clear()

        # Set up mock customer data
        customers_data.update({
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
            }
        })

        # Set up mock claims data
        claims_data.update({
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
            }
        })

    async def test_get_customer_profile_success(self):
        """Test successful customer profile retrieval."""
        result = await get_customer_profile("CUST001")
        response_data = self.assert_successful_response(result, ["id", "name", "email"])

        assert response_data["id"] == "CUST001"
        assert response_data["name"] == "John Doe"
        assert response_data["email"] == "john.doe@email.com"

    async def test_get_customer_profile_not_found(self):
        """Test customer profile retrieval for non-existent customer."""
        result = await get_customer_profile("CUST999")
        self.assert_error_response(result, "Customer not found")

    async def test_create_claim_success(self):
        """Test successful claim creation."""
        result = await create_claim("CUST001", "dishwasher", "Not draining", "medium")
        response_data = self.assert_successful_response(result, ["claim_id", "status"])

        assert response_data["status"] == "submitted"
        assert "claim_id" in response_data

    async def test_create_claim_appliance_not_covered(self):
        """Test claim creation for non-covered appliance."""
        result = await create_claim("CUST001", "air_conditioner", "Not cooling", "high")
        self.assert_error_response(result, "Appliance not covered under policy")


class CustomerServerIntegrationTest(BaseMCPIntegrationTest):
    """Integration tests for Customer Information MCP Server."""

    @property
    def server_name(self) -> str:
        return "Customer Information Server"

    @property
    def server_port(self) -> int:
        return 8001

    @property
    def server_module_path(self) -> str:
        return "mcp_servers.customer_server.server.main"

    @property
    def expected_tools(self) -> Set[str]:
        return {
            "get_customer_profile",
            "get_policy_details",
            "create_claim",
            "get_claim_history",
            "get_claim_details",
            "update_claim_status",
            "check_appliance_coverage"
        }

    async def _test_tool_calls(self, session) -> bool:
        """Test calling tools with sample data."""
        print("\nTesting tool calls...")

        # Test get_customer_profile
        try:
            print("Testing get_customer_profile...")
            result = await session.call_tool("get_customer_profile", {"customer_id": "CUST001"})
            print("✓ get_customer_profile call successful")

            if result.content:
                print(f"✓ Tool returned content (length: {len(str(result.content))})")

            return True

        except Exception as e:
            print(f"✗ Tool call failed: {e}")
            return False


class CustomerServerStandaloneTest(BaseMCPStandaloneTest):
    """Standalone tests for Customer Information MCP Server."""

    @property
    def server_name(self) -> str:
        return "Customer Information Server"

    @property
    def server_port(self) -> int:
        return 8001

    @property
    def server_module_path(self) -> str:
        return "mcp_servers.customer_server.server.main"

    @property
    def expected_tools(self) -> Set[str]:
        return {
            "get_customer_profile",
            "get_policy_details",
            "create_claim",
            "get_claim_history",
            "get_claim_details",
            "update_claim_status",
            "check_appliance_coverage"
        }

    async def _test_standalone_tool_calls(self, session):
        """Test tool calls in standalone mode."""
        print(f"\n🔧 Testing tool calls...")

        try:
            print("Testing get_customer_profile...")
            result = await session.call_tool("get_customer_profile", {"customer_id": "CUST001"})
            print("✓ get_customer_profile successful!")

            if result.content:
                content_str = str(result.content[0].text) if result.content else "No content"
                print(f"📄 Response preview: {content_str[:100]}...")

        except Exception as e:
            print(f"✗ get_customer_profile failed: {e}")


# Example of using the template system
def create_customer_server_test_suite():
    """Create a complete test suite for the Customer server using templates."""
    config = get_customer_server_config()
    return create_server_test_suite(
        config['name'],
        config['port'],
        config['module_path'],
        config['expected_tools'],
        config['sample_tool_calls']
    )


# Example test runner functions
async def run_customer_endpoint_tests():
    """Run endpoint tests for Customer server."""
    test_instance = CustomerServerEndpointTest()

    # Set up test data
    test_instance.setup_test_data()

    # Run tests
    test_methods = [
        'test_get_customer_profile_success',
        'test_get_customer_profile_not_found',
        'test_create_claim_success',
        'test_create_claim_appliance_not_covered'
    ]

    from test_helpers import TestRunner
    results = TestRunner.run_endpoint_test_suite(test_instance, test_methods)
    TestRunner.print_test_summary(results, "Customer Endpoint Tests")

    return results


async def run_customer_integration_test():
    """Run integration test for Customer server."""
    test_instance = CustomerServerIntegrationTest()
    success = await test_instance.test_mcp_client_connection()

    print(f"\nCustomer Integration Test: {'PASSED' if success else 'FAILED'}")
    return success


async def run_customer_standalone_test():
    """Run standalone test for Customer server."""
    test_instance = CustomerServerStandaloneTest()
    success = await test_instance.test_standalone_connection()

    print(f"\nCustomer Standalone Test: {'PASSED' if success else 'FAILED'}")
    return success


if __name__ == "__main__":
    import asyncio

    print("Running Customer Server Tests using MCP Testing Framework")
    print("=" * 60)

    # Run endpoint tests
    print("\n1. Running Endpoint Tests...")
    asyncio.run(run_customer_endpoint_tests())

    # Run integration test
    print("\n2. Running Integration Test...")
    asyncio.run(run_customer_integration_test())

    # Note: Standalone test requires server to be running
    print("\n3. Standalone Test Available")
    print("   To run: Start server with 'python test_customer_server.py'")
    print("   Then run: asyncio.run(run_customer_standalone_test())")
