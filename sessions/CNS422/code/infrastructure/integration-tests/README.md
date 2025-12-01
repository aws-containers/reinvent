# Integration Tests

This directory contains integration tests that run against live MCP servers. These tests assume the servers are already running and available.

## Prerequisites

Before running integration tests, you need to start the MCP servers:

### Appointment Server
```bash
cd infrastructure
python -m mcp_servers.appointment_server.server
```
The server will run on `http://localhost:8002`

### Customer Server
```bash
cd infrastructure
python -m mcp_servers.customer_server.server
```
The server will run on `http://localhost:8001`

### Technician Server
```bash
cd infrastructure
python -m mcp_servers.technician_server.server
```
The server will run on `http://localhost:8003`

## Running Tests

### Run All Integration Tests
```bash
make test-integration
```

### Run Specific Server Tests
```bash
# Appointment server integration tests
make test-appointment-integration

# Technician server integration tests
make test-technician-integration

# Customer server integration tests
make test-customer-integration

# Or run directly with pytest
cd infrastructure/integration-tests
pytest test_appointment_server_integration.py -v
pytest test_technician_server_integration.py -v
pytest test_customer_server_integration.py -v
```

### Run Individual Test Files
```bash
cd infrastructure/integration-tests

# Run appointment server tests
pytest test_appointment_server_integration.py -v

# Run with more verbose output
pytest test_appointment_server_integration.py -v -s
```

## Test Structure

- `test_appointment_server_integration.py` - Tests for the appointment management server
- `test_technician_server_integration.py` - Tests for the technician tracking server
- `test_customer_server_integration.py` - Tests for the customer information server
- `conftest.py` - Shared pytest configuration and fixtures
- `pytest.ini` - Pytest configuration for integration tests

## Adding New Integration Tests

1. Create a new test file following the pattern `test_<server_name>_integration.py`
2. Import the base test classes from `testing_framework.base_test_classes`
3. Extend `BaseMCPStandaloneTest` for your server
4. Implement the required properties and test methods
5. Add appropriate pytest decorators for async tests

Example:
```python
from testing_framework.base_test_classes import BaseMCPStandaloneTest
import pytest

class TestMyServerStandalone(BaseMCPStandaloneTest):
    @property
    def server_name(self) -> str:
        return "My Server"

    @property
    def server_port(self) -> int:
        return 8004

    @pytest.mark.asyncio
    async def test_standalone_connection(self) -> bool:
        return await super().test_standalone_connection()
```

## Troubleshooting

### Connection Errors
- Ensure the target server is running on the expected port
- Check that no firewall is blocking the connection
- Verify the server is responding to HTTP requests

### Test Failures
- Check server logs for errors
- Ensure mock data is properly loaded in the server
- Verify the server's tool definitions match the test expectations

### Port Conflicts
- Default ports are defined in `conftest.py`
- Update the port numbers if you need to run servers on different ports
- Make sure no other services are using the same ports
