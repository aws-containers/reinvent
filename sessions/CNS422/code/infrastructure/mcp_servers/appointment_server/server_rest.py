"""
FastAPI REST interface for Appointment Management Server

This module provides HTTP REST endpoints that mirror the MCP tool functionality
for appointment scheduling, updates, cancellations, and availability checking.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import uuid4

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
import uvicorn

from shared.models import Appointment, AppointmentStatus, Technician, TechnicianStatus
from shared.utils import generate_id, parse_datetime


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Key configuration from environment variable
# If API_KEY environment variable is not set, authentication is disabled
API_KEY = os.getenv("API_KEY")


def verify_api_key(api_key: str = None):
    """Verify the API key from query parameter

    If API_KEY environment variable is not set, authentication is disabled.

    Args:
        api_key: API key provided in query parameter

    Raises:
        HTTPException: If API key is required but missing or invalid
    """
    # If API_KEY is not configured, skip authentication
    if API_KEY is None:
        return

    # If API_KEY is configured, require and validate it
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required. Provide api_key query parameter."
        )
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for application startup and shutdown"""
    # Startup
    load_mock_data()
    yield
    # Shutdown (if needed)


# FastAPI app instance
app = FastAPI(
    title="Appointment Management Server REST API",
    description="REST API for appointment scheduling, updates, cancellations, and availability checking. Requires api_key query parameter for authentication.",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Import shared data storage
from .shared_data import load_mock_data, get_appointments_data, get_technicians_data


# Pydantic models for request/response validation
class AppointmentResponse(BaseModel):
    """Response model for appointment information"""
    id: str
    customer_id: str
    technician_id: str
    appliance_type: str
    issue_description: str
    scheduled_datetime: str
    status: str
    estimated_duration: int
    created_at: str
    notes: Optional[str] = None
    claim_id: Optional[str] = None
    service_details: Optional[Dict[str, Any]] = None


class ListAppointmentsResponse(BaseModel):
    """Response model for listing appointments"""
    customer_id: str
    total_appointments: int
    status_filter: str
    appointments: List[AppointmentResponse]


class CreateAppointmentRequest(BaseModel):
    """Request model for creating a new appointment"""
    customer_id: str = Field(..., description="Customer ID")
    technician_id: str = Field(..., description="Technician ID")
    appliance_type: str = Field(..., min_length=1, description="Type of appliance")
    issue_description: str = Field(..., min_length=5, description="Description of the issue")
    scheduled_datetime: str = Field(..., description="Scheduled date and time (ISO format)")
    estimated_duration: int = Field(90, ge=30, le=480, description="Estimated duration in minutes")
    claim_id: Optional[str] = Field(None, description="Associated claim ID")

    @field_validator('scheduled_datetime')
    @classmethod
    def validate_datetime(cls, v):
        try:
            dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            if dt <= datetime.now():
                raise ValueError('Scheduled datetime must be in the future')
            return v
        except ValueError as e:
            if 'future' in str(e):
                raise e
            raise ValueError('Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)')


class CreateAppointmentResponse(BaseModel):
    """Response model for appointment creation"""
    success: bool
    appointment_id: str
    status: str
    message: str
    appointment: AppointmentResponse


class UpdateAppointmentRequest(BaseModel):
    """Request model for updating an appointment"""
    status: Optional[str] = Field(None, description="New status")
    scheduled_datetime: Optional[str] = Field(None, description="New scheduled datetime")
    estimated_duration: Optional[int] = Field(None, ge=30, le=480, description="New estimated duration")
    notes: Optional[str] = Field(None, description="Additional notes")
    issue_description: Optional[str] = Field(None, min_length=5, description="Updated issue description")
    technician_id: Optional[str] = Field(None, description="New technician ID")
    service_details: Optional[Dict[str, Any]] = Field(None, description="Service details updates")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ['scheduled', 'confirmed', 'in_progress', 'completed', 'cancelled']
            if v.lower() not in valid_statuses:
                raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v.lower() if v else v

    @field_validator('scheduled_datetime')
    @classmethod
    def validate_datetime(cls, v):
        if v is not None:
            try:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
                return v
            except ValueError:
                raise ValueError('Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)')
        return v


class UpdateAppointmentResponse(BaseModel):
    """Response model for appointment update"""
    success: bool
    appointment_id: str
    updated_fields: List[str]
    old_data: Dict[str, Any]
    updated_appointment: AppointmentResponse


class CancelAppointmentRequest(BaseModel):
    """Request model for cancelling an appointment"""
    reason: str = Field("Customer request", description="Reason for cancellation")


class CancelAppointmentResponse(BaseModel):
    """Response model for appointment cancellation"""
    success: bool
    appointment_id: str
    old_status: str
    new_status: str
    cancellation_reason: str
    appointment: AppointmentResponse


class AvailableSlotsRequest(BaseModel):
    """Request model for getting available slots"""
    date_range_start: str = Field(..., description="Start date for availability search")
    date_range_end: str = Field(..., description="End date for availability search")
    appliance_type: str = Field(..., min_length=1, description="Type of appliance")
    duration_minutes: int = Field(90, ge=30, le=480, description="Required duration in minutes")

    @field_validator('date_range_start', 'date_range_end')
    @classmethod
    def validate_datetime(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError('Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)')


class AvailableSlot(BaseModel):
    """Model for an available time slot"""
    datetime: str
    technician_id: str
    technician_name: str
    duration_minutes: int
    specialties: List[str]
    rating: float


class AvailableSlotsResponse(BaseModel):
    """Response model for available slots"""
    appliance_type: str
    date_range: Dict[str, str]
    duration_minutes: int
    total_slots: int
    qualified_technicians: int
    available_slots: List[AvailableSlot]


class RescheduleAppointmentRequest(BaseModel):
    """Request model for rescheduling an appointment"""
    new_datetime: str = Field(..., description="New scheduled datetime")

    @field_validator('new_datetime')
    @classmethod
    def validate_datetime(cls, v):
        try:
            dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            if dt <= datetime.now():
                raise ValueError('New datetime must be in the future')
            return v
        except ValueError as e:
            if 'future' in str(e):
                raise e
            raise ValueError('Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)')


class RescheduleAppointmentResponse(BaseModel):
    """Response model for appointment rescheduling"""
    success: bool
    appointment_id: str
    old_datetime: str
    new_datetime: str
    message: str
    appointment: AppointmentResponse


class AppointmentDetailsResponse(BaseModel):
    """Response model for detailed appointment information"""
    id: str
    customer_id: str
    technician_id: str
    appliance_type: str
    issue_description: str
    scheduled_datetime: str
    status: str
    estimated_duration: int
    created_at: str
    notes: Optional[str] = None
    claim_id: Optional[str] = None
    service_details: Optional[Dict[str, Any]] = None
    technician_details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str
    detail: Optional[str] = None


# Note: get_appointments_data and get_technicians_data are imported from shared_data


# Startup event is now handled by lifespan context manager


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "appointment-management-server"}


@app.get("/appointments/available-slots", response_model=AvailableSlotsResponse, operation_id="get_available_slots")
async def get_available_slots(date_range_start: str, date_range_end: str, appliance_type: str, api_key: str = None, duration_minutes: int = 90):
    """Get available time slots for scheduling appointments

    Args:
        date_range_start: Start date for availability search in ISO format (e.g., "2025-09-05T00:00:00")
        date_range_end: End date for availability search in ISO format (e.g., "2025-09-06T00:00:00")
        appliance_type: Type of appliance needing service (e.g., "refrigerator", "washing_machine", "dryer", "dishwasher")
        api_key: API key for authentication (optional, required only if API_KEY env var is set)
        duration_minutes: Required duration in minutes (default: 90, range: 30-480)
    """
    verify_api_key(api_key)
    try:
        # Parse date range
        start_dt = datetime.fromisoformat(date_range_start.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(date_range_end.replace('Z', '+00:00'))

        # Find technicians who can handle this appliance type
        technicians_data = get_technicians_data()
        qualified_technicians = [
            tech for tech in technicians_data.values()
            if appliance_type.lower() in [spec.lower() for spec in tech["specialties"]]
            and tech["status"] in ["available", "busy"]  # Include busy techs for future slots
        ]

        if not qualified_technicians:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No technicians available for appliance type: {appliance_type}"
            )

        # Generate available slots
        available_slots = []
        current_dt = start_dt

        while current_dt < end_dt:
            # Check each qualified technician for this time slot
            for tech in qualified_technicians:
                if _is_slot_available(tech["id"], current_dt, duration_minutes):
                    slot = AvailableSlot(
                        datetime=current_dt.isoformat(),
                        technician_id=tech["id"],
                        technician_name=tech["name"],
                        duration_minutes=duration_minutes,
                        specialties=tech["specialties"],
                        rating=tech.get("profile", {}).get("rating", 0.0)
                    )
                    available_slots.append(slot)

            # Move to next hour
            current_dt += timedelta(hours=1)

        # Sort by datetime and rating
        available_slots.sort(key=lambda x: (x.datetime, -x.rating))

        return AvailableSlotsResponse(
            appliance_type=appliance_type,
            date_range={
                "start": date_range_start,
                "end": date_range_end
            },
            duration_minutes=duration_minutes,
            total_slots=len(available_slots),
            qualified_technicians=len(qualified_technicians),
            available_slots=available_slots[:20]  # Limit to first 20 slots
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid datetime format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting available slots: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/appointments", response_model=List[AppointmentResponse], operation_id="list_all_appointments")
async def list_all_appointments(api_key: str = None, status_filter: str = "all"):
    """List all appointments in the system with optional status filtering

    Args:
        api_key: API key for authentication (optional, required only if API_KEY env var is set)
        status_filter: Filter appointments by status. Valid values: "all", "active", "completed", "scheduled", "confirmed", "in_progress", "cancelled"
    """
    verify_api_key(api_key)
    try:
        # Get all appointments
        appointments_data = get_appointments_data()
        all_appointments = list(appointments_data.values())

        # Apply status filter
        if status_filter != "all":
            if status_filter == "active":
                all_appointments = [
                    appointment for appointment in all_appointments
                    if appointment["status"] in ["scheduled", "confirmed", "in_progress"]
                ]
            elif status_filter == "completed":
                all_appointments = [
                    appointment for appointment in all_appointments
                    if appointment["status"] in ["completed", "cancelled"]
                ]
            else:
                all_appointments = [
                    appointment for appointment in all_appointments
                    if appointment["status"] == status_filter
                ]

        # Sort by scheduled datetime (newest first)
        all_appointments.sort(key=lambda x: x["scheduled_datetime"], reverse=True)

        # Convert to response models
        appointment_responses = [
            AppointmentResponse(**appointment) for appointment in all_appointments
        ]

        return appointment_responses

    except Exception as e:
        logger.error(f"Error listing all appointments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/appointments/{customer_id}", response_model=ListAppointmentsResponse)
async def list_appointments(customer_id: str, api_key: str = None, status_filter: str = "all"):
    """List appointments for a customer with optional status filtering

    Args:
        customer_id: Unique identifier for the customer (e.g., "CUST001")
        api_key: API key for authentication (optional, required only if API_KEY env var is set)
        status_filter: Filter appointments by status. Valid values: "all", "active", "completed", "scheduled", "confirmed", "in_progress", "cancelled"
    """
    verify_api_key(api_key)
    try:
        # Filter appointments for this customer
        appointments_data = get_appointments_data()
        customer_appointments = [
            appointment for appointment in appointments_data.values()
            if appointment["customer_id"] == customer_id
        ]

        # Apply status filter
        if status_filter != "all":
            if status_filter == "active":
                customer_appointments = [
                    appointment for appointment in customer_appointments
                    if appointment["status"] in ["scheduled", "confirmed", "in_progress"]
                ]
            elif status_filter == "completed":
                customer_appointments = [
                    appointment for appointment in customer_appointments
                    if appointment["status"] in ["completed", "cancelled"]
                ]
            else:
                customer_appointments = [
                    appointment for appointment in customer_appointments
                    if appointment["status"] == status_filter
                ]

        # Sort by scheduled datetime (newest first)
        customer_appointments.sort(key=lambda x: x["scheduled_datetime"], reverse=True)

        # Convert to response models
        appointment_responses = [
            AppointmentResponse(**appointment) for appointment in customer_appointments
        ]

        return ListAppointmentsResponse(
            customer_id=customer_id,
            total_appointments=len(appointment_responses),
            status_filter=status_filter,
            appointments=appointment_responses
        )

    except Exception as e:
        logger.error(f"Error listing appointments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.post("/appointments", response_model=CreateAppointmentResponse)
async def create_appointment(request: CreateAppointmentRequest, api_key: str = None):
    """Create a new appointment with conflict detection

    Args:
        request: CreateAppointmentRequest containing:
            - customer_id: Unique identifier for the customer (e.g., "CUST001")
            - technician_id: Unique identifier for the technician (e.g., "TECH001")
            - appliance_type: Type of appliance (e.g., "refrigerator", "washing_machine", "dryer", "dishwasher")
            - issue_description: Detailed description of the issue (minimum 5 characters)
            - scheduled_datetime: Scheduled date and time in ISO format (e.g., "2025-09-05T08:00:00")
            - estimated_duration: Estimated duration in minutes (default: 90, range: 30-480)
            - claim_id: Optional associated claim identifier (e.g., "CLAIM001")
    """
    verify_api_key(api_key)
    try:
        # Parse the scheduled datetime
        scheduled_dt = datetime.fromisoformat(request.scheduled_datetime.replace('Z', '+00:00'))

        # Get shared data
        appointments_data = get_appointments_data()
        technicians_data = get_technicians_data()

        # Validate technician exists
        if request.technician_id not in technicians_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Technician not found: {request.technician_id}"
            )

        technician = technicians_data[request.technician_id]

        # Check if technician can handle this appliance type
        if request.appliance_type.lower() not in [spec.lower() for spec in technician["specialties"]]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Technician does not specialize in {request.appliance_type}. Specialties: {technician['specialties']}"
            )

        # Check for scheduling conflicts
        conflict = _check_scheduling_conflicts(request.technician_id, scheduled_dt, request.estimated_duration)
        if conflict:
            alternatives = _get_alternative_slots(request.technician_id, scheduled_dt, request.estimated_duration)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Scheduling conflict detected. Suggested alternatives: {alternatives[:3]}"
            )

        # Generate new appointment ID
        existing_ids = [int(appt_id.replace("APPT", "")) for appt_id in appointments_data.keys() if appt_id.startswith("APPT")]
        next_id = max(existing_ids, default=0) + 1
        appointment_id = f"APPT{next_id:03d}"

        # Create new appointment
        new_appointment = {
            "id": appointment_id,
            "customer_id": request.customer_id,
            "technician_id": request.technician_id,
            "appliance_type": request.appliance_type,
            "issue_description": request.issue_description,
            "scheduled_datetime": scheduled_dt.isoformat(),
            "status": "scheduled",
            "estimated_duration": request.estimated_duration,
            "created_at": datetime.now().isoformat(),
            "notes": f"Appointment created for {request.appliance_type} repair",
            "claim_id": request.claim_id,
            "service_details": {
                "priority": "medium",
                "parts_needed": [],
                "estimated_cost": 0.0,
                "warranty_covered": True
            }
        }

        # Store in memory
        appointments_data[appointment_id] = new_appointment

        return CreateAppointmentResponse(
            success=True,
            appointment_id=appointment_id,
            status="scheduled",
            message="Appointment created successfully",
            appointment=AppointmentResponse(**new_appointment)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.put("/appointments/{appointment_id}", response_model=UpdateAppointmentResponse, operation_id="update_appointment")
async def update_appointment(appointment_id: str, request: UpdateAppointmentRequest, api_key: str = None):
    """Update an existing appointment with new information

    Args:
        appointment_id: Unique identifier for the appointment (e.g., "APPT001")
        request: UpdateAppointmentRequest containing optional fields:
            - status: New status (scheduled/confirmed/in_progress/completed/cancelled)
            - scheduled_datetime: New scheduled datetime in ISO format
            - estimated_duration: New estimated duration in minutes (range: 30-480)
            - notes: Additional notes
            - issue_description: Updated issue description (minimum 5 characters)
            - technician_id: New technician ID
            - service_details: Service details updates
    """
    verify_api_key(api_key)
    try:
        appointments_data = get_appointments_data()
        technicians_data = get_technicians_data()
        if appointment_id not in appointments_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment not found: {appointment_id}"
            )

        appointment = appointments_data[appointment_id]
        old_data = appointment.copy()
        updated_fields = []

        # Update allowed fields
        if request.status is not None:
            appointment["status"] = request.status
            updated_fields.append("status")

        if request.scheduled_datetime is not None:
            appointment["scheduled_datetime"] = request.scheduled_datetime
            updated_fields.append("scheduled_datetime")

        if request.estimated_duration is not None:
            appointment["estimated_duration"] = request.estimated_duration
            updated_fields.append("estimated_duration")

        if request.notes is not None:
            appointment["notes"] = request.notes
            updated_fields.append("notes")

        if request.issue_description is not None:
            appointment["issue_description"] = request.issue_description
            updated_fields.append("issue_description")

        if request.technician_id is not None:
            if request.technician_id not in technicians_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Technician not found: {request.technician_id}"
                )
            appointment["technician_id"] = request.technician_id
            updated_fields.append("technician_id")

        # Update service details if provided
        if request.service_details is not None:
            if "service_details" not in appointment:
                appointment["service_details"] = {}
            appointment["service_details"].update(request.service_details)
            updated_fields.append("service_details")

        return UpdateAppointmentResponse(
            success=True,
            appointment_id=appointment_id,
            updated_fields=updated_fields,
            old_data=old_data,
            updated_appointment=AppointmentResponse(**appointment)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.delete("/appointments/{appointment_id}", response_model=CancelAppointmentResponse, operation_id="cancel_appointment")
async def cancel_appointment(appointment_id: str, request: CancelAppointmentRequest, api_key: str = None):
    """Cancel an existing appointment

    Args:
        appointment_id: Unique identifier for the appointment (e.g., "APPT001")
        request: CancelAppointmentRequest containing:
            - reason: Reason for cancellation (default: "Customer request")
    """
    verify_api_key(api_key)
    try:
        appointments_data = get_appointments_data()
        if appointment_id not in appointments_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment not found: {appointment_id}"
            )

        appointment = appointments_data[appointment_id]

        # Check if appointment can be cancelled
        if appointment["status"] in ["completed", "cancelled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel appointment with status: {appointment['status']}"
            )

        old_status = appointment["status"]
        appointment["status"] = "cancelled"
        appointment["notes"] = f"{appointment.get('notes', '')} | Cancelled: {request.reason}".strip(" |")

        # Add cancellation details
        if "service_details" not in appointment:
            appointment["service_details"] = {}
        appointment["service_details"]["cancellation_reason"] = request.reason
        appointment["service_details"]["cancelled_at"] = datetime.now().isoformat()

        return CancelAppointmentResponse(
            success=True,
            appointment_id=appointment_id,
            old_status=old_status,
            new_status="cancelled",
            cancellation_reason=request.reason,
            appointment=AppointmentResponse(**appointment)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Duplicate function removed - using the first definition above

@app.put("/appointments/{appointment_id}/reschedule", response_model=RescheduleAppointmentResponse, operation_id="reschedule_appointment")
async def reschedule_appointment(appointment_id: str, request: RescheduleAppointmentRequest, api_key: str = None):
    """Reschedule an existing appointment to a new time

    Args:
        appointment_id: Unique identifier for the appointment (e.g., "APPT001")
        request: RescheduleAppointmentRequest containing:
            - new_datetime: New scheduled date and time in ISO format (e.g., "2025-09-05T08:00:00")
    """
    verify_api_key(api_key)
    try:
        appointments_data = get_appointments_data()
        if appointment_id not in appointments_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment not found: {appointment_id}"
            )

        appointment = appointments_data[appointment_id]

        # Check if appointment can be rescheduled
        if appointment["status"] in ["completed", "cancelled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reschedule appointment with status: {appointment['status']}"
            )

        # Parse new datetime
        new_dt = datetime.fromisoformat(request.new_datetime.replace('Z', '+00:00'))

        # Check for conflicts with the new time
        technician_id = appointment["technician_id"]
        duration = appointment["estimated_duration"]

        conflict = _check_scheduling_conflicts(technician_id, new_dt, duration, exclude_appointment_id=appointment_id)
        if conflict:
            alternatives = _get_alternative_slots(technician_id, new_dt, duration)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Scheduling conflict detected. Suggested alternatives: {alternatives[:3]}"
            )

        old_datetime = appointment["scheduled_datetime"]
        appointment["scheduled_datetime"] = new_dt.isoformat()
        appointment["notes"] = f"{appointment.get('notes', '')} | Rescheduled from {old_datetime}".strip(" |")

        return RescheduleAppointmentResponse(
            success=True,
            appointment_id=appointment_id,
            old_datetime=old_datetime,
            new_datetime=new_dt.isoformat(),
            message="Appointment rescheduled successfully",
            appointment=AppointmentResponse(**appointment)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rescheduling appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/appointments/{appointment_id}/details", response_model=AppointmentDetailsResponse, operation_id="get_appointment_details")
async def get_appointment_details(appointment_id: str, api_key: str = None):
    """Get detailed information about a specific appointment

    Args:
        appointment_id: Unique identifier for the appointment (e.g., "APPT001")
    """
    verify_api_key(api_key)
    try:
        appointments_data = get_appointments_data()
        technicians_data = get_technicians_data()
        if appointment_id not in appointments_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment not found: {appointment_id}"
            )

        appointment = appointments_data[appointment_id]

        # Enrich with technician details
        technician_id = appointment["technician_id"]
        appointment_details = appointment.copy()

        if technician_id in technicians_data:
            technician = technicians_data[technician_id]
            appointment_details["technician_details"] = {
                "name": technician["name"],
                "phone": technician["phone"],
                "specialties": technician["specialties"],
                "current_location": technician["current_location"],
                "status": technician["status"],
                "profile": technician.get("profile", {})
            }

        return AppointmentDetailsResponse(**appointment_details)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting appointment details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


def _check_scheduling_conflicts(
    technician_id: str,
    scheduled_dt: datetime,
    duration_minutes: int,
    exclude_appointment_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Check for scheduling conflicts for a technician at a specific time."""
    # Get all appointments for this technician
    appointments_data = get_appointments_data()
    tech_appointments = [
        appt for appt in appointments_data.values()
        if appt["technician_id"] == technician_id
        and appt["status"] in ["scheduled", "confirmed", "in_progress"]
        and (exclude_appointment_id is None or appt["id"] != exclude_appointment_id)
    ]

    # Check for time conflicts
    new_end_time = scheduled_dt + timedelta(minutes=duration_minutes)

    for existing_appt in tech_appointments:
        existing_start = datetime.fromisoformat(existing_appt["scheduled_datetime"].replace('Z', '+00:00'))
        existing_end = existing_start + timedelta(minutes=existing_appt["estimated_duration"])

        # Check if times overlap
        if (scheduled_dt < existing_end and new_end_time > existing_start):
            return {
                "conflicting_appointment_id": existing_appt["id"],
                "conflicting_time": existing_appt["scheduled_datetime"],
                "conflicting_duration": existing_appt["estimated_duration"],
                "overlap_start": max(scheduled_dt, existing_start).isoformat(),
                "overlap_end": min(new_end_time, existing_end).isoformat()
            }

    return None


def _is_slot_available(technician_id: str, slot_datetime: datetime, duration_minutes: int) -> bool:
    """Check if a specific time slot is available for a technician."""
    return _check_scheduling_conflicts(technician_id, slot_datetime, duration_minutes) is None


def _get_alternative_slots(technician_id: str, preferred_datetime: datetime, duration_minutes: int) -> List[Dict[str, Any]]:
    """Get alternative time slots near the preferred datetime."""
    alternatives = []

    # Check slots within 3 days before and after
    for days_offset in [-3, -2, -1, 1, 2, 3]:
        for hour_offset in [0, 1, 2, -1, -2]:
            alt_datetime = preferred_datetime + timedelta(days=days_offset, hours=hour_offset)

            # Skip past times
            if alt_datetime <= datetime.now():
                continue

            if _is_slot_available(technician_id, alt_datetime, duration_minutes):
                alternatives.append({
                    "datetime": alt_datetime.isoformat(),
                    "technician_id": technician_id,
                    "duration_minutes": duration_minutes
                })

                # Limit to 5 alternatives
                if len(alternatives) >= 5:
                    break

        if len(alternatives) >= 5:
            break

    return alternatives


# Exception handlers for better error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with consistent error format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "status_code": 500}
    )


def main():
    """Main entry point for running the REST API server"""
    # Load mock data
    load_mock_data()

    # Run the server
    uvicorn.run(
        app,  # Use the app object directly instead of string import
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )


if __name__ == "__main__":
    main()
