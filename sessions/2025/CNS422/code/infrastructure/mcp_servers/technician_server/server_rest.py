"""
FastAPI REST interface for Technician Tracking Server

This module provides HTTP REST endpoints that mirror the MCP tool functionality
for technician location and status management, availability checking, and route tracking.
"""

import json
import logging
import math
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, ConfigDict
import uvicorn

from shared.models import Technician, TechnicianStatus
from shared.utils import generate_id, parse_datetime

# Import shared data storage
from .shared_data import load_mock_data, get_technicians_data


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
    title="Technician Tracking Server REST API",
    description="REST API for technician location and status management, availability checking, and route tracking",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# Pydantic models for request/response validation
class TechnicianStatusResponse(BaseModel):
    """Response model for technician status information"""
    technician_id: str
    name: str
    status: str
    specialties: List[str]
    phone: str
    current_appointment_id: Optional[str] = None
    estimated_arrival: Optional[str] = None
    last_updated: str


class LocationInfo(BaseModel):
    """Model for location coordinates"""
    latitude: float
    longitude: float


class TechnicianLocationResponse(BaseModel):
    """Response model for technician location information"""
    technician_id: str
    name: str
    current_location: LocationInfo
    status: str
    estimated_arrival: Optional[str] = None
    eta_minutes: Optional[int] = None
    status_note: Optional[str] = None
    last_location_update: str


class AvailableTechniciansRequest(BaseModel):
    """Request model for finding available technicians"""
    area: str = Field(..., description="Service area")
    datetime_str: str = Field(..., description="Requested datetime in ISO format")
    specialties: List[str] = Field(..., description="Required specialties")


class AvailableTechnicianInfo(BaseModel):
    """Model for available technician information"""
    technician_id: str
    name: str
    specialties: List[str]
    phone: str
    current_location: LocationInfo
    distance_miles: float
    eta_minutes: int
    estimated_arrival: str
    profile: Dict[str, Any] = {}


class AvailableTechniciansResponse(BaseModel):
    """Response model for available technicians"""
    area: str
    requested_datetime: str
    required_specialties: List[str]
    available_technicians: List[AvailableTechnicianInfo]
    total_found: int


class UpdateTechnicianStatusRequest(BaseModel):
    """Request model for updating technician status"""
    new_status: str = Field(..., description="New status for the technician")
    location: Optional[List[float]] = Field(None, description="Optional location coordinates [lat, lon]")
    appointment_id: Optional[str] = Field(None, description="Optional appointment ID")

    @field_validator('new_status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ["available", "en_route", "on_site", "busy", "off_duty"]
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v

    @field_validator('location')
    @classmethod
    def validate_location(cls, v):
        if v is not None and len(v) != 2:
            raise ValueError('Location must be a list of exactly 2 coordinates [latitude, longitude]')
        return v


class UpdateTechnicianStatusResponse(BaseModel):
    """Response model for technician status update"""
    success: bool
    technician_id: str
    old_status: str
    new_status: str
    updated_at: str
    current_appointment_id: Optional[str] = None
    estimated_arrival: Optional[str] = None


class RouteRequest(BaseModel):
    """Request model for route calculation"""
    destination: List[float] = Field(..., description="Destination coordinates [latitude, longitude]")

    @field_validator('destination')
    @classmethod
    def validate_destination(cls, v):
        if len(v) != 2:
            raise ValueError('Destination must be a list of exactly 2 coordinates [latitude, longitude]')
        return v


class RouteWaypoint(BaseModel):
    """Model for route waypoint"""
    latitude: float
    longitude: float
    instruction: str


class RouteResponse(BaseModel):
    """Response model for route information"""
    technician_id: str
    technician_name: str
    origin: LocationInfo
    destination: LocationInfo
    distance_miles: float
    estimated_travel_time_minutes: int
    estimated_arrival: str
    traffic_conditions: str
    route_waypoints: List[RouteWaypoint]
    calculated_at: str


class StatusNotificationRequest(BaseModel):
    """Request model for status change notification"""
    appointment_id: str = Field(..., description="Appointment ID")
    status_message: Optional[str] = Field(None, description="Optional custom status message")


class StatusNotificationResponse(BaseModel):
    """Response model for status change notification"""
    success: bool
    appointment_id: str
    technician_id: str
    technician_name: str
    current_status: str
    message: str
    timestamp: str
    estimated_arrival: Optional[str] = None
    current_location: Optional[LocationInfo] = None


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str
    detail: Optional[str] = None


# Utility functions (copied from server.py)
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the distance between two GPS coordinates using Haversine formula."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 3956  # Radius of earth in miles
    return c * r


def calculate_eta(distance_miles: float, traffic_factor: float = 1.2) -> int:
    """Calculate estimated time of arrival in minutes."""
    base_speed_mph = 25
    adjusted_speed = base_speed_mph / traffic_factor
    eta_hours = distance_miles / adjusted_speed
    eta_minutes = int(eta_hours * 60)
    eta_minutes += random.randint(-5, 5)
    return max(eta_minutes, 5)


def simulate_location_update(technician: Dict[str, Any], destination: Optional[Tuple[float, float]] = None) -> Tuple[float, float]:
    """Simulate technician location update based on their status."""
    current_lat, current_lon = technician["current_location"]
    status = technician["status"]

    if status == "available":
        new_lat = current_lat + random.uniform(-0.01, 0.01)
        new_lon = current_lon + random.uniform(-0.01, 0.01)
    elif status == "en_route" and destination:
        dest_lat, dest_lon = destination
        lat_diff = dest_lat - current_lat
        lon_diff = dest_lon - current_lon
        new_lat = current_lat + (lat_diff * 0.1)
        new_lon = current_lon + (lon_diff * 0.1)
    else:
        new_lat = current_lat + random.uniform(-0.001, 0.001)
        new_lon = current_lon + random.uniform(-0.001, 0.001)

    return new_lat, new_lon


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "technician-tracking-server"}


@app.get("/technicians", response_model=List[TechnicianStatusResponse], operation_id="list_all_technicians")
async def list_all_technicians(api_key: str = None, status_filter: str = "all"):
    """List all technicians in the system with optional status filtering

    Args:
        status_filter: Filter technicians by status. Valid values: "all", "available", "en_route", "on_site", "busy", "off_duty"
    """
    verify_api_key(api_key)
    try:
        technicians_data = get_technicians_data()
        all_technicians = list(technicians_data.values())

        # Apply status filter
        if status_filter != "all":
            all_technicians = [
                tech for tech in all_technicians
                if tech["status"] == status_filter
            ]

        # Sort by name
        all_technicians.sort(key=lambda x: x["name"])

        # Return technician list
        technician_list = [
            TechnicianStatusResponse(
                technician_id=tech["id"],
                name=tech["name"],
                status=tech["status"],
                specialties=tech["specialties"],
                phone=tech["phone"],
                current_appointment_id=tech.get("current_appointment_id"),
                estimated_arrival=tech.get("estimated_arrival"),
                last_updated=datetime.now().isoformat()
            ) for tech in all_technicians
        ]

        return technician_list

    except Exception as e:
        logger.error(f"Error listing all technicians: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/technicians/{technician_id}/status", response_model=TechnicianStatusResponse, operation_id="get_technician_status")
async def get_technician_status(technician_id: str, api_key: str = None):
    """Get current status and basic information for a specific technician

    Args:
        technician_id: Unique identifier for the technician (e.g., "TECH001")
    """
    verify_api_key(api_key)
    try:
        technicians_data = get_technicians_data()
        if technician_id not in technicians_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Technician not found: {technician_id}"
            )

        technician = technicians_data[technician_id]

        return TechnicianStatusResponse(
            technician_id=technician["id"],
            name=technician["name"],
            status=technician["status"],
            specialties=technician["specialties"],
            phone=technician["phone"],
            current_appointment_id=technician.get("current_appointment_id"),
            estimated_arrival=technician.get("estimated_arrival"),
            last_updated=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting technician status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/technicians/{technician_id}/location", response_model=TechnicianLocationResponse, operation_id="get_technician_location")
async def get_technician_location(technician_id: str, api_key: str = None):
    """Get real-time GPS location and ETA information for a technician

    Args:
        technician_id: Unique identifier for the technician (e.g., "TECH001")
    """
    verify_api_key(api_key)
    try:
        technicians_data = get_technicians_data()
        if technician_id not in technicians_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Technician not found: {technician_id}"
            )

        technician = technicians_data[technician_id]

        # Simulate location update
        new_location = simulate_location_update(technician)
        technician["current_location"] = list(new_location)

        response_data = {
            "technician_id": technician["id"],
            "name": technician["name"],
            "current_location": LocationInfo(
                latitude=new_location[0],
                longitude=new_location[1]
            ),
            "status": technician["status"],
            "estimated_arrival": technician.get("estimated_arrival"),
            "last_location_update": datetime.now().isoformat()
        }

        # Add ETA calculation if technician is en route
        if technician["status"] == "en_route" and technician.get("estimated_arrival"):
            try:
                arrival_time = datetime.fromisoformat(technician["estimated_arrival"])
                now = datetime.now()
                if arrival_time > now:
                    eta_minutes = int((arrival_time - now).total_seconds() / 60)
                    response_data["eta_minutes"] = eta_minutes
                else:
                    response_data["eta_minutes"] = 0
                    response_data["status_note"] = "Should have arrived"
            except ValueError:
                pass

        return TechnicianLocationResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting technician location: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.post("/technicians/available", response_model=AvailableTechniciansResponse, operation_id="list_available_technicians")
async def list_available_technicians(request: AvailableTechniciansRequest, api_key: str = None):
    """Find available technicians in a specific area with required specialties

    Args:
        request: AvailableTechniciansRequest containing:
            - area: Service area to search (e.g., "Chicago", "Denver")
            - datetime_str: Requested datetime in ISO format (e.g., "2025-09-05T08:00:00")
            - specialties: List of required specialties (e.g., ["refrigerator", "washing_machine"])
    """
    verify_api_key(api_key)
    try:
        # Parse the datetime
        try:
            requested_datetime = datetime.fromisoformat(request.datetime_str.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            )

        technicians_data = get_technicians_data()
        available_technicians = []

        for tech_id, technician in technicians_data.items():
            # Check if technician is available
            if technician["status"] != "available":
                continue

            # Check if technician has required specialties
            tech_specialties = [spec.lower() for spec in technician["specialties"]]
            required_specialties = [spec.lower() for spec in request.specialties]

            if not any(req_spec in tech_specialties for req_spec in required_specialties):
                continue

            # Calculate simulated distance (random for demo)
            distance_miles = random.uniform(2.0, 15.0)
            eta_minutes = calculate_eta(distance_miles)

            available_tech = AvailableTechnicianInfo(
                technician_id=technician["id"],
                name=technician["name"],
                specialties=technician["specialties"],
                phone=technician["phone"],
                current_location=LocationInfo(
                    latitude=technician["current_location"][0],
                    longitude=technician["current_location"][1]
                ),
                distance_miles=round(distance_miles, 1),
                eta_minutes=eta_minutes,
                estimated_arrival=(requested_datetime + timedelta(minutes=eta_minutes)).isoformat(),
                profile=technician.get("profile", {})
            )

            available_technicians.append(available_tech)

        # Sort by ETA (closest first)
        available_technicians.sort(key=lambda x: x.eta_minutes)

        return AvailableTechniciansResponse(
            area=request.area,
            requested_datetime=request.datetime_str,
            required_specialties=request.specialties,
            available_technicians=available_technicians,
            total_found=len(available_technicians)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing available technicians: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.put("/technicians/{technician_id}/status", response_model=UpdateTechnicianStatusResponse, operation_id="update_technician_status")
async def update_technician_status(technician_id: str, request: UpdateTechnicianStatusRequest, api_key: str = None):
    """Update technician status and optionally location and appointment assignment

    Args:
        technician_id: Unique identifier for the technician (e.g., "TECH001")
        request: UpdateTechnicianStatusRequest containing:
            - new_status: New status. Valid values: "available", "en_route", "on_site", "busy", "off_duty"
            - location: Optional location coordinates [latitude, longitude]
            - appointment_id: Optional appointment identifier (e.g., "APPT001")
    """
    verify_api_key(api_key)
    try:
        technicians_data = get_technicians_data()
        if technician_id not in technicians_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Technician not found: {technician_id}"
            )

        technician = technicians_data[technician_id]
        old_status = technician["status"]

        # Update status
        technician["status"] = request.new_status

        # Update location if provided
        if request.location and len(request.location) == 2:
            technician["current_location"] = request.location

        # Update appointment assignment
        if request.appointment_id:
            technician["current_appointment_id"] = request.appointment_id
        elif request.new_status == "available":
            # Clear appointment when becoming available
            technician["current_appointment_id"] = None

        # Update estimated arrival based on status
        if request.new_status == "en_route" and request.appointment_id:
            # Set estimated arrival time (simulate 30-60 minutes from now)
            eta_minutes = random.randint(30, 60)
            estimated_arrival = datetime.now() + timedelta(minutes=eta_minutes)
            technician["estimated_arrival"] = estimated_arrival.isoformat()
        elif request.new_status in ["available", "off_duty"]:
            technician["estimated_arrival"] = None

        return UpdateTechnicianStatusResponse(
            success=True,
            technician_id=technician_id,
            old_status=old_status,
            new_status=request.new_status,
            updated_at=datetime.now().isoformat(),
            current_appointment_id=technician.get("current_appointment_id"),
            estimated_arrival=technician.get("estimated_arrival")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating technician status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/technicians/{technician_id}/route", response_model=RouteResponse, operation_id="get_technician_route")
async def get_technician_route(technician_id: str, destination: str, api_key: str = None):
    """Get route information and travel time to a destination

    Args:
        technician_id: Unique identifier for the technician (e.g., "TECH001")
        destination: Destination coordinates as JSON array string (e.g., "[41.8781, -87.6298]")
    """
    verify_api_key(api_key)
    try:
        # Parse destination coordinates from query parameter
        try:
            dest_coords = json.loads(destination)
            if not isinstance(dest_coords, list) or len(dest_coords) != 2:
                raise ValueError("Invalid format")
        except (json.JSONDecodeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid destination format. Provide JSON array: [latitude, longitude]"
            )

        technicians_data = get_technicians_data()
        if technician_id not in technicians_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Technician not found: {technician_id}"
            )

        technician = technicians_data[technician_id]
        current_lat, current_lon = technician["current_location"]
        dest_lat, dest_lon = dest_coords

        # Calculate distance and ETA
        distance_miles = calculate_distance(current_lat, current_lon, dest_lat, dest_lon)

        # Simulate traffic conditions
        traffic_conditions = random.choice(["light", "moderate", "heavy"])
        traffic_factors = {"light": 1.0, "moderate": 1.2, "heavy": 1.5}
        traffic_factor = traffic_factors[traffic_conditions]

        eta_minutes = calculate_eta(distance_miles, traffic_factor)
        estimated_arrival = datetime.now() + timedelta(minutes=eta_minutes)

        # Generate simulated route waypoints
        waypoints = []
        num_waypoints = min(5, max(3, int(distance_miles / 2)))  # Ensure at least 3 waypoints

        for i in range(1, num_waypoints):
            progress = i / num_waypoints
            waypoint_lat = current_lat + (dest_lat - current_lat) * progress
            waypoint_lon = current_lon + (dest_lon - current_lon) * progress
            waypoints.append(RouteWaypoint(
                latitude=waypoint_lat,
                longitude=waypoint_lon,
                instruction=f"Continue for {random.uniform(0.5, 2.0):.1f} miles"
            ))

        return RouteResponse(
            technician_id=technician_id,
            technician_name=technician["name"],
            origin=LocationInfo(latitude=current_lat, longitude=current_lon),
            destination=LocationInfo(latitude=dest_lat, longitude=dest_lon),
            distance_miles=round(distance_miles, 1),
            estimated_travel_time_minutes=eta_minutes,
            estimated_arrival=estimated_arrival.isoformat(),
            traffic_conditions=traffic_conditions,
            route_waypoints=waypoints,
            calculated_at=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating technician route: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.post("/technicians/{technician_id}/route", response_model=RouteResponse, operation_id="get_technician_route_post")
async def get_technician_route_post(technician_id: str, request: RouteRequest, api_key: str = None):
    """Get route information and travel time to a destination (POST version)

    Args:
        technician_id: Unique identifier for the technician (e.g., "TECH001")
        request: RouteRequest containing:
            - destination: Destination coordinates [latitude, longitude]
    """
    verify_api_key(api_key)
    try:
        technicians_data = get_technicians_data()
        if technician_id not in technicians_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Technician not found: {technician_id}"
            )

        technician = technicians_data[technician_id]
        current_lat, current_lon = technician["current_location"]
        dest_lat, dest_lon = request.destination

        # Calculate distance and ETA
        distance_miles = calculate_distance(current_lat, current_lon, dest_lat, dest_lon)

        # Simulate traffic conditions
        traffic_conditions = random.choice(["light", "moderate", "heavy"])
        traffic_factors = {"light": 1.0, "moderate": 1.2, "heavy": 1.5}
        traffic_factor = traffic_factors[traffic_conditions]

        eta_minutes = calculate_eta(distance_miles, traffic_factor)
        estimated_arrival = datetime.now() + timedelta(minutes=eta_minutes)

        # Generate simulated route waypoints
        waypoints = []
        num_waypoints = min(5, max(3, int(distance_miles / 2)))  # Ensure at least 3 waypoints

        for i in range(1, num_waypoints):
            progress = i / num_waypoints
            waypoint_lat = current_lat + (dest_lat - current_lat) * progress
            waypoint_lon = current_lon + (dest_lon - current_lon) * progress
            waypoints.append(RouteWaypoint(
                latitude=waypoint_lat,
                longitude=waypoint_lon,
                instruction=f"Continue for {random.uniform(0.5, 2.0):.1f} miles"
            ))

        return RouteResponse(
            technician_id=technician_id,
            technician_name=technician["name"],
            origin=LocationInfo(latitude=current_lat, longitude=current_lon),
            destination=LocationInfo(latitude=dest_lat, longitude=dest_lon),
            distance_miles=round(distance_miles, 1),
            estimated_travel_time_minutes=eta_minutes,
            estimated_arrival=estimated_arrival.isoformat(),
            traffic_conditions=traffic_conditions,
            route_waypoints=waypoints,
            calculated_at=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating technician route: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.post("/technicians/{technician_id}/notify", response_model=StatusNotificationResponse, operation_id="notify_status_change")
async def notify_status_change(technician_id: str, request: StatusNotificationRequest, api_key: str = None):
    """Send proactive status change notification for an appointment

    Args:
        technician_id: Unique identifier for the technician (e.g., "TECH001")
        request: StatusNotificationRequest containing:
            - appointment_id: Unique identifier for the appointment (e.g., "APPT001")
            - status_message: Optional custom status message
    """
    verify_api_key(api_key)
    try:
        technicians_data = get_technicians_data()
        if technician_id not in technicians_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Technician not found: {technician_id}"
            )

        technician = technicians_data[technician_id]

        # Generate appropriate status message based on current status
        if not request.status_message:
            tech_status = technician["status"]
            name = technician["name"]

            if tech_status == "en_route":
                eta_str = ""
                if technician.get("estimated_arrival"):
                    try:
                        arrival_time = datetime.fromisoformat(technician["estimated_arrival"])
                        eta_minutes = int((arrival_time - datetime.now()).total_seconds() / 60)
                        if eta_minutes > 0:
                            eta_str = f" ETA: {eta_minutes} minutes"
                    except ValueError:
                        pass

                status_message = f"Technician {name} is on the way to your appointment.{eta_str}"

            elif tech_status == "on_site":
                status_message = f"Technician {name} has arrived and is beginning work on your appliance."

            elif tech_status == "busy":
                status_message = f"Technician {name} is currently working on your appliance repair."

            elif tech_status == "available":
                status_message = f"Technician {name} has completed the service call."

            else:
                status_message = f"Status update: Technician {name} status is now {tech_status}."
        else:
            status_message = request.status_message

        response_data = {
            "success": True,
            "appointment_id": request.appointment_id,
            "technician_id": technician_id,
            "technician_name": technician["name"],
            "current_status": technician["status"],
            "message": status_message,
            "timestamp": datetime.now().isoformat(),
            "estimated_arrival": technician.get("estimated_arrival")
        }

        # Add location info if technician is en route
        if technician["status"] == "en_route":
            response_data["current_location"] = LocationInfo(
                latitude=technician["current_location"][0],
                longitude=technician["current_location"][1]
            )

        return StatusNotificationResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending status notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


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
        port=8003,
        log_level="info"
    )


if __name__ == "__main__":
    main()
