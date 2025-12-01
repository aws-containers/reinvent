"""
EKS test base classes for REST API testing.

This module provides base classes for testing REST API endpoints deployed on EKS
clusters with ALB ingress controllers. It extends the existing base test classes
to support ALB URL configuration instead of localhost, with increased timeouts
and enhanced error reporting.
"""

import json
import time
from typing import Dict, List, Optional, Set, Any, Tuple
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .base_test_classes import BaseMCPEndpointTest, BaseMCPIntegrationTest, BaseMCPStandaloneTest
from .eks_test_helpers import EKSTestConfig, create_eks_test_config


class BaseEKSRESTTest(BaseMCPEndpointTest):
    """
    Base class for EKS REST API testing.

    Extends BaseMCPEndpointTest to support ALB URL configuration instead of localhost,
    with increased timeout settings for ALB requests and enhanced error reporting
    that includes actual ALB URLs being tested.
    """

    def __init__(self, *args, **kwargs):
        """Initialize EKS REST test with ALB configuration."""
        super().__init__(*args, **kwargs)
        self._eks_config: Optional[EKSTestConfig] = None
        self._http_client: Optional[requests.Session] = None

    @property
    def eks_config(self) -> EKSTestConfig:
        """Get or create EKS test configuration."""
        if self._eks_config is None:
            self._eks_config = create_eks_test_config(timeout=self.request_timeout)
        return self._eks_config

    @property
    def base_url(self) -> str:
        """Return ALB URL instead of localhost."""
        alb_url = self.eks_config.get_service_url(self.service_name)
        if alb_url:
            return alb_url
        else:
            # Fallback to localhost for development/testing
            return f"http://{self.server_host}:{self.server_port}"

    @property
    def request_timeout(self) -> int:
        """Increased timeout for ALB requests (30 seconds vs 5 seconds for local)."""
        return 30

    @property
    def service_name(self) -> str:
        """
        Service name for ALB URL discovery.

        Subclasses should override this to return the appropriate service name
        (e.g., 'customer-server', 'appointment-server', 'technician-server').
        """
        # Default mapping based on server port
        port_to_service = {
            8001: "customer-server",
            8002: "appointment-server",
            8003: "technician-server"
        }
        return port_to_service.get(self.server_port, f"unknown-service-{self.server_port}")

    @property
    def http_client(self) -> requests.Session:
        """Get HTTP client configured for ALB endpoints with proper headers and authentication."""
        if self._http_client is None:
            self._http_client = self._create_http_client()
        return self._http_client

    def _create_http_client(self) -> requests.Session:
        """Create HTTP client with retry strategy and proper configuration for ALB requests."""
        session = requests.Session()

        # Configure retry strategy for transient network issues
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set default headers for ALB requests
        session.headers.update({
            "User-Agent": "EKS-Test-Client/1.0",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

        return session

    def setup_test_data(self):
        """
        Set up test data before each test.

        Extends the base setup to include EKS-specific configuration
        and ALB endpoint validation.
        """
        # Only call parent setup if it's not a pytest fixture
        if hasattr(super(), 'setup_test_data') and not hasattr(super().setup_test_data, '_pytestfixturefunction'):
            try:
                super().setup_test_data()
            except Exception as e:
                # If parent setup fails (e.g., pytest fixture issue), continue with EKS setup
                print(f"Parent setup skipped: {e}")

        # Validate ALB endpoint accessibility before running tests
        self._validate_alb_endpoint()

    def _validate_alb_endpoint(self):
        """Validate that the ALB endpoint is accessible before running tests."""
        service_name = self.service_name
        alb_url = self.eks_config.get_service_url(service_name)

        if not alb_url:
            print(f"⚠ Warning: No ALB URL found for {service_name}, falling back to localhost")
            return

        print(f"🔍 Validating ALB endpoint for {service_name}: {alb_url}")

        is_accessible, message = self.eks_config.validate_alb_endpoint_accessibility(service_name)

        if not is_accessible:
            print(f"⚠ Warning: ALB endpoint validation failed: {message}")
            print(f"   Tests may fail or use fallback localhost configuration")
        else:
            print(f"✓ ALB endpoint is accessible: {message}")

    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make HTTP request to ALB endpoint with enhanced error reporting.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path (e.g., '/health', '/customers/CUST001/profile')
            **kwargs: Additional arguments passed to requests

        Returns:
            Response object

        Raises:
            AssertionError: If request fails with enhanced error context
        """
        url = f"{self.base_url.rstrip('/')}{endpoint}"

        # Set default timeout if not provided
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.request_timeout

        try:
            print(f"🌐 Making {method} request to: {url}")
            response = self.http_client.request(method, url, **kwargs)

            print(f"📊 Response: {response.status_code} {response.reason}")
            return response

        except requests.exceptions.Timeout as e:
            error_msg = (
                f"Request timeout after {self.request_timeout} seconds\n"
                f"URL: {url}\n"
                f"Service: {self.service_name}\n"
                f"ALB URL: {self.base_url}\n"
                f"Error: {str(e)}"
            )
            raise AssertionError(error_msg) from e

        except requests.exceptions.ConnectionError as e:
            error_msg = (
                f"Connection error to ALB endpoint\n"
                f"URL: {url}\n"
                f"Service: {self.service_name}\n"
                f"ALB URL: {self.base_url}\n"
                f"Error: {str(e)}\n"
                f"Troubleshooting:\n"
                f"  1. Verify ALB is provisioned and healthy\n"
                f"  2. Check ingress resource status: kubectl get ingress\n"
                f"  3. Verify service is running: kubectl get pods\n"
                f"  4. Check ALB target group health in AWS console"
            )
            raise AssertionError(error_msg) from e

        except requests.exceptions.RequestException as e:
            error_msg = (
                f"Request failed to ALB endpoint\n"
                f"URL: {url}\n"
                f"Service: {self.service_name}\n"
                f"ALB URL: {self.base_url}\n"
                f"Error: {str(e)}"
            )
            raise AssertionError(error_msg) from e

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """Make GET request to ALB endpoint."""
        return self.make_request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, json_data: Optional[Dict] = None, **kwargs) -> requests.Response:
        """Make POST request to ALB endpoint."""
        if json_data is not None:
            kwargs['json'] = json_data
        return self.make_request("POST", endpoint, **kwargs)

    def put(self, endpoint: str, json_data: Optional[Dict] = None, **kwargs) -> requests.Response:
        """Make PUT request to ALB endpoint."""
        if json_data is not None:
            kwargs['json'] = json_data
        return self.make_request("PUT", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """Make DELETE request to ALB endpoint."""
        return self.make_request("DELETE", endpoint, **kwargs)

    def assert_successful_response(self, response: requests.Response, expected_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Assert that an HTTP response is successful and contains expected data.

        Args:
            response: HTTP response object
            expected_keys: Optional list of keys that should be present in the response

        Returns:
            The parsed response data as a dictionary

        Raises:
            AssertionError: If the response is not successful or missing expected keys
        """
        # Enhanced error reporting with ALB context
        if not response.ok:
            error_msg = (
                f"HTTP request failed\n"
                f"Status: {response.status_code} {response.reason}\n"
                f"URL: {response.url}\n"
                f"Service: {self.service_name}\n"
                f"ALB URL: {self.base_url}\n"
                f"Response body: {response.text[:500]}..."
            )
            raise AssertionError(error_msg)

        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            error_msg = (
                f"Invalid JSON response from ALB endpoint\n"
                f"URL: {response.url}\n"
                f"Service: {self.service_name}\n"
                f"ALB URL: {self.base_url}\n"
                f"Status: {response.status_code}\n"
                f"Response body: {response.text[:500]}...\n"
                f"JSON Error: {str(e)}"
            )
            raise AssertionError(error_msg) from e

        if expected_keys:
            missing_keys = []
            for key in expected_keys:
                if key not in response_data:
                    missing_keys.append(key)

            if missing_keys:
                error_msg = (
                    f"Missing expected keys in response\n"
                    f"URL: {response.url}\n"
                    f"Service: {self.service_name}\n"
                    f"ALB URL: {self.base_url}\n"
                    f"Missing keys: {missing_keys}\n"
                    f"Response data: {response_data}"
                )
                raise AssertionError(error_msg)

        return response_data

    def assert_error_response(self, response: requests.Response, expected_status: int, expected_error: Optional[str] = None) -> Dict[str, Any]:
        """
        Assert that an HTTP response contains an expected error.

        Args:
            response: HTTP response object
            expected_status: Expected HTTP status code
            expected_error: Optional expected error message

        Returns:
            The parsed response data as a dictionary
        """
        if response.status_code != expected_status:
            error_msg = (
                f"Unexpected status code\n"
                f"Expected: {expected_status}\n"
                f"Actual: {response.status_code} {response.reason}\n"
                f"URL: {response.url}\n"
                f"Service: {self.service_name}\n"
                f"ALB URL: {self.base_url}\n"
                f"Response body: {response.text[:500]}..."
            )
            raise AssertionError(error_msg)

        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            error_msg = (
                f"Invalid JSON error response from ALB endpoint\n"
                f"URL: {response.url}\n"
                f"Service: {self.service_name}\n"
                f"ALB URL: {self.base_url}\n"
                f"Status: {response.status_code}\n"
                f"Response body: {response.text[:500]}...\n"
                f"JSON Error: {str(e)}"
            )
            raise AssertionError(error_msg) from e

        if expected_error and "error" in response_data:
            actual_error = response_data["error"]
            if expected_error not in actual_error:
                error_msg = (
                    f"Unexpected error message\n"
                    f"Expected: '{expected_error}'\n"
                    f"Actual: '{actual_error}'\n"
                    f"URL: {response.url}\n"
                    f"Service: {self.service_name}\n"
                    f"ALB URL: {self.base_url}"
                )
                raise AssertionError(error_msg)

        return response_data

    def wait_for_service_ready(self, max_wait_time: int = 300, check_interval: int = 10) -> bool:
        """
        Wait for the ALB endpoint to become ready and healthy.

        Args:
            max_wait_time: Maximum time to wait in seconds
            check_interval: Time between health checks in seconds

        Returns:
            True if endpoint becomes ready, False if timeout
        """
        return self.eks_config.wait_for_alb_readiness(
            self.service_name,
            max_wait_time=max_wait_time,
            check_interval=check_interval
        )

    def print_test_context(self):
        """Print test context information including ALB URLs."""
        print("\n" + "="*60)
        print(f"EKS REST API Test Context - {self.service_name}")
        print("="*60)
        print(f"Service Name: {self.service_name}")
        print(f"Server Port: {self.server_port}")
        print(f"ALB URL: {self.base_url}")
        print(f"Request Timeout: {self.request_timeout} seconds")

        # Test connectivity
        alb_url = self.eks_config.get_service_url(self.service_name)
        if alb_url:
            is_accessible, message = self.eks_config.validate_alb_endpoint_accessibility(self.service_name)
            status_icon = "✓" if is_accessible else "✗"
            print(f"Connectivity: {status_icon} {message}")
        else:
            print("Connectivity: ⚠ No ALB URL found, using localhost fallback")

        print("="*60)

    def cleanup(self):
        """Clean up resources used by the test."""
        if self._http_client:
            self._http_client.close()
            self._http_client = None

        if self._eks_config:
            self._eks_config.cleanup()
            self._eks_config = None


class BaseEKSIntegrationTest(BaseMCPIntegrationTest):
    """
    Base class for EKS integration testing.

    Extends BaseMCPIntegrationTest to support ALB endpoints for integration testing
    of services deployed on EKS clusters.
    """

    def __init__(self, *args, **kwargs):
        """Initialize EKS integration test with ALB configuration."""
        super().__init__(*args, **kwargs)
        self._eks_config: Optional[EKSTestConfig] = None

    @property
    def eks_config(self) -> EKSTestConfig:
        """Get or create EKS test configuration."""
        if self._eks_config is None:
            self._eks_config = create_eks_test_config(timeout=30)
        return self._eks_config

    @property
    def service_name(self) -> str:
        """Service name for ALB URL discovery."""
        port_to_service = {
            8001: "customer-server",
            8002: "appointment-server",
            8003: "technician-server"
        }
        return port_to_service.get(self.server_port, f"unknown-service-{self.server_port}")

    async def test_eks_integration(self) -> bool:
        """
        Test integration with EKS-deployed services.

        Returns:
            True if the test passed, False otherwise
        """
        print(f"Testing EKS integration for {self.server_name}...")

        # Validate ALB endpoint accessibility
        service_name = self.service_name
        alb_url = self.eks_config.get_service_url(service_name)

        if not alb_url:
            print(f"⚠ No ALB URL found for {service_name}")
            return False

        print(f"🔍 Testing ALB endpoint: {alb_url}")

        is_accessible, message = self.eks_config.validate_alb_endpoint_accessibility(service_name)

        if not is_accessible:
            print(f"✗ ALB endpoint not accessible: {message}")
            return False

        print(f"✓ ALB endpoint is accessible: {message}")

        # Test basic HTTP connectivity
        try:
            import requests
            response = requests.get(f"{alb_url}/health", timeout=30)
            if response.status_code == 200:
                print("✓ Health check endpoint responding")
                return True
            else:
                print(f"✗ Health check failed with status {response.status_code}")
                return False

        except Exception as e:
            print(f"✗ HTTP request failed: {e}")
            return False

    def cleanup(self):
        """Clean up resources used by the test."""
        if self._eks_config:
            self._eks_config.cleanup()
            self._eks_config = None


class BaseEKSStandaloneTest(BaseMCPStandaloneTest):
    """
    Base class for standalone EKS testing.

    Extends BaseMCPStandaloneTest to support testing against ALB endpoints
    for services already deployed on EKS clusters.
    """

    def __init__(self, *args, **kwargs):
        """Initialize EKS standalone test with ALB configuration."""
        super().__init__(*args, **kwargs)
        self._eks_config: Optional[EKSTestConfig] = None

    @property
    def eks_config(self) -> EKSTestConfig:
        """Get or create EKS test configuration."""
        if self._eks_config is None:
            self._eks_config = create_eks_test_config(timeout=30)
        return self._eks_config

    @property
    def service_name(self) -> str:
        """Service name for ALB URL discovery."""
        port_to_service = {
            8001: "customer-server",
            8002: "appointment-server",
            8003: "technician-server"
        }
        return port_to_service.get(self.server_port, f"unknown-service-{self.server_port}")

    async def test_eks_standalone_connection(self) -> bool:
        """
        Test connection to an already deployed EKS service via ALB.

        Returns:
            True if the test passed, False otherwise
        """
        service_name = self.service_name
        alb_url = self.eks_config.get_service_url(service_name)

        if not alb_url:
            print(f"❌ No ALB URL found for {service_name}")
            print("Make sure the service is deployed to EKS with ALB ingress")
            return False

        print(f"🔍 Testing standalone connection to {service_name}")
        print(f"ALB URL: {alb_url}")
        print("(Make sure the service is deployed and healthy)")

        try:
            import requests

            # Test health endpoint
            print("Testing health endpoint...")
            response = requests.get(f"{alb_url}/health", timeout=30)

            if response.status_code == 200:
                health_data = response.json()
                print(f"✓ Health check successful: {health_data}")
            else:
                print(f"⚠ Health check returned status {response.status_code}")

            # Test OpenAPI docs if available
            print("Testing OpenAPI documentation...")
            docs_response = requests.get(f"{alb_url}/docs", timeout=30)
            if docs_response.status_code == 200:
                print("✓ OpenAPI documentation available")
            else:
                print("ℹ OpenAPI documentation not available")

            # Test OpenAPI JSON spec
            openapi_response = requests.get(f"{alb_url}/openapi.json", timeout=30)
            if openapi_response.status_code == 200:
                openapi_spec = openapi_response.json()
                print(f"✓ OpenAPI spec available: {openapi_spec.get('info', {}).get('title', 'Unknown')}")
            else:
                print("ℹ OpenAPI JSON spec not available")

            print(f"\n🎉 Standalone connection test completed successfully!")
            return True

        except requests.exceptions.Timeout:
            print(f"❌ Connection timeout after 30 seconds")
            print(f"Check if the ALB and service are healthy")
            return False

        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection failed: {e}")
            print(f"Troubleshooting:")
            print(f"  1. Verify ALB is provisioned: kubectl get ingress")
            print(f"  2. Check service status: kubectl get pods")
            print(f"  3. Verify ALB target group health in AWS console")
            return False

        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

    def cleanup(self):
        """Clean up resources used by the test."""
        if self._eks_config:
            self._eks_config.cleanup()
            self._eks_config = None


# Utility functions for EKS testing

def create_eks_test_client(service_name: str, timeout: int = 30) -> Tuple[EKSTestConfig, requests.Session]:
    """
    Create EKS test client configuration and HTTP session.

    Args:
        service_name: Name of the service to test
        timeout: Request timeout in seconds

    Returns:
        Tuple of (EKSTestConfig, requests.Session)
    """
    config = create_eks_test_config(timeout=timeout)

    # Create HTTP session with retry strategy
    session = requests.Session()

    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE"]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Set default headers
    session.headers.update({
        "User-Agent": "EKS-Test-Client/1.0",
        "Content-Type": "application/json",
        "Accept": "application/json"
    })

    return config, session


def validate_eks_test_environment() -> bool:
    """
    Validate that the EKS test environment is ready.

    Returns:
        True if environment is ready, False otherwise
    """
    try:
        config = create_eks_test_config()

        # Check if any ALB URLs were discovered
        service_urls = config.get_all_service_urls()

        if not service_urls:
            print("❌ No ALB URLs discovered")
            print("Make sure services are deployed with ALB ingress")
            return False

        print(f"✓ Found {len(service_urls)} ALB endpoints")

        # Validate connectivity to all endpoints
        results = config.validate_all_alb_endpoints()

        healthy_count = sum(1 for is_healthy, _ in results.values() if is_healthy)
        total_count = len(results)

        print(f"✓ {healthy_count}/{total_count} endpoints are healthy")

        if healthy_count == 0:
            print("❌ No healthy endpoints found")
            return False

        return True

    except Exception as e:
        print(f"❌ Environment validation failed: {e}")
        return False
    finally:
        if 'config' in locals():
            config.cleanup()


def print_eks_test_summary(service_name: Optional[str] = None):
    """
    Print summary of EKS test environment.

    Args:
        service_name: Optional specific service to focus on
    """
    try:
        config = create_eks_test_config()

        if service_name:
            # Print summary for specific service
            alb_url = config.get_service_url(service_name)
            if alb_url:
                print(f"\n🎯 EKS Test Summary - {service_name}")
                print(f"ALB URL: {alb_url}")

                is_healthy, message = config.validate_alb_endpoint_accessibility(service_name)
                status_icon = "✓" if is_healthy else "✗"
                print(f"Status: {status_icon} {message}")
            else:
                print(f"❌ No ALB URL found for {service_name}")
        else:
            # Print summary for all services
            config.print_discovery_summary()

    except Exception as e:
        print(f"❌ Failed to generate test summary: {e}")
    finally:
        if 'config' in locals():
            config.cleanup()
