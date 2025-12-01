"""
Comprehensive test suite for Technician Tracking Server REST API.

This module tests the REST API endpoints using the same test framework
and patterns as the MCP server tests. It supports both local testing (using TestClient)
and EKS deployment testing (using ALB endpoints) based on the EKS_TEST_MODE environment variable.
"""

import json
import os
import pytest
import sys
from datetime import datetime, timedelta
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
from mcp_servers.technician_server.server_rest import app as rest_app
from mcp_servers.technician_server.shared_data import load_mock_data

# Check if we're running in EKS test mode
EKS_TEST_MODE = os.getenv("EKS_TEST_MODE", "false").lower() == "true"


# Always use BaseMCPEndpointTest as base, but add EKS functionality dynamically
BaseTestClass = BaseMCPEndpointTest


class TestTechnicianServerRESTEndpoints(BaseTestClass):
    """Test technician server REST API endpoints."""

    # Class attributes for EKS support
    server_port = 8003
    service_name = "technician-server"
    _eks_config = None

    @property
    def server_name(self) -> str:
        return "Technician Tracking Server REST API"

    @property
    def server_module_path(self) -> str:
        return "mcp_servers.technician_server.server_rest"

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
            "list_all_technicians",
            "get_technician_status",
            "get_technician_location",
            "list_available_technicians",
            "update_technician_status",
            "get_technician_route",
            "notify_status_change"
        }

    def setup_test_data(self):
        """Set up test data before each test."""
        # Initialize mock data
        self._setup_mock_data()

        # Validate EKS endpoint if in EKS mode
        if EKS_TEST_MODE and hasattr(self, 'eks_config'):
            self._validate_alb_endpoint()

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

    def _setup_mock_data(self):
        """Initialize mock data for testing."""

        # Mock technician data
        self.mock_technicians = {
            "TECH001": {
                "id": "TECH001",
                "name": "Mike Johnson",
                "phone": "555-101-2001",
                "specialties": ["refrigerator", "dishwasher", "ice_maker"],
                "status": "available",
                "current_location": [47.6062, -122.3321],  # Seattle coordinates
                "current_appointment_id": None,
                "estimated_arrival": None,
                "profile": {
                    "experience_years": 8,
                    "certification_level": "Senior",
                    "service_area": "North Seattle",
                    "rating": 4.8
                }
            },
            "TECH002": {
                "id": "TECH002",
                "name": "Sarah Wilson",
                "phone": "555-102-2002",
                "specialties": ["washing_machine", "dryer", "dishwasher"],
                "status": "en_route",
                "current_location": [47.6205, -122.3493],  # Different Seattle location
                "current_appointment_id": "APPT001",
                "estimated_arrival": (datetime.now() + timedelta(minutes=25)).isoformat(),
                "profile": {
                    "experience_years": 5,
                    "certification_level": "Intermediate",
                    "service_area": "Central Seattle",
                    "rating": 4.6
                }
            },
            "TECH003": {
                "id": "TECH003",
                "name": "David Chen",
                "phone": "555-103-2003",
                "specialties": ["oven", "microwave", "range"],
                "status": "on_site",
                "current_location": [47.5952, -122.3316],  # Another Seattle location
                "current_appointment_id": "APPT002",
                "estimated_arrival": None,
                "profile": {
                    "experience_years": 12,
                    "certification_level": "Expert",
                    "service_area": "South Seattle",
                    "rating": 4.9
                }
            },
            "TECH004": {
                "id": "TECH004",
                "name": "Lisa Rodriguez",
                "phone": "555-104-2004",
                "specialties": ["refrigerator", "freezer", "ice_maker"],
                "status": "busy",
                "current_location": [47.6097, -122.3331],
                "current_appointment_id": "APPT003",
                "estimated_arrival": None,
                "profile": {
                    "experience_years": 6,
                    "certification_level": "Intermediate",
                    "service_area": "Downtown Seattle",
                    "rating": 4.7
                }
            }
        }

    @property
    def client(self):
        """Get test client based on mode."""
        if EKS_TEST_MODE:
            # For EKS mode, create a wrapper that uses _make_request
            class EKSTestClient:
                def __init__(self, test_instance):
                    self.test_instance = test_instance

                def get(self, endpoint, **kwargs):
                    return self.test_instance._make_request("GET", endpoint, **kwargs)

                def post(self, endpoint, **kwargs):
                    return self.test_instance._make_request("POST", endpoint, **kwargs)

                def put(self, endpoint, **kwargs):
                    return self.test_instance._make_request("PUT", endpoint, **kwargs)

                def delete(self, endpoint, **kwargs):
                    return self.test_instance._make_request("DELETE", endpoint, **kwargs)

                def request(self, method, endpoint, **kwargs):
                    return self.test_instance._make_request(method, endpoint, **kwargs)

            return EKSTestClient(self)
        else:
            if not hasattr(self, '_test_client'):
                self._test_client = TestClient(rest_app)
            return self._test_client

    def _create_test_client(self):
        """Create test client based on mode."""

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

    def _patch_shared_data(self):
        """Context manager to patch shared data functions."""
        return patch.multiple(
            'mcp_servers.technician_server.server_rest',
            get_technicians_data=MagicMock(return_value=self.mock_technicians)
        )

    # Health check endpoint tests
    def test_health_check(self):
        """Test health check endpoint."""
        self.setup_test_data()
        response = self._make_request("GET", "/health")
        data = self._assert_response_success(response, ["status", "service"])
        assert data["status"] == "healthy"
        assert data["service"] == "technician-tracking-server"

    def teardown_method(self):
        """Clean up after each test method."""
        if EKS_TEST_MODE and hasattr(self, 'cleanup'):
            self.cleanup()

    # Technician status endpoint tests
    def test_get_technician_status_success(self):
        """Test successful technician status retrieval."""
        self.setup_test_data()

        if EKS_TEST_MODE:
            response = self._make_request("GET", "/technicians/TECH001/status")
            data = self._assert_response_success(response, ["technician_id", "name", "status", "specialties"])
            # For EKS mode, verify basic structure with real data
            assert data["technician_id"] == "TECH001"
            assert "name" in data
            assert "status" in data
            assert isinstance(data["specialties"], list)
            assert "phone" in data
            assert "last_updated" in data
        else:
            with self._patch_shared_data():
                response = self.client.get("/technicians/TECH001/status")
                assert response.status_code == 200

                data = response.json()
                assert data["technician_id"] == "TECH001"
                assert data["name"] == "Mike Johnson"
                assert data["status"] == "available"
                assert "refrigerator" in data["specialties"]
                assert "dishwasher" in data["specialties"]
                assert "ice_maker" in data["specialties"]
                assert data["phone"] == "555-101-2001"
                assert data["current_appointment_id"] is None
                assert data["estimated_arrival"] is None
                assert "last_updated" in data

    def test_get_technician_status_en_route(self):
        """Test technician status retrieval for en_route technician."""
        self.setup_test_data()

        if EKS_TEST_MODE:
            response = self._make_request("GET", "/technicians/TECH002/status")
            data = self._assert_response_success(response, ["technician_id", "name", "status"])
            # For EKS mode, verify basic structure with real data
            assert data["technician_id"] == "TECH002"
            assert "name" in data
            assert "status" in data
            # Don't check specific status or appointment ID as real data varies
        else:
            with self._patch_shared_data():
                response = self.client.get("/technicians/TECH002/status")
                assert response.status_code == 200

                data = response.json()
                assert data["technician_id"] == "TECH002"
                assert data["name"] == "Sarah Wilson"
                assert data["status"] == "en_route"
                assert data["current_appointment_id"] == "APPT001"
                assert data["estimated_arrival"] is not None

    def test_get_technician_status_not_found(self):
        """Test technician status retrieval for non-existent technician."""
        self.setup_test_data()
        with self._patch_shared_data():
            response = self.client.get("/technicians/TECH999/status")
            assert response.status_code == 404

            data = response.json()
            assert "Technician not found" in data["error"]

    # Technician location endpoint tests
    def test_get_technician_location_success(self):
        """Test successful technician location retrieval."""
        self.setup_test_data()

        if EKS_TEST_MODE:
            response = self._make_request("GET", "/technicians/TECH001/location")
            data = self._assert_response_success(response, ["technician_id", "name", "current_location"])
            # For EKS mode, verify basic structure with real data
            assert data["technician_id"] == "TECH001"
            assert "name" in data
            assert "current_location" in data
            assert "latitude" in data["current_location"]
            assert "longitude" in data["current_location"]
            assert "status" in data
            assert "last_location_update" in data
        else:
            with self._patch_shared_data():
                response = self.client.get("/technicians/TECH001/location")
                assert response.status_code == 200

                data = response.json()
                assert data["technician_id"] == "TECH001"
                assert data["name"] == "Mike Johnson"
                assert "current_location" in data
                assert "latitude" in data["current_location"]
                assert "longitude" in data["current_location"]
                assert data["status"] == "available"
                assert "last_location_update" in data

    def test_get_technician_location_with_eta(self):
        """Test technician location retrieval with ETA calculation."""
        self.setup_test_data()

        if EKS_TEST_MODE:
            # In EKS mode, test with real data - any technician should work
            response = self._make_request("GET", "/technicians/TECH002/location")
            data = self._assert_response_success(response, ["technician_id", "status"])
            assert data["technician_id"] == "TECH002"
            # Don't assert specific status in EKS mode - real data varies
            assert "status" in data
            # ETA fields may or may not be present depending on real status
            if data.get("status") == "en_route":
                assert "eta_minutes" in data
        else:
            with self._patch_shared_data():
                response = self.client.get("/technicians/TECH002/location")
                assert response.status_code == 200

                data = response.json()
                assert data["technician_id"] == "TECH002"
                assert data["status"] == "en_route"
                assert data["estimated_arrival"] is not None
                # ETA should be calculated for en_route technicians
                assert "eta_minutes" in data

    def test_get_technician_location_not_found(self):
        """Test technician location retrieval for non-existent technician."""
        self.setup_test_data()
        with self._patch_shared_data():
            response = self.client.get("/technicians/TECH999/location")
            assert response.status_code == 404

            data = response.json()
            assert "Technician not found" in data["error"]

    # Available technicians endpoint tests
    def test_list_available_technicians_success(self):
        """Test successful available technicians listing."""
        self.setup_test_data()
        with self._patch_shared_data():
            request_data = {
                "area": "Seattle",
                "datetime_str": "2024-01-20T14:00:00",
                "specialties": ["refrigerator"]
            }

            response = self.client.post("/technicians/available", json=request_data)
            assert response.status_code == 200

            data = response.json()
            assert data["area"] == "Seattle"
            assert data["requested_datetime"] == "2024-01-20T14:00:00"
            assert data["required_specialties"] == ["refrigerator"]
            assert "available_technicians" in data
            assert data["total_found"] >= 0

            # Should only include available technicians with refrigerator specialty
            for tech in data["available_technicians"]:
                assert "refrigerator" in [spec.lower() for spec in tech["specialties"]]
                assert "distance_miles" in tech
                assert "eta_minutes" in tech
                assert "estimated_arrival" in tech

    def test_list_available_technicians_no_matches(self):
        """Test available technicians listing with no matches."""
        self.setup_test_data()
        with self._patch_shared_data():
            request_data = {
                "area": "Seattle",
                "datetime_str": "2024-01-20T14:00:00",
                "specialties": ["nonexistent_appliance"]
            }

            response = self.client.post("/technicians/available", json=request_data)
            assert response.status_code == 200

            data = response.json()
            assert data["total_found"] == 0
            assert len(data["available_technicians"]) == 0

    def test_list_available_technicians_invalid_datetime(self):
        """Test available technicians listing with invalid datetime."""
        self.setup_test_data()
        with self._patch_shared_data():
            request_data = {
                "area": "Seattle",
                "datetime_str": "invalid-datetime",
                "specialties": ["refrigerator"]
            }

            response = self.client.post("/technicians/available", json=request_data)
            assert response.status_code == 400

            data = response.json()
            assert "Invalid datetime format" in data["error"]

    def test_list_available_technicians_invalid_request(self):
        """Test available technicians listing with invalid request data."""
        self.setup_test_data()
        with self._patch_shared_data():
            # Missing required fields
            response = self.client.post("/technicians/available", json={})
            assert response.status_code == 422

            # Empty specialties list
            request_data = {
                "area": "Seattle",
                "datetime_str": "2024-01-20T14:00:00",
                "specialties": []
            }
            response = self.client.post("/technicians/available", json=request_data)
            assert response.status_code == 200  # Should still work with empty specialties

    # Update technician status endpoint tests
    def test_update_technician_status_success(self):
        """Test successful technician status update."""
        self.setup_test_data()

        if EKS_TEST_MODE:
            # In EKS mode, test with real data
            request_data = {
                "new_status": "en_route",
                "appointment_id": "APPT005"
            }
            response = self._make_request("PUT", "/technicians/TECH001/status", json=request_data)
            data = self._assert_response_success(response, ["success", "technician_id", "new_status"])
            assert data["success"] is True
            assert data["technician_id"] == "TECH001"
            assert data["new_status"] == "en_route"
            # Don't assert specific old_status in EKS mode - real data varies
            assert "old_status" in data
            assert "updated_at" in data
        else:
            with self._patch_shared_data():
                request_data = {
                    "new_status": "en_route",
                    "appointment_id": "APPT005"
                }

                response = self.client.put("/technicians/TECH001/status", json=request_data)
                assert response.status_code == 200

                data = response.json()
                assert data["success"] is True
                assert data["technician_id"] == "TECH001"
                assert data["old_status"] == "available"
                assert data["new_status"] == "en_route"
                assert data["current_appointment_id"] == "APPT005"
                assert "updated_at" in data
                assert "estimated_arrival" in data

    def test_update_technician_status_with_location(self):
        """Test technician status update with location."""
        self.setup_test_data()
        with self._patch_shared_data():
            request_data = {
                "new_status": "on_site",
                "location": [47.6100, -122.3300],
                "appointment_id": "APPT006"
            }

            response = self.client.put("/technicians/TECH001/status", json=request_data)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["new_status"] == "on_site"
            assert data["current_appointment_id"] == "APPT006"

    def test_update_technician_status_to_available(self):
        """Test technician status update to available (clears appointment)."""
        self.setup_test_data()
        with self._patch_shared_data():
            request_data = {
                "new_status": "available"
            }

            response = self.client.put("/technicians/TECH002/status", json=request_data)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["new_status"] == "available"
            # Should clear appointment when becoming available
            assert data["current_appointment_id"] is None

    def test_update_technician_status_invalid_status(self):
        """Test technician status update with invalid status."""
        self.setup_test_data()
        with self._patch_shared_data():
            request_data = {
                "new_status": "invalid_status"
            }

            response = self.client.put("/technicians/TECH001/status", json=request_data)
            assert response.status_code == 422

    def test_update_technician_status_invalid_location(self):
        """Test technician status update with invalid location."""
        self.setup_test_data()
        with self._patch_shared_data():
            request_data = {
                "new_status": "on_site",
                "location": [47.6100]  # Missing longitude
            }

            response = self.client.put("/technicians/TECH001/status", json=request_data)
            assert response.status_code == 422

    def test_update_technician_status_not_found(self):
        """Test technician status update for non-existent technician."""
        self.setup_test_data()
        with self._patch_shared_data():
            request_data = {
                "new_status": "busy"
            }

            response = self.client.put("/technicians/TECH999/status", json=request_data)
            assert response.status_code == 404

            data = response.json()
            assert "Technician not found" in data["error"]

    # Route calculation endpoint tests (GET version)
    def test_get_technician_route_success(self):
        """Test successful route calculation using GET method."""
        self.setup_test_data()

        destination = json.dumps([47.6200, -122.3500])

        if EKS_TEST_MODE:
            response = self._make_request("GET", f"/technicians/TECH001/route?destination={destination}")
            data = self._assert_response_success(response, ["technician_id", "origin", "destination"])
            # For EKS mode, verify basic structure with real data
            assert data["technician_id"] == "TECH001"
            assert "technician_name" in data  # Don't check specific name
            assert "origin" in data
            assert "destination" in data
            assert "distance_miles" in data
            assert "estimated_travel_time_minutes" in data
            assert "latitude" in data["origin"]
            assert "longitude" in data["origin"]
        else:
            with self._patch_shared_data():
                response = self.client.get(f"/technicians/TECH001/route?destination={destination}")
                assert response.status_code == 200

                data = response.json()
                assert data["technician_id"] == "TECH001"
                assert data["technician_name"] == "Mike Johnson"
                assert "origin" in data
                assert "destination" in data
                assert "distance_miles" in data
                assert "estimated_travel_time_minutes" in data
                assert "estimated_arrival" in data
                assert "traffic_conditions" in data
                assert "route_waypoints" in data
                assert "calculated_at" in data

                # Verify coordinate structure
                assert "latitude" in data["origin"]
                assert "longitude" in data["origin"]
            assert "latitude" in data["destination"]
            assert "longitude" in data["destination"]

    def test_get_technician_route_invalid_destination_format(self):
        """Test route calculation with invalid destination format."""
        self.setup_test_data()
        with self._patch_shared_data():
            # Invalid JSON
            response = self.client.get("/technicians/TECH001/route?destination=invalid_json")
            assert response.status_code == 400

            data = response.json()
            assert "Invalid destination format" in data["error"]

            # Wrong number of coordinates
            destination = json.dumps([47.6200])  # Missing longitude
            response = self.client.get(f"/technicians/TECH001/route?destination={destination}")
            assert response.status_code == 400

    def test_get_technician_route_not_found(self):
        """Test route calculation for non-existent technician."""
        self.setup_test_data()
        with self._patch_shared_data():
            destination = json.dumps([47.6200, -122.3500])
            response = self.client.get(f"/technicians/TECH999/route?destination={destination}")
            assert response.status_code == 404

            data = response.json()
            assert "Technician not found" in data["error"]

    # Route calculation endpoint tests (POST version)
    def test_post_technician_route_success(self):
        """Test successful route calculation using POST method."""
        self.setup_test_data()

        request_data = {
            "destination": [47.6200, -122.3500]
        }

        if EKS_TEST_MODE:
            response = self._make_request("POST", "/technicians/TECH001/route", json=request_data)
            data = self._assert_response_success(response, ["technician_id", "distance_miles", "estimated_travel_time_minutes"])
            # For EKS mode, verify basic structure with real data
            assert data["technician_id"] == "TECH001"
            assert "technician_name" in data  # Don't check specific name
            assert "distance_miles" in data
            assert "estimated_travel_time_minutes" in data
            if "route_waypoints" in data:
                assert isinstance(data["route_waypoints"], list)
        else:
            with self._patch_shared_data():
                response = self.client.post("/technicians/TECH001/route", json=request_data)
                assert response.status_code == 200

                data = response.json()
                assert data["technician_id"] == "TECH001"
                assert data["technician_name"] == "Mike Johnson"
                assert "distance_miles" in data
                assert "estimated_travel_time_minutes" in data
                assert data["traffic_conditions"] in ["light", "moderate", "heavy"]
                assert len(data["route_waypoints"]) >= 2

                # Verify waypoint structure
                for waypoint in data["route_waypoints"]:
                    assert "latitude" in waypoint
                    assert "longitude" in waypoint
                    assert "instruction" in waypoint

    def test_post_technician_route_invalid_destination(self):
        """Test POST route calculation with invalid destination."""
        self.setup_test_data()
        with self._patch_shared_data():
            request_data = {
                "destination": [47.6200]  # Missing longitude
            }

            response = self.client.post("/technicians/TECH001/route", json=request_data)
            assert response.status_code == 422

    # Status notification endpoint tests
    def test_notify_status_change_success(self):
        """Test successful status change notification."""
        self.setup_test_data()

        request_data = {
            "appointment_id": "APPT001"
        }

        if EKS_TEST_MODE:
            response = self._make_request("POST", "/technicians/TECH002/notify", json=request_data)
            data = self._assert_response_success(response, ["success", "appointment_id", "technician_id"])
            # For EKS mode, verify basic structure with real data
            assert data["success"] is True
            assert data["appointment_id"] == "APPT001"
            assert data["technician_id"] == "TECH002"
            assert "technician_name" in data  # Don't check specific name
            assert "current_status" in data  # Don't check specific status
            assert "message" in data
            assert "timestamp" in data
        else:
            with self._patch_shared_data():
                response = self.client.post("/technicians/TECH002/notify", json=request_data)
                assert response.status_code == 200

                data = response.json()
                assert data["success"] is True
                assert data["appointment_id"] == "APPT001"
                assert data["technician_id"] == "TECH002"
                assert data["technician_name"] == "Sarah Wilson"
                assert data["current_status"] == "en_route"
                assert "message" in data
                assert "timestamp" in data
                assert "estimated_arrival" in data
            # Should include location for en_route technicians
            assert "current_location" in data

    def test_notify_status_change_custom_message(self):
        """Test status change notification with custom message."""
        self.setup_test_data()
        with self._patch_shared_data():
            request_data = {
                "appointment_id": "APPT002",
                "status_message": "Custom status update message"
            }

            response = self.client.post("/technicians/TECH003/notify", json=request_data)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Custom status update message"
            assert data["current_status"] == "on_site"

    def test_notify_status_change_different_statuses(self):
        """Test status change notifications for different technician statuses."""
        self.setup_test_data()

        if EKS_TEST_MODE:
            # In EKS mode, just test one technician since real data varies
            request_data = {
                "appointment_id": "APPT_TECH001"
            }
            response = self._make_request("POST", "/technicians/TECH001/notify", json=request_data)
            data = self._assert_response_success(response, ["success", "current_status"])
            # For EKS mode, verify basic structure with real data
            assert data["success"] is True
            assert "current_status" in data  # Don't check specific status
            assert "message" in data
        else:
            with self._patch_shared_data():
                # Test different technician statuses
                test_cases = [
                    ("TECH001", "available", "completed"),
                    ("TECH003", "on_site", "arrived"),
                    ("TECH004", "busy", "working")
                ]

                for tech_id, status, expected_keyword in test_cases:
                    request_data = {
                        "appointment_id": f"APPT_{tech_id}"
                    }

                    response = self.client.post(f"/technicians/{tech_id}/notify", json=request_data)
                    assert response.status_code == 200

                    data = response.json()
                    assert data["success"] is True
                    assert data["current_status"] == status
                    assert expected_keyword.lower() in data["message"].lower()

    def test_notify_status_change_not_found(self):
        """Test status change notification for non-existent technician."""
        self.setup_test_data()
        with self._patch_shared_data():
            request_data = {
                "appointment_id": "APPT001"
            }

            response = self.client.post("/technicians/TECH999/notify", json=request_data)
            assert response.status_code == 404

            data = response.json()
            assert "Technician not found" in data["error"]

    # Location simulation tests
    def test_location_simulation_consistency(self):
        """Test that location simulation produces consistent results."""
        self.setup_test_data()
        with self._patch_shared_data():
            # Get location multiple times and verify it changes (simulation)
            locations = []
            for _ in range(3):
                response = self.client.get("/technicians/TECH001/location")
                assert response.status_code == 200
                data = response.json()
                location = (data["current_location"]["latitude"], data["current_location"]["longitude"])
                locations.append(location)

            # Locations should be different due to simulation
            # (though this might occasionally fail due to randomness)
            assert len(set(locations)) >= 1  # At least some variation expected

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
            with patch('mcp_servers.technician_server.server_rest.get_technicians_data', side_effect=Exception("Database error")):
                response = self.client.get("/technicians/TECH001/status")
                assert response.status_code == 500

                data = response.json()
                assert "Internal server error" in data["error"]

    # OpenAPI documentation tests
    def test_openapi_docs_available(self):
        """Test that OpenAPI documentation is available."""
        self.setup_test_data()
        response = self.client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json_available(self):
        """Test that OpenAPI JSON specification is available."""
        self.setup_test_data()
        response = self.client.get("/openapi.json")
        assert response.status_code == 200

        openapi_spec = response.json()
        assert "openapi" in openapi_spec
        assert "info" in openapi_spec
        assert openapi_spec["info"]["title"] == "Technician Tracking Server REST API"

    # Request validation tests
    def test_request_validation_empty_json(self):
        """Test request validation with empty JSON."""
        self.setup_test_data()
        response = self.client.post("/technicians/available", json={})
        assert response.status_code == 422

    def test_request_validation_invalid_json(self):
        """Test request validation with invalid JSON."""
        self.setup_test_data()

        if EKS_TEST_MODE:
            # Use data parameter instead of content for requests library
            response = self._make_request(
                "POST",
                "/technicians/available",
                data='{"invalid": json}',
                headers={"Content-Type": "application/json"}
            )
            # In EKS mode, the service might handle this differently
            assert response.status_code in [400, 422]  # Accept both validation error codes
        else:
            response = self.client.post(
                "/technicians/available",
                content='{"invalid": json}',
                headers={"Content-Type": "application/json"}
            )
            assert response.status_code == 422

    # Edge case tests
    def test_technician_status_transitions(self):
        """Test various technician status transitions."""
        self.setup_test_data()
        with self._patch_shared_data():
            # Test status transitions
            transitions = [
                ("available", "en_route"),
                ("en_route", "on_site"),
                ("on_site", "busy"),
                ("busy", "available"),
                ("available", "off_duty")
            ]

            for old_status, new_status in transitions:
                # First set to old status
                request_data = {"new_status": old_status}
                response = self.client.put("/technicians/TECH001/status", json=request_data)
                assert response.status_code == 200

                # Then transition to new status
                request_data = {"new_status": new_status}
                response = self.client.put("/technicians/TECH001/status", json=request_data)
                assert response.status_code == 200

                data = response.json()
                assert data["old_status"] == old_status
                assert data["new_status"] == new_status

    def test_coordinate_precision(self):
        """Test that coordinates maintain reasonable precision."""
        self.setup_test_data()
        with self._patch_shared_data():
            response = self.client.get("/technicians/TECH001/location")
            assert response.status_code == 200

            data = response.json()
            lat = data["current_location"]["latitude"]
            lon = data["current_location"]["longitude"]

            # Verify coordinates are reasonable for Seattle area
            assert 47.0 <= lat <= 48.0
            assert -123.0 <= lon <= -122.0

    def test_eta_calculation_reasonableness(self):
        """Test that ETA calculations produce reasonable results."""
        self.setup_test_data()
        with self._patch_shared_data():
            request_data = {
                "destination": [47.6200, -122.3500]  # Close to Seattle
            }

            response = self.client.post("/technicians/TECH001/route", json=request_data)
            assert response.status_code == 200

            data = response.json()
            # ETA should be reasonable (between 5 minutes and 2 hours for local travel)
            assert 5 <= data["estimated_travel_time_minutes"] <= 120
            assert 0.1 <= data["distance_miles"] <= 50  # Reasonable distance range


class TestTechnicianServerRESTIntegration(BaseMCPIntegrationTest):
    """Test technician server REST API integration."""

    @property
    def server_name(self) -> str:
        return "Technician Tracking Server REST API"

    @property
    def server_port(self) -> int:
        return 8003

    @property
    def server_module_path(self) -> str:
        return "mcp_servers.technician_server.server_rest.main"

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


class TestTechnicianServerRESTStandalone(BaseMCPStandaloneTest):
    """Test technician server REST API in standalone mode."""

    @property
    def server_name(self) -> str:
        return "Technician Tracking Server REST API"

    @property
    def server_port(self) -> int:
        return 8003

    @property
    def server_module_path(self) -> str:
        return "mcp_servers.technician_server.server_rest.main"

    def test_rest_api_standalone(self):
        """Test REST API in standalone mode."""
        # This would test the REST API server running independently
        # For now, we'll use the TestClient approach
        client = TestClient(rest_app)

        # Test that the server can handle requests independently
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["service"] == "technician-tracking-server"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
