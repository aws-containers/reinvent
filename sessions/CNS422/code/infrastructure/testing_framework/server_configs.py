"""
Server configuration definitions for MCP server testing framework.

This module contains standardized configurations for all MCP servers
in the insurance agent chatbot system, including ports, expected tools,
and sample test calls.
"""

from typing import Dict, Set, Any, List


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
        "get_claim_history",
        "get_claim_details",
        "update_claim_status",
        "check_appliance_coverage"
    },
    'appointment': {
        "list_appointments",
        "create_appointment",
        "update_appointment",
        "cancel_appointment",
        "get_available_slots",
        "reschedule_appointment"
    },
    'technician': {
        "get_technician_status",
        "get_technician_location",
        "list_available_technicians",
        "update_technician_status",
        "get_technician_route",
        "notify_status_change"
    }
}

# Sample tool calls for testing
SAMPLE_TOOL_CALLS = {
    'customer': {
        "get_customer_profile": {"customer_id": "CUST001"},
        "get_policy_details": {"customer_id": "CUST001"},
        "check_appliance_coverage": {"customer_id": "CUST001", "appliance_type": "refrigerator"},
        "create_claim": {
            "customer_id": "CUST001",
            "appliance_type": "refrigerator",
            "issue_description": "Not cooling properly",
            "urgency_level": "high"
        }
    },
    'appointment': {
        "list_appointments": {"customer_id": "CUST001"},
        "get_available_slots": {
            "date_range": {"start": "2024-01-20", "end": "2024-01-27"},
            "technician_specialties": ["refrigerator"]
        }
    },
    'technician': {
        "list_available_technicians": {
            "area": "downtown",
            "datetime": "2024-01-20T10:00:00",
            "specialties": ["refrigerator"]
        },
        "get_technician_status": {"technician_id": "TECH001"}
    }
}


def get_customer_server_config() -> Dict[str, Any]:
    """Get configuration for Customer Information MCP Server."""
    return {
        'name': 'Customer Information Server',
        'port': SERVER_PORTS['customer'],
        'module_path': 'mcp_servers.customer_server.server',
        'expected_tools': EXPECTED_TOOLS['customer'],
        'sample_tool_calls': SAMPLE_TOOL_CALLS['customer']
    }


def get_appointment_server_config() -> Dict[str, Any]:
    """Get configuration for Appointment Management MCP Server."""
    return {
        'name': 'Appointment Management Server',
        'port': SERVER_PORTS['appointment'],
        'module_path': 'mcp_servers.appointment_server.server',
        'expected_tools': EXPECTED_TOOLS['appointment'],
        'sample_tool_calls': SAMPLE_TOOL_CALLS['appointment']
    }


def get_technician_server_config() -> Dict[str, Any]:
    """Get configuration for Technician Tracking MCP Server."""
    return {
        'name': 'Technician Tracking Server',
        'port': SERVER_PORTS['technician'],
        'module_path': 'mcp_servers.technician_server.server',
        'expected_tools': EXPECTED_TOOLS['technician'],
        'sample_tool_calls': SAMPLE_TOOL_CALLS['technician']
    }


def get_all_server_configs() -> List[Dict[str, Any]]:
    """Get configurations for all MCP servers."""
    return [
        get_customer_server_config(),
        get_appointment_server_config(),
        get_technician_server_config()
    ]


def get_server_config_by_name(server_name: str) -> Dict[str, Any]:
    """
    Get server configuration by name.

    Args:
        server_name: Name of the server ('customer', 'appointment', or 'technician')

    Returns:
        Server configuration dictionary

    Raises:
        ValueError: If server name is not recognized
    """
    configs = {
        'customer': get_customer_server_config,
        'appointment': get_appointment_server_config,
        'technician': get_technician_server_config
    }

    if server_name not in configs:
        raise ValueError(f"Unknown server name: {server_name}. Available: {list(configs.keys())}")

    return configs[server_name]()


def get_server_config_by_port(port: int) -> Dict[str, Any]:
    """
    Get server configuration by port number.

    Args:
        port: Port number of the server

    Returns:
        Server configuration dictionary

    Raises:
        ValueError: If port is not recognized
    """
    port_to_name = {v: k for k, v in SERVER_PORTS.items()}

    if port not in port_to_name:
        raise ValueError(f"Unknown server port: {port}. Available: {list(SERVER_PORTS.values())}")

    return get_server_config_by_name(port_to_name[port])


# Validation functions
def validate_server_config(config: Dict[str, Any]) -> bool:
    """
    Validate that a server configuration contains all required fields.

    Args:
        config: Server configuration dictionary

    Returns:
        True if configuration is valid, False otherwise
    """
    required_fields = ['name', 'port', 'module_path', 'expected_tools']

    for field in required_fields:
        if field not in config:
            print(f"Missing required field: {field}")
            return False

    # Validate port is in expected range
    if not isinstance(config['port'], int) or config['port'] < 8000 or config['port'] > 9000:
        print(f"Invalid port: {config['port']}. Should be between 8000-9000")
        return False

    # Validate expected_tools is a set or list
    if not isinstance(config['expected_tools'], (set, list)):
        print(f"Invalid expected_tools type: {type(config['expected_tools'])}. Should be set or list")
        return False

    return True


def validate_all_server_configs() -> bool:
    """
    Validate all server configurations.

    Returns:
        True if all configurations are valid, False otherwise
    """
    configs = get_all_server_configs()

    for config in configs:
        if not validate_server_config(config):
            print(f"Invalid configuration for {config.get('name', 'unknown server')}")
            return False

    # Check for port conflicts
    ports = [config['port'] for config in configs]
    if len(ports) != len(set(ports)):
        print("Port conflicts detected in server configurations")
        return False

    return True


if __name__ == "__main__":
    # Validate configurations when run directly
    print("Validating MCP server configurations...")

    if validate_all_server_configs():
        print("✓ All server configurations are valid")

        print("\nServer configurations:")
        for config in get_all_server_configs():
            print(f"  - {config['name']}: Port {config['port']}")
            print(f"    Tools: {len(config['expected_tools'])}")
            print(f"    Sample calls: {len(config.get('sample_tool_calls', {}))}")
    else:
        print("✗ Server configuration validation failed")
        exit(1)
