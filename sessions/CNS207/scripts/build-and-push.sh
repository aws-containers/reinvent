#!/bin/bash
set -e

# Build and push the demo app to ECR

# Configuration
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=${AWS_REGION:-us-east-1}
export ECR_REPO=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/eks-demo-app

echo "🚀 Building and pushing EKS Demo App"
echo "Account: ${AWS_ACCOUNT_ID}"
echo "Region: ${AWS_REGION}"
echo "Repository: ${ECR_REPO}"

# Create ECR repository if it doesn't exist
echo "📦 Creating ECR repository..."
aws ecr describe-repositories --repository-names eks-demo-app --region ${AWS_REGION} 2>/dev/null || \
  aws ecr create-repository --repository-name eks-demo-app --region ${AWS_REGION}

# Login to ECR
echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin ${ECR_REPO}

# Build the image for AMD64 (x86_64) architecture
echo "🔨 Building Docker image for AMD64..."
cd python-app
docker build --platform linux/amd64 -t eks-demo-app:latest .

# Tag and push
echo "📤 Pushing to ECR..."
docker tag eks-demo-app:latest ${ECR_REPO}:latest
docker push ${ECR_REPO}:latest

echo "✅ Done! Image available at: ${ECR_REPO}:latest"
echo ""
echo "Next steps:"
echo "1. Update python-app-workload.yaml with image: ${ECR_REPO}:latest"
echo "2. Deploy to your cluster: kubectl apply -f python-app-workload.yaml"
