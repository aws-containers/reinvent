#!/bin/bash

# Enhanced deployment script for Insurance Agent Demo with ECR integration
# Usage: ./deploy-with-ecr.sh [environment] [action] [terraform-dir]
# Environment: development, production
# Action: apply, delete, diff, dry-run
# Terraform-dir: path to terraform directory (default: ../terraform)

set -e

ENVIRONMENT=${1:-development}
ACTION=${2:-apply}
TERRAFORM_DIR=${3:-../terraform}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Cleanup function
cleanup() {
    if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
        print_status "Cleaning up temporary directory: $TEMP_DIR"
        rm -rf "$TEMP_DIR"
    fi
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Validate environment
case $ENVIRONMENT in
    development|dev)
        KUSTOMIZE_PATH="overlays/development"
        ;;
    production|prod)
        KUSTOMIZE_PATH="overlays/production"
        ;;
    *)
        print_error "Invalid environment: $ENVIRONMENT"
        echo "Valid environments: development, production"
        exit 1
        ;;
esac

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed or not in PATH"
    exit 1
fi

# Check if terraform directory exists
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TERRAFORM_FULL_PATH="$(cd "$SCRIPT_DIR" && cd "$TERRAFORM_DIR" && pwd)"
if [ ! -d "$TERRAFORM_FULL_PATH" ]; then
    print_error "Terraform directory not found: $TERRAFORM_FULL_PATH"
    exit 1
fi

# Check if terraform state exists by trying to get outputs
if ! terraform output customer_server_ecr_repository_url >/dev/null 2>&1; then
    print_error "Terraform state not found or not accessible. Please run 'terraform apply' first."
    exit 1
fi

print_status "Using environment: $ENVIRONMENT"
print_status "Terraform directory: $TERRAFORM_FULL_PATH"

# Get ECR repository URLs from Terraform outputs
print_status "Retrieving ECR repository information from Terraform..."
cd "$TERRAFORM_FULL_PATH"

CUSTOMER_ECR=$(terraform output -raw customer_server_ecr_repository_url 2>/dev/null || echo "")
APPOINTMENT_ECR=$(terraform output -raw appointment_server_ecr_repository_url 2>/dev/null || echo "")
TECHNICIAN_ECR=$(terraform output -raw technician_server_ecr_repository_url 2>/dev/null || echo "")

if [ -z "$CUSTOMER_ECR" ] || [ -z "$APPOINTMENT_ECR" ] || [ -z "$TECHNICIAN_ECR" ]; then
    print_error "Could not retrieve ECR repository URLs from Terraform outputs."
    print_error "Please ensure Terraform has been applied and ECR repositories are created."
    exit 1
fi

print_debug "Customer Server ECR: $CUSTOMER_ECR"
print_debug "Appointment Server ECR: $APPOINTMENT_ECR"
print_debug "Technician Server ECR: $TECHNICIAN_ECR"

# Extract account ID and region from ECR URL
ACCOUNT_ID=$(echo "$CUSTOMER_ECR" | cut -d'.' -f1)
REGION=$(echo "$CUSTOMER_ECR" | cut -d'.' -f4)

print_debug "Account ID: $ACCOUNT_ID"
print_debug "Region: $REGION"

# Create temporary directory for deployment
TEMP_DIR="$SCRIPT_DIR/temp-deploy-$(date +%s)"
mkdir -p "$TEMP_DIR"

print_status "Creating temporary manifests in: $TEMP_DIR"

# Copy manifests to temporary directory
cp -r "$SCRIPT_DIR/base" "$TEMP_DIR/"
cp -r "$SCRIPT_DIR/overlays" "$TEMP_DIR/"

# Update temporary files with actual ECR URIs
print_status "Updating manifests with ECR repository URIs..."

# Update base kustomization with actual ECR URIs
print_status "Replacing placeholders in base kustomization..."
sed -e "s|{ACCOUNT_ID}|$ACCOUNT_ID|g" \
    -e "s|{REGION}|$REGION|g" \
    "$SCRIPT_DIR/base/kustomization.yaml" > "$TEMP_DIR/base/kustomization.yaml"

# Update overlay kustomizations
print_status "Replacing placeholders in overlay kustomizations..."
if [ -f "$SCRIPT_DIR/overlays/development/kustomization.yaml" ]; then
    sed -e "s|{ACCOUNT_ID}|$ACCOUNT_ID|g" \
        -e "s|{REGION}|$REGION|g" \
        "$SCRIPT_DIR/overlays/development/kustomization.yaml" > "$TEMP_DIR/overlays/development/kustomization.yaml"
fi

if [ -f "$SCRIPT_DIR/overlays/production/kustomization.yaml" ]; then
    sed -e "s|{ACCOUNT_ID}|$ACCOUNT_ID|g" \
        -e "s|{REGION}|$REGION|g" \
        "$SCRIPT_DIR/overlays/production/kustomization.yaml" > "$TEMP_DIR/overlays/production/kustomization.yaml"
fi

# Also copy any other files that might be needed
find "$SCRIPT_DIR/base" -name "*.yaml" -not -name "kustomization.yaml" -exec cp {} "$TEMP_DIR/base/" \;
if [ -d "$SCRIPT_DIR/overlays/development" ]; then
    find "$SCRIPT_DIR/overlays/development" -name "*.yaml" -not -name "kustomization.yaml" -exec cp {} "$TEMP_DIR/overlays/development/" \; 2>/dev/null || true
fi
if [ -d "$SCRIPT_DIR/overlays/production" ]; then
    find "$SCRIPT_DIR/overlays/production" -name "*.yaml" -not -name "kustomization.yaml" -exec cp {} "$TEMP_DIR/overlays/production/" \; 2>/dev/null || true
fi

# Handle domain substitution for ingress resources
print_status "Applying domain substitution for environment: $ENVIRONMENT"

# Check if DOMAIN_NAME is set
if [ -z "$DOMAIN_NAME" ]; then
    print_error "DOMAIN_NAME environment variable is not set!"
    print_error "Please set it first: export DOMAIN_NAME=your-domain.com"
    exit 1
fi

    print_debug "Using domain: $DOMAIN_NAME"

    # Function to substitute domain in ingress files
    substitute_domain_in_file() {
        local file=$1
        local service=$2

        if [ ! -f "$file" ]; then
            print_debug "File not found, skipping: $file"
            return
        fi

        print_debug "Processing ingress file: $file"

        # Determine the host pattern based on environment
        if [ "$ENVIRONMENT" = "production" ]; then
            NEW_HOST="$service.$DOMAIN_NAME"
        else
            NEW_HOST="$service-$ENVIRONMENT.$DOMAIN_NAME"
        fi

        # Substitute the domain using sed
        sed -i.backup "s/host: [^[:space:]]*/host: $NEW_HOST/" "$file"
        rm -f "$file.backup"

        print_debug "Updated host to: $NEW_HOST"
    }

    # Apply domain substitution to ingress patch files
    substitute_domain_in_file "$TEMP_DIR/overlays/$ENVIRONMENT/customer-ingress-patch.yaml" "customer"
    substitute_domain_in_file "$TEMP_DIR/overlays/$ENVIRONMENT/appointment-ingress-patch.yaml" "appointment"
    substitute_domain_in_file "$TEMP_DIR/overlays/$ENVIRONMENT/technician-ingress-patch.yaml" "technician"

print_status "Domain substitution completed for: $DOMAIN_NAME"

# Validate kustomization file exists
TEMP_KUSTOMIZE_PATH="$TEMP_DIR/$KUSTOMIZE_PATH"
if [ ! -f "$TEMP_KUSTOMIZE_PATH/kustomization.yaml" ]; then
    print_error "Kustomization file not found: $TEMP_KUSTOMIZE_PATH/kustomization.yaml"
    exit 1
fi

print_status "Using kustomization path: $TEMP_KUSTOMIZE_PATH"

# Create namespace if needed for overlays
if [ "$ENVIRONMENT" = "development" ] || [ "$ENVIRONMENT" = "dev" ]; then
    print_status "Creating development namespace..."
    kubectl create namespace development --dry-run=client -o yaml | kubectl apply -f - --validate=false
elif [ "$ENVIRONMENT" = "production" ] || [ "$ENVIRONMENT" = "prod" ]; then
    print_status "Creating production namespace..."
    kubectl create namespace production --dry-run=client -o yaml | kubectl apply -f - --validate=false
fi

# Execute action
case $ACTION in
    apply)
        print_status "Applying manifests..."
        kubectl apply -k "$TEMP_KUSTOMIZE_PATH" --validate=false
        print_status "Deployment completed successfully!"

        # Show deployment status
        echo ""
        print_status "Checking deployment status..."
        if [ "$ENVIRONMENT" = "base" ]; then
            kubectl get deployments -l app.kubernetes.io/part-of=insurance-agent-demo -n default
        else
            kubectl get deployments -l app.kubernetes.io/part-of=insurance-agent-demo -n "$ENVIRONMENT"
        fi
        ;;
    delete)
        print_warning "Deleting manifests..."
        kubectl delete -k "$TEMP_KUSTOMIZE_PATH"
        print_status "Resources deleted successfully!"
        ;;
    diff)
        print_status "Showing diff..."
        kubectl diff -k "$TEMP_KUSTOMIZE_PATH" || true
        ;;
    dry-run)
        print_status "Dry run - showing what would be applied..."
        kubectl apply -k "$TEMP_KUSTOMIZE_PATH" --dry-run=client -o yaml
        ;;
    *)
        print_error "Invalid action: $ACTION"
        echo "Valid actions: apply, delete, diff, dry-run"
        exit 1
        ;;
esac

print_status "Operation completed successfully!"
