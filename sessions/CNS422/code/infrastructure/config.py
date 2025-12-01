"""
Configuration management for MCP servers infrastructure.
"""

import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class ServerConfig:
    """Base configuration for MCP servers."""

    host: str = "localhost"
    port: int = 8000
    debug: bool = True
    data_dir: str = "data"
    log_level: str = "INFO"


@dataclass
class AppointmentServerConfig(ServerConfig):
    """Configuration for appointment management server."""

    port: int = 8001
    max_appointments_per_day: int = 50
    booking_window_days: int = 30


@dataclass
class TechnicianServerConfig(ServerConfig):
    """Configuration for technician tracking server."""

    port: int = 8002
    location_update_interval: int = 30  # seconds
    max_travel_distance: float = 50.0  # miles


@dataclass
class CustomerServerConfig(ServerConfig):
    """Configuration for customer information server."""

    port: int = 8003
    max_claims_per_customer: int = 10


def load_server_config(server_type: str) -> ServerConfig:
    """Load configuration for a specific server type."""

    environment = os.getenv("INFRASTRUCTURE_ENV", "development")

    base_config = {
        "host": os.getenv(f"{server_type.upper()}_HOST", "localhost"),
        "debug": environment == "development",
        "log_level": os.getenv("LOG_LEVEL", "INFO" if environment == "demo" else "DEBUG"),
    }

    if server_type == "appointment":
        return AppointmentServerConfig(
            port=int(os.getenv("APPOINTMENT_SERVER_PORT", "8001")),
            **base_config
        )
    elif server_type == "technician":
        return TechnicianServerConfig(
            port=int(os.getenv("TECHNICIAN_SERVER_PORT", "8002")),
            **base_config
        )
    elif server_type == "customer":
        return CustomerServerConfig(
            port=int(os.getenv("CUSTOMER_SERVER_PORT", "8003")),
            **base_config
        )
    else:
        raise ValueError(f"Unknown server type: {server_type}")


# Environment-specific configurations
DEVELOPMENT_CONFIG = {
    "data_persistence": False,  # Use in-memory storage
    "mock_data": True,
    "cors_enabled": True,
}

DEMO_CONFIG = {
    "data_persistence": False,  # Use in-memory storage for demo
    "mock_data": True,
    "cors_enabled": True,
    "health_checks": True,
}
