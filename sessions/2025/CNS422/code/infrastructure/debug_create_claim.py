#!/usr/bin/env python3

import asyncio
import json
import sys
sys.path.append('.')

from mcp_servers.customer_server.server import create_claim, customers_data, claims_data

# Set up test data
customers_data.clear()
claims_data.clear()

customers_data['CUST001'] = {
    "id": "CUST001",
    "name": "John Doe",
    "email": "john.doe@email.com",
    "phone": "555-123-4567",
    "address": "123 Main St, City, State 12345",
    "policy_number": "POL-2024-001",
    "covered_appliances": ["refrigerator", "washing_machine", "dishwasher"],
    "created_at": "2023-01-15T10:30:00",
    "policy_details": {
        "coverage_type": "Premium Home Appliance Protection",
        "deductible": 50,
        "annual_limit": 5000,
        "policy_start": "2023-01-15T00:00:00",
        "policy_end": "2025-01-15T00:00:00",
        "monthly_premium": 29.99
    }
}

async def test_create_claim():
    print("Testing create_claim function...")
    print(f"Initial claims_data length: {len(claims_data)}")

    result = await create_claim("CUST001", "dishwasher", "Test issue", "low")
    print(f"Result type: {type(result)}")
    print(f"Result length: {len(result)}")
    print(f"Result content: {result[0].text}")

    try:
        response_data = json.loads(result[0].text)
        print(f"Parsed response keys: {list(response_data.keys())}")
        print(f"Response data: {json.dumps(response_data, indent=2)}")
    except Exception as e:
        print(f"Error parsing JSON: {e}")

if __name__ == "__main__":
    asyncio.run(test_create_claim())
