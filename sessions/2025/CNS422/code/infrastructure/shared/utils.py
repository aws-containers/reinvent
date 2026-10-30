"""
Utility functions for data serialization and common operations.

This module provides helper functions for converting between data models
and dictionaries, JSON serialization, ID generation, and other common
operations used across the system.
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Type, TypeVar, Tuple
from uuid import uuid4
import re

from .models import (
    Customer, Appointment, Technician, Claim,
    AppointmentStatus, TechnicianStatus, ClaimStatus, UrgencyLevel,
    CustomerDict, AppointmentDict, TechnicianDict, ClaimDict
)

# Type variable for generic model operations
T = TypeVar('T', Customer, Appointment, Technician, Claim)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique ID with optional prefix.

    Args:
        prefix: Optional prefix for the ID (e.g., 'CUST', 'APPT', 'TECH', 'CLAIM')

    Returns:
        A unique string ID
    """
    unique_id = str(uuid4()).replace('-', '')[:12].upper()
    return f"{prefix}{unique_id}" if prefix else unique_id


def parse_datetime(dt_str: Union[str, datetime]) -> datetime:
    """
    Parse a datetime string or return datetime object as-is.

    Args:
        dt_str: ISO format datetime string or datetime object

    Returns:
        datetime object

    Raises:
        ValueError: If the string cannot be parsed
    """
    if isinstance(dt_str, datetime):
        return dt_str

    if isinstance(dt_str, str):
        try:
            # Handle ISO format with or without microseconds
            if '.' in dt_str:
                return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            else:
                return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except ValueError:
            # Try common datetime formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M',
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(dt_str, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse datetime string: {dt_str}")

    raise ValueError(f"Expected string or datetime, got {type(dt_str)}")


def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if email is valid, False otherwise
    """
    # Email validation pattern that allows common formats but prevents consecutive dots
    if '..' in email:
        return False
    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9._%+-]*[a-zA-Z0-9]@[a-zA-Z0-9][a-zA-Z0-9.-]*[a-zA-Z0-9]\.[a-zA-Z]{2,}$|^[a-zA-Z0-9]@[a-zA-Z0-9][a-zA-Z0-9.-]*[a-zA-Z0-9]\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.

    Args:
        phone: Phone number to validate

    Returns:
        True if phone is valid, False otherwise
    """
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    # Check if it's a valid length (10-15 digits)
    return 10 <= len(digits_only) <= 15


def customer_to_dict(customer: Customer) -> CustomerDict:
    """
    Convert Customer object to dictionary.

    Args:
        customer: Customer object to convert

    Returns:
        Dictionary representation of the customer
    """
    return {
        'id': customer.id,
        'name': customer.name,
        'email': customer.email,
        'phone': customer.phone,
        'address': customer.address,
        'policy_number': customer.policy_number,
        'covered_appliances': customer.covered_appliances,
        'created_at': customer.created_at.isoformat()
    }


def dict_to_customer(data: CustomerDict) -> Customer:
    """
    Convert dictionary to Customer object.

    Args:
        data: Dictionary containing customer data

    Returns:
        Customer object

    Raises:
        ValueError: If required fields are missing or invalid
    """
    return Customer(
        id=data['id'],
        name=data['name'],
        email=data['email'],
        phone=data['phone'],
        address=data['address'],
        policy_number=data['policy_number'],
        covered_appliances=data['covered_appliances'],
        created_at=parse_datetime(data.get('created_at', datetime.now()))
    )


def appointment_to_dict(appointment: Appointment) -> AppointmentDict:
    """
    Convert Appointment object to dictionary.

    Args:
        appointment: Appointment object to convert

    Returns:
        Dictionary representation of the appointment
    """
    return {
        'id': appointment.id,
        'customer_id': appointment.customer_id,
        'technician_id': appointment.technician_id,
        'appliance_type': appointment.appliance_type,
        'issue_description': appointment.issue_description,
        'scheduled_datetime': appointment.scheduled_datetime.isoformat(),
        'status': appointment.status.value,
        'estimated_duration': appointment.estimated_duration,
        'created_at': appointment.created_at.isoformat(),
        'notes': appointment.notes,
        'claim_id': appointment.claim_id
    }


def dict_to_appointment(data: AppointmentDict) -> Appointment:
    """
    Convert dictionary to Appointment object.

    Args:
        data: Dictionary containing appointment data

    Returns:
        Appointment object

    Raises:
        ValueError: If required fields are missing or invalid
    """
    return Appointment(
        id=data['id'],
        customer_id=data['customer_id'],
        technician_id=data['technician_id'],
        appliance_type=data['appliance_type'],
        issue_description=data['issue_description'],
        scheduled_datetime=parse_datetime(data['scheduled_datetime']),
        status=AppointmentStatus(data['status']),
        estimated_duration=data['estimated_duration'],
        created_at=parse_datetime(data.get('created_at', datetime.now())),
        notes=data.get('notes'),
        claim_id=data.get('claim_id')
    )


def technician_to_dict(technician: Technician) -> TechnicianDict:
    """
    Convert Technician object to dictionary.

    Args:
        technician: Technician object to convert

    Returns:
        Dictionary representation of the technician
    """
    return {
        'id': technician.id,
        'name': technician.name,
        'specialties': technician.specialties,
        'current_location': list(technician.current_location),
        'status': technician.status.value,
        'phone': technician.phone,
        'estimated_arrival': technician.estimated_arrival.isoformat() if technician.estimated_arrival else None,
        'current_appointment_id': technician.current_appointment_id
    }


def dict_to_technician(data: TechnicianDict) -> Technician:
    """
    Convert dictionary to Technician object.

    Args:
        data: Dictionary containing technician data

    Returns:
        Technician object

    Raises:
        ValueError: If required fields are missing or invalid
    """
    return Technician(
        id=data['id'],
        name=data['name'],
        specialties=data['specialties'],
        current_location=tuple(data['current_location']),
        status=TechnicianStatus(data['status']),
        phone=data['phone'],
        estimated_arrival=parse_datetime(data['estimated_arrival']) if data.get('estimated_arrival') else None,
        current_appointment_id=data.get('current_appointment_id')
    )


def claim_to_dict(claim: Claim) -> ClaimDict:
    """
    Convert Claim object to dictionary.

    Args:
        claim: Claim object to convert

    Returns:
        Dictionary representation of the claim
    """
    return {
        'id': claim.id,
        'customer_id': claim.customer_id,
        'appliance_type': claim.appliance_type,
        'issue_description': claim.issue_description,
        'status': claim.status.value,
        'urgency_level': claim.urgency_level.value,
        'created_at': claim.created_at.isoformat(),
        'approved_at': claim.approved_at.isoformat() if claim.approved_at else None,
        'completed_at': claim.completed_at.isoformat() if claim.completed_at else None,
        'appointment_id': claim.appointment_id,
        'estimated_cost': claim.estimated_cost,
        'notes': claim.notes
    }


def dict_to_claim(data: ClaimDict) -> Claim:
    """
    Convert dictionary to Claim object.

    Args:
        data: Dictionary containing claim data

    Returns:
        Claim object

    Raises:
        ValueError: If required fields are missing or invalid
    """
    return Claim(
        id=data['id'],
        customer_id=data['customer_id'],
        appliance_type=data['appliance_type'],
        issue_description=data['issue_description'],
        status=ClaimStatus(data['status']),
        urgency_level=UrgencyLevel(data['urgency_level']),
        created_at=parse_datetime(data.get('created_at', datetime.now())),
        approved_at=parse_datetime(data['approved_at']) if data.get('approved_at') else None,
        completed_at=parse_datetime(data['completed_at']) if data.get('completed_at') else None,
        appointment_id=data.get('appointment_id'),
        estimated_cost=data.get('estimated_cost'),
        notes=data.get('notes')
    )


def serialize_to_json(obj: Union[Customer, Appointment, Technician, Claim, List, Dict]) -> str:
    """
    Serialize object to JSON string with proper datetime handling.

    Args:
        obj: Object to serialize

    Returns:
        JSON string representation
    """
    if isinstance(obj, Customer):
        data = customer_to_dict(obj)
    elif isinstance(obj, Appointment):
        data = appointment_to_dict(obj)
    elif isinstance(obj, Technician):
        data = technician_to_dict(obj)
    elif isinstance(obj, Claim):
        data = claim_to_dict(obj)
    else:
        data = obj

    return json.dumps(data, cls=DateTimeEncoder, indent=2)


def load_json_data(file_path: str) -> Dict[str, Any]:
    """
    Load JSON data from file with error handling.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON data

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in file {file_path}: {e.msg}", e.doc, e.pos)


def save_json_data(data: Dict[str, Any], file_path: str) -> None:
    """
    Save data to JSON file with proper formatting.

    Args:
        data: Data to save
        file_path: Path to save file

    Raises:
        IOError: If file cannot be written
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=DateTimeEncoder, indent=2, ensure_ascii=False)
    except IOError as e:
        raise IOError(f"Cannot write to file {file_path}: {e}")


def calculate_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """
    Calculate approximate distance between two coordinates in kilometers.
    Uses simple Euclidean distance for demo purposes.

    Args:
        coord1: First coordinate (latitude, longitude)
        coord2: Second coordinate (latitude, longitude)

    Returns:
        Distance in kilometers (approximate)
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    # Simple approximation: 1 degree ≈ 111 km
    lat_diff = abs(lat2 - lat1) * 111
    lon_diff = abs(lon2 - lon1) * 111 * 0.7  # Adjust for longitude at mid-latitudes

    return (lat_diff ** 2 + lon_diff ** 2) ** 0.5


def estimate_travel_time(distance_km: float, speed_kmh: float = 50) -> int:
    """
    Estimate travel time in minutes based on distance and speed.

    Args:
        distance_km: Distance in kilometers
        speed_kmh: Average speed in km/h (default: 50 km/h)

    Returns:
        Estimated travel time in minutes
    """
    if distance_km <= 0:
        return 0

    hours = distance_km / speed_kmh
    return max(1, int(hours * 60))  # At least 1 minute
