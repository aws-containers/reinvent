"""
Unit tests for data models.

Tests all data model classes including validation, methods, and edge cases.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from shared.models import (
    Customer, Appointment, Technician, Claim,
    AppointmentStatus, TechnicianStatus, ClaimStatus, UrgencyLevel
)


class TestCustomer:
    """Test cases for Customer model."""

    def test_valid_customer_creation(self):
        """Test creating a valid customer."""
        customer = Customer(
            id="CUST001",
            name="John Doe",
            email="john.doe@example.com",
            phone="555-123-4567",
            address="123 Main St, Anytown, USA",
            policy_number="POL123456",
            covered_appliances=["refrigerator", "washing_machine", "dishwasher"]
        )

        assert customer.id == "CUST001"
        assert customer.name == "John Doe"
        assert customer.email == "john.doe@example.com"
        assert len(customer.covered_appliances) == 3
        assert isinstance(customer.created_at, datetime)

    def test_customer_validation_empty_id(self):
        """Test customer validation with empty ID."""
        with pytest.raises(ValueError, match="Customer ID cannot be empty"):
            Customer(
                id="",
                name="John Doe",
                email="john.doe@example.com",
                phone="555-123-4567",
                address="123 Main St",
                policy_number="POL123456",
                covered_appliances=["refrigerator"]
            )

    def test_customer_validation_short_name(self):
        """Test customer validation with short name."""
        with pytest.raises(ValueError, match="Customer name must be at least 2 characters"):
            Customer(
                id="CUST001",
                name="J",
                email="john.doe@example.com",
                phone="555-123-4567",
                address="123 Main St",
                policy_number="POL123456",
                covered_appliances=["refrigerator"]
            )

    def test_customer_validation_invalid_email(self):
        """Test customer validation with invalid email."""
        with pytest.raises(ValueError, match="Valid email address is required"):
            Customer(
                id="CUST001",
                name="John Doe",
                email="invalid-email",
                phone="555-123-4567",
                address="123 Main St",
                policy_number="POL123456",
                covered_appliances=["refrigerator"]
            )

    def test_customer_validation_short_phone(self):
        """Test customer validation with short phone number."""
        with pytest.raises(ValueError, match="Valid phone number is required"):
            Customer(
                id="CUST001",
                name="John Doe",
                email="john.doe@example.com",
                phone="123",
                address="123 Main St",
                policy_number="POL123456",
                covered_appliances=["refrigerator"]
            )

    def test_customer_validation_empty_policy(self):
        """Test customer validation with empty policy number."""
        with pytest.raises(ValueError, match="Policy number is required"):
            Customer(
                id="CUST001",
                name="John Doe",
                email="john.doe@example.com",
                phone="555-123-4567",
                address="123 Main St",
                policy_number="",
                covered_appliances=["refrigerator"]
            )

    def test_customer_validation_invalid_appliances(self):
        """Test customer validation with invalid appliances list."""
        with pytest.raises(ValueError, match="Covered appliances must be a list"):
            Customer(
                id="CUST001",
                name="John Doe",
                email="john.doe@example.com",
                phone="555-123-4567",
                address="123 Main St",
                policy_number="POL123456",
                covered_appliances="not a list"
            )

    def test_is_appliance_covered(self):
        """Test appliance coverage checking."""
        customer = Customer(
            id="CUST001",
            name="John Doe",
            email="john.doe@example.com",
            phone="555-123-4567",
            address="123 Main St",
            policy_number="POL123456",
            covered_appliances=["Refrigerator", "Washing Machine"]
        )

        assert customer.is_appliance_covered("refrigerator")
        assert customer.is_appliance_covered("REFRIGERATOR")
        assert customer.is_appliance_covered("washing machine")
        assert not customer.is_appliance_covered("dishwasher")


class TestAppointment:
    """Test cases for Appointment model."""

    def test_valid_appointment_creation(self):
        """Test creating a valid appointment."""
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

        assert appointment.id == "APPT001"
        assert appointment.customer_id == "CUST001"
        assert appointment.technician_id == "TECH001"
        assert appointment.status == AppointmentStatus.SCHEDULED
        assert appointment.estimated_duration == 120
        assert isinstance(appointment.created_at, datetime)

    def test_appointment_validation_empty_id(self):
        """Test appointment validation with empty ID."""
        future_time = datetime.now() + timedelta(days=1)
        with pytest.raises(ValueError, match="Appointment ID cannot be empty"):
            Appointment(
                id="",
                customer_id="CUST001",
                technician_id="TECH001",
                appliance_type="refrigerator",
                issue_description="Not cooling properly",
                scheduled_datetime=future_time,
                status=AppointmentStatus.SCHEDULED,
                estimated_duration=120
            )

    def test_appointment_validation_short_description(self):
        """Test appointment validation with short issue description."""
        future_time = datetime.now() + timedelta(days=1)
        with pytest.raises(ValueError, match="Issue description must be at least 5 characters"):
            Appointment(
                id="APPT001",
                customer_id="CUST001",
                technician_id="TECH001",
                appliance_type="refrigerator",
                issue_description="Bad",
                scheduled_datetime=future_time,
                status=AppointmentStatus.SCHEDULED,
                estimated_duration=120
            )

    def test_appointment_validation_negative_duration(self):
        """Test appointment validation with negative duration."""
        future_time = datetime.now() + timedelta(days=1)
        with pytest.raises(ValueError, match="Estimated duration must be positive"):
            Appointment(
                id="APPT001",
                customer_id="CUST001",
                technician_id="TECH001",
                appliance_type="refrigerator",
                issue_description="Not cooling properly",
                scheduled_datetime=future_time,
                status=AppointmentStatus.SCHEDULED,
                estimated_duration=-30
            )

    def test_appointment_validation_past_datetime(self):
        """Test appointment validation with past datetime."""
        past_time = datetime.now() - timedelta(days=1)
        with pytest.raises(ValueError, match="Active appointments must be scheduled for a future time"):
            Appointment(
                id="APPT001",
                customer_id="CUST001",
                technician_id="TECH001",
                appliance_type="refrigerator",
                issue_description="Not cooling properly",
                scheduled_datetime=past_time,
                status=AppointmentStatus.SCHEDULED,
                estimated_duration=120
            )

    def test_appointment_validation_invalid_status(self):
        """Test appointment validation with invalid status."""
        future_time = datetime.now() + timedelta(days=1)
        with pytest.raises(ValueError, match="Status must be an AppointmentStatus enum"):
            Appointment(
                id="APPT001",
                customer_id="CUST001",
                technician_id="TECH001",
                appliance_type="refrigerator",
                issue_description="Not cooling properly",
                scheduled_datetime=future_time,
                status="invalid_status",
                estimated_duration=120
            )

    def test_is_active(self):
        """Test appointment active status checking."""
        future_time = datetime.now() + timedelta(days=1)

        # Active statuses
        for status in [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED, AppointmentStatus.IN_PROGRESS]:
            appointment = Appointment(
                id="APPT001",
                customer_id="CUST001",
                technician_id="TECH001",
                appliance_type="refrigerator",
                issue_description="Not cooling properly",
                scheduled_datetime=future_time,
                status=status,
                estimated_duration=120
            )
            assert appointment.is_active()

        # Inactive statuses
        for status in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]:
            appointment = Appointment(
                id="APPT001",
                customer_id="CUST001",
                technician_id="TECH001",
                appliance_type="refrigerator",
                issue_description="Not cooling properly",
                scheduled_datetime=future_time,
                status=status,
                estimated_duration=120
            )
            assert not appointment.is_active()


class TestTechnician:
    """Test cases for Technician model."""

    def test_valid_technician_creation(self):
        """Test creating a valid technician."""
        technician = Technician(
            id="TECH001",
            name="Bob Smith",
            specialties=["refrigerator", "washing_machine"],
            current_location=(40.7128, -74.0060),  # NYC coordinates
            status=TechnicianStatus.AVAILABLE,
            phone="555-987-6543"
        )

        assert technician.id == "TECH001"
        assert technician.name == "Bob Smith"
        assert len(technician.specialties) == 2
        assert technician.current_location == (40.7128, -74.0060)
        assert technician.status == TechnicianStatus.AVAILABLE

    def test_technician_validation_empty_id(self):
        """Test technician validation with empty ID."""
        with pytest.raises(ValueError, match="Technician ID cannot be empty"):
            Technician(
                id="",
                name="Bob Smith",
                specialties=["refrigerator"],
                current_location=(40.7128, -74.0060),
                status=TechnicianStatus.AVAILABLE,
                phone="555-987-6543"
            )

    def test_technician_validation_short_name(self):
        """Test technician validation with short name."""
        with pytest.raises(ValueError, match="Technician name must be at least 2 characters"):
            Technician(
                id="TECH001",
                name="B",
                specialties=["refrigerator"],
                current_location=(40.7128, -74.0060),
                status=TechnicianStatus.AVAILABLE,
                phone="555-987-6543"
            )

    def test_technician_validation_empty_specialties(self):
        """Test technician validation with empty specialties."""
        with pytest.raises(ValueError, match="Technician must have at least one specialty"):
            Technician(
                id="TECH001",
                name="Bob Smith",
                specialties=[],
                current_location=(40.7128, -74.0060),
                status=TechnicianStatus.AVAILABLE,
                phone="555-987-6543"
            )

    def test_technician_validation_invalid_location(self):
        """Test technician validation with invalid location."""
        with pytest.raises(ValueError, match="Current location must be a tuple"):
            Technician(
                id="TECH001",
                name="Bob Smith",
                specialties=["refrigerator"],
                current_location="invalid",
                status=TechnicianStatus.AVAILABLE,
                phone="555-987-6543"
            )

    def test_technician_validation_invalid_latitude(self):
        """Test technician validation with invalid latitude."""
        with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
            Technician(
                id="TECH001",
                name="Bob Smith",
                specialties=["refrigerator"],
                current_location=(100.0, -74.0060),  # Invalid latitude
                status=TechnicianStatus.AVAILABLE,
                phone="555-987-6543"
            )

    def test_technician_validation_invalid_longitude(self):
        """Test technician validation with invalid longitude."""
        with pytest.raises(ValueError, match="Longitude must be between -180 and 180"):
            Technician(
                id="TECH001",
                name="Bob Smith",
                specialties=["refrigerator"],
                current_location=(40.7128, -200.0),  # Invalid longitude
                status=TechnicianStatus.AVAILABLE,
                phone="555-987-6543"
            )

    def test_technician_validation_invalid_status(self):
        """Test technician validation with invalid status."""
        with pytest.raises(ValueError, match="Status must be a TechnicianStatus enum"):
            Technician(
                id="TECH001",
                name="Bob Smith",
                specialties=["refrigerator"],
                current_location=(40.7128, -74.0060),
                status="invalid_status",
                phone="555-987-6543"
            )

    def test_technician_validation_short_phone(self):
        """Test technician validation with short phone number."""
        with pytest.raises(ValueError, match="Valid phone number is required"):
            Technician(
                id="TECH001",
                name="Bob Smith",
                specialties=["refrigerator"],
                current_location=(40.7128, -74.0060),
                status=TechnicianStatus.AVAILABLE,
                phone="123"
            )

    def test_is_available(self):
        """Test technician availability checking."""
        technician = Technician(
            id="TECH001",
            name="Bob Smith",
            specialties=["refrigerator"],
            current_location=(40.7128, -74.0060),
            status=TechnicianStatus.AVAILABLE,
            phone="555-987-6543"
        )

        assert technician.is_available()

        technician.status = TechnicianStatus.BUSY
        assert not technician.is_available()

    def test_can_handle_appliance(self):
        """Test appliance handling capability checking."""
        technician = Technician(
            id="TECH001",
            name="Bob Smith",
            specialties=["Refrigerator", "Washing Machine"],
            current_location=(40.7128, -74.0060),
            status=TechnicianStatus.AVAILABLE,
            phone="555-987-6543"
        )

        assert technician.can_handle_appliance("refrigerator")
        assert technician.can_handle_appliance("REFRIGERATOR")
        assert technician.can_handle_appliance("washing machine")
        assert not technician.can_handle_appliance("dishwasher")


class TestClaim:
    """Test cases for Claim model."""

    def test_valid_claim_creation(self):
        """Test creating a valid claim."""
        claim = Claim(
            id="CLAIM001",
            customer_id="CUST001",
            appliance_type="refrigerator",
            issue_description="Not cooling properly, food spoiling",
            status=ClaimStatus.SUBMITTED,
            urgency_level=UrgencyLevel.HIGH
        )

        assert claim.id == "CLAIM001"
        assert claim.customer_id == "CUST001"
        assert claim.appliance_type == "refrigerator"
        assert claim.status == ClaimStatus.SUBMITTED
        assert claim.urgency_level == UrgencyLevel.HIGH
        assert isinstance(claim.created_at, datetime)

    def test_claim_validation_empty_id(self):
        """Test claim validation with empty ID."""
        with pytest.raises(ValueError, match="Claim ID cannot be empty"):
            Claim(
                id="",
                customer_id="CUST001",
                appliance_type="refrigerator",
                issue_description="Not cooling properly",
                status=ClaimStatus.SUBMITTED,
                urgency_level=UrgencyLevel.HIGH
            )

    def test_claim_validation_short_description(self):
        """Test claim validation with short issue description."""
        with pytest.raises(ValueError, match="Issue description must be at least 5 characters"):
            Claim(
                id="CLAIM001",
                customer_id="CUST001",
                appliance_type="refrigerator",
                issue_description="Bad",
                status=ClaimStatus.SUBMITTED,
                urgency_level=UrgencyLevel.HIGH
            )

    def test_claim_validation_invalid_status(self):
        """Test claim validation with invalid status."""
        with pytest.raises(ValueError, match="Status must be a ClaimStatus enum"):
            Claim(
                id="CLAIM001",
                customer_id="CUST001",
                appliance_type="refrigerator",
                issue_description="Not cooling properly",
                status="invalid_status",
                urgency_level=UrgencyLevel.HIGH
            )

    def test_claim_validation_invalid_urgency(self):
        """Test claim validation with invalid urgency level."""
        with pytest.raises(ValueError, match="Urgency level must be a UrgencyLevel enum"):
            Claim(
                id="CLAIM001",
                customer_id="CUST001",
                appliance_type="refrigerator",
                issue_description="Not cooling properly",
                status=ClaimStatus.SUBMITTED,
                urgency_level="invalid_urgency"
            )

    def test_claim_validation_negative_cost(self):
        """Test claim validation with negative estimated cost."""
        with pytest.raises(ValueError, match="Estimated cost cannot be negative"):
            Claim(
                id="CLAIM001",
                customer_id="CUST001",
                appliance_type="refrigerator",
                issue_description="Not cooling properly",
                status=ClaimStatus.SUBMITTED,
                urgency_level=UrgencyLevel.HIGH,
                estimated_cost=-100.0
            )

    def test_is_active(self):
        """Test claim active status checking."""
        # Active statuses
        for status in [ClaimStatus.SUBMITTED, ClaimStatus.UNDER_REVIEW, ClaimStatus.APPROVED]:
            claim = Claim(
                id="CLAIM001",
                customer_id="CUST001",
                appliance_type="refrigerator",
                issue_description="Not cooling properly",
                status=status,
                urgency_level=UrgencyLevel.HIGH
            )
            assert claim.is_active()

        # Inactive statuses
        for status in [ClaimStatus.REJECTED, ClaimStatus.COMPLETED]:
            claim = Claim(
                id="CLAIM001",
                customer_id="CUST001",
                appliance_type="refrigerator",
                issue_description="Not cooling properly",
                status=status,
                urgency_level=UrgencyLevel.HIGH
            )
            assert not claim.is_active()

    def test_can_schedule_appointment(self):
        """Test appointment scheduling capability checking."""
        # Can schedule when approved and no appointment
        claim = Claim(
            id="CLAIM001",
            customer_id="CUST001",
            appliance_type="refrigerator",
            issue_description="Not cooling properly",
            status=ClaimStatus.APPROVED,
            urgency_level=UrgencyLevel.HIGH
        )
        assert claim.can_schedule_appointment()

        # Cannot schedule when not approved
        claim.status = ClaimStatus.SUBMITTED
        assert not claim.can_schedule_appointment()

        # Cannot schedule when already has appointment
        claim.status = ClaimStatus.APPROVED
        claim.appointment_id = "APPT001"
        assert not claim.can_schedule_appointment()


class TestEnums:
    """Test cases for enum classes."""

    def test_appointment_status_values(self):
        """Test AppointmentStatus enum values."""
        assert AppointmentStatus.SCHEDULED.value == "scheduled"
        assert AppointmentStatus.CONFIRMED.value == "confirmed"
        assert AppointmentStatus.IN_PROGRESS.value == "in_progress"
        assert AppointmentStatus.COMPLETED.value == "completed"
        assert AppointmentStatus.CANCELLED.value == "cancelled"

    def test_technician_status_values(self):
        """Test TechnicianStatus enum values."""
        assert TechnicianStatus.AVAILABLE.value == "available"
        assert TechnicianStatus.EN_ROUTE.value == "en_route"
        assert TechnicianStatus.ON_SITE.value == "on_site"
        assert TechnicianStatus.BUSY.value == "busy"
        assert TechnicianStatus.OFF_DUTY.value == "off_duty"

    def test_claim_status_values(self):
        """Test ClaimStatus enum values."""
        assert ClaimStatus.SUBMITTED.value == "submitted"
        assert ClaimStatus.UNDER_REVIEW.value == "under_review"
        assert ClaimStatus.APPROVED.value == "approved"
        assert ClaimStatus.REJECTED.value == "rejected"
        assert ClaimStatus.COMPLETED.value == "completed"

    def test_urgency_level_values(self):
        """Test UrgencyLevel enum values."""
        assert UrgencyLevel.LOW.value == "low"
        assert UrgencyLevel.MEDIUM.value == "medium"
        assert UrgencyLevel.HIGH.value == "high"
        assert UrgencyLevel.EMERGENCY.value == "emergency"
