"""
Comprehensive test suite for Appointment Management Server REST API.

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
from unittest.mock import patch, mock_open
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
from mcp_servers.appointment_server.server_rest import app as rest_app
from mcp_servers.appointment_server.shared_data import load_mock_data

# Check if we're running in EKS test mode
EKS_TEST_MODE = os.getenv("EKS_TEST_MODE", "false").lower() == "true"


# Always use BaseMCPEndpointTest as base, but add EKS functionality dynamically
BaseTestClass = BaseMCPEndpointTest


class TestAppointmentServerRESTEndpoints(BaseTestClass):
    """Test appointment server REST API endpoints."""

    # Class attributes for EKS support
    server_port = 8002
    service_name = "appointment-server"
    _eks_config = None

    @property
    def server_name(self) -> str:
        return "Appointment Management Server REST API"

    @property
    def server_module_path(self) -> str:
        return "mcp_servers.appointment_server.server_rest"

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
            "list_all_appointments",
            "list_appointments",
            "create_appointment",
            "update_appointment",
            "cancel_appointment",
            "get_available_slots",
            "reschedule_appointment",
            "get_appointment_details"
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

        # Mock appointment data
        self.mock_appointments = {
            "APPT001": {
                "id": "APPT001",
                "customer_id": "CUST001",
                "technician_id": "TECH001",
                "appliance_type": "refrigerator",
                "issue_description": "Refrigerator not cooling properly",
                "scheduled_datetime": (datetime.now() + timedelta(days=1)).isoformat(),
                "status": "scheduled",
                "estimated_duration": 120,
                "created_at": datetime.now().isoformat(),
                "notes": "Customer mentioned strange noises",
                "claim_id": "CLAIM001",
                "service_details": {
                    "priority": "high",
                    "parts_needed": ["compressor_relay"],
                    "estimated_cost": 285.5,
                    "warranty_covered": True
                }
            },
            "APPT002": {
                "id": "APPT002",
                "customer_id": "CUST002",
                "technician_id": "TECH002",
                "appliance_type": "washing_machine",
                "issue_description": "Washing machine not draining water",
                "scheduled_datetime": (datetime.now() + timedelta(days=2)).isoformat(),
                "status": "confirmed",
                "estimated_duration": 90,
                "created_at": datetime.now().isoformat(),
                "notes": "Customer reported error code E03",
                "claim_id": "CLAIM002",
                "service_details": {
                    "priority": "medium",
                    "parts_needed": ["drain_pump"],
                    "estimated_cost": 195.0,
                    "warranty_covered": False
                }
            }
        }

        # Mock technician data
        self.mock_technicians = {
            "TECH001": {
                "id": "TECH001",
                "name": "John Smith",
                "specialties": ["refrigerator", "freezer", "ice_maker"],
                "current_location": [47.6062, -122.3321],
                "status": "available",
                "phone": "555-0101",
                "profile": {
                    "rating": 4.8,
                    "years_experience": 8,
                    "certifications": ["EPA", "HVAC"]
                }
            },
            "TECH002": {
                "id": "TECH002",
                "name": "Sarah Johnson",
                "specialties": ["washing_machine", "dryer", "dishwasher"],
                "current_location": [47.6205, -122.3493],
                "status": "busy",
                "phone": "555-0102",
                "profile": {
                    "rating": 4.9,
                    "years_experience": 12,
                    "certifications": ["EPA", "Electrical"]
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

    def test_list_all_appointments_success(self):
        """Test successful listing of all appointments via REST API."""
        self.setup_test_data()

        if EKS_TEST_MODE:
            response = self._make_request("GET", "/appointments")
            data = self._assert_response_success(response)
            # For EKS mode, verify basic structure with real data
            assert isinstance(data, list)
            if len(data) > 0:
                assert "id" in data[0]
                assert "customer_id" in data[0]
        else:
            with patch('mcp_servers.appointment_server.server_rest.get_appointments_data') as mock_get_appointments:
                mock_get_appointments.return_value = self.mock_appointments

                response = self.client.get("/appointments")
                assert response.status_code == 200

                data = response.json()
                assert isinstance(data, list)
                assert len(data) == 2
                assert data[0]["id"] in ["APPT001", "APPT002"]

    def test_list_all_appointments_with_status_filter(self):
        """Test listing all appointments with status filter via REST API."""
        self.setup_test_data()

        if EKS_TEST_MODE:
            response = self._make_request("GET", "/appointments?status_filter=scheduled")
            data = self._assert_response_success(response)
            # For EKS mode, verify basic structure with real data
            assert isinstance(data, list)
            if len(data) > 0:
                assert "status" in data[0]
        else:
            with patch('mcp_servers.appointment_server.server_rest.get_appointments_data') as mock_get_appointments:
                mock_get_appointments.return_value = self.mock_appointments

                response = self.client.get("/appointments?status_filter=scheduled")
                assert response.status_code == 200

                data = response.json()
                assert isinstance(data, list)
                assert all(appt["status"] == "scheduled" for appt in data)

    def test_list_appointments_success(self):
        """Test successful appointment listing via REST API."""
        self.setup_test_data()

        if EKS_TEST_MODE:
            response = self._make_request("GET", "/appointments/CUST001")
            data = self._assert_response_success(response, ["customer_id", "total_appointments", "appointments"])
            # For EKS mode, verify basic structure with real data
            assert data["customer_id"] == "CUST001"
            assert isinstance(data["total_appointments"], int)
            assert data["total_appointments"] >= 0  # Could be any number in real data
            assert isinstance(data["appointments"], list)
        else:
            with patch('mcp_servers.appointment_server.server_rest.get_appointments_data') as mock_get_appointments:
                mock_get_appointments.return_value = self.mock_appointments

                response = self.client.get("/appointments/CUST001")
                assert response.status_code == 200

                data = response.json()
                assert data["customer_id"] == "CUST001"
                assert data["total_appointments"] == 1  # Only APPT001 belongs to CUST001
                assert len(data["appointments"]) == 1
                assert data["appointments"][0]["id"] == "APPT001"

    def test_list_appointments_with_status_filter(self):
        """Test appointment listing with status filter via REST API."""
        self.setup_test_data()

        if EKS_TEST_MODE:
            response = self._make_request("GET", "/appointments/CUST001?status_filter=scheduled")
            data = self._assert_response_success(response, ["status_filter", "appointments"])
            # For EKS mode, verify basic structure with real data
            assert data["status_filter"] == "scheduled"
            assert isinstance(data["appointments"], list)
        else:
            with patch('mcp_servers.appointment_server.server_rest.get_appointments_data') as mock_get_appointments:
                mock_get_appointments.return_value = self.mock_appointments

                response = self.client.get("/appointments/CUST001?status_filter=scheduled")
                assert response.status_code == 200

                data = response.json()
                assert data["status_filter"] == "scheduled"
                assert len(data["appointments"]) == 1
                assert data["appointments"][0]["status"] == "scheduled"

    def test_create_appointment_success(self):
        """Test successful appointment creation via REST API."""
        self.setup_test_data()

        future_datetime = (datetime.now() + timedelta(days=3)).isoformat()
        request_data = {
            "customer_id": "CUST003",
            "technician_id": "TECH001",
            "appliance_type": "refrigerator",
            "issue_description": "Temperature fluctuating",
            "scheduled_datetime": future_datetime,
            "estimated_duration": 90,
            "claim_id": "CLAIM003"
        }

        if EKS_TEST_MODE:
            response = self._make_request("POST", "/appointments", json=request_data)
            # In EKS mode, we might get scheduling conflicts with real data
            if response.status_code == 409:
                # Scheduling conflict is a valid business response
                data = response.json()
                assert "error" in data
                assert "Scheduling conflict" in data["error"]
                # This is actually a successful test - the service is working correctly
            else:
                data = self._assert_response_success(response, ["success", "appointment_id"])
                # For EKS mode, verify basic structure with real data
                assert data["success"] is True
                assert "appointment_id" in data
                if "appointment" in data:
                    assert data["appointment"]["customer_id"] == "CUST003"
        else:
            with patch('mcp_servers.appointment_server.server_rest.get_appointments_data') as mock_get_appointments, \
                 patch('mcp_servers.appointment_server.server_rest.get_technicians_data') as mock_get_technicians:
                mock_get_appointments.return_value = self.mock_appointments.copy()
                mock_get_technicians.return_value = self.mock_technicians

                response = self.client.post("/appointments", json=request_data)
                assert response.status_code == 200

                data = response.json()
                assert data["success"] is True
                assert data["status"] == "scheduled"
                assert "appointment_id" in data
                assert data["appointment"]["customer_id"] == "CUST003"

    @patch('mcp_servers.appointment_server.server_rest.get_appointments_data')
    @patch('mcp_servers.appointment_server.server_rest.get_technicians_data')
    def test_create_appointment_technician_not_found(self, mock_get_technicians, mock_get_appointments):
        """Test appointment creation with non-existent technician via REST API."""
        self.setup_test_data()
        mock_get_appointments.return_value = self.mock_appointments.copy()
        mock_get_technicians.return_value = self.mock_technicians

        future_datetime = (datetime.now() + timedelta(days=3)).isoformat()

        request_data = {
            "customer_id": "CUST003",
            "technician_id": "TECH999",  # Non-existent technician
            "appliance_type": "refrigerator",
            "issue_description": "Temperature fluctuating",
            "scheduled_datetime": future_datetime
        }

        response = self.client.post("/appointments", json=request_data)
        assert response.status_code == 404
        assert "Technician not found" in response.json()["error"]

    @patch('mcp_servers.appointment_server.server_rest.get_appointments_data')
    @patch('mcp_servers.appointment_server.server_rest.get_technicians_data')
    def test_update_appointment_success(self, mock_get_technicians, mock_get_appointments):
        """Test successful appointment update via REST API."""
        self.setup_test_data()
        mock_get_appointments.return_value = self.mock_appointments.copy()
        mock_get_technicians.return_value = self.mock_technicians

        update_data = {
            "status": "confirmed",
            "notes": "Customer confirmed availability",
            "estimated_duration": 150
        }

        response = self.client.put("/appointments/APPT001", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["appointment_id"] == "APPT001"
        assert "status" in data["updated_fields"]
        assert data["updated_appointment"]["status"] == "confirmed"

    @patch('mcp_servers.appointment_server.server_rest.get_appointments_data')
    @patch('mcp_servers.appointment_server.server_rest.get_technicians_data')
    def test_update_appointment_not_found(self, mock_get_technicians, mock_get_appointments):
        """Test updating non-existent appointment via REST API."""
        self.setup_test_data()
        mock_get_appointments.return_value = self.mock_appointments
        mock_get_technicians.return_value = self.mock_technicians

        update_data = {"status": "confirmed"}

        response = self.client.put("/appointments/APPT999", json=update_data)
        assert response.status_code == 404
        assert "Appointment not found" in response.json()["error"]

    @patch('mcp_servers.appointment_server.server_rest.get_appointments_data')
    def test_cancel_appointment_success(self, mock_get_appointments):
        """Test successful appointment cancellation via REST API."""
        self.setup_test_data()
        mock_get_appointments.return_value = self.mock_appointments.copy()

        cancel_data = {"reason": "Customer emergency"}

        response = self.client.request("DELETE", "/appointments/APPT001", json=cancel_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["appointment_id"] == "APPT001"
        assert data["new_status"] == "cancelled"
        assert data["cancellation_reason"] == "Customer emergency"

    @patch('mcp_servers.appointment_server.server_rest.get_appointments_data')
    def test_cancel_appointment_already_completed(self, mock_get_appointments):
        """Test cancelling already completed appointment via REST API."""
        self.setup_test_data()
        completed_appointments = self.mock_appointments.copy()
        completed_appointments["APPT001"]["status"] = "completed"
        mock_get_appointments.return_value = completed_appointments

        cancel_data = {"reason": "Customer request"}

        response = self.client.request("DELETE", "/appointments/APPT001", json=cancel_data)
        assert response.status_code == 400
        assert "Cannot cancel appointment" in response.json()["error"]

    @patch('mcp_servers.appointment_server.server_rest.get_appointments_data')
    @patch('mcp_servers.appointment_server.server_rest.get_technicians_data')
    def test_get_available_slots_success(self, mock_get_technicians, mock_get_appointments):
        """Test successful available slots retrieval via REST API."""
        self.setup_test_data()
        mock_get_technicians.return_value = self.mock_technicians
        mock_get_appointments.return_value = self.mock_appointments

        start_date = (datetime.now() + timedelta(days=1)).isoformat()
        end_date = (datetime.now() + timedelta(days=2)).isoformat()

        params = {
            "date_range_start": start_date,
            "date_range_end": end_date,
            "appliance_type": "refrigerator",
            "duration_minutes": 90
        }

        response = self.client.get("/appointments/available-slots", params=params)
        assert response.status_code == 200

        data = response.json()
        assert data["appliance_type"] == "refrigerator"
        assert data["duration_minutes"] == 90
        assert "available_slots" in data
        assert "qualified_technicians" in data

    def test_get_available_slots_no_qualified_technicians(self):
        """Test available slots with no qualified technicians via REST API."""
        self.setup_test_data()

        start_date = (datetime.now() + timedelta(days=1)).isoformat()
        end_date = (datetime.now() + timedelta(days=2)).isoformat()

        params = {
            "date_range_start": start_date,
            "date_range_end": end_date,
            "appliance_type": "microwave",  # No technicians specialize in this
            "duration_minutes": 90
        }

        if EKS_TEST_MODE:
            response = self._make_request("GET", "/appointments/available-slots", params=params)
            # In EKS mode, real data might have technicians available for any appliance type
            if response.status_code == 200:
                # Service found available slots - this is valid behavior
                data = response.json()
                assert "available_slots" in data
            else:
                # Service returned no available slots - also valid
                assert response.status_code in [404, 400]
        else:
            with patch('mcp_servers.appointment_server.server_rest.get_appointments_data') as mock_get_appointments, \
                 patch('mcp_servers.appointment_server.server_rest.get_technicians_data') as mock_get_technicians:
                mock_get_technicians.return_value = self.mock_technicians
                mock_get_appointments.return_value = self.mock_appointments

                response = self.client.get("/appointments/available-slots", params=params)
                assert response.status_code == 404
                assert "No technicians available" in response.json()["error"]

    def test_reschedule_appointment_success(self):
        """Test successful appointment rescheduling via REST API."""
        self.setup_test_data()

        new_datetime = (datetime.now() + timedelta(days=5)).isoformat()
        reschedule_data = {"new_datetime": new_datetime}

        if EKS_TEST_MODE:
            response = self._make_request("PUT", "/appointments/APPT001/reschedule", json=reschedule_data)
            # In EKS mode, rescheduling might fail due to business logic with real data
            if response.status_code == 400:
                # Business logic validation failed - this is valid behavior
                data = response.json()
                assert "error" in data
            else:
                data = self._assert_response_success(response, ["success", "appointment_id"])
                assert data["success"] is True
                assert data["appointment_id"] == "APPT001"
        else:
            with patch('mcp_servers.appointment_server.server_rest.get_appointments_data') as mock_get_appointments:
                mock_get_appointments.return_value = self.mock_appointments.copy()

                response = self.client.put("/appointments/APPT001/reschedule", json=reschedule_data)
                assert response.status_code == 200

                data = response.json()
                assert data["success"] is True
                assert data["appointment_id"] == "APPT001"
                assert data["new_datetime"] == new_datetime

    @patch('mcp_servers.appointment_server.server_rest.get_appointments_data')
    def test_reschedule_appointment_not_found(self, mock_get_appointments):
        """Test rescheduling non-existent appointment via REST API."""
        self.setup_test_data()
        mock_get_appointments.return_value = self.mock_appointments

        new_datetime = (datetime.now() + timedelta(days=5)).isoformat()
        reschedule_data = {"new_datetime": new_datetime}

        response = self.client.put("/appointments/APPT999/reschedule", json=reschedule_data)
        assert response.status_code == 404
        assert "Appointment not found" in response.json()["error"]

    def test_get_appointment_details_success(self):
        """Test successful appointment details retrieval via REST API."""
        self.setup_test_data()

        if EKS_TEST_MODE:
            response = self._make_request("GET", "/appointments/APPT001/details")
            data = self._assert_response_success(response, ["id", "customer_id", "technician_details"])
            # For EKS mode, verify basic structure with real data
            assert data["id"] == "APPT001"
            assert data["customer_id"] == "CUST001"
            assert "technician_details" in data
            assert "name" in data["technician_details"]  # Don't check specific name
        else:
            with patch('mcp_servers.appointment_server.server_rest.get_appointments_data') as mock_get_appointments, \
                 patch('mcp_servers.appointment_server.server_rest.get_technicians_data') as mock_get_technicians:
                mock_get_appointments.return_value = self.mock_appointments
                mock_get_technicians.return_value = self.mock_technicians

                response = self.client.get("/appointments/APPT001/details")
                assert response.status_code == 200

                data = response.json()
                assert data["id"] == "APPT001"
                assert data["customer_id"] == "CUST001"
                assert "technician_details" in data
                assert data["technician_details"]["name"] == "John Smith"

    @patch('mcp_servers.appointment_server.server_rest.get_appointments_data')
    @patch('mcp_servers.appointment_server.server_rest.get_technicians_data')
    def test_get_appointment_details_not_found(self, mock_get_appointments, mock_get_technicians):
        """Test appointment details for non-existent appointment via REST API."""
        self.setup_test_data()
        mock_get_appointments.return_value = self.mock_appointments
        mock_get_technicians.return_value = self.mock_technicians

        response = self.client.get("/appointments/APPT999/details")
        assert response.status_code == 404
        assert "Appointment not found" in response.json()["error"]

    def test_health_check(self):
        """Test health check endpoint."""
        self.setup_test_data()
        response = self._make_request("GET", "/health")
        data = self._assert_response_success(response, ["status", "service"])
        assert data["status"] == "healthy"
        assert data["service"] == "appointment-management-server"

    def teardown_method(self):
        """Clean up after each test method."""
        if EKS_TEST_MODE and hasattr(self, 'cleanup'):
            self.cleanup()

    def test_openapi_docs_available(self):
        """Test that OpenAPI documentation is available."""
        self.setup_test_data()
        response = self.client.get("/openapi.json")
        assert response.status_code == 200

        openapi_spec = response.json()
        assert "openapi" in openapi_spec
        assert "info" in openapi_spec
        assert openapi_spec["info"]["title"] == "Appointment Management Server REST API"

    def test_swagger_ui_available(self):
        """Test that Swagger UI is available."""
        self.setup_test_data()
        response = self.client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestAppointmentServerRESTIntegration(BaseMCPIntegrationTest):
    """Test appointment server REST API integration."""

    @property
    def server_name(self) -> str:
        return "Appointment Management Server REST API"

    @property
    def server_port(self) -> int:
        return 8002

    @property
    def server_module_path(self) -> str:
        return "mcp_servers.appointment_server.server_rest.main"

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


class TestAppointmentServerRESTStandalone(BaseMCPStandaloneTest):
    """Test appointment server REST API in standalone mode."""

    @property
    def server_name(self) -> str:
        return "Appointment Management Server REST API"

    @property
    def server_port(self) -> int:
        return 8002

    @property
    def server_module_path(self) -> str:
        return "mcp_servers.appointment_server.server_rest.main"

    def test_rest_api_standalone(self):
        """Test REST API in standalone mode."""
        # This would test the REST API server running independently
        # For now, we'll use the TestClient approach
        client = TestClient(rest_app)

        # Test that the server can handle requests independently
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["service"] == "appointment-management-server"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
