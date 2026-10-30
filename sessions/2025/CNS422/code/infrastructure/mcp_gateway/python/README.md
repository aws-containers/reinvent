# MCP Gateway Python Tools

This package provides tools for setting up and testing AWS Bedrock AgentCore MCP Gateway infrastructure.

## Prerequisites

- Python 3.13+
- AWS CLI configured with appropriate permissions
- `DOMAIN_NAME` environment variable set to your EKS REST API domain

## Installation

```bash
# Create virtual environment with Python 3.13
uv venv --python 3.13

# Activate virtual environment
source .venv/bin/activate

# Install package in development mode
uv pip install -e .
```

## Available Scripts

### 1. Setup MCP Gateway Infrastructure

```bash
mcp-gateway-setup [--rest-api-domain DOMAIN] [--rest-api-env ENV]
```

Creates or updates the complete MCP Gateway infrastructure including:

- IAM roles for AgentCore Gateway
- Cognito User Pool, Resource Server, and M2M Client
- Bedrock AgentCore Gateway
- API Key Credential Provider
- Gateway Targets for appointment, customer, and technician services
- S3 bucket with OpenAPI specifications

**Options:**

- `--rest-api-domain`: REST API domain (default: from DOMAIN_NAME env var)
- `--rest-api-env`: Environment suffix (default: dev)

### 2. Test MCP Gateway with AI Agent

```bash
mcp-gateway-test
```

Runs a comprehensive test using the Strands AI Agent framework:

- Sets up or retrieves gateway credentials
- Creates MCP client connection
- Tests tool listing and customer queries
- Demonstrates end-to-end functionality

### 3. Test Gateway Connection

```bash
mcp-gateway-test-connection [--prefix PREFIX]
```

Performs a lightweight connection test:

- Verifies gateway exists
- Tests Cognito token retrieval
- Validates basic connectivity
- Quick health check without full agent setup

**Options:**

- `--prefix`: Resource prefix (default: reinvent)

### 4. Cleanup Scripts

```bash
# Delete specific resources
delete-s3-bucket
delete-cognito
delete-credential-provider
delete-gateway-targets
delete-gateway
```

## Usage Examples

### Complete Setup and Test

```bash
# Set up infrastructure
export DOMAIN_NAME="your-domain.com"
mcp-gateway-setup

# Test with AI agent
mcp-gateway-test

# Quick connection test
mcp-gateway-test-connection
```

### Development Workflow

```bash
# Quick connection check
mcp-gateway-test-connection

# If connection fails, run setup
mcp-gateway-setup

# Test full functionality
mcp-gateway-test
```

## Makefile Integration

For easier usage, use the Makefile targets from the project root:

```bash
# Setup environment and infrastructure
make setup-mcp-gateway-env
make setup-mcp-gateway

# Run tests
make test-mcp-gateway-connection
make test-mcp-gateway

# Get help
make setup-mcp-gateway-help
```

See the main [README.md](../../../README.md#-mcp-gateway-testing) for comprehensive testing documentation.

## Environment Variables

- `DOMAIN_NAME`: Required. Your EKS REST API domain
- `REST_API_ENV`: Optional. Environment suffix (default: dev)

## Architecture

The MCP Gateway provides a unified interface to three backend services:

- **Customer Service**: Claims and policy management
- **Appointment Service**: Scheduling and appointment management
- **Technician Service**: Technician tracking and status

Each service is exposed through both MCP protocol and REST API endpoints.

## Troubleshooting

### Python Version Issues

Ensure you're using Python 3.13+:

```bash
python3.13 --version
uv venv --python 3.13
```

### AWS Permissions

Ensure your AWS credentials have permissions for:

- IAM role creation and management
- Cognito User Pool operations
- Bedrock AgentCore Gateway operations
- S3 bucket operations

### Domain Configuration

Verify your DOMAIN_NAME environment variable:

```bash
echo $DOMAIN_NAME
```

The domain should point to your EKS cluster where the REST APIs are deployed.
