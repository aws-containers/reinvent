"""
Customer Information MCP Server

This server provides customer profile and policy management functionality
for the Insurance Agent ChatBot system. It handles customer data retrieval,
policy information, and claim management operations.
"""

import json
import logging
from datetime import datetime
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

from shared.models import Customer, Claim, ClaimStatus, UrgencyLevel
from shared.utils import generate_id, parse_datetime

# Import shared data storage
from .shared_data import load_mock_data, get_customers_data, get_claims_data

# Import FastAPI components for dual interface
from fastapi import FastAPI


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastMCP server instance for streamable-http transport
mcp = FastMCP("customer-info-server")


@mcp.resource("customer://profiles")
def customer_profiles() -> str:
    """Access to customer profile information"""
    return "Customer profile data"

@mcp.resource("customer://policies")
def customer_policies() -> str:
    """Insurance policy details and coverage"""
    return "Policy information data"

@mcp.resource("customer://claims")
def customer_claims() -> str:
    """Insurance claims and history"""
    return "Claims data"

@mcp.tool()
def list_all_customers() -> str:
    """List all customers in the system

    Args:
        None
    """
    try:
        customers_data = get_customers_data()
        all_customers = list(customers_data.values())

        # Sort by id
        all_customers.sort(key=lambda x: x["id"])

        # Return simplified customer list
        customer_list = [{
            "id": customer["id"],
            "name": customer["name"],
            "email": customer["email"],
            "phone": customer["phone"],
            "policy_number": customer["policy_number"],
            "covered_appliances": customer["covered_appliances"]
        } for customer in all_customers]

        return json.dumps({
            "total_customers": len(customer_list),
            "customers": customer_list
        }, indent=2)

    except Exception as e:
        logger.error(f"Error listing all customers: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def list_all_claims(status_filter: str = "all") -> str:
    """List all claims in the system with optional status filtering

    Args:
        status_filter: Filter claims by status. Valid values: "all", "active", "completed", "submitted", "under_review", "approved", "rejected"
    """
    try:
        claims_data = get_claims_data()
        all_claims = list(claims_data.values())

        # Apply status filter
        if status_filter != "all":
            if status_filter == "active":
                all_claims = [
                    claim for claim in all_claims
                    if claim["status"] in ["submitted", "under_review", "approved"]
                ]
            elif status_filter == "completed":
                all_claims = [
                    claim for claim in all_claims
                    if claim["status"] in ["completed", "rejected"]
                ]
            else:
                all_claims = [
                    claim for claim in all_claims
                    if claim["status"] == status_filter
                ]

        # Sort by creation date (newest first)
        all_claims.sort(key=lambda x: x["created_at"], reverse=True)

        return json.dumps({
            "total_claims": len(all_claims),
            "status_filter": status_filter,
            "claims": all_claims
        }, indent=2)

    except Exception as e:
        logger.error(f"Error listing all claims: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_customer_profile(customer_id: str) -> str:
    """Retrieve customer profile information by customer ID

    Args:
        customer_id: Unique identifier for the customer (e.g., "CUST001")
    """
    try:
        customers_data = get_customers_data()
        if customer_id not in customers_data:
            return json.dumps({
                "error": "Customer not found",
                "customer_id": customer_id
            })

        customer = customers_data[customer_id]

        # Return customer profile without policy details
        profile = {
            "id": customer["id"],
            "name": customer["name"],
            "email": customer["email"],
            "phone": customer["phone"],
            "address": customer["address"],
            "policy_number": customer["policy_number"],
            "covered_appliances": customer["covered_appliances"],
            "created_at": customer["created_at"]
        }

        return json.dumps(profile, indent=2)

    except Exception as e:
        logger.error(f"Error getting customer profile: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_policy_details(customer_id: str) -> str:
    """Get insurance policy details and coverage information

    Args:
        customer_id: Unique identifier for the customer (e.g., "CUST001")
    """
    try:
        customers_data = get_customers_data()
        if customer_id not in customers_data:
            return json.dumps({
                "error": "Customer not found",
                "customer_id": customer_id
            })

        customer = customers_data[customer_id]

        policy_info = {
            "customer_id": customer["id"],
            "policy_number": customer["policy_number"],
            "covered_appliances": customer["covered_appliances"],
            "policy_details": customer.get("policy_details", {}),
            "active": True  # Simplified for demo
        }

        return json.dumps(policy_info, indent=2)

    except Exception as e:
        logger.error(f"Error getting policy details: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def create_claim(customer_id: str, appliance_type: str, issue_description: str, urgency_level: str) -> str:
    """Create a new insurance claim for appliance repair

    Args:
        customer_id: Unique identifier for the customer (e.g., "CUST001")
        appliance_type: Type of appliance needing service (e.g., "refrigerator", "washing_machine", "dryer", "dishwasher")
        issue_description: Detailed description of the issue (minimum 5 characters)
        urgency_level: Urgency level of the claim. Valid values: "low", "medium", "high", "emergency"
    """
    try:
        customers_data = get_customers_data()
        claims_data = get_claims_data()

        # Validate customer exists
        if customer_id not in customers_data:
            return json.dumps({
                "error": "Customer not found",
                "customer_id": customer_id
            })

        customer = customers_data[customer_id]

        # Check if appliance is covered
        if appliance_type.lower() not in [app.lower() for app in customer["covered_appliances"]]:
            return json.dumps({
                "error": "Appliance not covered under policy",
                "appliance_type": appliance_type,
                "covered_appliances": customer["covered_appliances"]
            })

        # Generate new claim ID (find next available ID)
        existing_ids = [int(claim_id.replace("CLAIM", "")) for claim_id in claims_data.keys() if claim_id.startswith("CLAIM")]
        next_id = max(existing_ids, default=0) + 1
        claim_id = f"CLAIM{next_id:03d}"

        # Create new claim
        new_claim = {
            "id": claim_id,
            "customer_id": customer_id,
            "appliance_type": appliance_type,
            "issue_description": issue_description,
            "status": "submitted",
            "urgency_level": urgency_level,
            "created_at": datetime.now().isoformat(),
            "approved_at": None,
            "completed_at": None,
            "appointment_id": None,
            "estimated_cost": None,
            "notes": f"Claim created for {appliance_type} issue"
        }

        # Store in memory
        claims_data[claim_id] = new_claim

        return json.dumps({
            "success": True,
            "claim_id": claim_id,
            "status": "submitted",
            "message": "Claim created successfully",
            "claim": new_claim
        }, indent=2)

    except Exception as e:
        logger.error(f"Error creating claim: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_claim_history(customer_id: str, status_filter: str = "all") -> str:
    """Retrieve claim history for a customer

    Args:
        customer_id: Unique identifier for the customer (e.g., "CUST001")
        status_filter: Filter claims by status. Valid values: "all", "active", "completed", "submitted", "under_review", "approved", "rejected"
    """
    try:
        customers_data = get_customers_data()
        claims_data = get_claims_data()

        # Validate customer exists
        if customer_id not in customers_data:
            return json.dumps({
                "error": "Customer not found",
                "customer_id": customer_id
            })

        # Filter claims for this customer
        customer_claims = [
            claim for claim in claims_data.values()
            if claim["customer_id"] == customer_id
        ]

        # Apply status filter
        if status_filter != "all":
            if status_filter == "active":
                customer_claims = [
                    claim for claim in customer_claims
                    if claim["status"] in ["submitted", "under_review", "approved"]
                ]
            elif status_filter == "completed":
                customer_claims = [
                    claim for claim in customer_claims
                    if claim["status"] in ["completed", "rejected"]
                ]
            else:
                customer_claims = [
                    claim for claim in customer_claims
                    if claim["status"] == status_filter
                ]

        # Sort by creation date (newest first)
        customer_claims.sort(key=lambda x: x["created_at"], reverse=True)

        return json.dumps({
            "customer_id": customer_id,
            "total_claims": len(customer_claims),
            "status_filter": status_filter,
            "claims": customer_claims
        }, indent=2)

    except Exception as e:
        logger.error(f"Error getting claim history: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_claim_details(claim_id: str) -> str:
    """Get detailed information about a specific claim

    Args:
        claim_id: Unique identifier for the claim (e.g., "CLAIM001")
    """
    try:
        claims_data = get_claims_data()
        if claim_id not in claims_data:
            return json.dumps({
                "error": "Claim not found",
                "claim_id": claim_id
            })

        claim = claims_data[claim_id]
        return json.dumps(claim, indent=2)

    except Exception as e:
        logger.error(f"Error getting claim details: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def update_claim_status(claim_id: str, new_status: str, notes: Optional[str] = None) -> str:
    """Update the status of an existing claim

    Args:
        claim_id: Unique identifier for the claim (e.g., "CLAIM001")
        new_status: New status for the claim. Valid values: "submitted", "under_review", "approved", "rejected", "completed"
        notes: Optional notes for the status update
    """
    try:
        claims_data = get_claims_data()
        if claim_id not in claims_data:
            return json.dumps({
                "error": "Claim not found",
                "claim_id": claim_id
            })

        claim = claims_data[claim_id]
        old_status = claim["status"]

        # Update status
        claim["status"] = new_status

        # Update timestamps based on status
        if new_status == "approved" and not claim.get("approved_at"):
            claim["approved_at"] = datetime.now().isoformat()
        elif new_status == "completed" and not claim.get("completed_at"):
            claim["completed_at"] = datetime.now().isoformat()

        # Add notes if provided
        if notes:
            if claim.get("notes"):
                claim["notes"] += f" | Status update: {notes}"
            else:
                claim["notes"] = f"Status update: {notes}"

        return json.dumps({
            "success": True,
            "claim_id": claim_id,
            "old_status": old_status,
            "new_status": new_status,
            "updated_at": datetime.now().isoformat(),
            "claim": claim
        }, indent=2)

    except Exception as e:
        logger.error(f"Error updating claim status: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def check_appliance_coverage(customer_id: str, appliance_type: str) -> str:
    """Check if an appliance is covered under customer's policy

    Args:
        customer_id: Unique identifier for the customer (e.g., "CUST001")
        appliance_type: Type of appliance to check coverage for (e.g., "refrigerator", "washing_machine", "dryer", "dishwasher")
    """
    try:
        customers_data = get_customers_data()
        if customer_id not in customers_data:
            return json.dumps({
                "error": "Customer not found",
                "customer_id": customer_id
            })

        customer = customers_data[customer_id]
        covered_appliances = customer["covered_appliances"]

        is_covered = appliance_type.lower() in [app.lower() for app in covered_appliances]

        result = {
            "customer_id": customer_id,
            "appliance_type": appliance_type,
            "is_covered": is_covered,
            "covered_appliances": covered_appliances
        }

        if is_covered:
            policy_details = customer.get("policy_details", {})
            result["policy_info"] = {
                "coverage_type": policy_details.get("coverage_type"),
                "deductible": policy_details.get("deductible"),
                "annual_limit": policy_details.get("annual_limit")
            }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error checking appliance coverage: {e}")
        return json.dumps({"error": str(e)})


def main():
    """Main server entry point."""
    # Load mock data on startup
    load_mock_data()

    # Configure server to run on all IP addresses on port 8001
    mcp.settings.host = '0.0.0.0'
    mcp.settings.port = 8001

    # For now, run only the MCP server
    # The REST API will be available as a separate service
    # TODO: Integrate FastAPI with FastMCP when the API supports it

    # Run the server with streamable-http transport
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
