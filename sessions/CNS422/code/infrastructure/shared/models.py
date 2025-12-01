"""
Core data models for the Insurance Agent ChatBot system.

This module contains all the shared data models used across the MCP servers
and agent components, including proper validation and serialization support.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Tuple, Dict, Any
import json
from uuid import uuid4


class AppointmentStatus(Enum):
    """Status values for appointments."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TechnicianStatus(Enum):
    """Status values for technicians."""
    AVAILABLE = "available"
    EN_ROUTE = "en_route"
    ON_SITE = "on_site"
    BUSY = "busy"
    OFF_DUTY = "off_duty"


class ClaimStatus(Enum):
    """Status values for insurance claims."""
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class UrgencyLevel(Enum):
    """Urgency levels for service requests."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


@dataclass
class Customer:
    """Customer profile and policy information."""
    id: str
    name: str
    email: str
    phone: str
    address: str
    policy_number: str
    covered_appliances: List[str]
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate customer data after initialization."""
        if not self.id:
            raise ValueError("Customer ID cannot be empty")
        if not self.name or len(self.name.strip()) < 2:
            raise ValueError("Customer name must be at least 2 characters")
        if not self.email or "@" not in self.email:
            raise ValueError("Valid email address is required")
        if not self.phone or len(self.phone.strip()) < 10:
            raise ValueError("Valid phone number is required")
        if not self.policy_number:
            raise ValueError("Policy number is required")
        if not isinstance(self.covered_appliances, list):
            raise ValueError("Covered appliances must be a list")

    def is_appliance_covered(self, appliance_type: str) -> bool:
        """Check if an appliance type is covered under the policy."""
        return appliance_type.lower() in [app.lower() for app in self.covered_appliances]


@dataclass
class Appointment:
    """Appointment information for technician visits."""
    id: str
    customer_id: str
    technician_id: str
    appliance_type: str
    issue_description: str
    scheduled_datetime: datetime
    status: AppointmentStatus
    estimated_duration: int  # in minutes
    created_at: datetime = field(default_factory=datetime.now)
    notes: Optional[str] = None
    claim_id: Optional[str] = None

    def __post_init__(self):
        """Validate appointment data after initialization."""
        if not self.id:
            raise ValueError("Appointment ID cannot be empty")
        if not self.customer_id:
            raise ValueError("Customer ID is required")
        if not self.technician_id:
            raise ValueError("Technician ID is required")
        if not self.appliance_type:
            raise ValueError("Appliance type is required")
        if not self.issue_description or len(self.issue_description.strip()) < 5:
            raise ValueError("Issue description must be at least 5 characters")
        if self.estimated_duration <= 0:
            raise ValueError("Estimated duration must be positive")
        if not isinstance(self.status, AppointmentStatus):
            raise ValueError("Status must be an AppointmentStatus enum")
        # Only require future scheduling for active appointments
        if self.status in [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED] and self.scheduled_datetime <= datetime.now():
            raise ValueError("Active appointments must be scheduled for a future time")

    def is_active(self) -> bool:
        """Check if the appointment is currently active."""
        return self.status in [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED, AppointmentStatus.IN_PROGRESS]


@dataclass
class Technician:
    """Technician profile and current status information."""
    id: str
    name: str
    specialties: List[str]
    current_location: Tuple[float, float]  # (latitude, longitude)
    status: TechnicianStatus
    phone: str
    estimated_arrival: Optional[datetime] = None
    current_appointment_id: Optional[str] = None

    def __post_init__(self):
        """Validate technician data after initialization."""
        if not self.id:
            raise ValueError("Technician ID cannot be empty")
        if not self.name or len(self.name.strip()) < 2:
            raise ValueError("Technician name must be at least 2 characters")
        if not isinstance(self.specialties, list) or not self.specialties:
            raise ValueError("Technician must have at least one specialty")
        if not isinstance(self.current_location, tuple) or len(self.current_location) != 2:
            raise ValueError("Current location must be a tuple of (latitude, longitude)")
        if not (-90 <= self.current_location[0] <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if not (-180 <= self.current_location[1] <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        if not isinstance(self.status, TechnicianStatus):
            raise ValueError("Status must be a TechnicianStatus enum")
        if not self.phone or len(self.phone.strip()) < 10:
            raise ValueError("Valid phone number is required")

    def is_available(self) -> bool:
        """Check if the technician is available for new appointments."""
        return self.status == TechnicianStatus.AVAILABLE

    def can_handle_appliance(self, appliance_type: str) -> bool:
        """Check if the technician can handle a specific appliance type."""
        return appliance_type.lower() in [spec.lower() for spec in self.specialties]


@dataclass
class Claim:
    """Insurance claim information."""
    id: str
    customer_id: str
    appliance_type: str
    issue_description: str
    status: ClaimStatus
    urgency_level: UrgencyLevel
    created_at: datetime = field(default_factory=datetime.now)
    approved_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    appointment_id: Optional[str] = None
    estimated_cost: Optional[float] = None
    notes: Optional[str] = None

    def __post_init__(self):
        """Validate claim data after initialization."""
        if not self.id:
            raise ValueError("Claim ID cannot be empty")
        if not self.customer_id:
            raise ValueError("Customer ID is required")
        if not self.appliance_type:
            raise ValueError("Appliance type is required")
        if not self.issue_description or len(self.issue_description.strip()) < 5:
            raise ValueError("Issue description must be at least 5 characters")
        if not isinstance(self.status, ClaimStatus):
            raise ValueError("Status must be a ClaimStatus enum")
        if not isinstance(self.urgency_level, UrgencyLevel):
            raise ValueError("Urgency level must be a UrgencyLevel enum")
        if self.estimated_cost is not None and self.estimated_cost < 0:
            raise ValueError("Estimated cost cannot be negative")

    def is_active(self) -> bool:
        """Check if the claim is still being processed."""
        return self.status in [ClaimStatus.SUBMITTED, ClaimStatus.UNDER_REVIEW, ClaimStatus.APPROVED]

    def can_schedule_appointment(self) -> bool:
        """Check if an appointment can be scheduled for this claim."""
        return self.status == ClaimStatus.APPROVED and not self.appointment_id


# Type aliases for better code readability
CustomerDict = Dict[str, Any]
AppointmentDict = Dict[str, Any]
TechnicianDict = Dict[str, Any]
ClaimDict = Dict[str, Any]
