"""
FastAPI REST interface for Customer Information Server

This module provides HTTP REST endpoints that mirror the MCP tool functionality
for customer profile management, policy information, and claim operations.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import uuid4

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, ConfigDict
import uvicorn

from shared.models import Customer, Claim, ClaimStatus, UrgencyLevel
from shared.utils import generate_id, parse_datetime

# Import shared data storage
from .shared_data import load_mock_data, get_customers_data, get_claims_data


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
    title="Customer Information Server REST API",
    description="REST API for customer profile management, policy information, and claim operations",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# Pydantic models for request/response validation
class CustomerProfileResponse(BaseModel):
    """Response model for customer profile information"""
    id: str
    name: str
    email: str
    phone: str
    address: str
    policy_number: str
    covered_appliances: List[str]
    created_at: str


class PolicyDetailsResponse(BaseModel):
    """Response model for policy details"""
    customer_id: str
    policy_number: str
    covered_appliances: List[str]
    policy_details: Dict[str, Any] = {}
    active: bool = True


class CreateClaimRequest(BaseModel):
    """Request model for creating a new claim"""
    customer_id: str = Field(..., description="Customer ID")
    appliance_type: str = Field(..., min_length=1, description="Type of appliance")
    issue_description: str = Field(..., min_length=5, description="Description of the issue")
    urgency_level: str = Field(..., description="Urgency level: low, medium, high, emergency")

    @field_validator('urgency_level')
    @classmethod
    def validate_urgency_level(cls, v):
        valid_levels = ['low', 'medium', 'high', 'emergency']
        if v.lower() not in valid_levels:
            raise ValueError(f'Urgency level must be one of: {", ".join(valid_levels)}')
        return v.lower()


class CreateClaimResponse(BaseModel):
    """Response model for claim creation"""
    success: bool
    claim_id: str
    status: str
    message: str
    claim: Dict[str, Any]


class ClaimHistoryResponse(BaseModel):
    """Response model for claim history"""
    customer_id: str
    total_claims: int
    status_filter: str
    claims: List[Dict[str, Any]]


class ClaimDetailsResponse(BaseModel):
    """Response model for claim details"""
    id: str
    customer_id: str
    appliance_type: str
    issue_description: str
    status: str
    urgency_level: str
    created_at: str
    approved_at: Optional[str] = None
    completed_at: Optional[str] = None
    appointment_id: Optional[str] = None
    estimated_cost: Optional[float] = None
    notes: Optional[str] = None


class UpdateClaimStatusRequest(BaseModel):
    """Request model for updating claim status"""
    new_status: str = Field(..., description="New status for the claim")
    notes: Optional[str] = Field(None, description="Optional notes for the status update")

    @field_validator('new_status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ['submitted', 'under_review', 'approved', 'rejected', 'completed']
        if v.lower() not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v.lower()


class UpdateClaimStatusResponse(BaseModel):
    """Response model for claim status update"""
    success: bool
    claim_id: str
    old_status: str
    new_status: str
    updated_at: str
    claim: Dict[str, Any]


class CoverageCheckRequest(BaseModel):
    """Request model for checking appliance coverage"""
    appliance_type: str = Field(..., min_length=1, description="Type of appliance to check")


class CoverageCheckResponse(BaseModel):
    """Response model for coverage check"""
    customer_id: str
    appliance_type: str
    is_covered: bool
    covered_appliances: List[str]
    policy_info: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(exclude_none=True)


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str
    detail: Optional[str] = None





# Startup event is now handled by lifespan context manager


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "customer-info-server"}


@app.get("/customers", response_model=List[CustomerProfileResponse], operation_id="list_all_customers")
async def list_all_customers(api_key: str = None):
    """List all customers in the system

    Args:
        None
    """
    verify_api_key(api_key)
    try:
        customers_data = get_customers_data()
        all_customers = list(customers_data.values())

        # Sort by id
        all_customers.sort(key=lambda x: x["id"])

        # Return simplified customer list
        customer_list = [
            CustomerProfileResponse(
                id=customer["id"],
                name=customer["name"],
                email=customer["email"],
                phone=customer["phone"],
                address=customer["address"],
                policy_number=customer["policy_number"],
                covered_appliances=customer["covered_appliances"],
                created_at=customer["created_at"]
            ) for customer in all_customers
        ]

        return customer_list

    except Exception as e:
        logger.error(f"Error listing all customers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/claims", response_model=List[ClaimDetailsResponse], operation_id="list_all_claims")
async def list_all_claims(api_key: str = None, status_filter: str = "all"):
    """List all claims in the system with optional status filtering

    Args:
        status_filter: Filter claims by status. Valid values: "all", "active", "completed", "submitted", "under_review", "approved", "rejected"
    """
    verify_api_key(api_key)
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

        return [ClaimDetailsResponse(**claim) for claim in all_claims]

    except Exception as e:
        logger.error(f"Error listing all claims: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/customers/{customer_id}/profile", response_model=CustomerProfileResponse, operation_id="get_customer_profile")
async def get_customer_profile(customer_id: str, api_key: str = None):
    """Retrieve customer profile information by customer ID

    Args:
        customer_id: Unique identifier for the customer (e.g., "CUST001")
    """
    verify_api_key(api_key)
    try:
        customers_data = get_customers_data()
        if customer_id not in customers_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer not found: {customer_id}"
            )

        customer = customers_data[customer_id]

        # Return customer profile without policy details
        profile = CustomerProfileResponse(
            id=customer["id"],
            name=customer["name"],
            email=customer["email"],
            phone=customer["phone"],
            address=customer["address"],
            policy_number=customer["policy_number"],
            covered_appliances=customer["covered_appliances"],
            created_at=customer["created_at"]
        )

        return profile

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/customers/{customer_id}/policy", response_model=PolicyDetailsResponse, operation_id="get_policy_details")
async def get_policy_details(customer_id: str, api_key: str = None):
    """Get insurance policy details and coverage information

    Args:
        customer_id: Unique identifier for the customer (e.g., "CUST001")
    """
    verify_api_key(api_key)
    try:
        customers_data = get_customers_data()
        if customer_id not in customers_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer not found: {customer_id}"
            )

        customer = customers_data[customer_id]

        policy_info = PolicyDetailsResponse(
            customer_id=customer["id"],
            policy_number=customer["policy_number"],
            covered_appliances=customer["covered_appliances"],
            policy_details=customer.get("policy_details", {}),
            active=True  # Simplified for demo
        )

        return policy_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting policy details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.post("/customers/{customer_id}/validate-coverage", response_model=CoverageCheckResponse, operation_id="check_coverage")
async def check_appliance_coverage(customer_id: str, request: CoverageCheckRequest, api_key: str = None):
    """Check if an appliance is covered under customer's policy

    Args:
        customer_id: Unique identifier for the customer (e.g., "CUST001")
        request: CoverageCheckRequest containing:
            - appliance_type: Type of appliance to check (e.g., "refrigerator", "washing_machine", "dryer", "dishwasher")
    """
    verify_api_key(api_key)
    try:
        customers_data = get_customers_data()
        if customer_id not in customers_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer not found: {customer_id}"
            )

        customer = customers_data[customer_id]
        covered_appliances = customer["covered_appliances"]

        is_covered = request.appliance_type.lower() in [app.lower() for app in covered_appliances]

        if is_covered:
            policy_details = customer.get("policy_details", {})
            policy_info = {
                "coverage_type": policy_details.get("coverage_type"),
                "deductible": policy_details.get("deductible"),
                "annual_limit": policy_details.get("annual_limit")
            }
            result = CoverageCheckResponse(
                customer_id=customer_id,
                appliance_type=request.appliance_type,
                is_covered=is_covered,
                covered_appliances=covered_appliances,
                policy_info=policy_info
            )
        else:
            result = CoverageCheckResponse(
                customer_id=customer_id,
                appliance_type=request.appliance_type,
                is_covered=is_covered,
                covered_appliances=covered_appliances
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking appliance coverage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.post("/claims", response_model=CreateClaimResponse)
async def create_claim(request: CreateClaimRequest, api_key: str = None):
    """Create a new insurance claim for appliance repair

    Args:
        request: CreateClaimRequest containing:
            - customer_id: Unique identifier for the customer (e.g., "CUST001")
            - appliance_type: Type of appliance (e.g., "refrigerator", "washing_machine", "dryer", "dishwasher")
            - issue_description: Detailed description of the issue (minimum 5 characters)
            - urgency_level: Urgency level. Valid values: "low", "medium", "high", "emergency"
    """
    verify_api_key(api_key)
    try:
        customers_data = get_customers_data()
        claims_data = get_claims_data()

        # Validate customer exists
        if request.customer_id not in customers_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer not found: {request.customer_id}"
            )

        customer = customers_data[request.customer_id]

        # Check if appliance is covered
        if request.appliance_type.lower() not in [app.lower() for app in customer["covered_appliances"]]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Appliance '{request.appliance_type}' not covered under policy. Covered appliances: {customer['covered_appliances']}"
            )

        # Generate new claim ID (find next available ID)
        existing_ids = [int(claim_id.replace("CLAIM", "")) for claim_id in claims_data.keys() if claim_id.startswith("CLAIM")]
        next_id = max(existing_ids, default=0) + 1
        claim_id = f"CLAIM{next_id:03d}"

        # Create new claim
        new_claim = {
            "id": claim_id,
            "customer_id": request.customer_id,
            "appliance_type": request.appliance_type,
            "issue_description": request.issue_description,
            "status": "submitted",
            "urgency_level": request.urgency_level,
            "created_at": datetime.now().isoformat(),
            "approved_at": None,
            "completed_at": None,
            "appointment_id": None,
            "estimated_cost": None,
            "notes": f"Claim created for {request.appliance_type} issue"
        }

        # Store in memory
        claims_data[claim_id] = new_claim

        return CreateClaimResponse(
            success=True,
            claim_id=claim_id,
            status="submitted",
            message="Claim created successfully",
            claim=new_claim
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating claim: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/customers/{customer_id}/claims", response_model=ClaimHistoryResponse, operation_id="get_claim_history")
async def get_claim_history(customer_id: str, api_key: str = None, status_filter: str = "all"):
    """Retrieve claim history for a customer

    Args:
        customer_id: Unique identifier for the customer (e.g., "CUST001")
        status_filter: Filter claims by status. Valid values: "all", "active", "completed", "submitted", "under_review", "approved", "rejected"
    """
    verify_api_key(api_key)
    try:
        customers_data = get_customers_data()
        claims_data = get_claims_data()

        # Validate customer exists
        if customer_id not in customers_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer not found: {customer_id}"
            )

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

        return ClaimHistoryResponse(
            customer_id=customer_id,
            total_claims=len(customer_claims),
            status_filter=status_filter,
            claims=customer_claims
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting claim history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.get("/claims/{claim_id}", response_model=ClaimDetailsResponse)
async def get_claim_details(claim_id: str, api_key: str = None):
    """Get detailed information about a specific claim

    Args:
        claim_id: Unique identifier for the claim (e.g., "CLAIM001")
    """
    verify_api_key(api_key)
    try:
        claims_data = get_claims_data()
        if claim_id not in claims_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Claim not found: {claim_id}"
            )

        claim = claims_data[claim_id]

        return ClaimDetailsResponse(**claim)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting claim details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@app.put("/claims/{claim_id}/status", response_model=UpdateClaimStatusResponse)
async def update_claim_status(claim_id: str, request: UpdateClaimStatusRequest, api_key: str = None):
    """Update the status of an existing claim

    Args:
        claim_id: Unique identifier for the claim (e.g., "CLAIM001")
        request: UpdateClaimStatusRequest containing:
            - new_status: New status. Valid values: "submitted", "under_review", "approved", "rejected", "completed"
            - notes: Optional notes for the status update
    """
    verify_api_key(api_key)
    try:
        claims_data = get_claims_data()
        if claim_id not in claims_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Claim not found: {claim_id}"
            )

        claim = claims_data[claim_id]
        old_status = claim["status"]

        # Update status
        claim["status"] = request.new_status

        # Update timestamps based on status
        if request.new_status == "approved" and not claim.get("approved_at"):
            claim["approved_at"] = datetime.now().isoformat()
        elif request.new_status == "completed" and not claim.get("completed_at"):
            claim["completed_at"] = datetime.now().isoformat()

        # Add notes if provided
        if request.notes:
            if claim.get("notes"):
                claim["notes"] += f" | Status update: {request.notes}"
            else:
                claim["notes"] = f"Status update: {request.notes}"

        return UpdateClaimStatusResponse(
            success=True,
            claim_id=claim_id,
            old_status=old_status,
            new_status=request.new_status,
            updated_at=datetime.now().isoformat(),
            claim=claim
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating claim status: {e}")
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
        port=8001,
        log_level="info"
    )


if __name__ == "__main__":
    main()
