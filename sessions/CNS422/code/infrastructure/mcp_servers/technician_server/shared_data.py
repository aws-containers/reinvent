"""
Shared data storage for Technician Tracking Server

This module provides shared in-memory storage that can be used by both
the MCP server and REST API interfaces.
"""

import json
import logging
from pathlib import Path
from typing import Dict

# Configure logging
logger = logging.getLogger(__name__)

# Shared in-memory storage for demo
technicians_data: Dict[str, Dict] = {}

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

TECHNICIANS_FILE = _find_data_file("technicians.json")


def load_mock_data() -> None:
    """Load mock data from JSON files into memory."""
    global technicians_data

    try:
        # Load technicians
        with open(TECHNICIANS_FILE, 'r') as f:
            technician_file_data = json.load(f)
            technicians_data = {
                technician['id']: technician
                for technician in technician_file_data.get('technicians', [])
            }

        logger.info(f"Loaded {len(technicians_data)} technicians")

    except Exception as e:
        logger.error(f"Error loading mock data: {e}")
        technicians_data = {}


def get_technicians_data() -> Dict[str, Dict]:
    """Get the technicians data dictionary."""
    return technicians_data
