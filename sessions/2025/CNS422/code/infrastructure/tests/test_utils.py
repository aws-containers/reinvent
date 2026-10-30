"""
Unit tests for utility functions.

Tests all utility functions including data serialization, validation,
and common operations.
"""

import pytest
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open

from shared.utils import (
    generate_id, parse_datetime, validate_email, validate_phone,
    customer_to_dict, dict_to_customer,
    appointment_to_dict, dict_to_appointment,
    technician_to_dict, dict_to_technician,
    claim_to_dict, dict_to_claim,
    serialize_to_json, load_json_data, save_json_data,
    calculate_distance, estimate_travel_time,
    DateTimeEncoder
)
from shared.models import (
    Customer, Appointment, Technician, Claim,
    AppointmentStatus, TechnicianStatus, ClaimStatus, UrgencyLevel
)


class TestIdGeneration:
    """Test cases for ID generation."""

    def test_generate_id_without_prefix(self):
        """Test generating ID without prefix."""
        id1 = generate_id()
        id2 = generate_id()

        assert len(id1) == 12
        assert len(id2) == 12
        assert id1 != id2
        assert id1.isupper()
        assert id2.isupper()

    def test_generate_id_with_prefix(self):
        """Test generating ID with prefix."""
        id1 = generate_id("CUST")
        id2 = generate_id("APPT")

        assert id1.startswith("CUST")
        assert id2.startswith("APPT")
        assert len(id1) == 16  # 4 (prefix) + 12 (id)
        assert len(id2) == 16  # 4 (prefix) + 12 (id)
        assert id1 != id2


class TestDateTimeParsing:
    """Test cases for datetime parsing."""

    def test_parse_datetime_with_datetime_object(self):
        """Test parsing datetime object."""
        dt = datetime.now()
        result = parse_datetime(dt)
        assert result == dt

    def test_parse_datetime_with_iso_string(self):
        """Test parsing ISO format datetime string."""
        dt_str = "2024-01-15T10:30:00"
        result = parse_datetime(dt_str)
        expected = datetime(2024, 1, 15, 10, 30, 0)
        assert result == expected

    def test_parse_datetime_with_iso_string_z(self):
        """Test parsing ISO format datetime string with Z suffix."""
        dt_str = "2024-01-15T10:30:00Z"
        result = parse_datetime(dt_str)
        # Should handle Z as UTC
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_datetime_with_microseconds(self):
        """Test parsing datetime string with microseconds."""
        dt_str = "2024-01-15T10:30:00.123456"
        result = parse_datetime(dt_str)
        expected = datetime(2024, 1, 15, 10, 30, 0, 123456)
        assert result == expected

    def test_parse_datetime_with_common_formats(self):
        """Test parsing common datetime formats."""
        test_cases = [
            ("2024-01-15 10:30:00", datetime(2024, 1, 15, 10, 30, 0)),
            ("2024-01-15 10:30", datetime(2024, 1, 15, 10, 30, 0)),
            ("2024-01-15T10:30", datetime(2024, 1, 15, 10, 30, 0)),
        ]

        for dt_str, expected in test_cases:
            result = parse_datetime(dt_str)
            assert result == expected

    def test_parse_datetime_invalid_string(self):
        """Test parsing invalid datetime string."""
        with pytest.raises(ValueError, match="Unable to parse datetime string"):
            parse_datetime("invalid-datetime")

    def test_parse_datetime_invalid_type(self):
        """Test parsing invalid type."""
        with pytest.raises(ValueError, match="Expected string or datetime"):
            parse_datetime(123)


class TestValidation:
    """Test cases for validation functions."""

    def test_validate_email_valid(self):
        """Test email validation with valid emails."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@numbers.com"
        ]

        for email in valid_emails:
            assert validate_email(email), f"Should be valid: {email}"

    def test_validate_email_invalid(self):
        """Test email validation with invalid emails."""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user@.com",
            "user..name@example.com"
        ]

        for email in invalid_emails:
            assert not validate_email(email), f"Should be invalid: {email}"

    def test_validate_phone_valid(self):
        """Test phone validation with valid phone numbers."""
        valid_phones = [
            "555-123-4567",
            "(555) 123-4567",
            "5551234567",
            "+1-555-123-4567",
            "1234567890"
        ]

        for phone in valid_phones:
            assert validate_phone(phone), f"Should be valid: {phone}"

    def test_validate_phone_invalid(self):
        """Test phone validation with invalid phone numbers."""
        invalid_phones = [
            "123",
            "12345",
            "abc-def-ghij",
            "",
            "123456789012345678901"  # Too long
        ]

        for phone in invalid_phones:
            assert not validate_phone(phone), f"Should be invalid: {phone}"


class TestCustomerSerialization:
    """Test cases for Customer serialization."""

    def test_customer_to_dict(self):
        """Test converting Customer to dictionary."""
        customer = Customer(
            id="CUST001",
            name="John Doe",
            email="john.doe@example.com",
            phone="555-123-4567",
            address="123 Main St",
            policy_number="POL123456",
            covered_appliances=["refrigerator", "washing_machine"]
        )

        result = customer_to_dict(customer)

        assert result["id"] == "CUST001"
        assert result["name"] == "John Doe"
        assert result["email"] == "john.doe@example.com"
        assert result["covered_appliances"] == ["refrigerator", "washing_machine"]
        assert "created_at" in result

    def test_dict_to_customer(self):
        """Test converting dictionary to Customer."""
        data = {
            "id": "CUST001",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "555-123-4567",
            "address": "123 Main St",
            "policy_number": "POL123456",
            "covered_appliances": ["refrigerator", "washing_machine"],
            "created_at": "2024-01-15T10:30:00"
        }

        result = dict_to_customer(data)

        assert result.id == "CUST001"
        assert result.name == "John Doe"
        assert result.email == "john.doe@example.com"
        assert result.covered_appliances == ["refrigerator", "washing_machine"]
        assert isinstance(result.created_at, datetime)

    def test_customer_roundtrip(self):
        """Test Customer to dict and back conversion."""
        original = Customer(
            id="CUST001",
            name="John Doe",
            email="john.doe@example.com",
            phone="555-123-4567",
            address="123 Main St",
            policy_number="POL123456",
            covered_appliances=["refrigerator"]
        )

        dict_data = customer_to_dict(original)
        restored = dict_to_customer(dict_data)

        assert original.id == restored.id
        assert original.name == restored.name
        assert original.email == restored.email
        assert original.covered_appliances == restored.covered_appliances


class TestAppointmentSerialization:
    """Test cases for Appointment serialization."""

    def test_appointment_to_dict(self):
        """Test converting Appointment to dictionary."""
        future_time = datetime.now() + timedelta(days=1)
        appointment = Appointment(
            id="APPT001",
            customer_id="CUST001",
            technician_id="TECH001",
            appliance_type="refrigerator",
            issue_description="Not cooling properly",
            scheduled_datetime=future_time,
            status=AppointmentStatus.SCHEDULED,
            estimated_duration=120
        )

        result = appointment_to_dict(appointment)

        assert result["id"] == "APPT001"
        assert result["customer_id"] == "CUST001"
        assert result["status"] == "scheduled"
        assert result["estimated_duration"] == 120
        assert "scheduled_datetime" in result
        assert "created_at" in result

    def test_dict_to_appointment(self):
        """Test converting dictionary to Appointment."""
        future_time = datetime.now() + timedelta(days=1)
        data = {
            "id": "APPT001",
            "customer_id": "CUST001",
            "technician_id": "TECH001",
            "appliance_type": "refrigerator",
            "issue_description": "Not cooling properly",
            "scheduled_datetime": future_time.isoformat(),
            "status": "scheduled",
            "estimated_duration": 120,
            "created_at": datetime.now().isoformat()
        }

        result = dict_to_appointment(data)

        assert result.id == "APPT001"
        assert result.customer_id == "CUST001"
        assert result.status == AppointmentStatus.SCHEDULED
        assert result.estimated_duration == 120
        assert isinstance(result.scheduled_datetime, datetime)


class TestTechnicianSerialization:
    """Test cases for Technician serialization."""

    def test_technician_to_dict(self):
        """Test converting Technician to dictionary."""
        technician = Technician(
            id="TECH001",
            name="Bob Smith",
            specialties=["refrigerator", "washing_machine"],
            current_location=(40.7128, -74.0060),
            status=TechnicianStatus.AVAILABLE,
            phone="555-987-6543"
        )

        result = technician_to_dict(technician)

        assert result["id"] == "TECH001"
        assert result["name"] == "Bob Smith"
        assert result["specialties"] == ["refrigerator", "washing_machine"]
        assert result["current_location"] == [40.7128, -74.0060]
        assert result["status"] == "available"

    def test_dict_to_technician(self):
        """Test converting dictionary to Technician."""
        data = {
            "id": "TECH001",
            "name": "Bob Smith",
            "specialties": ["refrigerator", "washing_machine"],
            "current_location": [40.7128, -74.0060],
            "status": "available",
            "phone": "555-987-6543"
        }

        result = dict_to_technician(data)

        assert result.id == "TECH001"
        assert result.name == "Bob Smith"
        assert result.specialties == ["refrigerator", "washing_machine"]
        assert result.current_location == (40.7128, -74.0060)
        assert result.status == TechnicianStatus.AVAILABLE


class TestClaimSerialization:
    """Test cases for Claim serialization."""

    def test_claim_to_dict(self):
        """Test converting Claim to dictionary."""
        claim = Claim(
            id="CLAIM001",
            customer_id="CUST001",
            appliance_type="refrigerator",
            issue_description="Not cooling properly",
            status=ClaimStatus.SUBMITTED,
            urgency_level=UrgencyLevel.HIGH
        )

        result = claim_to_dict(claim)

        assert result["id"] == "CLAIM001"
        assert result["customer_id"] == "CUST001"
        assert result["status"] == "submitted"
        assert result["urgency_level"] == "high"
        assert "created_at" in result

    def test_dict_to_claim(self):
        """Test converting dictionary to Claim."""
        data = {
            "id": "CLAIM001",
            "customer_id": "CUST001",
            "appliance_type": "refrigerator",
            "issue_description": "Not cooling properly",
            "status": "submitted",
            "urgency_level": "high",
            "created_at": datetime.now().isoformat()
        }

        result = dict_to_claim(data)

        assert result.id == "CLAIM001"
        assert result.customer_id == "CUST001"
        assert result.status == ClaimStatus.SUBMITTED
        assert result.urgency_level == UrgencyLevel.HIGH


class TestJSONOperations:
    """Test cases for JSON operations."""

    def test_serialize_to_json_customer(self):
        """Test serializing Customer to JSON."""
        customer = Customer(
            id="CUST001",
            name="John Doe",
            email="john.doe@example.com",
            phone="555-123-4567",
            address="123 Main St",
            policy_number="POL123456",
            covered_appliances=["refrigerator"]
        )

        result = serialize_to_json(customer)

        assert isinstance(result, str)
        data = json.loads(result)
        assert data["id"] == "CUST001"
        assert data["name"] == "John Doe"

    def test_serialize_to_json_list(self):
        """Test serializing list to JSON."""
        data = [{"id": "1", "name": "Test"}]
        result = serialize_to_json(data)

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == data

    def test_datetime_encoder(self):
        """Test DateTimeEncoder with datetime objects."""
        encoder = DateTimeEncoder()
        dt = datetime(2024, 1, 15, 10, 30, 0)

        result = encoder.default(dt)
        assert result == "2024-01-15T10:30:00"

    def test_load_json_data_success(self):
        """Test loading JSON data from file successfully."""
        test_data = {"test": "data", "number": 123}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            result = load_json_data(temp_path)
            assert result == test_data
        finally:
            os.unlink(temp_path)

    def test_load_json_data_file_not_found(self):
        """Test loading JSON data from non-existent file."""
        with pytest.raises(FileNotFoundError, match="JSON file not found"):
            load_json_data("non_existent_file.json")

    def test_load_json_data_invalid_json(self):
        """Test loading invalid JSON data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_path = f.name

        try:
            with pytest.raises(json.JSONDecodeError, match="Invalid JSON"):
                load_json_data(temp_path)
        finally:
            os.unlink(temp_path)

    def test_save_json_data_success(self):
        """Test saving JSON data to file successfully."""
        test_data = {"test": "data", "number": 123}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            save_json_data(test_data, temp_path)

            # Verify the file was written correctly
            with open(temp_path, 'r') as f:
                loaded_data = json.load(f)
            assert loaded_data == test_data
        finally:
            os.unlink(temp_path)

    @patch("builtins.open", side_effect=IOError("Permission denied"))
    def test_save_json_data_io_error(self, mock_open):
        """Test saving JSON data with IO error."""
        test_data = {"test": "data"}

        with pytest.raises(IOError, match="Cannot write to file"):
            save_json_data(test_data, "test.json")


class TestDistanceCalculations:
    """Test cases for distance and travel time calculations."""

    def test_calculate_distance_same_point(self):
        """Test distance calculation for same point."""
        coord = (40.7128, -74.0060)
        distance = calculate_distance(coord, coord)
        assert distance == 0.0

    def test_calculate_distance_different_points(self):
        """Test distance calculation for different points."""
        coord1 = (40.7128, -74.0060)  # NYC
        coord2 = (34.0522, -118.2437)  # LA

        distance = calculate_distance(coord1, coord2)
        assert distance > 0
        assert isinstance(distance, float)

    def test_calculate_distance_symmetry(self):
        """Test distance calculation symmetry."""
        coord1 = (40.7128, -74.0060)
        coord2 = (34.0522, -118.2437)

        distance1 = calculate_distance(coord1, coord2)
        distance2 = calculate_distance(coord2, coord1)
        assert distance1 == distance2

    def test_estimate_travel_time_zero_distance(self):
        """Test travel time estimation for zero distance."""
        time_minutes = estimate_travel_time(0)
        assert time_minutes == 0

    def test_estimate_travel_time_positive_distance(self):
        """Test travel time estimation for positive distance."""
        time_minutes = estimate_travel_time(50, 50)  # 50km at 50km/h = 1 hour
        assert time_minutes == 60

    def test_estimate_travel_time_minimum(self):
        """Test travel time estimation minimum value."""
        time_minutes = estimate_travel_time(0.1, 100)  # Very short distance
        assert time_minutes >= 1  # Should be at least 1 minute

    def test_estimate_travel_time_custom_speed(self):
        """Test travel time estimation with custom speed."""
        time_minutes = estimate_travel_time(100, 100)  # 100km at 100km/h = 1 hour
        assert time_minutes == 60

        time_minutes = estimate_travel_time(100, 25)  # 100km at 25km/h = 4 hours
        assert time_minutes == 240
