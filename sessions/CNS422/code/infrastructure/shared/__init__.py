# Shared utilities and models package

from .models import (
    Customer, Appointment, Technician, Claim,
    AppointmentStatus, TechnicianStatus, ClaimStatus, UrgencyLevel,
    CustomerDict, AppointmentDict, TechnicianDict, ClaimDict
)

from .utils import (
    generate_id, parse_datetime, validate_email, validate_phone,
    customer_to_dict, dict_to_customer,
    appointment_to_dict, dict_to_appointment,
    technician_to_dict, dict_to_technician,
    claim_to_dict, dict_to_claim,
    serialize_to_json, load_json_data, save_json_data,
    calculate_distance, estimate_travel_time,
    DateTimeEncoder
)

__all__ = [
    # Models
    'Customer', 'Appointment', 'Technician', 'Claim',
    'AppointmentStatus', 'TechnicianStatus', 'ClaimStatus', 'UrgencyLevel',
    'CustomerDict', 'AppointmentDict', 'TechnicianDict', 'ClaimDict',

    # Utilities
    'generate_id', 'parse_datetime', 'validate_email', 'validate_phone',
    'customer_to_dict', 'dict_to_customer',
    'appointment_to_dict', 'dict_to_appointment',
    'technician_to_dict', 'dict_to_technician',
    'claim_to_dict', 'dict_to_claim',
    'serialize_to_json', 'load_json_data', 'save_json_data',
    'calculate_distance', 'estimate_travel_time',
    'DateTimeEncoder'
]
