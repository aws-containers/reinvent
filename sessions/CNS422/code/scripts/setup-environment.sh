#!/bin/bash

# Environment Setup Script for Insurance Agent ChatBot Demo
# This script helps set up the required environment variables and validates the configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to validate domain format
validate_domain() {
    local domain=$1
    if [[ $domain =~ ^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}$ ]]; then
        return 0
    else
        return 1
    fi
}

echo "🚀 Insurance Agent ChatBot Demo - Environment Setup"
echo "=================================================="
echo ""

# Check for required tools
print_status "Checking required tools..."

MISSING_TOOLS=()

if ! command_exists "aws"; then
    MISSING_TOOLS+=("aws-cli")
fi

if ! command_exists "terraform"; then
    MISSING_TOOLS+=("terraform")
fi

if ! command_exists "kubectl"; then
    MISSING_TOOLS+=("kubectl")
fi

if ! command_exists "uv"; then
    MISSING_TOOLS+=("uv")
fi

if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
    print_error "Missing required tools: ${MISSING_TOOLS[*]}"
    echo ""
    echo "Please install the missing tools and run this script again."
    echo "Installation guides:"
    echo "  - AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    echo "  - Terraform: https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli"
    echo "  - kubectl: https://kubernetes.io/docs/tasks/tools/"
    echo "  - uv: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

print_success "All required tools are installed"

# Check AWS credentials
print_status "Checking AWS credentials..."
if aws sts get-caller-identity >/dev/null 2>&1; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    REGION=$(aws configure get region || echo "us-west-2")
    print_success "AWS credentials configured (Account: $ACCOUNT_ID, Region: $REGION)"
else
    print_error "AWS credentials not configured"
    echo "Please run 'aws configure' to set up your credentials"
    exit 1
fi

# Domain configuration
echo ""
print_status "Domain Configuration"
echo "===================="

if [ -z "$DOMAIN_NAME" ]; then
    echo ""
    print_warning "DOMAIN_NAME environment variable is not set"
    echo ""
    echo "Please enter your domain name (e.g., example.com):"
    read -r DOMAIN_INPUT

    if [ -z "$DOMAIN_INPUT" ]; then
        print_error "Domain name cannot be empty"
        exit 1
    fi

    if ! validate_domain "$DOMAIN_INPUT"; then
        print_error "Invalid domain format: $DOMAIN_INPUT"
        echo "Please enter a valid domain name (e.g., example.com)"
        exit 1
    fi

    export DOMAIN_NAME="$DOMAIN_INPUT"
    echo ""
    print_success "Domain set to: $DOMAIN_NAME"

    # Ask if user wants to persist this
    echo ""
    echo "Would you like to add this to your shell profile? (y/n)"
    read -r PERSIST_CHOICE

    if [[ $PERSIST_CHOICE =~ ^[Yy]$ ]]; then
        SHELL_PROFILE=""
        if [ -f "$HOME/.zshrc" ]; then
            SHELL_PROFILE="$HOME/.zshrc"
        elif [ -f "$HOME/.bashrc" ]; then
            SHELL_PROFILE="$HOME/.bashrc"
        elif [ -f "$HOME/.bash_profile" ]; then
            SHELL_PROFILE="$HOME/.bash_profile"
        fi

        if [ -n "$SHELL_PROFILE" ]; then
            echo "export DOMAIN_NAME=$DOMAIN_NAME" >> "$SHELL_PROFILE"
            print_success "Added DOMAIN_NAME to $SHELL_PROFILE"
            print_warning "Please run 'source $SHELL_PROFILE' or restart your terminal"
        else
            print_warning "Could not detect shell profile. Please manually add: export DOMAIN_NAME=$DOMAIN_NAME"
        fi
    fi
else
    if ! validate_domain "$DOMAIN_NAME"; then
        print_error "Invalid domain format in DOMAIN_NAME: $DOMAIN_NAME"
        exit 1
    fi
    print_success "Using domain from environment: $DOMAIN_NAME"
fi

# Environment selection
echo ""
print_status "Environment Configuration"
echo "========================="

if [ -z "$REST_API_ENV" ]; then
    echo ""
    echo "Select environment (default: dev):"
    echo "1) development"
    echo "2) production"
    echo ""
    read -r ENV_CHOICE

    case $ENV_CHOICE in
        2)
            export REST_API_ENV="production"
            ;;
        *)
            export REST_API_ENV="development"
            ;;
    esac
fi

print_success "Using environment: $REST_API_ENV"

# Update environment files
echo ""
print_status "Updating environment configuration files..."

# Update .env.demo
if [ -f ".env.demo" ]; then
    if grep -q "DOMAIN_NAME=" .env.demo; then
        sed -i.backup "s/DOMAIN_NAME=.*/DOMAIN_NAME=$DOMAIN_NAME/" .env.demo
        rm -f .env.demo.backup
    else
        echo "DOMAIN_NAME=$DOMAIN_NAME" >> .env.demo
    fi
    print_success "Updated .env.demo"
fi

# Update .env.development
if [ -f ".env.development" ]; then
    if grep -q "DOMAIN_NAME=" .env.development; then
        sed -i.backup "s/DOMAIN_NAME=.*/DOMAIN_NAME=$DOMAIN_NAME/" .env.development
        rm -f .env.development.backup
    else
        echo "DOMAIN_NAME=$DOMAIN_NAME" >> .env.development
    fi
    print_success "Updated .env.development"
fi

# Create terraform.tfvars if it doesn't exist
echo ""
print_status "Terraform configuration..."

if [ ! -f "infrastructure/terraform/terraform.tfvars" ]; then
    if [ -f "infrastructure/terraform/terraform.tfvars.example" ]; then
        cp infrastructure/terraform/terraform.tfvars.example infrastructure/terraform/terraform.tfvars
        sed -i.backup "s/domain_name = .*/domain_name = \"$DOMAIN_NAME\"/" infrastructure/terraform/terraform.tfvars
        rm -f infrastructure/terraform/terraform.tfvars.backup
        print_success "Created terraform.tfvars with your domain"
    else
        print_warning "terraform.tfvars.example not found, creating basic terraform.tfvars"
        cat > infrastructure/terraform/terraform.tfvars << EOF
# Terraform Variables Configuration
domain_name = "$DOMAIN_NAME"
region = "$REGION"
cluster_name = "eks-cluster"
kubernetes_version = "1.33"
vpc_cidr = "10.0.0.0/16"
number_availability_zones = 2
node_pools = ["general-purpose", "system"]
EOF
        print_success "Created terraform.tfvars"
    fi
else
    print_success "terraform.tfvars already exists"
fi

# Validate Route53 hosted zone
echo ""
print_status "Validating Route53 hosted zone..."

if aws route53 list-hosted-zones --query "HostedZones[?Name=='$DOMAIN_NAME.']" --output text | grep -q "$DOMAIN_NAME"; then
    print_success "Route53 hosted zone found for $DOMAIN_NAME"
else
    print_warning "Route53 hosted zone not found for $DOMAIN_NAME"
    echo ""
    echo "You need to create a Route53 hosted zone for your domain."
    echo "You can create it manually in the AWS Console or run:"
    echo "  aws route53 create-hosted-zone --name $DOMAIN_NAME --caller-reference \$(date +%s)"
    echo ""
    echo "Would you like to create it now? (y/n)"
    read -r CREATE_ZONE

    if [[ $CREATE_ZONE =~ ^[Yy]$ ]]; then
        CALLER_REF=$(date +%s)
        if aws route53 create-hosted-zone --name "$DOMAIN_NAME" --caller-reference "$CALLER_REF" >/dev/null 2>&1; then
            print_success "Created Route53 hosted zone for $DOMAIN_NAME"
        else
            print_error "Failed to create Route53 hosted zone"
            echo "Please create it manually in the AWS Console"
        fi
    fi
fi

# Summary
echo ""
echo "🎉 Environment Setup Complete!"
echo "=============================="
echo ""
echo "Configuration Summary:"
echo "  Domain Name: $DOMAIN_NAME"
echo "  Environment: $REST_API_ENV"
echo "  AWS Account: $ACCOUNT_ID"
echo "  AWS Region: $REGION"
echo ""
echo "Next Steps:"
echo "1. Deploy infrastructure: make terraform-init && make terraform-apply"
echo "2. Deploy applications: make deploy-all"
echo "3. Setup MCP Gateway: make setup-mcp-gateway"
echo ""
echo "Environment variables set for this session:"
echo "  export DOMAIN_NAME=$DOMAIN_NAME"
echo "  export REST_API_ENV=$REST_API_ENV"
echo ""
print_success "Ready to deploy! 🚀"
