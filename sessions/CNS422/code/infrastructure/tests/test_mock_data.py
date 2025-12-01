"""
Unit tests for mock data and data loader.

Tests the mock data files and data loader functionality to ensure
realistic and consistent demo scenarios.
"""

import pytest
from datetime import datetime
from pathlib import Path

from mock_data.data_loader import MockDataLoader, get_mock_data
from shared.models import (
    Customer, Appointment, Technician, Claim,
    AppointmentStatus, TechnicianStatus, ClaimStatus, UrgencyLevel
)


class TestMockDataLoader:
    """Test cases for MockDataLoader class."""

    @pytest.fixture
    def loader(self):
        """Create a MockDataLoader instance for testing."""
        return MockDataLoader()

    def test_load_customers(self, loader):
        """Test loading customer data."""
        customers = loader.load_customers()

        assert len(customers) > 0
        assert all(isinstance(c, Customer) for c in customers)

        # Check that all customers have required fields
        for customer in customers:
            assert customer.id
            assert customer.name
            assert customer.email
            assert customer.phone
            assert customer.policy_number
            assert len(customer.covered_appliances) > 0
            assert isinstance(customer.created_at, datetime)

    def test_load_technicians(self, loader):
        """Test loading technician data."""
        technicians = loader.load_technicians()

        assert len(technicians) > 0
        assert all(isinstance(t, Technician) for t in technicians)

        # Check that all technicians have required fields
        for technician in technicians:
            assert technician.id
            assert technician.name
            assert len(technician.specialties) > 0
            assert len(technician.current_location) == 2
            assert isinstance(technician.status, TechnicianStatus)
            assert technician.phone

    def test_load_appointments(self, loader):
        """Test loading appointment data."""
        appointments = loader.load_appointments()

        assert len(appointments) > 0
        assert all(isinstance(a, Appointment) for a in appointments)

        # Check that all appointments have required fields
        for appointment in appointments:
            assert appointment.id
            assert appointment.customer_id
            assert appointment.technician_id
            assert appointment.appliance_type
            assert appointment.issue_description
            assert isinstance(appointment.scheduled_datetime, datetime)
            assert isinstance(appointment.status, AppointmentStatus)
            assert appointment.estimated_duration > 0

    def test_load_claims(self, loader):
        """Test loading claim data."""
        claims = loader.load_claims()

        assert len(claims) > 0
        assert all(isinstance(c, Claim) for c in claims)

        # Check that all claims have required fields
        for claim in claims:
            assert claim.id
            assert claim.customer_id
            assert claim.appliance_type
            assert claim.issue_description
            assert isinstance(claim.status, ClaimStatus)
            assert isinstance(claim.urgency_level, UrgencyLevel)
            assert isinstance(claim.created_at, datetime)

    def test_customer_lookups(self, loader):
        """Test customer lookup methods."""
        customers = loader.load_customers()
        first_customer = customers[0]

        # Test lookup by ID
        found_customer = loader.get_customer_by_id(first_customer.id)
        assert found_customer is not None
        assert found_customer.id == first_customer.id

        # Test lookup by email
        found_customer = loader.get_customer_by_email(first_customer.email)
        assert found_customer is not None
        assert found_customer.email == first_customer.email

        # Test lookup by policy number
        found_customer = loader.get_customer_by_policy(first_customer.policy_number)
        assert found_customer is not None
        assert found_customer.policy_number == first_customer.policy_number

        # Test non-existent customer
        assert loader.get_customer_by_id("NONEXISTENT") is None

    def test_technician_lookups(self, loader):
        """Test technician lookup methods."""
        technicians = loader.load_technicians()
        first_tech = technicians[0]

        # Test lookup by ID
        found_tech = loader.get_technician_by_id(first_tech.id)
        assert found_tech is not None
        assert found_tech.id == first_tech.id

        # Test available technicians
        available = loader.get_available_technicians()
        assert all(t.is_available() for t in available)

        # Test technicians by specialty
        if first_tech.specialties:
            specialty = first_tech.specialties[0]
            specialists = loader.get_available_technicians(specialty)
            assert all(t.can_handle_appliance(specialty) for t in specialists)

    def test_appointment_lookups(self, loader):
        """Test appointment lookup methods."""
        appointments = loader.load_appointments()
        first_appt = appointments[0]

        # Test lookup by ID
        found_appt = loader.get_appointment_by_id(first_appt.id)
        assert found_appt is not None
        assert found_appt.id == first_appt.id

        # Test appointments by customer
        customer_appts = loader.get_appointments_by_customer(first_appt.customer_id)
        assert all(a.customer_id == first_appt.customer_id for a in customer_appts)

        # Test appointments by technician
        tech_appts = loader.get_appointments_by_technician(first_appt.technician_id)
        assert all(a.technician_id == first_appt.technician_id for a in tech_appts)

        # Test active appointments
        active_appts = loader.get_active_appointments()
        assert all(a.is_active() for a in active_appts)

    def test_claim_lookups(self, loader):
        """Test claim lookup methods."""
        claims = loader.load_claims()
        first_claim = claims[0]

        # Test lookup by ID
        found_claim = loader.get_claim_by_id(first_claim.id)
        assert found_claim is not None
        assert found_claim.id == first_claim.id

        # Test claims by customer
        customer_claims = loader.get_claims_by_customer(first_claim.customer_id)
        assert all(c.customer_id == first_claim.customer_id for c in customer_claims)

        # Test active claims
        active_claims = loader.get_active_claims()
        assert all(c.is_active() for c in active_claims)

        # Test claims by status
        for status in ClaimStatus:
            status_claims = loader.get_claims_by_status(status)
            assert all(c.status == status for c in status_claims)

        # Test emergency claims
        emergency_claims = loader.get_emergency_claims()
        assert all(c.urgency_level == UrgencyLevel.EMERGENCY for c in emergency_claims)

    def test_demo_scenarios(self, loader):
        """Test predefined demo scenarios."""
        scenarios = loader.get_demo_scenarios()

        assert len(scenarios) > 0

        for scenario_name, scenario_data in scenarios.items():
            assert "description" in scenario_data
            assert "customer" in scenario_data

            # Verify scenario data integrity
            customer = scenario_data["customer"]
            claim = scenario_data.get("claim")
            appointment = scenario_data.get("appointment")
            technician = scenario_data.get("technician")

            if customer:
                assert isinstance(customer, Customer)

            if claim:
                assert isinstance(claim, Claim)
                if customer:
                    assert claim.customer_id == customer.id

            if appointment:
                assert isinstance(appointment, Appointment)
                if customer:
                    assert appointment.customer_id == customer.id
                if claim:
                    assert appointment.claim_id == claim.id

            if technician:
                assert isinstance(technician, Technician)
                if appointment:
                    assert appointment.technician_id == technician.id

    def test_statistics(self, loader):
        """Test statistics generation."""
        stats = loader.get_statistics()

        # Check structure
        assert "customers" in stats
        assert "technicians" in stats
        assert "appointments" in stats
        assert "claims" in stats

        # Check customer stats
        customer_stats = stats["customers"]
        assert "total" in customer_stats
        assert customer_stats["total"] > 0

        # Check technician stats
        tech_stats = stats["technicians"]
        assert "total" in tech_stats
        assert "available" in tech_stats
        assert "specialties" in tech_stats
        assert tech_stats["total"] > 0

        # Check appointment stats
        appt_stats = stats["appointments"]
        assert "total" in appt_stats
        assert "by_status" in appt_stats
        assert "active" in appt_stats
        assert appt_stats["total"] > 0

        # Check claim stats
        claim_stats = stats["claims"]
        assert "total" in claim_stats
        assert "by_status" in claim_stats
        assert "by_urgency" in claim_stats
        assert "active" in claim_stats
        assert claim_stats["total"] > 0

    def test_caching(self, loader):
        """Test data caching functionality."""
        # Load data twice and verify it's cached
        customers1 = loader.load_customers()
        customers2 = loader.load_customers()
        assert customers1 is customers2  # Should be same object (cached)

        # Force reload and verify it's different
        customers3 = loader.load_customers(reload=True)
        assert customers1 is not customers3  # Should be different object
        assert len(customers1) == len(customers3)  # But same data


class TestMockDataIntegrity:
    """Test cases for mock data integrity and relationships."""

    @pytest.fixture
    def loader(self):
        """Create a MockDataLoader instance for testing."""
        return MockDataLoader()

    def test_customer_policy_coverage(self, loader):
        """Test that customer policies have realistic coverage."""
        customers = loader.load_customers()

        for customer in customers:
            # Check policy number format
            assert customer.policy_number.startswith("POL-")

            # Check covered appliances are realistic
            valid_appliances = {
                "refrigerator", "washing_machine", "dryer", "dishwasher",
                "oven", "microwave", "air_conditioner", "water_heater",
                "garbage_disposal", "ice_maker", "wine_cooler"
            }
            for appliance in customer.covered_appliances:
                assert appliance in valid_appliances

    def test_technician_specialties(self, loader):
        """Test that technician specialties are realistic."""
        technicians = loader.load_technicians()

        valid_specialties = {
            "refrigerator", "washing_machine", "dryer", "dishwasher",
            "oven", "stove", "cooktop", "range_hood", "microwave",
            "air_conditioner", "heat_pump", "ventilation",
            "water_heater", "garbage_disposal", "ice_maker",
            "wine_cooler", "freezer", "laundry_center"
        }

        for technician in technicians:
            for specialty in technician.specialties:
                assert specialty in valid_specialties

            # Check location coordinates are realistic (US coordinates)
            lat, lon = technician.current_location
            assert -180 <= lon <= -60  # US longitude range
            assert 20 <= lat <= 70     # US latitude range

    def test_appointment_claim_relationships(self, loader):
        """Test relationships between appointments and claims."""
        appointments = loader.load_appointments()
        claims = loader.load_claims()

        # Create lookup dictionaries
        claim_dict = {c.id: c for c in claims}

        for appointment in appointments:
            if appointment.claim_id:
                # Verify claim exists
                assert appointment.claim_id in claim_dict

                claim = claim_dict[appointment.claim_id]

                # Verify customer matches
                assert appointment.customer_id == claim.customer_id

                # Verify appliance type matches
                assert appointment.appliance_type == claim.appliance_type

    def test_customer_appointment_relationships(self, loader):
        """Test relationships between customers and appointments."""
        customers = loader.load_customers()
        appointments = loader.load_appointments()

        customer_dict = {c.id: c for c in customers}

        for appointment in appointments:
            # Verify customer exists
            assert appointment.customer_id in customer_dict

            customer = customer_dict[appointment.customer_id]

            # Verify appliance is covered by customer's policy
            assert appointment.appliance_type in customer.covered_appliances

    def test_technician_appointment_relationships(self, loader):
        """Test relationships between technicians and appointments."""
        technicians = loader.load_technicians()
        appointments = loader.load_appointments()

        tech_dict = {t.id: t for t in technicians}

        for appointment in appointments:
            # Verify technician exists
            assert appointment.technician_id in tech_dict

            technician = tech_dict[appointment.technician_id]

            # Verify technician can handle the appliance type
            assert technician.can_handle_appliance(appointment.appliance_type)

    def test_appointment_scheduling_realism(self, loader):
        """Test that appointment scheduling is realistic."""
        appointments = loader.load_appointments()

        for appointment in appointments:
            # Check that scheduled time is reasonable (business hours)
            scheduled_hour = appointment.scheduled_datetime.hour
            assert 7 <= scheduled_hour <= 18  # 7 AM to 6 PM

            # Check duration is reasonable (15 minutes to 4 hours)
            assert 15 <= appointment.estimated_duration <= 240

            # Check that creation time is before scheduled time
            if appointment.status in [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]:
                assert appointment.created_at <= appointment.scheduled_datetime


class TestGlobalMockData:
    """Test cases for global mock data instance."""

    def test_global_instance(self):
        """Test that global mock data instance works."""
        mock_data_instance = get_mock_data()
        assert isinstance(mock_data_instance, MockDataLoader)

        # Test that it returns the same instance
        mock_data_instance2 = get_mock_data()
        assert mock_data_instance is mock_data_instance2

    def test_global_instance_functionality(self):
        """Test that global instance has full functionality."""
        mock_data_instance = get_mock_data()

        customers = mock_data_instance.load_customers()
        assert len(customers) > 0

        stats = mock_data_instance.get_statistics()
        assert "customers" in stats
