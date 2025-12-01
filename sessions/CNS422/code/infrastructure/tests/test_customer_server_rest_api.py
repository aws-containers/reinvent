"""
Comprehensive test suite for Customer Information Server REST API.

This module tests the REST API endpoints using the same test framework
and patterns as the MCP server tests. It supports both local testing (using TestClient)
and EKS deployment testing (using ALB endpoints) based on the EKS_TEST_MODE environment variable.
"""

import json
import os
import pytest
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from testing_framework.base_test_classes import (
    BaseMCPEndpointTest,
    BaseMCPIntegrationTest,
    BaseMCPStandaloneTest
)

# Import EKS testing infrastructure
from testing_framework.eks_base_test_classes import BaseEKSRESTTest

# Import the REST API app
from mcp_servers.customer_server.server_rest import app as rest_app
from mcp_servers.customer_server.shared_data import load_mock_data

# Check if we're running in EKS test mode
EKS_TEST_MODE = os.getenv("EKS_TEST_MODE", "false").lower() == "true"


# Always use BaseMCPEndpointTest as base, but add EKS functionality dynamically
BaseTestClass = BaseMCPEndpointTest





class TestCustomerServerRESTEndpoints(BaseTestClass):
    """Test customer server REST API endpoints."""

    # Class attributes for EKS support
    server_port = 8001
    service_name = "customer-server"
    _eks_config = None

    @property
    def server_name(self) -> str:
        return "Customer Information Server REST API"

    @property
    def eks_config(self):
        """Get or create EKS test configuration."""
        if EKS_TEST_MODE and self._eks_config is None:
            from testing_framework.eks_test_helpers import create_eks_test_config
            self._eks_config = create_eks_test_config(timeout=30)
        return self._eks_config

    @property
    def base_url(self) -> str:
        """Return ALB URL in EKS mode, localhost otherwise."""
        if EKS_TEST_MODE and self.eks_config:
            alb_url = self.eks_config.get_service_url(self.service_name)
            if alb_url:
                return alb_url
        return f"http://localhost:{self.server_port}"

    @property
    def request_timeout(self) -> int:
        """Return appropriate timeout based on test mode."""
        return 30 if EKS_TEST_MODE else 5

    @property
    def server_module_path(self) -> str:
        """Return the server module path for the base class."""
        return "mcp_servers.customer_server.server_rest"

    def get(self, endpoint: str, **kwargs):
        """Make GET request to ALB endpoint."""
        if not EKS_TEST_MODE:
            raise AttributeError("get method only available in EKS test mode")

        import requests
        url = f"{self.base_url.rstrip('/')}{endpoint}"
        kwargs.setdefault('timeout', self.request_timeout)
        return requests.get(url, **kwargs)

    def post(self, endpoint: str, json_data=None, **kwargs):
        """Make POST request to ALB endpoint."""
        if not EKS_TEST_MODE:
            raise AttributeError("post method only available in EKS test mode")

        import requests
        url = f"{self.base_url.rstrip('/')}{endpoint}"
        kwargs.setdefault('timeout', self.request_timeout)
        if json_data is not None:
            kwargs['json'] = json_data
        return requests.post(url, **kwargs)

    def put(self, endpoint: str, json_data=None, **kwargs):
        """Make PUT request to ALB endpoint."""
        if not EKS_TEST_MODE:
            raise AttributeError("put method only available in EKS test mode")

        import requests
        url = f"{self.base_url.rstrip('/')}{endpoint}"
        kwargs.setdefault('timeout', self.request_timeout)
        if json_data is not None:
            kwargs['json'] = json_data
        return requests.put(url, **kwargs)

    def delete(self, endpoint: str, **kwargs):
        """Make DELETE request to ALB endpoint."""
        if not EKS_TEST_MODE:
            raise AttributeError("delete method only available in EKS test mode")

        import requests
        url = f"{self.base_url.rstrip('/')}{endpoint}"
        kwargs.setdefault('timeout', self.request_timeout)
        return requests.delete(url, **kwargs)

    @property
    def expected_tools(self) -> set:
        # For REST API, we test endpoints instead of tools
        return {
            "list_all_customers",
            "list_all_claims",
            "get_customer_profile",
            "get_policy_details",
            "create_claim",
            "get_claim_history",
            "get_claim_details",
            "update_claim_status",
            "check_appliance_coverage"
        }

    def setup_test_data(self):
        """Set up test data before each test."""
        # Initialize mock data
        self._setup_mock_data()

        # Validate EKS endpoint if in EKS mode
        if EKS_TEST_MODE and hasattr(self, 'eks_config'):
            self._validate_alb_endpoint()

    def _setup_mock_data(self):
        """Initialize mock data for testing."""
        # Mock customer data
        self.mock_customers = {
            "CUST001": {
                "id": "CUST001",
                "name": "John Doe",
                "email": "john.doe@email.com",
                "phone": "555-123-4567",
                "address": "123 Main St, City, State 12345",
                "policy_number": "POL-2024-001",
                "covered_appliances": ["refrigerator", "washing_machine", "dishwasher"],
                "created_at": "2023-01-15T10:30:00",
                "policy_details": {
                    "coverage_type": "Premium Home Appliance Protection",
                    "deductible": 50,
                    "annual_limit": 5000,
                    "policy_start": "2023-01-15T00:00:00",
                    "policy_end": "2025-01-15T00:00:00",
                    "monthly_premium": 29.99
                }
            },
            "CUST002": {
                "id": "CUST002",
                "name": "Jane Smith",
                "email": "jane.smith@email.com",
                "phone": "555-987-6543",
                "address": "456 Oak Ave, Town, State 67890",
                "policy_number": "POL-2024-002",
                "covered_appliances": ["refrigerator", "oven", "microwave"],
                "created_at": "2023-02-20T14:15:00",
                "policy_details": {
                    "coverage_type": "Basic Home Appliance Protection",
                    "deductible": 100,
                    "annual_limit": 3000,
                    "policy_start": "2023-02-20T00:00:00",
                    "policy_end": "2025-02-20T00:00:00",
                    "monthly_premium": 19.99
                }
            }
        }

        # Mock claims data
        self.mock_claims = {
            "CLAIM001": {
                "id": "CLAIM001",
                "customer_id": "CUST001",
                "appliance_type": "refrigerator",
                "issue_description": "Refrigerator not cooling properly",
                "status": "approved",
                "urgency_level": "high",
                "created_at": "2024-01-15T10:30:00",
                "approved_at": "2024-01-15T11:00:00",
                "completed_at": None,
                "appointment_id": "APPT001",
                "estimated_cost": 250.0,
                "notes": "Emergency repair needed"
            },
            "CLAIM002": {
                "id": "CLAIM002",
                "customer_id": "CUST001",
                "appliance_type": "washing_machine",
                "issue_description": "Washing machine making loud noises",
                "status": "completed",
                "urgency_level": "medium",
                "created_at": "2024-01-10T09:00:00",
                "approved_at": "2024-01-10T10:00:00",
                "completed_at": "2024-01-12T15:30:00",
                "appointment_id": "APPT002",
                "estimated_cost": 150.0,
                "notes": "Repair completed successfully"
            }
        }

    def _validate_alb_endpoint(self):
        """Validate that the ALB endpoint is accessible before running tests."""
        if not hasattr(self, 'eks_config') or not self.eks_config:
            return

        alb_url = self.eks_config.get_service_url(self.service_name)
        if not alb_url:
            print(f"⚠ Warning: No ALB URL found for {self.service_name}, falling back to localhost")
            return

        print(f"🔍 Validating ALB endpoint for {self.service_name}: {alb_url}")
        is_accessible, message = self.eks_config.validate_alb_endpoint_accessibility(self.service_name)

        if not is_accessible:
            print(f"⚠ Warning: ALB endpoint validation failed: {message}")
            print(f"   Tests may fail or use fallback localhost configuration")
        else:
            print(f"✓ ALB endpoint is accessible: {message}")

    def make_request(self, method: str, endpoint: str, **kwargs):
        """Make HTTP request to either ALB endpoint or localhost based on test mode."""
        if EKS_TEST_MODE and self.eks_config:
            return self._make_eks_request(method, endpoint, **kwargs)
        else:
            return self._make_local_request(method, endpoint, **kwargs)

    def _make_eks_request(self, method: str, endpoint: str, **kwargs):
        """Make HTTP request to ALB endpoint."""
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        url = f"{self.base_url.rstrip('/')}{endpoint}"

        # Set default timeout if not provided
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.request_timeout

        # Create session with retry strategy
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

        try:
            print(f"🌐 Making {method} request to: {url}")

            # Handle 'content' parameter (convert to 'data' for requests)
            if 'content' in kwargs:
                kwargs['data'] = kwargs.pop('content')

            response = session.request(method, url, **kwargs)
            print(f"📊 Response: {response.status_code} {response.reason}")
            return response
        except Exception as e:
            print(f"❌ Request failed: {e}")
            raise

    def _make_local_request(self, method: str, endpoint: str, **kwargs):
        """Make HTTP request to localhost using TestClient."""
        if not hasattr(self, '_test_client'):
            self._test_client = TestClient(rest_app)

        # Convert method to TestClient method
        client_method = getattr(self._test_client, method.lower())

        # Handle JSON data
        if 'json' in kwargs:
            kwargs['json'] = kwargs.pop('json')

        return client_method(endpoint, **kwargs)

    def _make_request(self, method: str, endpoint: str, **kwargs):
        """Alias for make_request for backward compatibility."""
        return self.make_request(method, endpoint, **kwargs)

    def _assert_response_success(self, response, expected_keys=None):
        """Assert that an HTTP response is successful and contains expected data."""
        if not response.ok:
            error_msg = (
                f"HTTP request failed\n"
                f"Status: {response.status_code} {response.reason}\n"
                f"URL: {getattr(response, 'url', 'N/A')}\n"
                f"Service: {self.service_name}\n"
                f"Base URL: {self.base_url}\n"
                f"Response body: {response.text[:500]}..."
            )
            raise AssertionError(error_msg)

        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            error_msg = (
                f"Invalid JSON response\n"
                f"URL: {getattr(response, 'url', 'N/A')}\n"
                f"Service: {self.service_name}\n"
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
                    f"URL: {getattr(response, 'url', 'N/A')}\n"
                    f"Service: {self.service_name}\n"
                    f"Missing keys: {missing_keys}\n"
                    f"Response data: {response_data}"
                )
                raise AssertionError(error_msg)

        return response_data

    def _assert_response_error(self, response, expected_status, expected_error=None):
        """Assert that an HTTP response contains an expected error."""
        if response.status_code != expected_status:
            error_msg = (
                f"Unexpected status code\n"
                f"Expected: {expected_status}\n"
                f"Actual: {response.status_code} {response.reason}\n"
                f"URL: {getattr(response, 'url', 'N/A')}\n"
                f"Service: {self.service_name}\n"
                f"Response body: {response.text[:500]}..."
            )
            raise AssertionError(error_msg)

        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            error_msg = (
                f"Invalid JSON error response\n"
                f"URL: {getattr(response, 'url', 'N/A')}\n"
                f"Service: {self.service_name}\n"
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
                    f"URL: {getattr(response, 'url', 'N/A')}\n"
                    f"Service: {self.service_name}"
                )
                raise AssertionError(error_msg)

        return response_data

    def _patch_shared_data(self):
        """Context manager for patching shared data in local testing mode."""
        if EKS_TEST_MODE:
            # In EKS mode, we use real data, so return a no-op context manager
            from contextlib import nullcontext
            return nullcontext()
        else:
            # In local mode, patch the shared data
            return patch('mcp_servers.customer_server.shared_data.customers', self.mock_customers)

    @property
    def client(self):
        """Get test client for backward compatibility with existing tests."""
        if EKS_TEST_MODE:
            # For EKS mode, we don't use TestClient, but provide a compatible interface
            class EKSTestClient:
                def __init__(self, test_instance):
                    self.test_instance = test_instance

                def get(self, endpoint, **kwargs):
                    return self.test_instance.make_request("GET", endpoint, **kwargs)

                def post(self, endpoint, **kwargs):
                    return self.test_instance.make_request("POST", endpoint, **kwargs)

                def put(self, endpoint, **kwargs):
                    return self.test_instance.make_request("PUT", endpoint, **kwargs)

                def delete(self, endpoint, **kwargs):
                    return self.test_instance.make_request("DELETE", endpoint, **kwargs)

            return EKSTestClient(self)
        else:
            if not hasattr(self, '_test_client'):
                self._test_client = TestClient(rest_app)
            return self._test_client

    def _create_test_client(self):
        """Create test client based on mode."""
        if EKS_TEST_MODE:
            # For EKS mode, we'll use the HTTP client from the base class
            self.client = None  # Will use self.get(), self.post(), etc. methods
        else:
            # For local mode, use FastAPI TestClient
            self.client = TestClient(rest_app)

    def _patch_shared_data(self):
        """Context manager to patch shared data functions."""
        return patch.multiple(
            'mcp_servers.customer_server.server_rest',
            get_customers_data=MagicMock(return_value=self.mock_customers),
            get_claims_data=MagicMock(return_value=self.mock_claims)
        )

    def _make_request(self, method: str, endpoint: str, **kwargs):
        """Make HTTP request using appropriate client based on test mode."""
        if EKS_TEST_MODE:
            # Use ALB endpoint via BaseEKSRESTTest methods
            if method.upper() == "GET":
                return self.get(endpoint, **kwargs)
            elif method.upper() == "POST":
                json_data = kwargs.pop('json', None)
                return self.post(endpoint, json_data=json_data, **kwargs)
            elif method.upper() == "PUT":
                json_data = kwargs.pop('json', None)
                return self.put(endpoint, json_data=json_data, **kwargs)
            elif method.upper() == "DELETE":
                return self.delete(endpoint, **kwargs)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
        else:
            # Use local TestClient
            return getattr(self.client, method.lower())(endpoint, **kwargs)

    def _assert_response_success(self, response, expected_keys=None):
        """Assert response success using appropriate method based on test mode."""
        if EKS_TEST_MODE:
            # For ALB requests (requests.Response object)
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()
            if expected_keys:
                for key in expected_keys:
                    assert key in data, f"Expected key '{key}' not found in response"
            return data
        else:
            # For local TestClient
            assert response.status_code == 200
            data = response.json()
            if expected_keys:
                for key in expected_keys:
                    assert key in data
            return data

    def _assert_response_error(self, response, expected_status, expected_error=None):
        """Assert response error using appropriate method based on test mode."""
        if EKS_TEST_MODE:
            # For ALB requests (requests.Response object)
            assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"
            data = response.json()
            if expected_error:
                assert expected_error in data.get("error", ""), f"Expected error '{expected_error}' not found in response"
            return data
        else:
            # For local TestClient
            assert response.status_code == expected_status
            data = response.json()
            if expected_error:
                assert expected_error in data.get("error", "")
            return data

    # Health check endpoint tests
    def test_health_check(self):
        """Test health check endpoint."""
        self.setup_test_data()
        response = self._make_request("GET", "/health")
        data = self._assert_response_success(response, ["status", "service"])
        assert data["status"] == "healthy"
        assert data["service"] == "customer-info-server"

    # Customer profile endpoint tests
    def test_get_customer_profile_success(self):
        """Test successful customer profile retrieval."""
        self.setup_test_data()

        # Skip data patching for EKS mode (uses real deployed data)
        if EKS_TEST_MODE:
            response = self._make_request("GET", "/customers/CUST001/profile")
            data = self._assert_response_success(response, ["id", "name", "email"])
            # For EKS mode, just verify basic structure since we use real data
            assert "id" in data
            assert "name" in data
            assert "email" in data
        else:
            with self._patch_shared_data():
                response = self._make_request("GET", "/customers/CUST001/profile")
                data = self._assert_response_success(response)
                assert data["id"] == "CUST001"
                assert data["name"] == "John Doe"
                assert data["email"] == "john.doe@email.com"
                assert data["phone"] == "555-123-4567"
                assert data["address"] == "123 Main St, City, State 12345"
                assert data["policy_number"] == "POL-2024-001"
                assert "refrigerator" in data["covered_appliances"]
                assert "washing_machine" in data["covered_appliances"]
                assert "dishwasher" in data["covered_appliances"]
                assert data["created_at"] == "2023-01-15T10:30:00"

    def test_get_customer_profile_not_found(self):
        """Test customer profile retrieval for non-existent customer."""
        self.setup_test_data()

        if EKS_TEST_MODE:
            response = self._make_request("GET", "/customers/CUST999/profile")
            self._assert_response_error(response, 404, "Customer not found")
        else:
            with self._patch_shared_data():
                response = self._make_request("GET", "/customers/CUST999/profile")
                data = self._assert_response_error(response, 404)
                assert "Customer not found" in data["error"]

    # Policy details endpoint tests
    def test_get_policy_details_success(self):
        """Test successful policy details retrieval."""
        self.setup_test_data()
        with self._patch_shared_data():
            response = self.client.get("/customers/CUST001/policy")
            assert response.status_code == 200

            data = response.json()
            assert data["customer_id"] == "CUST001"
            assert data["policy_number"] == "POL-2024-001"
            assert "refrigerator" in data["covered_appliances"]
            assert data["policy_details"]["coverage_type"] == "Premium Home Appliance Protection"
            assert data["policy_details"]["deductible"] == 50
            assert data["policy_details"]["annual_limit"] == 5000
            assert data["active"] is True

    def test_get_policy_details_not_found(self):
        """Test policy details retrieval for non-existent customer."""
        self.setup_test_data()
        with self._patch_shared_data():
            response = self.client.get("/customers/CUST999/policy")
            assert response.status_code == 404

            data = response.json()
            assert "Customer not found" in data["error"]

    # Coverage validation endpoint tests
    def test_check_appliance_coverage_covered(self):
        """Test appliance coverage check for covered appliance."""
        self.setup_test_data()
        request_data = {"appliance_type": "refrigerator"}

        if EKS_TEST_MODE:
            response = self._make_request("POST", "/customers/CUST001/validate-coverage", json=request_data)
            data = self._assert_response_success(response, ["customer_id", "appliance_type", "is_covered"])
            # For EKS mode, verify basic structure with real data
            assert data["customer_id"] == "CUST001"
            assert data["appliance_type"] == "refrigerator"
            assert isinstance(data["is_covered"], bool)
        else:
            with self._patch_shared_data():
                response = self._make_request("POST", "/customers/CUST001/validate-coverage", json=request_data)
                data = self._assert_response_success(response)
                assert data["customer_id"] == "CUST001"
                assert data["appliance_type"] == "refrigerator"
                assert data["is_covered"] is True
                assert "refrigerator" in data["covered_appliances"]
                assert data["policy_info"] is not None
                assert data["policy_info"]["coverage_type"] == "Premium Home Appliance Protection"

    def test_check_appliance_coverage_not_covered(self):
        """Test appliance coverage check for non-covered appliance."""
        self.setup_test_data()
        with self._patch_shared_data():
            request_data = {"appliance_type": "air_conditioner"}
            response = self.client.post("/customers/CUST001/validate-coverage", json=request_data)
            assert response.status_code == 200

            data = response.json()
            assert data["customer_id"] == "CUST001"
            assert data["appliance_type"] == "air_conditioner"
            assert data["is_covered"] is False
            assert "air_conditioner" not in data["covered_appliances"]
            # policy_info should be None for non-covered appliances (due to exclude_none=True)

    def test_check_appliance_coverage_customer_not_found(self):
        """Test appliance coverage check for non-existent customer."""
        self.setup_test_data()
        with self._patch_shared_data():
            request_data = {"appliance_type": "refrigerator"}
            response = self.client.post("/customers/CUST999/validate-coverage", json=request_data)
            assert response.status_code == 404

            data = response.json()
            assert "Customer not found" in data["error"]

    def test_check_appliance_coverage_invalid_request(self):
        """Test appliance coverage check with invalid request data."""
        self.setup_test_data()
        with self._patch_shared_data():
            # Missing appliance_type
            response = self.client.post("/customers/CUST001/validate-coverage", json={})
            assert response.status_code == 422

            # Empty appliance_type
            request_data = {"appliance_type": ""}
            response = self.client.post("/customers/CUST001/validate-coverage", json=request_data)
            assert response.status_code == 422

    # Claim creation endpoint tests
    def test_create_claim_success(self):
        """Test successful claim creation."""
        self.setup_test_data()
        request_data = {
            "customer_id": "CUST001",
            "appliance_type": "refrigerator",
            "issue_description": "Refrigerator temperature fluctuating",
            "urgency_level": "medium"
        }

        if EKS_TEST_MODE:
            response = self._make_request("POST", "/claims", json=request_data)
            data = self._assert_response_success(response, ["success", "claim_id", "status"])
            # For EKS mode, verify basic structure with real data
            assert data["success"] is True
            assert "claim_id" in data
            assert "status" in data
        else:
            with self._patch_shared_data():
                response = self._make_request("POST", "/claims", json=request_data)
                data = self._assert_response_success(response)
                assert data["success"] is True
                assert "claim_id" in data
                assert data["status"] == "submitted"
                assert data["message"] == "Claim created successfully"

                claim = data["claim"]
                assert claim["customer_id"] == "CUST001"
                assert claim["appliance_type"] == "refrigerator"
                assert claim["issue_description"] == "Refrigerator temperature fluctuating"
                assert claim["urgency_level"] == "medium"
                assert claim["status"] == "submitted"

    def test_create_claim_customer_not_found(self):
        """Test claim creation for non-existent customer."""
        self.setup_test_data()
        with self._patch_shared_data():
            request_data = {
                "customer_id": "CUST999",
                "appliance_type": "refrigerator",
                "issue_description": "Not working",
                "urgency_level": "medium"
            }

            response = self.client.post("/claims", json=request_data)
            assert response.status_code == 404

            data = response.json()
            assert "Customer not found" in data["error"]

    def test_create_claim_appliance_not_covered(self):
        """Test claim creation for non-covered appliance."""
        self.setup_test_data()
        with self._patch_shared_data():
            request_data = {
                "customer_id": "CUST001",
                "appliance_type": "air_conditioner",
                "issue_description": "Not cooling",
                "urgency_level": "high"
            }

            response = self.client.post("/claims", json=request_data)
            assert response.status_code == 400

            data = response.json()
            assert "not covered under policy" in data["error"]

    def test_create_claim_invalid_request(self):
        """Test claim creation with invalid request data."""
        self.setup_test_data()
        with self._patch_shared_data():
            # Missing required fields
            response = self.client.post("/claims", json={})
            assert response.status_code == 422

            # Invalid urgency level
            request_data = {
                "customer_id": "CUST001",
                "appliance_type": "refrigerator",
                "issue_description": "Not working",
                "urgency_level": "invalid_level"
            }
            response = self.client.post("/claims", json=request_data)
            assert response.status_code == 422

            # Issue description too short
            request_data = {
                "customer_id": "CUST001",
                "appliance_type": "refrigerator",
                "issue_description": "Bad",  # Too short
                "urgency_level": "medium"
            }
            response = self.client.post("/claims", json=request_data)
            assert response.status_code == 422

    # Claim history endpoint tests
    def test_get_claim_history_success(self):
        """Test successful claim history retrieval."""
        self.setup_test_data()

        if EKS_TEST_MODE:
            response = self._make_request("GET", "/customers/CUST001/claims")
            data = self._assert_response_success(response, ["customer_id", "total_claims", "status_filter"])
            # For EKS mode, just verify basic structure with real data
            assert data["customer_id"] == "CUST001"
            assert isinstance(data["total_claims"], int)
            assert data["total_claims"] >= 0  # Could be any number in real data
            assert data["status_filter"] == "all"
        else:
            with self._patch_shared_data():
                response = self.client.get("/customers/CUST001/claims")
                assert response.status_code == 200

                data = response.json()
                assert data["customer_id"] == "CUST001"
                assert data["total_claims"] == 2
                assert data["status_filter"] == "all"

            claims = data["claims"]
            assert len(claims) == 2
            # Should be sorted by creation date (newest first)
            assert claims[0]["id"] == "CLAIM001"  # Newer
            assert claims[1]["id"] == "CLAIM002"  # Older

    def test_get_claim_history_with_status_filter(self):
        """Test claim history retrieval with status filter."""
        self.setup_test_data()
        with self._patch_shared_data():
            response = self.client.get("/customers/CUST001/claims?status_filter=approved")
            assert response.status_code == 200

            data = response.json()
            assert data["status_filter"] == "approved"
            assert len(data["claims"]) == 1
            assert data["claims"][0]["status"] == "approved"

    def test_get_claim_history_customer_not_found(self):
        """Test claim history retrieval for non-existent customer."""
        self.setup_test_data()
        with self._patch_shared_data():
            response = self.client.get("/customers/CUST999/claims")
            assert response.status_code == 404

            data = response.json()
            assert "Customer not found" in data["error"]

    # Claim details endpoint tests
    def test_get_claim_details_success(self):
        """Test successful claim details retrieval."""
        self.setup_test_data()

        if EKS_TEST_MODE:
            response = self._make_request("GET", "/claims/CLAIM001")
            data = self._assert_response_success(response, ["id", "customer_id", "appliance_type", "issue_description"])
            # For EKS mode, verify basic structure with real data
            assert data["id"] == "CLAIM001"
            assert data["customer_id"] == "CUST001"
            assert data["appliance_type"] == "refrigerator"
            assert "refrigerator" in data["issue_description"].lower()  # Flexible description check
            assert "status" in data
            assert "urgency_level" in data
        else:
            with self._patch_shared_data():
                response = self.client.get("/claims/CLAIM001")
                assert response.status_code == 200

                data = response.json()
                assert data["id"] == "CLAIM001"
                assert data["customer_id"] == "CUST001"
                assert data["appliance_type"] == "refrigerator"
                assert data["issue_description"] == "Refrigerator not cooling properly"
                assert data["status"] == "approved"
                assert data["urgency_level"] == "high"
                assert data["created_at"] == "2024-01-15T10:30:00"
                assert data["approved_at"] == "2024-01-15T11:00:00"
                assert data["completed_at"] is None
                assert data["appointment_id"] == "APPT001"
                assert data["estimated_cost"] == 250.0
                assert data["notes"] == "Emergency repair needed"

    def test_get_claim_details_not_found(self):
        """Test claim details retrieval for non-existent claim."""
        self.setup_test_data()
        with self._patch_shared_data():
            response = self.client.get("/claims/CLAIM999")
            assert response.status_code == 404

            data = response.json()
            assert "Claim not found" in data["error"]

    # Claim status update endpoint tests
    def test_update_claim_status_success(self):
        """Test successful claim status update."""
        self.setup_test_data()

        if EKS_TEST_MODE:
            request_data = {
                "new_status": "completed",
                "notes": "Repair completed successfully"
            }
            response = self._make_request("PUT", "/claims/CLAIM001/status", json=request_data)
            data = self._assert_response_success(response, ["success", "claim_id", "new_status"])
            # For EKS mode, verify basic structure with real data
            assert data["success"] is True
            assert data["claim_id"] == "CLAIM001"
            assert data["new_status"] == "completed"
            assert "old_status" in data  # Don't check specific value since it varies with real data
            assert "updated_at" in data
        else:
            with self._patch_shared_data():
                request_data = {
                    "new_status": "completed",
                    "notes": "Repair completed successfully"
                }

                response = self.client.put("/claims/CLAIM001/status", json=request_data)
                assert response.status_code == 200

                data = response.json()
                assert data["success"] is True
                assert data["claim_id"] == "CLAIM001"
                assert data["old_status"] == "approved"
                assert data["new_status"] == "completed"
                assert "updated_at" in data
                assert "claim" in data

    def test_update_claim_status_not_found(self):
        """Test claim status update for non-existent claim."""
        self.setup_test_data()
        with self._patch_shared_data():
            request_data = {
                "new_status": "completed",
                "notes": "Repair completed"
            }

            response = self.client.put("/claims/CLAIM999/status", json=request_data)
            assert response.status_code == 404

            data = response.json()
            assert "Claim not found" in data["error"]

    def test_update_claim_status_invalid_request(self):
        """Test claim status update with invalid request data."""
        self.setup_test_data()
        with self._patch_shared_data():
            # Invalid status
            request_data = {
                "new_status": "invalid_status",
                "notes": "Test notes"
            }

            response = self.client.put("/claims/CLAIM001/status", json=request_data)
            assert response.status_code == 422

    # Case sensitivity tests
    def test_case_insensitive_appliance_matching(self):
        """Test that appliance matching is case insensitive."""
        self.setup_test_data()
        with self._patch_shared_data():
            # Test coverage check with different cases
            test_cases = ["REFRIGERATOR", "Refrigerator", "refrigerator", "rEfRiGeRaToR"]

            for appliance_type in test_cases:
                request_data = {"appliance_type": appliance_type}
                response = self.client.post("/customers/CUST001/validate-coverage", json=request_data)
                assert response.status_code == 200

                data = response.json()
                assert data["is_covered"] is True, f"Failed for case: {appliance_type}"

            # Test claim creation with different cases
            for appliance_type in test_cases:
                request_data = {
                    "customer_id": "CUST001",
                    "appliance_type": appliance_type,
                    "issue_description": "Test issue description",
                    "urgency_level": "medium"
                }
                response = self.client.post("/claims", json=request_data)
                assert response.status_code == 200, f"Failed for case: {appliance_type}"

    # Error handling tests
    def test_internal_server_error_handling(self):
        """Test internal server error handling."""
        self.setup_test_data()

        if EKS_TEST_MODE:
            # Skip error simulation in EKS mode - can't patch real deployed services
            import pytest
            pytest.skip("Error simulation not supported in EKS mode with real deployed services")
        else:
            # Patch to raise an exception
            with patch('mcp_servers.customer_server.server_rest.get_customers_data', side_effect=Exception("Database error")):
                response = self.client.get("/customers/CUST001/profile")
                assert response.status_code == 500

                data = response.json()
                assert "Internal server error" in data["error"]

    # OpenAPI documentation tests
    def test_openapi_docs_available(self):
        """Test that OpenAPI documentation is available."""
        self.setup_test_data()
        response = self._make_request("GET", "/docs")
        # For docs endpoint, we just check that it returns successfully
        if EKS_TEST_MODE:
            assert response.status_code == 200
        else:
            assert response.status_code == 200

    def test_openapi_json_available(self):
        """Test that OpenAPI JSON specification is available."""
        self.setup_test_data()
        response = self._make_request("GET", "/openapi.json")
        data = self._assert_response_success(response, ["openapi", "info"])
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Customer Information Server REST API"

    def teardown_method(self):
        """Clean up after each test method."""
        if EKS_TEST_MODE and hasattr(self, 'cleanup'):
            self.cleanup()

    # Request validation tests
    def test_request_validation_empty_json(self):
        """Test request validation with empty JSON."""
        self.setup_test_data()
        response = self.client.post("/claims", json={})
        assert response.status_code == 422

    def test_request_validation_invalid_json(self):
        """Test request validation with invalid JSON."""
        self.setup_test_data()
        response = self.client.post(
            "/claims",
            content='{"invalid": json}',
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_request_validation_missing_content_type(self):
        """Test request validation with missing content type."""
        self.setup_test_data()
        response = self.client.post("/claims", content='{"test": "data"}')
        assert response.status_code == 422


class TestCustomerServerRESTIntegration(BaseMCPIntegrationTest):
    """Test customer server REST API integration."""

    @property
    def server_name(self) -> str:
        return "Customer Information Server REST API"

    @property
    def server_port(self) -> int:
        return 8001

    @property
    def server_module_path(self) -> str:
        return "mcp_servers.customer_server.server_rest.main"

    def test_rest_api_integration(self):
        """Test REST API integration with real server."""
        # This would test the actual REST API server
        # For now, we'll use the TestClient approach
        client = TestClient(rest_app)

        # Test basic connectivity
        response = client.get("/health")
        assert response.status_code == 200

        # Test OpenAPI docs
        response = client.get("/openapi.json")
        assert response.status_code == 200


class TestCustomerServerRESTStandalone(BaseMCPStandaloneTest):
    """Test customer server REST API in standalone mode."""

    @property
    def server_name(self) -> str:
        return "Customer Information Server REST API"

    @property
    def server_port(self) -> int:
        return 8001

    @property
    def server_module_path(self) -> str:
        return "mcp_servers.customer_server.server_rest.main"

    def test_rest_api_standalone(self):
        """Test REST API in standalone mode."""
        # This would test the REST API server running independently
        # For now, we'll use the TestClient approach
        client = TestClient(rest_app)

        # Test that the server can handle requests independently
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["service"] == "customer-info-server"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
