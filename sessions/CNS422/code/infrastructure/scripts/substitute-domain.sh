#!/bin/bash

# Script to substitute domain names in Kubernetes manifests
# Usage: ./substitute-domain.sh [environment]

set -e

# Check if DOMAIN_NAME environment variable is set
if [ -z "$DOMAIN_NAME" ]; then
    echo "❌ Error: DOMAIN_NAME environment variable must be set"
    echo "Example: export DOMAIN_NAME=your-domain.com"
    exit 1
fi

# Get environment from argument or default to 'development'
ENVIRONMENT=${1:-development}

echo "🔧 Substituting domain names in Kubernetes manifests..."
echo "📍 Domain: $DOMAIN_NAME"
echo "🏷️  Environment: $ENVIRONMENT"

# Define the manifests directory
MANIFESTS_DIR="infrastructure/manifests/overlays/$ENVIRONMENT"

if [ ! -d "$MANIFESTS_DIR" ]; then
    echo "❌ Error: Environment directory '$MANIFESTS_DIR' does not exist"
    exit 1
fi

# Function to substitute domain in a file
substitute_domain() {
    local file=$1
    local service=$2

    if [ ! -f "$file" ]; then
        echo "⚠️  Warning: File '$file' does not exist, skipping..."
        return
    fi

    echo "📝 Processing $file..."

    # Create backup
    cp "$file" "$file.backup"

    # Determine the host pattern based on environment
    if [ "$ENVIRONMENT" = "production" ]; then
        NEW_HOST="$service.$DOMAIN_NAME"
    else
        NEW_HOST="$service-$ENVIRONMENT.$DOMAIN_NAME"
    fi

    # Substitute the domain
    sed -i.tmp "s/host: [^[:space:]]*/host: $NEW_HOST/" "$file"
    rm "$file.tmp"

    echo "✅ Updated host to: $NEW_HOST"
}

# Process each service ingress file
substitute_domain "$MANIFESTS_DIR/customer-ingress-patch.yaml" "customer"
substitute_domain "$MANIFESTS_DIR/appointment-ingress-patch.yaml" "appointment"
substitute_domain "$MANIFESTS_DIR/technician-ingress-patch.yaml" "technician"

echo ""
echo "✅ Domain substitution completed successfully!"
echo "💡 Backup files created with .backup extension"
echo ""
echo "🚀 You can now apply the manifests with:"
echo "   kubectl apply -k infrastructure/manifests/overlays/$ENVIRONMENT"
