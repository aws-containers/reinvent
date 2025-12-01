"""
Technician Tracking MCP Server

This server provides technician location and status management functionality
for the Insurance Agent ChatBot system. It handles real-time location simulation,
technician availability checking, and status tracking operations.
"""

import json
import logging
import math
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
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

from shared.models import Technician, TechnicianStatus
from shared.utils import generate_id, parse_datetime


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastMCP server instance for streamable-http transport
mcp = FastMCP("technician-tracking-server")

# Import shared data storage
from .shared_data import load_mock_data, get_technicians_data


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the distance between two GPS coordinates using Haversine formula.

    Args:
        lat1, lon1: Latitude and longitude of first point
        lat2, lon2: Latitude and longitude of second point

    Returns:
        Distance in miles
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    # Radius of earth in miles
    r = 3956

    return c * r


def calculate_eta(distance_miles: float, traffic_factor: float = 1.2) -> int:
    """
    Calculate estimated time of arrival in minutes.

    Args:
        distance_miles: Distance to travel in miles
        traffic_factor: Traffic multiplier (1.0 = no traffic, 1.5 = heavy traffic)

    Returns:
        ETA in minutes
    """
    # Assume average speed of 25 mph in city traffic
    base_speed_mph = 25
    adjusted_speed = base_speed_mph / traffic_factor

    # Convert to minutes
    eta_hours = distance_miles / adjusted_speed
    eta_minutes = int(eta_hours * 60)

    # Add some randomness for realism (±5 minutes)
    eta_minutes += random.randint(-5, 5)

    return max(eta_minutes, 5)  # Minimum 5 minutes


def simulate_location_update(technician: Dict[str, Any], destination: Optional[Tuple[float, float]] = None) -> Tuple[float, float]:
    """
    Simulate technician location update based on their status.

    Args:
        technician: Technician data dictionary
        destination: Optional destination coordinates for en_route technicians

    Returns:
        Updated (latitude, longitude) coordinates
    """
    current_lat, current_lon = technician["current_location"]
    status = technician["status"]

    if status == "available":
        # Small random movement within service area (±0.01 degrees ≈ 0.7 miles)
        new_lat = current_lat + random.uniform(-0.01, 0.01)
        new_lon = current_lon + random.uniform(-0.01, 0.01)

    elif status == "en_route" and destination:
        # Move towards destination
        dest_lat, dest_lon = destination

        # Calculate direction and move 10% of the way there
        lat_diff = dest_lat - current_lat
        lon_diff = dest_lon - current_lon

        new_lat = current_lat + (lat_diff * 0.1)
        new_lon = current_lon + (lon_diff * 0.1)

    else:
        # On site or busy - stay at current location with minimal drift
        new_lat = current_lat + random.uniform(-0.001, 0.001)
        new_lon = current_lon + random.uniform(-0.001, 0.001)

    return new_lat, new_lon


@mcp.resource("technician://status")
def technician_status() -> str:
    """Access to technician status information"""
    return "Technician status and availability data"

@mcp.resource("technician://locations")
def technician_locations() -> str:
    """Real-time technician location tracking"""
    return "GPS location and tracking data"

@mcp.resource("technician://routes")
def technician_routes() -> str:
    """Technician routing and ETA information"""
    return "Route planning and travel time data"

@mcp.tool()
def list_all_technicians(status_filter: str = "all") -> str:
    """List all technicians in the system with optional status filtering

    Args:
        status_filter: Filter technicians by status. Valid values: "all", "available", "en_route", "on_site", "busy", "off_duty"
    """
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

        # Return simplified technician list
        technician_list = [{
            "technician_id": tech["id"],
            "name": tech["name"],
            "status": tech["status"],
            "specialties": tech["specialties"],
            "phone": tech["phone"],
            "current_appointment_id": tech.get("current_appointment_id"),
            "current_location": {
                "latitude": tech["current_location"][0],
                "longitude": tech["current_location"][1]
            }
        } for tech in all_technicians]

        return json.dumps({
            "total_technicians": len(technician_list),
            "status_filter": status_filter,
            "technicians": technician_list
        }, indent=2)

    except Exception as e:
        logger.error(f"Error listing all technicians: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_technician_status(technician_id: str) -> str:
    """Get current status and basic information for a specific technician

    Args:
        technician_id: Unique identifier for the technician (e.g., "TECH001")
    """
    try:
        technicians_data = get_technicians_data()
        if technician_id not in technicians_data:
            return json.dumps({
                "error": "Technician not found",
                "technician_id": technician_id
            })

        technician = technicians_data[technician_id]

        status_info = {
            "technician_id": technician["id"],
            "name": technician["name"],
            "status": technician["status"],
            "specialties": technician["specialties"],
            "phone": technician["phone"],
            "current_appointment_id": technician.get("current_appointment_id"),
            "estimated_arrival": technician.get("estimated_arrival"),
            "last_updated": datetime.now().isoformat()
        }

        return json.dumps(status_info, indent=2)

    except Exception as e:
        logger.error(f"Error getting technician status: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_technician_location(technician_id: str) -> str:
    """Get real-time GPS location and ETA information for a technician

    Args:
        technician_id: Unique identifier for the technician (e.g., "TECH001")
    """
    try:
        technicians_data = get_technicians_data()
        if technician_id not in technicians_data:
            return json.dumps({
                "error": "Technician not found",
                "technician_id": technician_id
            })

        technician = technicians_data[technician_id]

        # Simulate location update
        new_location = simulate_location_update(technician)
        technician["current_location"] = list(new_location)

        location_info = {
            "technician_id": technician["id"],
            "name": technician["name"],
            "current_location": {
                "latitude": new_location[0],
                "longitude": new_location[1]
            },
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
                    location_info["eta_minutes"] = eta_minutes
                else:
                    location_info["eta_minutes"] = 0
                    location_info["status_note"] = "Should have arrived"
            except ValueError:
                pass

        return json.dumps(location_info, indent=2)

    except Exception as e:
        logger.error(f"Error getting technician location: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def list_available_technicians(area: str, datetime_str: str, specialties: List[str]) -> str:
    """Find available technicians in a specific area with required specialties

    Args:
        area: Service area to search (e.g., "Chicago", "Denver")
        datetime_str: Requested datetime in ISO format (e.g., "2025-09-05T08:00:00")
        specialties: List of required specialties (e.g., ["refrigerator", "washing_machine"])
    """
    try:
        # Parse the datetime
        try:
            requested_datetime = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except ValueError:
            return json.dumps({
                "error": "Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            })

        available_technicians = []
        technicians_data = get_technicians_data()

        for tech_id, technician in technicians_data.items():
            # Check if technician is available
            if technician["status"] != "available":
                continue

            # Check if technician has required specialties
            tech_specialties = [spec.lower() for spec in technician["specialties"]]
            required_specialties = [spec.lower() for spec in specialties]

            if not any(req_spec in tech_specialties for req_spec in required_specialties):
                continue

            # For demo purposes, assume all technicians can serve the requested area
            # In a real system, this would check geographic boundaries

            # Calculate simulated distance (random for demo)
            distance_miles = random.uniform(2.0, 15.0)
            eta_minutes = calculate_eta(distance_miles)

            available_tech = {
                "technician_id": technician["id"],
                "name": technician["name"],
                "specialties": technician["specialties"],
                "phone": technician["phone"],
                "current_location": {
                    "latitude": technician["current_location"][0],
                    "longitude": technician["current_location"][1]
                },
                "distance_miles": round(distance_miles, 1),
                "eta_minutes": eta_minutes,
                "estimated_arrival": (requested_datetime + timedelta(minutes=eta_minutes)).isoformat(),
                "profile": technician.get("profile", {})
            }

            available_technicians.append(available_tech)

        # Sort by ETA (closest first)
        available_technicians.sort(key=lambda x: x["eta_minutes"])

        result = {
            "area": area,
            "requested_datetime": datetime_str,
            "required_specialties": specialties,
            "available_technicians": available_technicians,
            "total_found": len(available_technicians)
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error listing available technicians: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def update_technician_status(technician_id: str, new_status: str, location: Optional[List[float]] = None, appointment_id: Optional[str] = None) -> str:
    """Update technician status and optionally location and appointment assignment

    Args:
        technician_id: Unique identifier for the technician (e.g., "TECH001")
        new_status: New status for the technician. Valid values: "available", "en_route", "on_site", "busy", "off_duty"
        location: Optional location coordinates [latitude, longitude]
        appointment_id: Optional appointment identifier (e.g., "APPT001")
    """
    try:
        technicians_data = get_technicians_data()
        if technician_id not in technicians_data:
            return json.dumps({
                "error": "Technician not found",
                "technician_id": technician_id
            })

        # Validate status
        valid_statuses = ["available", "en_route", "on_site", "busy", "off_duty"]
        if new_status not in valid_statuses:
            return json.dumps({
                "error": f"Invalid status. Must be one of: {valid_statuses}",
                "provided_status": new_status
            })

        technician = technicians_data[technician_id]
        old_status = technician["status"]

        # Update status
        technician["status"] = new_status

        # Update location if provided
        if location and len(location) == 2:
            technician["current_location"] = location

        # Update appointment assignment
        if appointment_id:
            technician["current_appointment_id"] = appointment_id
        elif new_status == "available":
            # Clear appointment when becoming available
            technician["current_appointment_id"] = None

        # Update estimated arrival based on status
        if new_status == "en_route" and appointment_id:
            # Set estimated arrival time (simulate 30-60 minutes from now)
            eta_minutes = random.randint(30, 60)
            estimated_arrival = datetime.now() + timedelta(minutes=eta_minutes)
            technician["estimated_arrival"] = estimated_arrival.isoformat()
        elif new_status in ["available", "off_duty"]:
            technician["estimated_arrival"] = None

        result = {
            "success": True,
            "technician_id": technician_id,
            "old_status": old_status,
            "new_status": new_status,
            "updated_at": datetime.now().isoformat(),
            "current_appointment_id": technician.get("current_appointment_id"),
            "estimated_arrival": technician.get("estimated_arrival")
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error updating technician status: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_technician_route(technician_id: str, destination: List[float]) -> str:
    """Get route information and travel time to a destination

    Args:
        technician_id: Unique identifier for the technician (e.g., "TECH001")
        destination: Destination coordinates [latitude, longitude]
    """
    try:
        technicians_data = get_technicians_data()
        if technician_id not in technicians_data:
            return json.dumps({
                "error": "Technician not found",
                "technician_id": technician_id
            })

        if not destination or len(destination) != 2:
            return json.dumps({
                "error": "Invalid destination. Provide [latitude, longitude]"
            })

        technician = technicians_data[technician_id]
        current_lat, current_lon = technician["current_location"]
        dest_lat, dest_lon = destination

        # Calculate distance and ETA
        distance_miles = calculate_distance(current_lat, current_lon, dest_lat, dest_lon)

        # Simulate traffic conditions
        traffic_conditions = random.choice(["light", "moderate", "heavy"])
        traffic_factors = {"light": 1.0, "moderate": 1.2, "heavy": 1.5}
        traffic_factor = traffic_factors[traffic_conditions]

        eta_minutes = calculate_eta(distance_miles, traffic_factor)
        estimated_arrival = datetime.now() + timedelta(minutes=eta_minutes)

        # Generate simulated route waypoints (for demo purposes)
        waypoints = []
        num_waypoints = min(5, max(2, int(distance_miles / 3)))  # More waypoints for longer routes

        for i in range(1, num_waypoints):
            progress = i / num_waypoints
            waypoint_lat = current_lat + (dest_lat - current_lat) * progress
            waypoint_lon = current_lon + (dest_lon - current_lon) * progress
            waypoints.append({
                "latitude": waypoint_lat,
                "longitude": waypoint_lon,
                "instruction": f"Continue for {random.uniform(0.5, 2.0):.1f} miles"
            })

        route_info = {
            "technician_id": technician_id,
            "technician_name": technician["name"],
            "origin": {
                "latitude": current_lat,
                "longitude": current_lon
            },
            "destination": {
                "latitude": dest_lat,
                "longitude": dest_lon
            },
            "distance_miles": round(distance_miles, 1),
            "estimated_travel_time_minutes": eta_minutes,
            "estimated_arrival": estimated_arrival.isoformat(),
            "traffic_conditions": traffic_conditions,
            "route_waypoints": waypoints,
            "calculated_at": datetime.now().isoformat()
        }

        return json.dumps(route_info, indent=2)

    except Exception as e:
        logger.error(f"Error calculating technician route: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def notify_status_change(technician_id: str, appointment_id: str, status_message: Optional[str] = None) -> str:
    """Send proactive status change notification for an appointment

    Args:
        technician_id: Unique identifier for the technician (e.g., "TECH001")
        appointment_id: Unique identifier for the appointment (e.g., "APPT001")
        status_message: Optional custom status message
    """
    try:
        technicians_data = get_technicians_data()
        if technician_id not in technicians_data:
            return json.dumps({
                "error": "Technician not found",
                "technician_id": technician_id
            })

        technician = technicians_data[technician_id]

        # Generate appropriate status message based on current status
        if not status_message:
            status = technician["status"]
            name = technician["name"]

            if status == "en_route":
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

            elif status == "on_site":
                status_message = f"Technician {name} has arrived and is beginning work on your appliance."

            elif status == "busy":
                status_message = f"Technician {name} is currently working on your appliance repair."

            elif status == "available":
                status_message = f"Technician {name} has completed the service call."

            else:
                status_message = f"Status update: Technician {name} status is now {status}."

        notification = {
            "success": True,
            "appointment_id": appointment_id,
            "technician_id": technician_id,
            "technician_name": technician["name"],
            "current_status": technician["status"],
            "message": status_message,
            "timestamp": datetime.now().isoformat(),
            "estimated_arrival": technician.get("estimated_arrival")
        }

        # Add location info if technician is en route
        if technician["status"] == "en_route":
            notification["current_location"] = {
                "latitude": technician["current_location"][0],
                "longitude": technician["current_location"][1]
            }

        return json.dumps(notification, indent=2)

    except Exception as e:
        logger.error(f"Error sending status notification: {e}")
        return json.dumps({"error": str(e)})


def main():
    """Main server entry point."""
    # Load mock data on startup
    load_mock_data()

    # Configure server to run on all IP addresses on port 8003
    mcp.settings.host = '0.0.0.0'
    mcp.settings.port = 8003

    # Run the server with streamable-http transport
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
