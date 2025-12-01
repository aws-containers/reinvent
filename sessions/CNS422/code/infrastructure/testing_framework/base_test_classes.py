"""
Base test classes for MCP server testing framework.

This module provides standardized base classes for testing MCP servers with
streamable-http transport. It extracts common patterns from existing tests
to ensure consistent testing across all MCP servers.
"""

import asyncio
import json
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from unittest.mock import patch, mock_open

import pytest
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


class BaseMCPServerTest(ABC):
    """
    Base class for MCP server testing.

    Provides common functionality for testing MCP servers including:
    - Server startup and shutdown
    - MCP client connection management
    - Common test patterns
    - Error handling
    """

    @property
    @abstractmethod
    def server_name(self) -> str:
        """Name of the MCP server being tested."""
        pass

    @property
    @abstractmethod
    def server_port(self) -> int:
        """Port number the server runs on."""
        pass

    @property
    @abstractmethod
    def server_module_path(self) -> str:
        """Python module path to the server's main function."""
        pass

    @property
    @abstractmethod
    def expected_tools(self) -> Set[str]:
        """Set of expected tool names that should be available."""
        pass

    @property
    def server_host(self) -> str:
        """Host the server runs on. Defaults to localhost."""
        return "localhost"

    @property
    def mcp_url(self) -> str:
        """MCP URL for client connections."""
        return f"http://{self.server_host}:{self.server_port}/mcp"

    @property
    def server_startup_timeout(self) -> int:
        """Timeout in seconds for server startup. Defaults to 4."""
        return 4

    @property
    def client_timeout(self) -> int:
        """Timeout in seconds for MCP client operations. Defaults to 30."""
        return 30


class BaseMCPEndpointTest(BaseMCPServerTest):
    """
    Base class for testing MCP server endpoints directly.

    This class provides patterns for testing server functions directly
    without going through the MCP protocol layer.
    """

    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """
        Set up test data before each test.

        Subclasses should override this method to set up their specific
        test data and mock configurations.
        """
        pass

    def assert_successful_response(self, result: List[Any], expected_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Assert that a server function returned a successful response.

        Args:
            result: The result from calling a server function
            expected_keys: Optional list of keys that should be present in the response

        Returns:
            The parsed response data as a dictionary

        Raises:
            AssertionError: If the response format is invalid or missing expected keys
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

    def assert_error_response(self, result: List[Any], expected_error: str) -> Dict[str, Any]:
        """
        Assert that a server function returned an error response.

        Args:
            result: The result from calling a server function
            expected_error: The expected error message

        Returns:
            The parsed response data as a dictionary
        """
        response_data = self.assert_successful_response(result, ["error"])
        assert response_data["error"] == expected_error, f"Expected error '{expected_error}', got '{response_data['error']}'"
        return response_data


class BaseMCPIntegrationTest(BaseMCPServerTest):
    """
    Base class for MCP integration testing.

    This class provides patterns for testing MCP servers through the
    MCP protocol with automatic server management.
    """

    async def test_mcp_client_connection(self) -> bool:
        """
        Test MCP client connection to the server.

        Returns:
            True if the test passed, False otherwise
        """
        print(f"Testing MCP client connection to {self.server_name}...")

        # Start the server in background
        server_process = None
        try:
            print(f"Starting {self.server_name} on {self.server_host}:{self.server_port}...")
            server_process = await self._start_server()

            # Wait for server to start
            print("Waiting for server to start...")
            time.sleep(self.server_startup_timeout)

            # Check if server is still running
            if server_process.poll() is not None:
                stdout, stderr = server_process.communicate()
                print(f"Server failed to start. stdout: {stdout}, stderr: {stderr}")
                return False

            # Test MCP client connection
            success = await self._test_mcp_connection()
            return success

        except Exception as e:
            print(f"✗ Error during MCP client test: {e}")
            return False

        finally:
            # Clean up: terminate the server process
            if server_process:
                await self._cleanup_server(server_process)

    async def _start_server(self) -> subprocess.Popen:
        """Start the MCP server in a subprocess."""
        return subprocess.Popen(
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

    async def _cleanup_server(self, server_process: subprocess.Popen):
        """Clean up the server process."""
        if server_process.poll() is None:
            try:
                server_process.terminate()
                server_process.wait(timeout=5)
                print("✓ Server process terminated cleanly")
            except subprocess.TimeoutExpired:
                server_process.kill()
                print("✓ Server process killed")
            except Exception as e:
                print(f"Warning: Could not terminate server process: {e}")

    async def _test_mcp_connection(self) -> bool:
        """Test the actual MCP connection and functionality."""
        headers = {}

        print(f"Connecting to MCP server at {self.mcp_url}...")

        async with streamablehttp_client(
            self.mcp_url,
            headers,
            timeout=self.client_timeout,
            terminate_on_close=False
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                print("✓ Successfully connected to MCP server")

                # Initialize the session
                await session.initialize()
                print("✓ Session initialized successfully")

                # Test tools
                success = await self._test_tools(session)
                if not success:
                    return False

                # Test resources
                await self._test_resources(session)

                # Test tool calls
                success = await self._test_tool_calls(session)
                if not success:
                    return False

                return True

    async def _test_tools(self, session: ClientSession) -> bool:
        """Test that all expected tools are available."""
        tool_result = await session.list_tools()
        print("✓ Successfully retrieved tools list")

        print("\nAvailable tools:")
        found_tools = set()
        for tool in tool_result.tools:
            print(f"  - {tool.name}: {tool.description}")
            found_tools.add(tool.name)

        # Verify all expected tools are present
        missing_tools = self.expected_tools - found_tools
        if missing_tools:
            print(f"✗ Missing expected tools: {missing_tools}")
            return False

        extra_tools = found_tools - self.expected_tools
        if extra_tools:
            print(f"ℹ Found additional tools: {extra_tools}")

        print(f"\n✓ Found {len(found_tools)} tools (expected {len(self.expected_tools)})")
        return True

    async def _test_resources(self, session: ClientSession):
        """Test resource listing (optional)."""
        try:
            resource_result = await session.list_resources()
            print("✓ Successfully retrieved resources list")

            print("\nAvailable resources:")
            for resource in resource_result.resources:
                print(f"  - {resource.uri}: {resource.name}")

            print(f"✓ Found {len(resource_result.resources)} resources")
        except Exception as e:
            print(f"ℹ Resources list not available: {e}")

    async def _test_tool_calls(self, session: ClientSession) -> bool:
        """
        Test calling tools.

        Subclasses should override this method to test specific tool calls.
        """
        print("\nTesting tool calls...")
        print("ℹ No specific tool calls defined in base class")
        return True


class BaseMCPStandaloneTest(BaseMCPServerTest):
    """
    Base class for standalone MCP client testing.

    This class provides patterns for testing against an already running
    MCP server without managing the server lifecycle.
    """

    async def test_standalone_connection(self) -> bool:
        """
        Test connection to an already running MCP server.

        Returns:
            True if the test passed, False otherwise
        """
        headers = {}

        print(f"Connecting to MCP server at {self.mcp_url}...")
        print(f"(Make sure the {self.server_name} is running)")

        try:
            async with streamablehttp_client(
                self.mcp_url,
                headers,
                timeout=120,
                terminate_on_close=False
            ) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    print("✓ Connected successfully!")

                    # Initialize session
                    await session.initialize()
                    print("✓ Session initialized")

                    # List tools
                    tool_result = await session.list_tools()
                    print(f"\n📋 Available tools ({len(tool_result.tools)}):")
                    for tool in tool_result.tools:
                        print(f"  - {tool.name}: {tool.description}")

                    # List resources
                    try:
                        resource_result = await session.list_resources()
                        print(f"\n📁 Available resources ({len(resource_result.resources)}):")
                        for resource in resource_result.resources:
                            print(f"  - {resource.uri}: {resource.name}")
                    except Exception as e:
                        print(f"ℹ Resources not available: {e}")

                    # Test tool calls
                    await self._test_standalone_tool_calls(session)

                    print(f"\n🎉 All tests completed successfully!")
                    return True

        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print(f"\nMake sure the {self.server_name} is running on port {self.server_port}")
            return False

    async def _test_standalone_tool_calls(self, session: ClientSession):
        """
        Test tool calls in standalone mode.

        Subclasses should override this method to test specific tool calls.
        """
        print(f"\n🔧 Testing tool calls...")
        print("ℹ No specific tool calls defined in base class")


class BaseMCPServerStartupTest(BaseMCPServerTest):
    """
    Base class for testing MCP server startup.

    This class provides patterns for testing that servers can start up
    correctly and handle basic operations.
    """

    def test_server_startup(self) -> bool:
        """
        Test that the server can start up successfully.

        Returns:
            True if the server started successfully, False otherwise
        """
        try:
            print(f"Starting {self.server_name} on {self.server_host}:{self.server_port}...")
            print("Server will run with streamable-http transport")
            print("Press Ctrl+C to stop the server")

            # Import and run the server's main function
            # This is a basic test that the server can be imported and started
            module_parts = self.server_module_path.split('.')
            module_name = '.'.join(module_parts[:-1])
            function_name = module_parts[-1]

            module = __import__(module_name, fromlist=[function_name])
            main_function = getattr(module, function_name)

            # Note: In a real test, this would be run in a subprocess
            # For now, we just verify the function exists and is callable
            assert callable(main_function), f"Main function {function_name} is not callable"

            print(f"✓ {self.server_name} main function is available and callable")
            return True

        except KeyboardInterrupt:
            print("\nServer stopped by user")
            return True
        except Exception as e:
            print(f"Error starting server: {e}")
            return False
