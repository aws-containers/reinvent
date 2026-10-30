# MCP Server Testing Framework

A standardized testing framework for Model Context Protocol (MCP) servers with streamable-http transport. This framework provides consistent patterns, base classes, and utilities for testing MCP servers across different ports and configurations.

## Overview

The MCP Server Testing Framework extracts common testing patterns from existing MCP server tests and provides reusable components for:

- **Endpoint Testing**: Direct testing of server functions without MCP protocol
- **Integration Testing**: Full MCP client-server testing with automatic server management
- **Standalone Testing**: Testing against already running MCP servers
- **Multi-Server Testing**: Coordinated testing across multiple MCP servers

## Framework Structure

```
testing_framework/
├── __init__.py                     # Framework initialization
├── base_test_classes.py           # Abstract base classes for different test types
├── test_helpers.py                # Utility functions and helper classes
├── test_templates.py              # Template classes for quick test creation
├── server_configs.py              # Centralized server configuration management
├── examples/                      # Example implementations
│   ├── customer_server_tests.py   # Example Customer server tests
│   └── multi_server_test_runner.py # Example multi-server test runner
└── README.md                      # This documentation
```

## Key Components

### Base Test Classes

#### `BaseMCPServerTest`
Abstract base class providing common functionality for all MCP server tests:
- Server configuration properties (name, port, module path, expected tools)
- MCP URL generation
- Timeout configuration

#### `BaseMCPEndpointTest`
For testing server functions directly without MCP protocol:
- Test data setup patterns
- Response validation helpers
- Error assertion utilities

#### `BaseMCPIntegrationTest`
For full MCP client-server integration testing:
- Automatic server startup and shutdown
- MCP client connection management
- Tool and resource verification
- Tool call testing patterns

#### `BaseMCPStandaloneTest`
For testing against already running servers:
- Connection to existing servers
- Tool verification without server management
- Suitable for manual testing scenarios

### Helper Classes

#### `ServerManager`
Manages MCP server processes during testing:
- Server startup and shutdown
- Process monitoring
- Error handling and cleanup

#### `MCPClientHelper`
Simplifies MCP client operations:
- Connection management
- Tool listing and verification
- Tool call execution

#### `TestDataManager`
Manages test data and assertions:
- Mock data creation
- JSON response validation
- Error response assertions
- File operation mocking

#### `TestRunner`
Coordinates test execution across multiple servers:
- Multi-server test orchestration
- Result collection and reporting
- Test summary generation

### Server Configuration

The framework uses centralized configuration in `server_configs.py`:

```python
# Server port assignments
SERVER_PORTS = {
    'customer': 8001,
    'appointment': 8002,
    'technician': 8003
}

# Expected tools for each server
EXPECTED_TOOLS = {
    'customer': {
        "get_customer_profile",
        "get_policy_details",
        "create_claim",
        # ... more tools
    }
}

# Sample tool calls for testing
SAMPLE_TOOL_CALLS = {
    'customer': {
        "get_customer_profile": {"customer_id": "CUST001"},
        # ... more sample calls
    }
}
```

## Usage Patterns

### 1. Creating Endpoint Tests

```python
from testing_framework.base_test_classes import BaseMCPEndpointTest

class MyServerEndpointTest(BaseMCPEndpointTest):
    @property
    def server_name(self) -> str:
        return "My Server"

    @property
    def server_port(self) -> int:
        return 8001

    @property
    def server_module_path(self) -> str:
        return "my_server.server.main"

    @property
    def expected_tools(self) -> Set[str]:
        return {"tool1", "tool2"}

    async def test_my_function(self):
        result = await my_server_function("test_input")
        response_data = self.assert_successful_response(result, ["expected_key"])
        assert response_data["expected_key"] == "expected_value"
```

### 2. Creating Integration Tests

```python
from testing_framework.base_test_classes import BaseMCPIntegrationTest

class MyServerIntegrationTest(BaseMCPIntegrationTest):
    # ... implement required properties

    async def _test_tool_calls(self, session) -> bool:
        try:
            result = await session.call_tool("my_tool", {"param": "value"})
            print("✓ Tool call successful")
            return True
        except Exception as e:
            print(f"✗ Tool call failed: {e}")
            return False
```

### 3. Using Templates for Quick Setup

```python
from testing_framework.test_templates import create_server_test_suite

# Create a complete test suite
test_suite = create_server_test_suite(
    server_name="My Server",
    server_port=8001,
    server_module_path="my_server.server.main",
    expected_tools={"tool1", "tool2"},
    sample_tool_calls={"tool1": {"param": "value"}}
)

# Use the generated test classes
endpoint_test = test_suite['endpoint_test']()
integration_test = test_suite['integration_test']()
```

### 4. Multi-Server Testing

```python
from testing_framework.test_helpers import TestRunner
from testing_framework.server_configs import get_all_server_configs

# Run integration tests for all servers
server_configs = get_all_server_configs()
results = await TestRunner.run_integration_test_suite(server_configs)
TestRunner.print_test_summary(results, "Integration Tests")
```

## Testing Standards and Patterns

### 1. Test Data Setup

- Use `@pytest.fixture(autouse=True)` for automatic test data setup
- Clear existing data before setting up new test data
- Use realistic but safe mock data
- Implement both success and error scenarios

### 2. Response Validation

```python
# For successful responses
response_data = self.assert_successful_response(result, ["required_key"])

# For error responses
self.assert_error_response(result, "Expected error message")

# For custom validation
response_data = TestDataManager.assert_json_response(result, ["key1", "key2"])
```

### 3. Server Configuration

- Define server configurations in `server_configs.py`
- Use consistent port assignments (8001, 8002, 8003)
- Include expected tools and sample tool calls
- Validate configurations before testing

### 4. Error Handling

- Test both success and failure scenarios
- Use appropriate timeout values
- Implement graceful server cleanup
- Provide clear error messages

## Port Assignments

The framework supports testing servers on different ports:

- **Customer Server**: Port 8001
- **Appointment Server**: Port 8002
- **Technician Server**: Port 8003

Each server runs with streamable-http transport and is accessible at:
`http://localhost:{port}/mcp`

## Running Tests

### Individual Server Tests

```bash
# Run endpoint tests for a specific server
python customer_server_tests.py

# Run integration test (manages server lifecycle)
python -c "import asyncio; from customer_server_tests import run_customer_integration_test; asyncio.run(run_customer_integration_test())"

# Run standalone test (requires running server)
python -c "import asyncio; from customer_server_tests import run_customer_standalone_test; asyncio.run(run_customer_standalone_test())"
```

### Multi-Server Tests

```bash
# Run integration tests for all servers
python multi_server_test_runner.py --integration

# Run standalone tests (requires all servers running)
python multi_server_test_runner.py --standalone

# Validate server configurations
python multi_server_test_runner.py --validate

# Show server status
python multi_server_test_runner.py --status
```

### Using pytest

```bash
# Run all tests in a file
pytest customer_server_tests.py -v

# Run specific test methods
pytest customer_server_tests.py::CustomerServerEndpointTest::test_get_customer_profile_success -v

# Run with coverage
pytest customer_server_tests.py --cov=mcp_servers --cov-report=html
```

## Best Practices

### 1. Test Organization

- Separate endpoint, integration, and standalone tests
- Use descriptive test method names
- Group related tests in the same class
- Include both positive and negative test cases

### 2. Mock Data Management

- Use realistic but safe test data
- Clear data state between tests
- Test edge cases and boundary conditions
- Include error scenarios in test data

### 3. Server Management

- Use appropriate startup timeouts
- Implement proper cleanup in finally blocks
- Handle server startup failures gracefully
- Monitor server process health

### 4. Assertions and Validation

- Use framework assertion helpers for consistency
- Validate response structure and content
- Check for required fields in responses
- Verify error messages are appropriate

## Extending the Framework

### Adding New Server Types

1. Add server configuration to `server_configs.py`:
```python
def get_new_server_config() -> Dict[str, Any]:
    return {
        'name': 'New Server',
        'port': 8004,
        'module_path': 'new_server.server.main',
        'expected_tools': {'new_tool1', 'new_tool2'},
        'sample_tool_calls': {'new_tool1': {'param': 'value'}}
    }
```

2. Create test classes using base classes or templates
3. Add to multi-server test configurations

### Custom Test Patterns

Extend base classes to add custom functionality:

```python
class CustomMCPTest(BaseMCPEndpointTest):
    def custom_assertion_helper(self, result, custom_validation):
        response_data = self.assert_successful_response(result)
        # Add custom validation logic
        return response_data

    async def test_custom_scenario(self):
        # Implement custom test logic
        pass
```

## Troubleshooting

### Common Issues

1. **Server startup failures**
   - Check port availability
   - Verify module paths are correct
   - Increase startup timeout if needed

2. **MCP connection failures**
   - Ensure server is running on expected port
   - Check firewall settings
   - Verify MCP URL format

3. **Test data issues**
   - Clear data state between tests
   - Check mock data format
   - Verify data loading functions

4. **Tool call failures**
   - Verify tool names match server implementation
   - Check parameter formats
   - Ensure server has required test data

### Debug Mode

Enable debug output by setting environment variables:

```bash
export MCP_TEST_DEBUG=1
export MCP_TEST_VERBOSE=1
python customer_server_tests.py
```

## Contributing

When adding new tests or extending the framework:

1. Follow existing patterns and naming conventions
2. Add comprehensive documentation
3. Include both success and failure test cases
4. Update configuration files as needed
5. Test with multiple servers to ensure compatibility

## Requirements

The framework requires:

- Python 3.8+
- pytest
- mcp (Model Context Protocol library)
- asyncio support
- Access to MCP server implementations

See `pyproject.toml` for complete dependency list.
