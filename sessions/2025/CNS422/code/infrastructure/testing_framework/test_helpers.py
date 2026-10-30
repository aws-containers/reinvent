"""
Helper functions for MCP server testing framework.

This module provides utility functions for common testing operations
including server management, data setup, and test execution patterns.
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
from unittest.mock import patch, mock_open

import pytest


class ServerManager:
    """
    Helper class for managing MCP server processes during testing.

    Provides standardized methods for starting, stopping, and monitoring
    MCP servers across different ports and configurations.
    """

    def __init__(self, server_name: str, server_port: int, server_module_path: str,
                 startup_timeout: int = 4, host: str = "localhost"):
        """
        Initialize the server manager.

        Args:
            server_name: Human-readable name of the server
            server_port: Port number the server runs on
            server_module_path: Python module path to the server's main function
            startup_timeout: Timeout in seconds for server startup
            host: Host the server runs on
        """
        self.server_name = server_name
        self.server_port = server_port
        self.server_module_path = server_module_path
        self.startup_timeout = startup_timeout
        self.host = host
        self.process: Optional[subprocess.Popen] = None

    async def start_server(self) -> subprocess.Popen:
        """
        Start the MCP server in a subprocess.

        Returns:
            The subprocess.Popen object for the server process

        Raises:
            RuntimeError: If the server fails to start
        """
        print(f"Starting {self.server_name} on {self.host}:{self.server_port}...")

        self.process = subprocess.Popen(
            [sys.executable, "-c", f"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from {self.server_module_path} import main
main()
"""],
            cwd=Path(__file__).parent.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait for server to start
        print(f"Waiting {self.startup_timeout} seconds for server to start...")
        time.sleep(self.startup_timeout)

        # Check if server is still running
        if self.process.poll() is not None:
            stdout, stderr = self.process.communicate()
            raise RuntimeError(f"Server failed to start. stdout: {stdout}, stderr: {stderr}")

        print(f"✓ {self.server_name} started successfully")
        return self.process

    async def stop_server(self):
        """Stop the MCP server process."""
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                print(f"✓ {self.server_name} terminated cleanly")
            except subprocess.TimeoutExpired:
                self.process.kill()
                print(f"✓ {self.server_name} killed")
            except Exception as e:
                print(f"Warning: Could not terminate {self.server_name}: {e}")
        self.process = None

    def is_running(self) -> bool:
        """Check if the server process is currently running."""
        return self.process is not None and self.process.poll() is None

    @property
    def mcp_url(self) -> str:
        """Get the MCP URL for client connections."""
        return f"http://{self.host}:{self.server_port}/mcp"


class MCPClientHelper:
    """
    Helper class for MCP client operations.

    Provides standardized methods for connecting to MCP servers and
    performing common operations like listing tools and calling functions.
    """

    def __init__(self, mcp_url: str, timeout: int = 30):
        """
        Initialize the MCP client helper.

        Args:
            mcp_url: URL of the MCP server
            timeout: Timeout in seconds for client operations
        """
        self.mcp_url = mcp_url
        self.timeout = timeout

    async def test_connection_and_tools(self, expected_tools: set) -> bool:
        """
        Test MCP connection and verify expected tools are available.

        Args:
            expected_tools: Set of expected tool names

        Returns:
            True if connection successful and all tools found, False otherwise
        """
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client

        headers = {}

        try:
            async with streamablehttp_client(
                self.mcp_url,
                headers,
                timeout=self.timeout,
                terminate_on_close=False
            ) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    print("✓ Successfully connected to MCP server")

                    # Initialize the session
                    await session.initialize()
                    print("✓ Session initialized successfully")

                    # List and verify tools
                    tool_result = await session.list_tools()
                    print("✓ Successfully retrieved tools list")

                    found_tools = {tool.name for tool in tool_result.tools}

                    print("\nAvailable tools:")
                    for tool in tool_result.tools:
                        print(f"  - {tool.name}: {tool.description}")

                    # Verify all expected tools are present
                    missing_tools = expected_tools - found_tools
                    if missing_tools:
                        print(f"✗ Missing expected tools: {missing_tools}")
                        return False

                    extra_tools = found_tools - expected_tools
                    if extra_tools:
                        print(f"ℹ Found additional tools: {extra_tools}")

                    print(f"\n✓ Found {len(found_tools)} tools (expected {len(expected_tools)})")

                    # Test resources (optional)
                    try:
                        resource_result = await session.list_resources()
                        print("✓ Successfully retrieved resources list")
                        print(f"✓ Found {len(resource_result.resources)} resources")
                    except Exception as e:
                        print(f"ℹ Resources list not available: {e}")

                    return True

        except Exception as e:
            print(f"✗ MCP connection failed: {e}")
            return False

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a specific tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            The result of the tool call

        Raises:
            Exception: If the tool call fails
        """
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client

        headers = {}

        async with streamablehttp_client(
            self.mcp_url,
            headers,
            timeout=self.timeout,
            terminate_on_close=False
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                return result


class TestDataManager:
    """
    Helper class for managing test data across different MCP servers.

    Provides standardized methods for setting up mock data, clearing state,
    and creating test fixtures that can be reused across different test suites.
    """

    @staticmethod
    def create_mock_file_patch(file_content: Dict[str, Any]) -> Any:
        """
        Create a mock file patch for testing file loading operations.

        Args:
            file_content: Dictionary to be serialized as JSON file content

        Returns:
            Mock patch object for file operations
        """
        json_content = json.dumps(file_content, indent=2)
        return mock_open(read_data=json_content)

    @staticmethod
    def create_file_not_found_patch() -> Any:
        """
        Create a mock patch that simulates file not found errors.

        Returns:
            Mock patch object that raises FileNotFoundError
        """
        return patch('builtins.open', side_effect=FileNotFoundError)

    @staticmethod
    def create_invalid_json_patch() -> Any:
        """
        Create a mock patch that simulates invalid JSON content.

        Returns:
            Mock patch object with invalid JSON content
        """
        return patch('builtins.open', mock_open(read_data='invalid json'))

    @staticmethod
    def assert_json_response(result: List[Any], expected_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Assert that a result contains valid JSON and optionally check for specific keys.

        Args:
            result: The result from a server function call
            expected_keys: Optional list of keys that should be present

        Returns:
            The parsed JSON data as a dictionary

        Raises:
            AssertionError: If the response is invalid or missing expected keys
        """
        assert len(result) == 1, f"Expected 1 result item, got {len(result)}"

        try:
            response_data = json.loads(result[0].text)
        except (json.JSONDecodeError, AttributeError) as e:
            pytest.fail(f"Invalid JSON response: {result[0] if result else 'No result'}")

        if expected_keys:
            for key in expected_keys:
                assert key in response_data, f"Expected key '{key}' not found in response: {response_data}"

        return response_data

    @staticmethod
    def assert_error_response(result: List[Any], expected_error: str) -> Dict[str, Any]:
        """
        Assert that a result contains an error response with the expected message.

        Args:
            result: The result from a server function call
            expected_error: The expected error message

        Returns:
            The parsed JSON data as a dictionary
        """
        response_data = TestDataManager.assert_json_response(result, ["error"])
        assert response_data["error"] == expected_error, \
            f"Expected error '{expected_error}', got '{response_data['error']}'"
        return response_data

    @staticmethod
    def assert_success_response(result: List[Any], expected_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Assert that a result contains a successful response.

        Args:
            result: The result from a server function call
            expected_keys: Optional list of keys that should be present

        Returns:
            The parsed JSON data as a dictionary
        """
        if expected_keys is None:
            expected_keys = ["success"]
        elif "success" not in expected_keys:
            expected_keys = ["success"] + expected_keys

        response_data = TestDataManager.assert_json_response(result, expected_keys)
        assert response_data.get("success") is True, \
            f"Expected successful response, got: {response_data}"
        return response_data


class TestRunner:
    """
    Helper class for running standardized test suites across multiple MCP servers.

    Provides methods for executing common test patterns and collecting results
    in a consistent format.
    """

    @staticmethod
    async def run_integration_test_suite(server_configs: List[Dict[str, Any]]) -> Dict[str, bool]:
        """
        Run integration tests for multiple MCP servers.

        Args:
            server_configs: List of server configuration dictionaries, each containing:
                - name: Server name
                - port: Server port
                - module_path: Python module path
                - expected_tools: Set of expected tool names

        Returns:
            Dictionary mapping server names to test results (True/False)
        """
        results = {}

        for config in server_configs:
            print(f"\n{'='*60}")
            print(f"Testing {config['name']} (Port {config['port']})")
            print(f"{'='*60}")

            server_manager = ServerManager(
                config['name'],
                config['port'],
                config['module_path']
            )

            try:
                # Start server
                await server_manager.start_server()

                # Test MCP connection
                client_helper = MCPClientHelper(server_manager.mcp_url)
                success = await client_helper.test_connection_and_tools(config['expected_tools'])

                results[config['name']] = success

                if success:
                    print(f"\n🎉 {config['name']} integration test PASSED!")
                else:
                    print(f"\n❌ {config['name']} integration test FAILED!")

            except Exception as e:
                print(f"\n❌ {config['name']} integration test FAILED with exception: {e}")
                results[config['name']] = False

            finally:
                # Clean up
                await server_manager.stop_server()

        return results

    @staticmethod
    def run_endpoint_test_suite(test_class_instance: Any, test_methods: List[str]) -> Dict[str, bool]:
        """
        Run endpoint tests for a specific server.

        Args:
            test_class_instance: Instance of a test class
            test_methods: List of test method names to run

        Returns:
            Dictionary mapping test method names to results (True/False)
        """
        results = {}

        for method_name in test_methods:
            try:
                method = getattr(test_class_instance, method_name)
                if asyncio.iscoroutinefunction(method):
                    asyncio.run(method())
                else:
                    method()
                results[method_name] = True
                print(f"✓ {method_name} passed")
            except Exception as e:
                results[method_name] = False
                print(f"✗ {method_name} failed: {e}")

        return results

    @staticmethod
    def print_test_summary(results: Dict[str, bool], test_type: str = "Test"):
        """
        Print a summary of test results.

        Args:
            results: Dictionary mapping test names to results
            test_type: Type of tests being summarized
        """
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        failed_tests = total_tests - passed_tests

        print(f"\n{'='*60}")
        print(f"{test_type} Summary")
        print(f"{'='*60}")
        print(f"Total: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")

        if failed_tests > 0:
            print(f"\nFailed tests:")
            for test_name, result in results.items():
                if not result:
                    print(f"  ✗ {test_name}")

        print(f"\nSuccess rate: {(passed_tests/total_tests)*100:.1f}%")
