"""
Pytest configuration for integration tests.

This module provides shared fixtures and configuration for integration tests
that run against live MCP servers.
"""

import sys
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

import pytest


@pytest.fixture(scope="session")
def server_base_url():
    """Base URL for MCP servers."""
    return "http://localhost"


@pytest.fixture(scope="session")
def appointment_server_port():
    """Port for the appointment server."""
    return 8002


@pytest.fixture(scope="session")
def customer_server_port():
    """Port for the customer server."""
    return 8001


@pytest.fixture(scope="session")
def technician_server_port():
    """Port for the technician server."""
    return 8003
