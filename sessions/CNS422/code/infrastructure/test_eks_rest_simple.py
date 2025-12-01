#!/usr/bin/env python3
"""
Simple EKS REST API test for validating ALB endpoints.

This is a minimal test script that validates EKS REST API functionality
without the complexity of the full test framework.
"""

import os
import sys
import requests
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

def test_customer_server_health():
    """Test customer server health endpoint via ALB."""
    from testing_framework.eks_test_helpers import create_eks_test_config

    print("🔍 Testing Customer server health endpoint via ALB...")

    # Get EKS configuration
    config = create_eks_test_config(timeout=30)
    service_name = "customer-server"

    # Get ALB URL
    alb_url = config.get_service_url(service_name)
    if not alb_url:
        print(f"❌ No ALB URL found for {service_name}")
        return False

    print(f"🌐 Testing ALB endpoint: {alb_url}")

    try:
        # Test health endpoint
        response = requests.get(f"{alb_url}/health", timeout=30)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check successful: {data}")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False
    finally:
        config.cleanup()


def test_appointment_server_health():
    """Test appointment server health endpoint via ALB."""
    from testing_framework.eks_test_helpers import create_eks_test_config

    print("🔍 Testing Appointment server health endpoint via ALB...")

    # Get EKS configuration
    config = create_eks_test_config(timeout=30)
    service_name = "appointment-server"

    # Get ALB URL
    alb_url = config.get_service_url(service_name)
    if not alb_url:
        print(f"❌ No ALB URL found for {service_name}")
        return False

    print(f"🌐 Testing ALB endpoint: {alb_url}")

    try:
        # Test health endpoint
        response = requests.get(f"{alb_url}/health", timeout=30)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check successful: {data}")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False
    finally:
        config.cleanup()


def test_technician_server_health():
    """Test technician server health endpoint via ALB."""
    from testing_framework.eks_test_helpers import create_eks_test_config

    print("🔍 Testing Technician server health endpoint via ALB...")

    # Get EKS configuration
    config = create_eks_test_config(timeout=30)
    service_name = "technician-server"

    # Get ALB URL
    alb_url = config.get_service_url(service_name)
    if not alb_url:
        print(f"❌ No ALB URL found for {service_name}")
        return False

    print(f"🌐 Testing ALB endpoint: {alb_url}")

    try:
        # Test health endpoint
        response = requests.get(f"{alb_url}/health", timeout=30)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check successful: {data}")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False
    finally:
        config.cleanup()


def main():
    """Run all EKS REST API tests."""
    print("🚀 Starting EKS REST API tests...")

    results = []

    # Test each service
    results.append(("Customer Server", test_customer_server_health()))
    results.append(("Appointment Server", test_appointment_server_health()))
    results.append(("Technician Server", test_technician_server_health()))

    # Print summary
    print("\n" + "="*60)
    print("EKS REST API Test Summary")
    print("="*60)

    passed = 0
    total = len(results)

    for service_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{service_name:20} {status}")
        if result:
            passed += 1

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All EKS REST API tests passed!")
        return 0
    else:
        print("❌ Some EKS REST API tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
