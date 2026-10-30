"""
Standardized test templates for MCP servers.

This module provides template classes and functions that can be used to
quickly create consistent test suites for new MCP servers. Templates
include common test patterns and can be customized for specific server needs.
"""

import asyncio
import pytest
from abc import ABC, abstractmethod
from typing import Dict, List, Set, Any, Optional

try:
    from .base_test_classes import (
        BaseMCPEndpointTest,
        BaseMCPIntegrationTest,
        BaseMCPStandaloneTest,
        BaseMCPServerStartupTest
    )
    from .test_helpers import TestDataManager, MCPClientHelper
except ImportError:
    # Handle case when imported directly
    from base_test_classes import (
        BaseMCPEndpointTest,
        BaseMCPIntegrationTest,
        BaseMCPStandaloneTest,
        BaseMCPServerStartupTest
    )
    from test_helpers import TestDataManager, MCPClientHelper


class StandardMCPServerEndpointTestTemplate(BaseMCPEndpointTest):
    """
    Template for creating endpoint tests for MCP servers.

    This template provides a standard structure for testing server endpoints
    directly. Subclasses need to implement the abstract methods and can
    override test methods as needed.
    """

    @abstractmethod
    def get_test_data(self) -> Dict[str, Any]:
        """
        Get test data for the server.

        Returns:
            Dictionary containing test data that will be used in tests
        """
        pass

    @abstractmethod
    def setup_mock_data(self):
        """Set up mock data for testing."""
        pass

    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Set up test data before each test."""
        self.setup_mock_data()

    async def test_server_functions_exist(self):
        """Test that all expected server functions exist and are callable."""
        # This is a basic test that can be overridden by subclasses
        print(f"Testing {self.server_name} function availability...")

        # Subclasses should implement specific function existence tests
        assert True, "Override this method to test specific server functions"

    async def test_data_loading(self):
        """Test that mock data can be loaded successfully."""
        print(f"Testing {self.server_name} data loading...")

        # Test successful data loading
        try:
            self.setup_mock_data()
            print("✓ Mock data loaded successfully")
        except Exception as e:
            assert False, f"Failed to load mock data: {e}"

    async def test_error_handling(self):
        """Test error handling for common failure scenarios."""
        print(f"Testing {self.server_name} error handling...")

        # Subclasses should implement specific error handling tests
        print("ℹ Override this method to test specific error scenarios")


class StandardMCPServerIntegrationTestTemplate(BaseMCPIntegrationTest):
    """
    Template for creating integration tests for MCP servers.

    This template provides a standard structure for testing MCP servers
    through the MCP protocol. It includes common test patterns that
    most servers will need.
    """

    async def _test_tool_calls(self, session) -> bool:
        """Test calling tools with sample data."""
        print("\nTesting tool calls...")

        # Get sample tool calls from subclass
        sample_calls = self.get_sample_tool_calls()

        if not sample_calls:
            print("ℹ No sample tool calls defined")
            return True

        for tool_name, arguments in sample_calls.items():
            try:
                print(f"Testing {tool_name}...")
                result = await session.call_tool(tool_name, arguments)
                print(f"✓ {tool_name} call successful")

                if result.content:
                    print(f"✓ Tool returned content (length: {len(str(result.content))})")

            except Exception as e:
                print(f"✗ {tool_name} call failed: {e}")
                return False

        return True

    def get_sample_tool_calls(self) -> Dict[str, Dict[str, Any]]:
        """
        Get sample tool calls for testing.

        Returns:
            Dictionary mapping tool names to their arguments for testing
        """
        # Subclasses should override this to provide specific tool calls
        return {}


class StandardMCPServerStandaloneTestTemplate(BaseMCPStandaloneTest):
    """
    Template for creating standalone tests for MCP servers.

    This template provides a standard structure for testing against
    already running MCP servers.
    """

    async def _test_standalone_tool_calls(self, session):
        """Test tool calls in standalone mode."""
        print(f"\n🔧 Testing tool calls...")

        # Get sample tool calls from subclass
        sample_calls = self.get_sample_tool_calls()

        if not sample_calls:
            print("ℹ No sample tool calls defined")
            return

        for tool_name, arguments in sample_calls.items():
            try:
                print(f"Testing {tool_name}...")
                result = await session.call_tool(tool_name, arguments)
                print(f"✓ {tool_name} successful!")

                if result.content:
                    content_str = str(result.content[0].text) if result.content else "No content"
                    print(f"📄 Response preview: {content_str[:100]}...")

            except Exception as e:
                print(f"✗ {tool_name} failed: {e}")

    def get_sample_tool_calls(self) -> Dict[str, Dict[str, Any]]:
        """
        Get sample tool calls for testing.

        Returns:
            Dictionary mapping tool names to their arguments for testing
        """
        # Subclasses should override this to provide specific tool calls
        return {}


def create_server_test_suite(
    server_name: str,
    server_port: int,
    server_module_path: str,
    expected_tools: Set[str],
    sample_tool_calls: Optional[Dict[str, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Create a complete test suite for an MCP server.

    This function generates test classes for endpoint testing, integration testing,
    and standalone testing based on the provided server configuration.

    Args:
        server_name: Human-readable name of the server
        server_port: Port number the server runs on
        server_module_path: Python module path to the server's main function
        expected_tools: Set of expected tool names
        sample_tool_calls: Optional dictionary of sample tool calls for testing

    Returns:
        Dictionary containing test classes and helper functions
    """

    if sample_tool_calls is None:
        sample_tool_calls = {}

    class GeneratedEndpointTest(StandardMCPServerEndpointTestTemplate):
        @property
        def server_name(self) -> str:
            return server_name

        @property
        def server_port(self) -> int:
            return server_port

        @property
        def server_module_path(self) -> str:
            return server_module_path

        @property
        def expected_tools(self) -> Set[str]:
            return expected_tools

        def get_test_data(self) -> Dict[str, Any]:
            return {}

        def setup_mock_data(self):
            pass

    class GeneratedIntegrationTest(StandardMCPServerIntegrationTestTemplate):
        @property
        def server_name(self) -> str:
            return server_name

        @property
        def server_port(self) -> int:
            return server_port

        @property
        def server_module_path(self) -> str:
            return server_module_path

        @property
        def expected_tools(self) -> Set[str]:
            return expected_tools

        def get_sample_tool_calls(self) -> Dict[str, Dict[str, Any]]:
            return sample_tool_calls

    class GeneratedStandaloneTest(StandardMCPServerStandaloneTestTemplate):
        @property
        def server_name(self) -> str:
            return server_name

        @property
        def server_port(self) -> int:
            return server_port

        @property
        def server_module_path(self) -> str:
            return server_module_path

        @property
        def expected_tools(self) -> Set[str]:
            return expected_tools

        def get_sample_tool_calls(self) -> Dict[str, Dict[str, Any]]:
            return sample_tool_calls

    class GeneratedStartupTest(BaseMCPServerStartupTest):
        @property
        def server_name(self) -> str:
            return server_name

        @property
        def server_port(self) -> int:
            return server_port

        @property
        def server_module_path(self) -> str:
            return server_module_path

        @property
        def expected_tools(self) -> Set[str]:
            return expected_tools

    return {
        'endpoint_test': GeneratedEndpointTest,
        'integration_test': GeneratedIntegrationTest,
        'standalone_test': GeneratedStandaloneTest,
        'startup_test': GeneratedStartupTest,
        'server_config': {
            'name': server_name,
            'port': server_port,
            'module_path': server_module_path,
            'expected_tools': expected_tools,
            'sample_tool_calls': sample_tool_calls
        }
    }


def create_multi_server_test_runner(server_configs: List[Dict[str, Any]]) -> Any:
    """
    Create a test runner for multiple MCP servers.

    Args:
        server_configs: List of server configuration dictionaries

    Returns:
        Test runner class that can execute tests across multiple servers
    """

    class MultiServerTestRunner:
        def __init__(self):
            self.server_configs = server_configs

        async def run_all_integration_tests(self) -> Dict[str, bool]:
            """Run integration tests for all configured servers."""
            from .test_helpers import TestRunner
            return await TestRunner.run_integration_test_suite(self.server_configs)

        async def run_all_standalone_tests(self) -> Dict[str, bool]:
            """Run standalone tests for all configured servers."""
            results = {}

            for config in self.server_configs:
                print(f"\n{'='*60}")
                print(f"Standalone Test: {config['name']} (Port {config['port']})")
                print(f"{'='*60}")

                test_suite = create_server_test_suite(
                    config['name'],
                    config['port'],
                    config['module_path'],
                    config['expected_tools'],
                    config.get('sample_tool_calls', {})
                )

                standalone_test = test_suite['standalone_test']()

                try:
                    success = await standalone_test.test_standalone_connection()
                    results[config['name']] = success
                except Exception as e:
                    print(f"❌ Standalone test failed: {e}")
                    results[config['name']] = False

            return results

        def print_summary(self, results: Dict[str, bool], test_type: str = "Test"):
            """Print test results summary."""
            from .test_helpers import TestRunner
            TestRunner.print_test_summary(results, test_type)

    return MultiServerTestRunner
