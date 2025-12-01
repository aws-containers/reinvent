"""
Example multi-server test runner using the MCP testing framework.

This demonstrates how to run tests across all MCP servers in the system
using the standardized testing framework.
"""

import asyncio
import sys
from pathlib import Path

# Import the testing framework
sys.path.append(str(Path(__file__).parent.parent))

from test_helpers import TestRunner
from server_configs import get_all_server_configs, validate_all_server_configs
from test_templates import create_multi_server_test_runner


async def run_all_integration_tests():
    """Run integration tests for all MCP servers."""
    print("Running Integration Tests for All MCP Servers")
    print("=" * 60)

    # Validate configurations first
    if not validate_all_server_configs():
        print("❌ Server configuration validation failed")
        return False

    # Get all server configurations
    server_configs = get_all_server_configs()

    # Run integration tests
    results = await TestRunner.run_integration_test_suite(server_configs)

    # Print summary
    TestRunner.print_test_summary(results, "Integration Tests")

    # Return overall success
    return all(results.values())


async def run_all_standalone_tests():
    """Run standalone tests for all MCP servers."""
    print("Running Standalone Tests for All MCP Servers")
    print("=" * 60)
    print("Note: This requires all servers to be running on their respective ports")
    print()

    # Get all server configurations
    server_configs = get_all_server_configs()

    # Create multi-server test runner
    test_runner = create_multi_server_test_runner(server_configs)()

    # Run standalone tests
    results = await test_runner.run_all_standalone_tests()

    # Print summary
    test_runner.print_summary(results, "Standalone Tests")

    # Return overall success
    return all(results.values())


def print_server_status():
    """Print the status of all configured servers."""
    print("MCP Server Configuration Status")
    print("=" * 60)

    if validate_all_server_configs():
        print("✓ All server configurations are valid\n")

        configs = get_all_server_configs()
        for config in configs:
            print(f"📋 {config['name']}")
            print(f"   Port: {config['port']}")
            print(f"   Module: {config['module_path']}")
            print(f"   Expected Tools: {len(config['expected_tools'])}")
            print(f"   Sample Calls: {len(config.get('sample_tool_calls', {}))}")
            print(f"   URL: http://localhost:{config['port']}/mcp")
            print()
    else:
        print("❌ Server configuration validation failed")


def print_usage_instructions():
    """Print instructions for using the test framework."""
    print("MCP Testing Framework Usage Instructions")
    print("=" * 60)
    print()
    print("1. Integration Tests (manages server lifecycle):")
    print("   python multi_server_test_runner.py --integration")
    print("   - Starts each server automatically")
    print("   - Tests MCP client connections")
    print("   - Verifies all expected tools are available")
    print("   - Stops servers after testing")
    print()
    print("2. Standalone Tests (requires running servers):")
    print("   # First, start all servers in separate terminals:")
    print("   python test_customer_server.py      # Port 8001")
    print("   python test_appointment_server.py   # Port 8002")
    print("   python test_technician_server.py    # Port 8003")
    print()
    print("   # Then run standalone tests:")
    print("   python multi_server_test_runner.py --standalone")
    print()
    print("3. Individual Server Tests:")
    print("   python customer_server_tests.py")
    print("   python appointment_server_tests.py")
    print("   python technician_server_tests.py")
    print()
    print("4. Configuration Validation:")
    print("   python multi_server_test_runner.py --validate")
    print()


async def main():
    """Main test runner function."""
    import argparse

    parser = argparse.ArgumentParser(description="MCP Multi-Server Test Runner")
    parser.add_argument("--integration", action="store_true",
                       help="Run integration tests (manages server lifecycle)")
    parser.add_argument("--standalone", action="store_true",
                       help="Run standalone tests (requires running servers)")
    parser.add_argument("--validate", action="store_true",
                       help="Validate server configurations")
    parser.add_argument("--status", action="store_true",
                       help="Show server configuration status")
    parser.add_argument("--help-usage", action="store_true",
                       help="Show detailed usage instructions")

    args = parser.parse_args()

    if args.help_usage:
        print_usage_instructions()
        return

    if args.status:
        print_server_status()
        return

    if args.validate:
        print("Validating MCP server configurations...")
        if validate_all_server_configs():
            print("✅ All configurations are valid")
        else:
            print("❌ Configuration validation failed")
            sys.exit(1)
        return

    if args.integration:
        success = await run_all_integration_tests()
        if not success:
            print("\n❌ Some integration tests failed")
            sys.exit(1)
        else:
            print("\n✅ All integration tests passed")
        return

    if args.standalone:
        success = await run_all_standalone_tests()
        if not success:
            print("\n❌ Some standalone tests failed")
            sys.exit(1)
        else:
            print("\n✅ All standalone tests passed")
        return

    # Default: show help
    parser.print_help()
    print("\nFor detailed usage instructions, run:")
    print("python multi_server_test_runner.py --help-usage")


if __name__ == "__main__":
    asyncio.run(main())
