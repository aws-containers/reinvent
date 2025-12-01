"""
Mock data loader for Insurance Agent ChatBot demo.

This module provides utilities to load and work with realistic mock data
for customers, technicians, appointments, and claims.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from shared.models import (
    Customer, Appointment, Technician, Claim,
    AppointmentStatus, TechnicianStatus, ClaimStatus, UrgencyLevel
)
from shared.utils import (
    dict_to_customer, dict_to_appointment,
    dict_to_technician, dict_to_claim,
    parse_datetime
)


class MockDataLoader:
    """Loads and manages mock data for demo scenarios."""

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the mock data loader.

        Args:
            data_dir: Directory containing mock data files.
                     Defaults to the mock_data directory.
        """
        if data_dir is None:
            data_dir = Path(__file__).parent
        self.data_dir = Path(data_dir)

        # Cache for loaded data
        self._customers_cache: Optional[List[Customer]] = None
        self._technicians_cache: Optional[List[Technician]] = None
        self._appointments_cache: Optional[List[Appointment]] = None
        self._claims_cache: Optional[List[Claim]] = None

    def _load_json_file(self, filename: str) -> Dict[str, Any]:
        """Load JSON data from file."""
        file_path = self.data_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Mock data file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_customers(self, reload: bool = False) -> List[Customer]:
        """
        Load customer data from JSON file.

        Args:
            reload: Force reload from file even if cached

        Returns:
            List of Customer objects
        """
        if self._customers_cache is None or reload:
            data = self._load_json_file('customers.json')
            self._customers_cache = [
                dict_to_customer(customer_data)
                for customer_data in data['customers']
            ]
        return self._customers_cache

    def load_technicians(self, reload: bool = False) -> List[Technician]:
        """
        Load technician data from JSON file.

        Args:
            reload: Force reload from file even if cached

        Returns:
            List of Technician objects
        """
        if self._technicians_cache is None or reload:
            data = self._load_json_file('technicians.json')
            self._technicians_cache = [
                dict_to_technician(tech_data)
                for tech_data in data['technicians']
            ]
        return self._technicians_cache

    def load_appointments(self, reload: bool = False) -> List[Appointment]:
        """
        Load appointment data from JSON file.

        Args:
            reload: Force reload from file even if cached

        Returns:
            List of Appointment objects
        """
        if self._appointments_cache is None or reload:
            data = self._load_json_file('appointments.json')
            self._appointments_cache = [
                dict_to_appointment(appt_data)
                for appt_data in data['appointments']
            ]
        return self._appointments_cache

    def load_claims(self, reload: bool = False) -> List[Claim]:
        """
        Load claim data from JSON file.

        Args:
            reload: Force reload from file even if cached

        Returns:
            List of Claim objects
        """
        if self._claims_cache is None or reload:
            data = self._load_json_file('claims.json')
            self._claims_cache = [
                dict_to_claim(claim_data)
                for claim_data in data['claims']
            ]
        return self._claims_cache

    def get_customer_by_id(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID."""
        customers = self.load_customers()
        return next((c for c in customers if c.id == customer_id), None)

    def get_customer_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email address."""
        customers = self.load_customers()
        return next((c for c in customers if c.email.lower() == email.lower()), None)

    def get_customer_by_policy(self, policy_number: str) -> Optional[Customer]:
        """Get customer by policy number."""
        customers = self.load_customers()
        return next((c for c in customers if c.policy_number == policy_number), None)

    def get_technician_by_id(self, technician_id: str) -> Optional[Technician]:
        """Get technician by ID."""
        technicians = self.load_technicians()
        return next((t for t in technicians if t.id == technician_id), None)

    def get_available_technicians(self, appliance_type: str = None) -> List[Technician]:
        """
        Get available technicians, optionally filtered by appliance specialty.

        Args:
            appliance_type: Filter by appliance type specialty

        Returns:
            List of available technicians
        """
        technicians = self.load_technicians()
        available = [t for t in technicians if t.is_available()]

        if appliance_type:
            available = [t for t in available if t.can_handle_appliance(appliance_type)]

        return available

    def get_appointment_by_id(self, appointment_id: str) -> Optional[Appointment]:
        """Get appointment by ID."""
        appointments = self.load_appointments()
        return next((a for a in appointments if a.id == appointment_id), None)

    def get_appointments_by_customer(self, customer_id: str) -> List[Appointment]:
        """Get all appointments for a customer."""
        appointments = self.load_appointments()
        return [a for a in appointments if a.customer_id == customer_id]

    def get_appointments_by_technician(self, technician_id: str) -> List[Appointment]:
        """Get all appointments for a technician."""
        appointments = self.load_appointments()
        return [a for a in appointments if a.technician_id == technician_id]

    def get_active_appointments(self) -> List[Appointment]:
        """Get all active (non-completed, non-cancelled) appointments."""
        appointments = self.load_appointments()
        return [a for a in appointments if a.is_active()]

    def get_claim_by_id(self, claim_id: str) -> Optional[Claim]:
        """Get claim by ID."""
        claims = self.load_claims()
        return next((c for c in claims if c.id == claim_id), None)

    def get_claims_by_customer(self, customer_id: str) -> List[Claim]:
        """Get all claims for a customer."""
        claims = self.load_claims()
        return [c for c in claims if c.customer_id == customer_id]

    def get_active_claims(self) -> List[Claim]:
        """Get all active (being processed) claims."""
        claims = self.load_claims()
        return [c for c in claims if c.is_active()]

    def get_claims_by_status(self, status: ClaimStatus) -> List[Claim]:
        """Get claims by status."""
        claims = self.load_claims()
        return [c for c in claims if c.status == status]

    def get_emergency_claims(self) -> List[Claim]:
        """Get all emergency priority claims."""
        claims = self.load_claims()
        return [c for c in claims if c.urgency_level == UrgencyLevel.EMERGENCY]

    def get_demo_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """
        Get predefined demo scenarios with related data.

        Returns:
            Dictionary of demo scenarios with customer, claim, and appointment data
        """
        scenarios = {
            "refrigerator_emergency": {
                "description": "Emergency refrigerator repair with food spoilage risk",
                "customer": self.get_customer_by_id("CUST001"),
                "claim": self.get_claim_by_id("CLAIM001"),
                "appointment": self.get_appointment_by_id("APPT001"),
                "technician": self.get_technician_by_id("TECH001")
            },
            "washing_machine_standard": {
                "description": "Standard washing machine drain issue",
                "customer": self.get_customer_by_id("CUST002"),
                "claim": self.get_claim_by_id("CLAIM002"),
                "appointment": self.get_appointment_by_id("APPT002"),
                "technician": self.get_technician_by_id("TECH002")
            },
            "microwave_safety": {
                "description": "Safety concern with sparking microwave",
                "customer": self.get_customer_by_id("CUST007"),
                "claim": self.get_claim_by_id("CLAIM007"),
                "appointment": self.get_appointment_by_id("APPT007"),
                "technician": self.get_technician_by_id("TECH004")
            },
            "completed_repair": {
                "description": "Successfully completed oven repair",
                "customer": self.get_customer_by_id("CUST004"),
                "claim": self.get_claim_by_id("CLAIM004"),
                "appointment": self.get_appointment_by_id("APPT004"),
                "technician": self.get_technician_by_id("TECH004")
            },
            "in_progress_service": {
                "description": "Technician currently on site for garbage disposal",
                "customer": self.get_customer_by_id("CUST005"),
                "claim": self.get_claim_by_id("CLAIM005"),
                "appointment": self.get_appointment_by_id("APPT005"),
                "technician": self.get_technician_by_id("TECH003")
            }
        }
        return scenarios

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the mock data."""
        customers = self.load_customers()
        technicians = self.load_technicians()
        appointments = self.load_appointments()
        claims = self.load_claims()

        return {
            "customers": {
                "total": len(customers),
                "coverage_types": list(set(c.policy_number.split('-')[0] for c in customers))
            },
            "technicians": {
                "total": len(technicians),
                "available": len([t for t in technicians if t.is_available()]),
                "specialties": list(set(spec for t in technicians for spec in t.specialties))
            },
            "appointments": {
                "total": len(appointments),
                "by_status": {
                    status.value: len([a for a in appointments if a.status == status])
                    for status in AppointmentStatus
                },
                "active": len([a for a in appointments if a.is_active()])
            },
            "claims": {
                "total": len(claims),
                "by_status": {
                    status.value: len([c for c in claims if c.status == status])
                    for status in ClaimStatus
                },
                "by_urgency": {
                    level.value: len([c for c in claims if c.urgency_level == level])
                    for level in UrgencyLevel
                },
                "active": len([c for c in claims if c.is_active()])
            }
        }


# Global instance for easy access
mock_data = MockDataLoader()


def get_mock_data() -> MockDataLoader:
    """Get the global mock data loader instance."""
    return mock_data
