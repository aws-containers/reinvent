"""
Appointment Management MCP Server

This server provides appointment scheduling and management functionality
for the Insurance Agent ChatBot system. It handles appointment operations
including scheduling, updates, cancellations, and availability checking.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import uuid4

from mcp.server.fastmcp import FastMCP
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.types as types

from shared.models import Appointment, AppointmentStatus, Technician, TechnicianStatus
from shared.utils import generate_id, parse_datetime


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastMCP server instance for streamable-http transport
mcp = FastMCP("appointment-management-server")

# Import shared data storage
from .shared_data import load_mock_data, get_appointments_data, get_technicians_data


@mcp.resource("appointment://schedules")
def appointment_schedules() -> str:
    """Access to appointment scheduling information"""
    return "Appointment scheduling data"

@mcp.resource("appointment://availability")
def appointment_availability() -> str:
    """Technician availability and time slots"""
    return "Availability data"

@mcp.resource("appointment://status")
def appointment_status() -> str:
    """Appointment status and tracking"""
    return "Status tracking data"


@mcp.tool()
def list_all_appointments(status_filter: str = "all") -> str:
    """List all appointments in the system with optional status filtering

    Args:
        status_filter: Filter appointments by status. Valid values: "all", "active", "completed", "scheduled", "confirmed", "in_progress", "cancelled"
    """
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

        return json.dumps({
            "total_appointments": len(all_appointments),
            "status_filter": status_filter,
            "appointments": all_appointments
        }, indent=2)

    except Exception as e:
        logger.error(f"Error listing all appointments: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def list_appointments(customer_id: str, status_filter: str = "all") -> str:
    """List appointments for a customer with optional status filtering

    Args:
        customer_id: Unique identifier for the customer (e.g., "CUST001")
        status_filter: Filter appointments by status. Valid values: "all", "active", "completed", "scheduled", "confirmed", "in_progress", "cancelled"
    """
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

        return json.dumps({
            "customer_id": customer_id,
            "total_appointments": len(customer_appointments),
            "status_filter": status_filter,
            "appointments": customer_appointments
        }, indent=2)

    except Exception as e:
        logger.error(f"Error listing appointments: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def create_appointment(
    customer_id: str,
    technician_id: str,
    appliance_type: str,
    issue_description: str,
    scheduled_datetime: str,
    estimated_duration: int = 90,
    claim_id: Optional[str] = None
) -> str:
    """Create a new appointment with conflict detection

    Args:
        customer_id: Unique identifier for the customer (e.g., "CUST001")
        technician_id: Unique identifier for the technician (e.g., "TECH001")
        appliance_type: Type of appliance needing service (e.g., "refrigerator", "washing_machine", "dryer", "dishwasher")
        issue_description: Detailed description of the issue (minimum 5 characters)
        scheduled_datetime: Scheduled date and time in ISO format (e.g., "2025-09-05T08:00:00")
        estimated_duration: Estimated duration in minutes (default: 90, range: 30-480)
        claim_id: Optional associated claim identifier (e.g., "CLAIM001")
    """
    try:
        # Parse the scheduled datetime
        try:
            scheduled_dt = datetime.fromisoformat(scheduled_datetime.replace('Z', '+00:00'))
        except ValueError:
            return json.dumps({
                "error": "Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            })

        # Validate technician exists
        technicians_data = get_technicians_data()
        if technician_id not in technicians_data:
            return json.dumps({
                "error": "Technician not found",
                "technician_id": technician_id
            })

        technician = technicians_data[technician_id]

        # Check if technician can handle this appliance type
        if appliance_type.lower() not in [spec.lower() for spec in technician["specialties"]]:
            return json.dumps({
                "error": "Technician does not specialize in this appliance type",
                "appliance_type": appliance_type,
                "technician_specialties": technician["specialties"]
            })

        # Check for scheduling conflicts
        conflict = _check_scheduling_conflicts(technician_id, scheduled_dt, estimated_duration)
        if conflict:
            return json.dumps({
                "error": "Scheduling conflict detected",
                "conflict_details": conflict,
                "suggested_alternatives": _get_alternative_slots(technician_id, scheduled_dt, estimated_duration)
            })

        # Generate new appointment ID
        appointments_data = get_appointments_data()
        existing_ids = [int(appt_id.replace("APPT", "")) for appt_id in appointments_data.keys() if appt_id.startswith("APPT")]
        next_id = max(existing_ids, default=0) + 1
        appointment_id = f"APPT{next_id:03d}"

        # Create new appointment
        new_appointment = {
            "id": appointment_id,
            "customer_id": customer_id,
            "technician_id": technician_id,
            "appliance_type": appliance_type,
            "issue_description": issue_description,
            "scheduled_datetime": scheduled_dt.isoformat(),
            "status": "scheduled",
            "estimated_duration": estimated_duration,
            "created_at": datetime.now().isoformat(),
            "notes": f"Appointment created for {appliance_type} repair",
            "claim_id": claim_id,
            "service_details": {
                "priority": "medium",
                "parts_needed": [],
                "estimated_cost": 0.0,
                "warranty_covered": True
            }
        }

        # Store in memory
        appointments_data[appointment_id] = new_appointment

        return json.dumps({
            "success": True,
            "appointment_id": appointment_id,
            "status": "scheduled",
            "message": "Appointment created successfully",
            "appointment": new_appointment
        }, indent=2)

    except Exception as e:
        logger.error(f"Error creating appointment: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def update_appointment(appointment_id: str, updates: str) -> str:
    """Update an existing appointment with new information

    Args:
        appointment_id: Unique identifier for the appointment (e.g., "APPT001")
        updates: JSON string containing fields to update. Valid fields: "status" (scheduled/confirmed/in_progress/completed/cancelled), "scheduled_datetime" (ISO format), "estimated_duration" (30-480 minutes), "notes", "issue_description", "technician_id", "service_details"
    """
    try:
        appointments_data = get_appointments_data()
        if appointment_id not in appointments_data:
            return json.dumps({
                "error": "Appointment not found",
                "appointment_id": appointment_id
            })

        # Parse updates JSON
        try:
            update_data = json.loads(updates)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON format for updates"})

        appointment = appointments_data[appointment_id]
        old_data = appointment.copy()

        # Update allowed fields
        allowed_fields = [
            "status", "scheduled_datetime", "estimated_duration",
            "notes", "issue_description", "technician_id"
        ]

        for field, value in update_data.items():
            if field in allowed_fields:
                # Special handling for datetime fields
                if field == "scheduled_datetime" and isinstance(value, str):
                    try:
                        # Validate datetime format
                        datetime.fromisoformat(value.replace('Z', '+00:00'))
                        appointment[field] = value
                    except ValueError:
                        return json.dumps({
                            "error": f"Invalid datetime format for {field}. Use ISO format"
                        })
                else:
                    appointment[field] = value

        # Update service details if provided
        if "service_details" in update_data:
            if "service_details" not in appointment:
                appointment["service_details"] = {}
            appointment["service_details"].update(update_data["service_details"])

        return json.dumps({
            "success": True,
            "appointment_id": appointment_id,
            "updated_fields": list(update_data.keys()),
            "old_data": old_data,
            "updated_appointment": appointment
        }, indent=2)

    except Exception as e:
        logger.error(f"Error updating appointment: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def cancel_appointment(appointment_id: str, reason: str = "Customer request") -> str:
    """Cancel an existing appointment

    Args:
        appointment_id: Unique identifier for the appointment (e.g., "APPT001")
        reason: Reason for cancellation (default: "Customer request")
    """
    try:
        appointments_data = get_appointments_data()
        if appointment_id not in appointments_data:
            return json.dumps({
                "error": "Appointment not found",
                "appointment_id": appointment_id
            })

        appointment = appointments_data[appointment_id]

        # Check if appointment can be cancelled
        if appointment["status"] in ["completed", "cancelled"]:
            return json.dumps({
                "error": "Cannot cancel appointment",
                "current_status": appointment["status"],
                "reason": "Appointment is already completed or cancelled"
            })

        old_status = appointment["status"]
        appointment["status"] = "cancelled"
        appointment["notes"] = f"{appointment.get('notes', '')} | Cancelled: {reason}".strip(" |")

        # Add cancellation details
        if "service_details" not in appointment:
            appointment["service_details"] = {}
        appointment["service_details"]["cancellation_reason"] = reason
        appointment["service_details"]["cancelled_at"] = datetime.now().isoformat()

        return json.dumps({
            "success": True,
            "appointment_id": appointment_id,
            "old_status": old_status,
            "new_status": "cancelled",
            "cancellation_reason": reason,
            "appointment": appointment
        }, indent=2)

    except Exception as e:
        logger.error(f"Error cancelling appointment: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_available_slots(
    date_range_start: str,
    date_range_end: str,
    appliance_type: str,
    duration_minutes: int = 90
) -> str:
    """Get available time slots for scheduling appointments

    Args:
        date_range_start: Start date for availability search in ISO format (e.g., "2025-09-05T00:00:00")
        date_range_end: End date for availability search in ISO format (e.g., "2025-09-06T00:00:00")
        appliance_type: Type of appliance needing service (e.g., "refrigerator", "washing_machine", "dryer", "dishwasher")
        duration_minutes: Required duration in minutes (default: 90, range: 30-480)
    """
    try:
        # Parse date range
        try:
            start_dt = datetime.fromisoformat(date_range_start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(date_range_end.replace('Z', '+00:00'))
        except ValueError:
            return json.dumps({
                "error": "Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            })

        # Find technicians who can handle this appliance type
        technicians_data = get_technicians_data()
        qualified_technicians = [
            tech for tech in technicians_data.values()
            if appliance_type.lower() in [spec.lower() for spec in tech["specialties"]]
            and tech["status"] in ["available", "busy"]  # Include busy techs for future slots
        ]

        if not qualified_technicians:
            return json.dumps({
                "error": "No technicians available for this appliance type",
                "appliance_type": appliance_type
            })

        # Generate available slots
        available_slots = []
        current_dt = start_dt

        while current_dt < end_dt:
            # Check each qualified technician for this time slot
            for tech in qualified_technicians:
                if _is_slot_available(tech["id"], current_dt, duration_minutes):
                    slot = {
                        "datetime": current_dt.isoformat(),
                        "technician_id": tech["id"],
                        "technician_name": tech["name"],
                        "duration_minutes": duration_minutes,
                        "specialties": tech["specialties"],
                        "rating": tech.get("profile", {}).get("rating", 0.0)
                    }
                    available_slots.append(slot)

            # Move to next hour
            current_dt += timedelta(hours=1)

        # Sort by datetime and rating
        available_slots.sort(key=lambda x: (x["datetime"], -x["rating"]))

        return json.dumps({
            "appliance_type": appliance_type,
            "date_range": {
                "start": date_range_start,
                "end": date_range_end
            },
            "duration_minutes": duration_minutes,
            "total_slots": len(available_slots),
            "qualified_technicians": len(qualified_technicians),
            "available_slots": available_slots[:20]  # Limit to first 20 slots
        }, indent=2)

    except Exception as e:
        logger.error(f"Error getting available slots: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def reschedule_appointment(appointment_id: str, new_datetime: str) -> str:
    """Reschedule an existing appointment to a new time

    Args:
        appointment_id: Unique identifier for the appointment (e.g., "APPT001")
        new_datetime: New scheduled date and time in ISO format (e.g., "2025-09-05T08:00:00")
    """
    try:
        appointments_data = get_appointments_data()
        if appointment_id not in appointments_data:
            return json.dumps({
                "error": "Appointment not found",
                "appointment_id": appointment_id
            })

        appointment = appointments_data[appointment_id]

        # Check if appointment can be rescheduled
        if appointment["status"] in ["completed", "cancelled"]:
            return json.dumps({
                "error": "Cannot reschedule appointment",
                "current_status": appointment["status"],
                "reason": "Appointment is already completed or cancelled"
            })

        # Parse new datetime
        try:
            new_dt = datetime.fromisoformat(new_datetime.replace('Z', '+00:00'))
        except ValueError:
            return json.dumps({
                "error": "Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            })

        # Check for conflicts with the new time
        technician_id = appointment["technician_id"]
        duration = appointment["estimated_duration"]

        conflict = _check_scheduling_conflicts(technician_id, new_dt, duration, exclude_appointment_id=appointment_id)
        if conflict:
            return json.dumps({
                "error": "Scheduling conflict detected for new time",
                "conflict_details": conflict,
                "suggested_alternatives": _get_alternative_slots(technician_id, new_dt, duration)
            })

        old_datetime = appointment["scheduled_datetime"]
        appointment["scheduled_datetime"] = new_dt.isoformat()
        appointment["notes"] = f"{appointment.get('notes', '')} | Rescheduled from {old_datetime}".strip(" |")

        return json.dumps({
            "success": True,
            "appointment_id": appointment_id,
            "old_datetime": old_datetime,
            "new_datetime": new_dt.isoformat(),
            "message": "Appointment rescheduled successfully",
            "appointment": appointment
        }, indent=2)

    except Exception as e:
        logger.error(f"Error rescheduling appointment: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_appointment_details(appointment_id: str) -> str:
    """Get detailed information about a specific appointment

    Args:
        appointment_id: Unique identifier for the appointment (e.g., "APPT001")
    """
    try:
        appointments_data = get_appointments_data()
        technicians_data = get_technicians_data()
        if appointment_id not in appointments_data:
            return json.dumps({
                "error": "Appointment not found",
                "appointment_id": appointment_id
            })

        appointment = appointments_data[appointment_id]

        # Enrich with technician details
        technician_id = appointment["technician_id"]
        if technician_id in technicians_data:
            technician = technicians_data[technician_id]
            appointment_details = appointment.copy()
            appointment_details["technician_details"] = {
                "name": technician["name"],
                "phone": technician["phone"],
                "specialties": technician["specialties"],
                "current_location": technician["current_location"],
                "status": technician["status"],
                "profile": technician.get("profile", {})
            }
        else:
            appointment_details = appointment

        return json.dumps(appointment_details, indent=2)

    except Exception as e:
        logger.error(f"Error getting appointment details: {e}")
        return json.dumps({"error": str(e)})


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


def main():
    """Main server entry point."""
    # Load mock data on startup
    load_mock_data()

    # Import and integrate REST API
    from .server_rest import app as rest_app, load_mock_data as rest_load_data

    # Ensure REST API uses the same data
    rest_load_data()

    # Configure server to run on all IP addresses on port 8002
    mcp.settings.host = '0.0.0.0'
    mcp.settings.port = 8002

    # Run the server with streamable-http transport
    # Note: REST API integration is handled separately
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
