#!/bin/bash

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License").

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="agent-ui"
AWS_PROFILE="${AWS_PROFILE:-carrlos+salaunch-Admin}"
AWS_REGION="${AWS_REGION:-us-west-2}"
CLUSTER_NAME="${ECS_CLUSTER_NAME:-${PROJECT_NAME}-cluster}"
SERVICE_NAME="${ECS_SERVICE_NAME:-${PROJECT_NAME}-service}"
TASK_FAMILY="${ECS_TASK_FAMILY:-${PROJECT_NAME}-task}"
ECR_REPO_NAME="${ECR_REPO_NAME:-${PROJECT_NAME}}"
CONTAINER_PORT=8000
DESIRED_COUNT=1

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    command -v aws >/dev/null 2>&1 || { log_error "AWS CLI is required but not installed. Aborting."; exit 1; }
    command -v docker >/dev/null 2>&1 || { log_error "Docker is required but not installed. Aborting."; exit 1; }
    command -v jq >/dev/null 2>&1 || { log_error "jq is required but not installed. Aborting."; exit 1; }

    # Check AWS credentials with profile
    aws sts get-caller-identity --profile "${AWS_PROFILE}" >/dev/null 2>&1 || {
        log_error "AWS credentials not configured for profile '${AWS_PROFILE}'. Aborting.";
        exit 1;
    }

    # Check .env file exists
    if [ ! -f "${SCRIPT_DIR}/.env" ]; then
        log_error ".env file not found at ${SCRIPT_DIR}/.env"
        exit 1
    fi

    log_info "All prerequisites met"
    log_info "Using AWS Profile: ${AWS_PROFILE}"
}

get_aws_account_id() {
    aws sts get-caller-identity --profile "${AWS_PROFILE}" --query Account --output text
}

create_ecr_repository() {
    local account_id=$1
    local ecr_uri="${account_id}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"

    log_info "Checking ECR repository..." >&2

    if aws ecr describe-repositories --repository-names "${ECR_REPO_NAME}" --region "${AWS_REGION}" --profile "${AWS_PROFILE}" >/dev/null 2>&1; then
        log_info "ECR repository already exists: ${ECR_REPO_NAME}" >&2
    else
        log_info "Creating ECR repository: ${ECR_REPO_NAME}" >&2
        aws ecr create-repository \
            --repository-name "${ECR_REPO_NAME}" \
            --region "${AWS_REGION}" \
            --profile "${AWS_PROFILE}" \
            --image-scanning-configuration scanOnPush=true \
            --encryption-configuration encryptionType=AES256 >/dev/null
    fi

    echo "${ecr_uri}"
}

build_and_push_image() {
    local ecr_uri=$1
    local image_tag="${2:-latest}"

    # Skip ECR login - assuming already logged in via plugin
    # log_info "Logging into ECR..."
    # aws ecr get-login-password --region "${AWS_REGION}" --profile "${AWS_PROFILE}" | \
    #     docker login --username AWS --password-stdin "${ecr_uri%%/*}"

    log_info "Building Docker image..."
    docker build --platform linux/amd64 -t "${PROJECT_NAME}:${image_tag}" "${SCRIPT_DIR}"

    log_info "Tagging image for ECR..."
    docker tag "${PROJECT_NAME}:${image_tag}" "${ecr_uri}:${image_tag}"

    log_info "Pushing image to ECR..."
    docker push "${ecr_uri}:${image_tag}"

    log_info "Image pushed successfully: ${ecr_uri}:${image_tag}"
}

load_env_variables() {
    log_info "Loading environment variables from .env file..." >&2

    local env_vars="["
    local first=true

    while IFS='=' read -r key value; do
        # Skip empty lines and comments
        [[ -z "$key" || "$key" =~ ^#.*$ ]] && continue

        # Remove leading/trailing whitespace
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)

        if [ "$first" = true ]; then
            first=false
        else
            env_vars+=","
        fi

        env_vars+="{\"name\":\"${key}\",\"value\":\"${value}\"}"
    done < "${SCRIPT_DIR}/.env"

    env_vars+="]"
    echo "$env_vars"
}

create_ecs_cluster() {
    log_info "Checking ECS cluster..."

    if aws ecs describe-clusters --clusters "${CLUSTER_NAME}" --region "${AWS_REGION}" --profile "${AWS_PROFILE}" \
        --query 'clusters[0].status' --output text 2>/dev/null | grep -q "ACTIVE"; then
        log_info "ECS cluster already exists: ${CLUSTER_NAME}"
    else
        log_info "Creating ECS cluster: ${CLUSTER_NAME}"
        aws ecs create-cluster \
            --cluster-name "${CLUSTER_NAME}" \
            --region "${AWS_REGION}" \
            --profile "${AWS_PROFILE}" >/dev/null
    fi
}

create_task_execution_role() {
    local role_name="${TASK_FAMILY}-execution-role"

    log_info "Checking IAM execution role..." >&2

    if aws iam get-role --role-name "${role_name}" --profile "${AWS_PROFILE}" >/dev/null 2>&1; then
        log_info "IAM execution role already exists: ${role_name}" >&2
    else
        log_info "Creating IAM execution role: ${role_name}" >&2

        # Create trust policy
        cat > /tmp/trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

        aws iam create-role \
            --role-name "${role_name}" \
            --profile "${AWS_PROFILE}" \
            --assume-role-policy-document file:///tmp/trust-policy.json >/dev/null

        aws iam attach-role-policy \
            --role-name "${role_name}" \
            --profile "${AWS_PROFILE}" \
            --policy-arn "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy" >/dev/null

        # Add CloudWatch Logs permissions
        cat > /tmp/logs-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
EOF

        aws iam put-role-policy \
            --role-name "${role_name}" \
            --profile "${AWS_PROFILE}" \
            --policy-name "CloudWatchLogsPolicy" \
            --policy-document file:///tmp/logs-policy.json >/dev/null

        rm /tmp/trust-policy.json /tmp/logs-policy.json

        log_info "Waiting for IAM role to propagate..." >&2
        sleep 10
    fi

    aws iam get-role --role-name "${role_name}" --profile "${AWS_PROFILE}" --query 'Role.Arn' --output text 2>/dev/null
}

create_task_role() {
    local role_name="${TASK_FAMILY}-task-role"

    log_info "Checking IAM task role..." >&2

    if aws iam get-role --role-name "${role_name}" --profile "${AWS_PROFILE}" >/dev/null 2>&1; then
        log_info "IAM task role already exists: ${role_name}" >&2
    else
        log_info "Creating IAM task role: ${role_name}" >&2

        # Create trust policy
        cat > /tmp/task-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

        aws iam create-role \
            --role-name "${role_name}" \
            --profile "${AWS_PROFILE}" \
            --assume-role-policy-document file:///tmp/task-trust-policy.json >/dev/null

        # Create policy for Bedrock access
        cat > /tmp/task-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:*",
        "bedrock-agentcore:*"
      ],
      "Resource": "*"
    }
  ]
}
EOF

        aws iam put-role-policy \
            --role-name "${role_name}" \
            --profile "${AWS_PROFILE}" \
            --policy-name "BedrockAccess" \
            --policy-document file:///tmp/task-policy.json >/dev/null

        rm /tmp/task-trust-policy.json /tmp/task-policy.json

        log_info "Waiting for IAM role to propagate..." >&2
        sleep 10
    fi

    aws iam get-role --role-name "${role_name}" --profile "${AWS_PROFILE}" --query 'Role.Arn' --output text 2>/dev/null
}

get_default_vpc_and_subnets() {
    log_info "Getting default VPC and subnets..." >&2

    local vpc_id=$(aws ec2 describe-vpcs \
        --filters "Name=isDefault,Values=true" \
        --region "${AWS_REGION}" \
        --profile "${AWS_PROFILE}" \
        --query 'Vpcs[0].VpcId' \
        --output text)

    if [ "$vpc_id" = "None" ] || [ -z "$vpc_id" ]; then
        log_error "No default VPC found. Please create a VPC first." >&2
        exit 1
    fi

    local subnets=$(aws ec2 describe-subnets \
        --filters "Name=vpc-id,Values=${vpc_id}" \
        --region "${AWS_REGION}" \
        --profile "${AWS_PROFILE}" \
        --query 'Subnets[*].SubnetId' \
        --output text)

    echo "${vpc_id}|${subnets}"
}

create_security_group() {
    local vpc_id=$1
    local sg_name="${PROJECT_NAME}-sg"

    log_info "Checking security group..." >&2

    local sg_id=$(aws ec2 describe-security-groups \
        --filters "Name=group-name,Values=${sg_name}" "Name=vpc-id,Values=${vpc_id}" \
        --region "${AWS_REGION}" \
        --profile "${AWS_PROFILE}" \
        --query 'SecurityGroups[0].GroupId' \
        --output text 2>/dev/null)

    if [ "$sg_id" != "None" ] && [ -n "$sg_id" ]; then
        log_info "Security group already exists: ${sg_id}" >&2
    else
        log_info "Creating security group: ${sg_name}" >&2

        sg_id=$(aws ec2 create-security-group \
            --group-name "${sg_name}" \
            --description "Security group for ${PROJECT_NAME}" \
            --vpc-id "${vpc_id}" \
            --region "${AWS_REGION}" \
            --profile "${AWS_PROFILE}" \
            --query 'GroupId' \
            --output text)

        # Allow inbound traffic on container port
        aws ec2 authorize-security-group-ingress \
            --group-id "${sg_id}" \
            --protocol tcp \
            --port "${CONTAINER_PORT}" \
            --cidr 0.0.0.0/0 \
            --region "${AWS_REGION}" \
            --profile "${AWS_PROFILE}" >/dev/null

        # Allow inbound traffic on ALB port (80)
        aws ec2 authorize-security-group-ingress \
            --group-id "${sg_id}" \
            --protocol tcp \
            --port 80 \
            --cidr 0.0.0.0/0 \
            --region "${AWS_REGION}" \
            --profile "${AWS_PROFILE}" >/dev/null 2>&1 || true

        log_info "Security group created: ${sg_id}" >&2
    fi

    echo "${sg_id}"
}

create_load_balancer() {
    local vpc_id=$1
    local subnets=$2
    local sg_id=$3
    local lb_name="${PROJECT_NAME}-alb"

    log_info "Checking Application Load Balancer..." >&2

    local lb_arn=$(aws elbv2 describe-load-balancers \
        --names "${lb_name}" \
        --region "${AWS_REGION}" \
        --profile "${AWS_PROFILE}" \
        --query 'LoadBalancers[0].LoadBalancerArn' \
        --output text 2>/dev/null)

    if [ "$lb_arn" != "None" ] && [ -n "$lb_arn" ]; then
        log_info "Load balancer already exists" >&2
    else
        log_info "Creating Application Load Balancer: ${lb_name}" >&2

        # Convert space-separated subnets to array and build args
        local subnet_array=($subnets)

        lb_arn=$(aws elbv2 create-load-balancer \
            --name "${lb_name}" \
            --subnets ${subnet_array[@]} \
            --security-groups "${sg_id}" \
            --scheme internet-facing \
            --type application \
            --ip-address-type ipv4 \
            --region "${AWS_REGION}" \
            --profile "${AWS_PROFILE}" \
            --query 'LoadBalancers[0].LoadBalancerArn' \
            --output text)

        log_info "Waiting for load balancer to become active..." >&2
        aws elbv2 wait load-balancer-available \
            --load-balancer-arns "${lb_arn}" \
            --region "${AWS_REGION}" \
            --profile "${AWS_PROFILE}" 2>&1 >&2
    fi

    echo "${lb_arn}"
}

create_target_group() {
    local vpc_id=$1
    local tg_name="${PROJECT_NAME}-tg"

    log_info "Checking target group..." >&2

    local tg_arn=$(aws elbv2 describe-target-groups \
        --names "${tg_name}" \
        --region "${AWS_REGION}" \
        --profile "${AWS_PROFILE}" \
        --query 'TargetGroups[0].TargetGroupArn' \
        --output text 2>/dev/null)

    if [ "$tg_arn" != "None" ] && [ -n "$tg_arn" ]; then
        log_info "Target group already exists" >&2
    else
        log_info "Creating target group: ${tg_name}" >&2

        tg_arn=$(aws elbv2 create-target-group \
            --name "${tg_name}" \
            --protocol HTTP \
            --port "${CONTAINER_PORT}" \
            --vpc-id "${vpc_id}" \
            --target-type ip \
            --health-check-path "/" \
            --health-check-interval-seconds 30 \
            --health-check-timeout-seconds 5 \
            --healthy-threshold-count 2 \
            --unhealthy-threshold-count 3 \
            --region "${AWS_REGION}" \
            --profile "${AWS_PROFILE}" \
            --query 'TargetGroups[0].TargetGroupArn' \
            --output text)
    fi

    echo "${tg_arn}"
}

create_listener() {
    local lb_arn=$1
    local tg_arn=$2

    log_info "Checking load balancer listener..." >&2

    local listener_arn=$(aws elbv2 describe-listeners \
        --load-balancer-arn "${lb_arn}" \
        --region "${AWS_REGION}" \
        --profile "${AWS_PROFILE}" \
        --query 'Listeners[0].ListenerArn' \
        --output text 2>/dev/null)

    if [ "$listener_arn" != "None" ] && [ -n "$listener_arn" ]; then
        log_info "Listener already exists" >&2
    else
        log_info "Creating listener..." >&2

        listener_arn=$(aws elbv2 create-listener \
            --load-balancer-arn "${lb_arn}" \
            --protocol HTTP \
            --port 80 \
            --default-actions Type=forward,TargetGroupArn="${tg_arn}" \
            --region "${AWS_REGION}" \
            --profile "${AWS_PROFILE}" \
            --query 'Listeners[0].ListenerArn' \
            --output text)
    fi

    echo "${listener_arn}"
}

register_task_definition() {
    local ecr_uri=$1
    local image_tag=$2
    local execution_role_arn=$3
    local task_role_arn=$4
    local env_vars=$5

    log_info "Registering ECS task definition..."

    cat > /tmp/task-definition.json <<EOF
{
  "family": "${TASK_FAMILY}",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "${execution_role_arn}",
  "taskRoleArn": "${task_role_arn}",
  "containerDefinitions": [
    {
      "name": "${PROJECT_NAME}",
      "image": "${ecr_uri}:${image_tag}",
      "essential": true,
      "portMappings": [
        {
          "containerPort": ${CONTAINER_PORT},
          "protocol": "tcp"
        }
      ],
      "environment": ${env_vars},
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/${TASK_FAMILY}",
          "awslogs-region": "${AWS_REGION}",
          "awslogs-stream-prefix": "ecs",
          "awslogs-create-group": "true"
        }
      }
    }
  ]
}
EOF

    aws ecs register-task-definition \
        --cli-input-json file:///tmp/task-definition.json \
        --region "${AWS_REGION}" \
        --profile "${AWS_PROFILE}" >/dev/null

    rm /tmp/task-definition.json

    log_info "Task definition registered: ${TASK_FAMILY}"
}

create_or_update_service() {
    local tg_arn=$1
    local subnets=$2
    local sg_id=$3

    log_info "Checking ECS service..." >&2

    local service_exists=$(aws ecs describe-services \
        --cluster "${CLUSTER_NAME}" \
        --services "${SERVICE_NAME}" \
        --region "${AWS_REGION}" \
        --profile "${AWS_PROFILE}" \
        --query 'services[0].status' \
        --output text 2>/dev/null)

    # Convert tab/space-separated subnets to comma-separated, removing any extra whitespace
    local subnet_list=$(echo "$subnets" | tr -s '[:space:]' ',' | sed 's/^,//;s/,$//')

    if [ "$service_exists" = "ACTIVE" ]; then
        log_info "Updating existing ECS service..." >&2

        aws ecs update-service \
            --cluster "${CLUSTER_NAME}" \
            --service "${SERVICE_NAME}" \
            --task-definition "${TASK_FAMILY}" \
            --desired-count "${DESIRED_COUNT}" \
            --force-new-deployment \
            --region "${AWS_REGION}" \
            --profile "${AWS_PROFILE}" >/dev/null

        log_info "Service update initiated" >&2
    else
        log_info "Creating ECS service: ${SERVICE_NAME}" >&2

        aws ecs create-service \
            --cluster "${CLUSTER_NAME}" \
            --service-name "${SERVICE_NAME}" \
            --task-definition "${TASK_FAMILY}" \
            --desired-count "${DESIRED_COUNT}" \
            --launch-type FARGATE \
            --network-configuration "awsvpcConfiguration={subnets=[${subnet_list}],securityGroups=[${sg_id}],assignPublicIp=ENABLED}" \
            --load-balancers "targetGroupArn=${tg_arn},containerName=${PROJECT_NAME},containerPort=${CONTAINER_PORT}" \
            --region "${AWS_REGION}" \
            --profile "${AWS_PROFILE}" >/dev/null

        log_info "Service created successfully" >&2
    fi
}

get_load_balancer_url() {
    local lb_arn=$1

    local lb_dns=$(aws elbv2 describe-load-balancers \
        --load-balancer-arns "${lb_arn}" \
        --region "${AWS_REGION}" \
        --profile "${AWS_PROFILE}" \
        --query 'LoadBalancers[0].DNSName' \
        --output text 2>/dev/null)

    echo "http://${lb_dns}"
}

check_deployment_status() {
    log_info "Checking deployment status..."

    local running_count=$(aws ecs describe-services \
        --cluster "${CLUSTER_NAME}" \
        --services "${SERVICE_NAME}" \
        --region "${AWS_REGION}" \
        --profile "${AWS_PROFILE}" \
        --query 'services[0].runningCount' \
        --output text 2>/dev/null)

    local desired_count=$(aws ecs describe-services \
        --cluster "${CLUSTER_NAME}" \
        --services "${SERVICE_NAME}" \
        --region "${AWS_REGION}" \
        --profile "${AWS_PROFILE}" \
        --query 'services[0].desiredCount' \
        --output text 2>/dev/null)

    log_info "Running tasks: ${running_count}/${desired_count}"

    if [ "$running_count" = "$desired_count" ] && [ "$running_count" != "0" ]; then
        log_info "✓ Service is healthy and running"
        return 0
    else
        log_warn "Service is still deploying. This may take 2-3 minutes."
        return 1
    fi
}

# Main deployment flow
main() {
    log_info "Starting deployment of ${PROJECT_NAME}..."

    check_prerequisites

    local account_id=$(get_aws_account_id)
    log_info "AWS Account ID: ${account_id}"
    log_info "AWS Region: ${AWS_REGION}"

    # Build and push image
    local ecr_uri=$(create_ecr_repository "${account_id}")
    local image_tag="$(date +%Y%m%d-%H%M%S)"
    build_and_push_image "${ecr_uri}" "${image_tag}"

    # Load environment variables
    local env_vars=$(load_env_variables)

    # Create ECS infrastructure
    create_ecs_cluster

    local execution_role_arn=$(create_task_execution_role)
    local task_role_arn=$(create_task_role)

    # Get VPC and networking
    local vpc_info=$(get_default_vpc_and_subnets)
    local vpc_id=$(echo "$vpc_info" | cut -d'|' -f1)
    local subnets=$(echo "$vpc_info" | cut -d'|' -f2)

    log_info "Using VPC: ${vpc_id}"

    local sg_id=$(create_security_group "${vpc_id}")

    # Create load balancer infrastructure
    local lb_arn=$(create_load_balancer "${vpc_id}" "${subnets}" "${sg_id}")
    local tg_arn=$(create_target_group "${vpc_id}")
    create_listener "${lb_arn}" "${tg_arn}"

    # Register task and create/update service
    register_task_definition "${ecr_uri}" "${image_tag}" "${execution_role_arn}" "${task_role_arn}" "${env_vars}"
    create_or_update_service "${tg_arn}" "${subnets}" "${sg_id}"

    # Get the public URL
    local app_url=$(get_load_balancer_url "${lb_arn}")

    log_info "=========================================="
    log_info "Deployment completed successfully!"
    log_info "=========================================="
    log_info "Cluster: ${CLUSTER_NAME}"
    log_info "Service: ${SERVICE_NAME}"
    log_info "Image: ${ecr_uri}:${image_tag}"
    log_info "Application URL: ${app_url}"
    log_info "=========================================="

    # Wait a moment and check status
    log_info "Waiting 30 seconds before checking deployment status..."
    sleep 30
    check_deployment_status || true

    log_info ""
    log_info "Useful commands:"
    log_info "  Check service status:"
    log_info "    aws ecs describe-services --cluster ${CLUSTER_NAME} --services ${SERVICE_NAME} --region ${AWS_REGION} --profile ${AWS_PROFILE}"
    log_info "  View logs:"
    log_info "    aws logs tail /ecs/${TASK_FAMILY} --follow --region ${AWS_REGION} --profile ${AWS_PROFILE}"
    log_info "  Force new deployment:"
    log_info "    aws ecs update-service --cluster ${CLUSTER_NAME} --service ${SERVICE_NAME} --force-new-deployment --region ${AWS_REGION} --profile ${AWS_PROFILE}"
}

# Run main function
main
