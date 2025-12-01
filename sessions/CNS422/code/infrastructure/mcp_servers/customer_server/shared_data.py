"""
Shared data storage for Customer Information Server

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
customers_data: Dict[str, Dict] = {}
claims_data: Dict[str, Dict] = {}

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

CUSTOMERS_FILE = _find_data_file("customers.json")
CLAIMS_FILE = _find_data_file("claims.json")


def load_mock_data() -> None:
    """Load mock data from JSON files into memory."""
    global customers_data, claims_data

    try:
        # Load customers
        with open(CUSTOMERS_FILE, 'r') as f:
            customer_file_data = json.load(f)
            customers_data = {
                customer['id']: customer
                for customer in customer_file_data.get('customers', [])
            }

        # Load claims
        with open(CLAIMS_FILE, 'r') as f:
            claims_file_data = json.load(f)
            claims_data = {
                claim['id']: claim
                for claim in claims_file_data.get('claims', [])
            }

        logger.info(f"Loaded {len(customers_data)} customers and {len(claims_data)} claims")

    except Exception as e:
        logger.error(f"Error loading mock data: {e}")
        customers_data = {}
        claims_data = {}


def get_customers_data() -> Dict[str, Dict]:
    """Get the customers data dictionary."""
    return customers_data


def get_claims_data() -> Dict[str, Dict]:
    """Get the claims data dictionary."""
    return claims_data
