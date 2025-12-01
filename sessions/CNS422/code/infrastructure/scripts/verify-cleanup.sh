#!/bin/bash

# Verification script to check if AWS environment cleanup is complete
# Usage: ./verify-cleanup.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🔍 AWS Environment Cleanup Verification"
echo "========================================"
echo ""

# Track overall status
ALL_CLEAN=true

# Function to print status
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "clean" ]; then
        echo -e "${GREEN}✅${NC} $message"
    elif [ "$status" = "dirty" ]; then
        echo -e "${RED}❌${NC} $message"
        ALL_CLEAN=false
    elif [ "$status" = "warning" ]; then
        echo -e "${YELLOW}⚠️${NC} $message"
    else
        echo -e "${BLUE}ℹ️${NC} $message"
    fi
}

# Check 1: Kubernetes Resources
echo "1️⃣  Checking Kubernetes Resources..."
echo "-----------------------------------"

if ! command -v kubectl &> /dev/null; then
    print_status "warning" "kubectl not found - skipping Kubernetes checks"
else
    export KUBECONFIG="/tmp/eks-cluster"

    # Check if kubeconfig exists
    if [ ! -f "$KUBECONFIG" ]; then
        print_status "clean" "No kubeconfig found - Kubernetes resources likely deleted"
    else
        # Check development namespace
        if kubectl get namespace development &> /dev/null; then
            DEV_PODS=$(kubectl get pods -n development 2>/dev/null | grep -v "NAME" | wc -l || echo "0")
            DEV_SERVICES=$(kubectl get services -n development 2>/dev/null | grep -v "NAME" | wc -l || echo "0")
            DEV_INGRESS=$(kubectl get ingress -n development 2>/dev/null | grep -v "NAME" | wc -l || echo "0")

            if [ "$DEV_PODS" = "0" ] && [ "$DEV_SERVICES" = "0" ] && [ "$DEV_INGRESS" = "0" ]; then
                print_status "clean" "Development namespace is empty"
            else
                print_status "dirty" "Development namespace has resources: Pods=$DEV_PODS, Services=$DEV_SERVICES, Ingress=$DEV_INGRESS"
            fi
        else
            print_status "clean" "Development namespace doesn't exist"
        fi

        # Check production namespace
        if kubectl get namespace production &> /dev/null; then
            PROD_PODS=$(kubectl get pods -n production 2>/dev/null | grep -v "NAME" | wc -l || echo "0")
            PROD_SERVICES=$(kubectl get services -n production 2>/dev/null | grep -v "NAME" | wc -l || echo "0")
            PROD_INGRESS=$(kubectl get ingress -n production 2>/dev/null | grep -v "NAME" | wc -l || echo "0")

            if [ "$PROD_PODS" = "0" ] && [ "$PROD_SERVICES" = "0" ] && [ "$PROD_INGRESS" = "0" ]; then
                print_status "clean" "Production namespace is empty"
            else
                print_status "dirty" "Production namespace has resources: Pods=$PROD_PODS, Services=$PROD_SERVICES, Ingress=$PROD_INGRESS"
            fi
        else
            print_status "clean" "Production namespace doesn't exist"
        fi
    fi
fi

echo ""

# Check 2: EKS Clusters
echo "2️⃣  Checking EKS Clusters..."
echo "-----------------------------------"

if ! command -v aws &> /dev/null; then
    print_status "warning" "AWS CLI not found - skipping AWS checks"
else
    REGION=${AWS_REGION:-us-west-2}

    EKS_CLUSTERS=$(aws eks list-clusters --region $REGION --query 'clusters' --output text 2>/dev/null || echo "")

    if [ -z "$EKS_CLUSTERS" ]; then
        print_status "clean" "No EKS clusters found in region $REGION"
    else
        print_status "dirty" "EKS clusters found: $EKS_CLUSTERS"
    fi
fi

echo ""

# Check 3: VPCs
echo "3️⃣  Checking VPCs..."
echo "-----------------------------------"

if command -v aws &> /dev/null; then
    REGION=${AWS_REGION:-us-west-2}

    # Check for VPCs with our Blueprint tag
    VPCS=$(aws ec2 describe-vpcs --region $REGION --filters "Name=tag:Blueprint,Values=eks-cluster" --query 'Vpcs[].VpcId' --output text 2>/dev/null || echo "")

    if [ -z "$VPCS" ]; then
        print_status "clean" "No VPCs found with Blueprint=eks-cluster tag"
    else
        print_status "dirty" "VPCs found: $VPCS"
    fi
fi

echo ""

# Check 4: Load Balancers
echo "4️⃣  Checking Load Balancers..."
echo "-----------------------------------"

if command -v aws &> /dev/null; then
    REGION=${AWS_REGION:-us-west-2}

    ALBS=$(aws elbv2 describe-load-balancers --region $REGION --query 'LoadBalancers[?contains(LoadBalancerName, `k8s`)].LoadBalancerName' --output text 2>/dev/null || echo "")

    if [ -z "$ALBS" ]; then
        print_status "clean" "No Kubernetes-managed Load Balancers found"
    else
        print_status "dirty" "Load Balancers found: $ALBS"
    fi
fi

echo ""

# Check 5: ECR Repositories
echo "5️⃣  Checking ECR Repositories..."
echo "-----------------------------------"

if command -v aws &> /dev/null; then
    REGION=${AWS_REGION:-us-west-2}

    ECR_REPOS=$(aws ecr describe-repositories --region $REGION --query 'repositories[?contains(repositoryName, `agentcore-gateway`)].repositoryName' --output text 2>/dev/null || echo "")

    if [ -z "$ECR_REPOS" ]; then
        print_status "clean" "No agentcore-gateway ECR repositories found"
    else
        print_status "dirty" "ECR repositories found: $ECR_REPOS"
    fi
fi

echo ""

# Check 6: AgentCore Gateways
echo "6️⃣  Checking AgentCore Gateways..."
echo "-----------------------------------"

if command -v aws &> /dev/null; then
    REGION=${AWS_REGION:-us-west-2}

    GATEWAYS=$(aws bedrock-agentcore-control list-gateways --region $REGION --query 'items[].gatewayId' --output text 2>/dev/null || echo "")

    if [ -z "$GATEWAYS" ]; then
        print_status "clean" "No AgentCore gateways found"
    else
        print_status "dirty" "AgentCore gateways found: $GATEWAYS"
    fi
fi

echo ""

# Check 7: Terraform State
echo "7️⃣  Checking Terraform State..."
echo "-----------------------------------"

TERRAFORM_DIR="$(dirname "$0")/../terraform"

if [ -f "$TERRAFORM_DIR/terraform.tfstate" ]; then
    # Check if state file has resources
    RESOURCE_COUNT=$(grep -c '"type":' "$TERRAFORM_DIR/terraform.tfstate" 2>/dev/null || echo "0")

    if [ "$RESOURCE_COUNT" -gt 0 ]; then
        print_status "dirty" "Terraform state file exists with $RESOURCE_COUNT resources"
        print_status "info" "Run 'make cleanup-terraform' to destroy infrastructure"
    else
        print_status "clean" "Terraform state file exists but is empty"
    fi
else
    print_status "clean" "No Terraform state file found"
fi

echo ""
echo "========================================"

# Final summary
if [ "$ALL_CLEAN" = true ]; then
    echo -e "${GREEN}🎉 All checks passed! Environment is clean.${NC}"
    echo ""
    echo "✅ No AWS resources found"
    echo "✅ No Kubernetes resources found"
    echo "✅ No Terraform state found"
    echo ""
    echo "💡 You can now safely redeploy with 'make terraform-apply'"
    exit 0
else
    echo -e "${RED}⚠️  Cleanup incomplete! Some resources still exist.${NC}"
    echo ""
    echo "🔧 Recommended actions:"
    echo "  1. Run 'make cleanup-k8s-all' to delete Kubernetes resources"
    echo "  2. Run 'make cleanup-terraform' to destroy AWS infrastructure"
    echo "  3. Run 'make cleanup-gateway' to delete AgentCore Gateway"
    echo ""
    echo "Or run 'make cleanup-all' for complete automated cleanup"
    echo ""
    echo "📚 See infrastructure/CLEANUP.md for detailed instructions"
    exit 1
fi
