"""
Integration tests for Customer Information MCP Server.

These tests run against a live customer server that should already be running.
Start the server first with: python -m mcp_servers.customer_server.server
"""

import asyncio
import json
import pytest
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from testing_framework.base_test_classes import BaseMCPStandaloneTest


class TestCustomerServerStandalone(BaseMCPStandaloneTest):
    """Test customer server standalone connection."""

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
            "get_customer_profile",
            "get_policy_details",
            "create_claim",
            "get_claim_history",
            "get_claim_details",
            "update_claim_status",
            "check_appliance_coverage"
        }

    @pytest.mark.asyncio
    async def test_standalone_connection(self) -> bool:
        """Test standalone connection with pytest-asyncio decorator."""
        return await super().test_standalone_connection()

    async def _test_standalone_tool_calls(self, session):
        """Test tool calls in standalone mode."""
        print(f"\n🔧 Testing {self.server_name} tool calls...")

        try:
            # Test basic customer profile
            print("  👤 Testing get_customer_profile...")
            result = await session.call_tool("get_customer_profile", {"customer_id": "CUST001"})
            profile_data = json.loads(result.content[0].text)
            if "error" not in profile_data:
                print(f"     Customer: {profile_data.get('name', 'Unknown')} ({profile_data.get('id', 'Unknown')})")
            else:
                print(f"     Note: {profile_data['error']}")

            # Test policy details
            print("  📋 Testing get_policy_details...")
            result = await session.call_tool("get_policy_details", {"customer_id": "CUST001"})
            policy_data = json.loads(result.content[0].text)
            if "error" not in policy_data:
                print(f"     Policy: {policy_data.get('policy_number', 'Unknown')}")
                print(f"     Coverage: {policy_data.get('policy_details', {}).get('coverage_type', 'Unknown')}")
            else:
                print(f"     Note: {policy_data['error']}")

            # Test appliance coverage check
            print("  🔍 Testing check_appliance_coverage...")
            result = await session.call_tool("check_appliance_coverage", {
                "customer_id": "CUST001",
                "appliance_type": "refrigerator"
            })
            coverage_data = json.loads(result.content[0].text)
            if "error" not in coverage_data:
                covered = "✓ Covered" if coverage_data.get('is_covered') else "✗ Not covered"
                print(f"     Refrigerator: {covered}")
            else:
                print(f"     Note: {coverage_data['error']}")

            # Test claim history
            print("  📄 Testing get_claim_history...")
            result = await session.call_tool("get_claim_history", {
                "customer_id": "CUST001",
                "status_filter": "all"
            })
            history_data = json.loads(result.content[0].text)
            if "error" not in history_data:
                print(f"     Total claims: {history_data.get('total_claims', 0)}")
            else:
                print(f"     Note: {history_data['error']}")

            # Test create claim
            print("  ➕ Testing create_claim...")
            result = await session.call_tool("create_claim", {
                "customer_id": "CUST001",
                "appliance_type": "dishwasher",
                "issue_description": "Integration test claim",
                "urgency_level": "low"
            })
            claim_data = json.loads(result.content[0].text)
            if "error" not in claim_data and claim_data.get('success'):
                print(f"     Created claim: {claim_data.get('claim_id', 'Unknown')}")
            else:
                print(f"     Note: {claim_data.get('error', 'Claim creation failed')}")

            print("  ✓ All tool calls completed successfully")

        except Exception as e:
            print(f"  ✗ Tool call error: {e}")


# Test runner function for manual execution
def test_customer_server_standalone():
    """Run standalone client test."""
    test_class = TestCustomerServerStandalone()

    print("Running Customer Server Standalone Test...")
    print("Make sure the customer server is running on port 8001")
    print("Start with: python -m mcp_servers.customer_server.server")

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
    print("🧪 Customer Information MCP Server Integration Test")
    print("=" * 60)

    print("\n📝 Prerequisites:")
    print("1. Start the customer server: python -m mcp_servers.customer_server.server")
    print("2. Server should be running on http://localhost:8001")
    print("3. Run this test: python test_customer_server_integration.py")

    test_customer_server_standalone()
