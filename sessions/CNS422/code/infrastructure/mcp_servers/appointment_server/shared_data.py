"""
Shared data storage for Appointment Management Server

This module provides shared access to appointment and technician data
for both MCP and REST interfaces to ensure data consistency.
"""

import json
import logging
from pathlib import Path
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Shared in-memory storage
_appointments_data: Dict[str, Dict] = {}
_technicians_data: Dict[str, Dict] = {}

# Data file paths - try multiple possible locations
def _find_data_file(filename: str) -> Path:
    """Find data file in possible locations."""
    possible_paths = [
        Path(__file__).parent.parent.parent / "mock_data" / filename,  # Standard structure
        Path("/app/mock_data") / filename,  # Docker container structure
        Path("mock_data") / filename,  # Current directory
        Path(__file__).parent / "mock_data" / filename,  # Local mock_data
    ]

    for path in possible_paths:
        if path.exists():
            return path

    # Return the first path as fallback
    return possible_paths[0]

APPOINTMENTS_FILE = _find_data_file("appointments.json")
TECHNICIANS_FILE = _find_data_file("technicians.json")


def load_mock_data() -> None:
    """Load mock data from JSON files into shared memory storage."""
    global _appointments_data, _technicians_data

    try:
        # Load appointments
        with open(APPOINTMENTS_FILE, 'r') as f:
            appointment_file_data = json.load(f)
            _appointments_data = {
                appointment['id']: appointment
                for appointment in appointment_file_data.get('appointments', [])
            }

        # Load technicians
        with open(TECHNICIANS_FILE, 'r') as f:
            technician_file_data = json.load(f)
            _technicians_data = {
                technician['id']: technician
                for technician in technician_file_data.get('technicians', [])
            }

        logger.info(f"Loaded {len(_appointments_data)} appointments and {len(_technicians_data)} technicians")

    except Exception as e:
        logger.error(f"Error loading mock data: {e}")
        _appointments_data = {}
        _technicians_data = {}


def get_appointments_data() -> Dict[str, Dict]:
    """Get shared appointments data."""
    return _appointments_data


def get_technicians_data() -> Dict[str, Dict]:
    """Get shared technicians data."""
    return _technicians_data


def set_appointments_data(data: Dict[str, Dict]) -> None:
    """Set shared appointments data."""
    global _appointments_data
    _appointments_data = data


def set_technicians_data(data: Dict[str, Dict]) -> None:
    """Set shared technicians data."""
    global _technicians_data
    _technicians_data = data
