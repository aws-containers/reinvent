# Agent UI Deployment Guide

This guide explains how to deploy and update the agent-ui application to AWS ECS.

## Prerequisites

- AWS CLI installed and configured
- Docker installed and running
- jq installed (`brew install jq` on macOS)
- AWS profile configured: `carrlos+salaunch-Admin`
- ECR login plugin (already configured)

## Initial Deployment

```bash
cd agent/agent-ui
AWS_PROFILE="carrlos+salaunch-Admin" AWS_REGION="us-west-2" ./deploy.sh
```

The script will:
1. ✅ Build Docker image for linux/amd64
2. ✅ Push image to ECR with timestamp tag
3. ✅ Create/verify ECS cluster
4. ✅ Create/verify IAM roles with Bedrock and CloudWatch permissions
5. ✅ Create/verify VPC networking (security groups, load balancer, target groups)
6. ✅ Register new task definition with environment variables from `.env`
7. ✅ Update ECS service with new task definition (triggers rolling deployment)
8. ✅ Wait and check deployment status

**Deployment time:** ~3-5 minutes for initial deployment, ~2-3 minutes for updates

## Updating Your Application

When you make code changes, simply run the deployment script again:

```bash
AWS_PROFILE="carrlos+salaunch-Admin" AWS_REGION="us-west-2" ./deploy.sh
```

The script is **idempotent** and will:
- Build a new Docker image with a new timestamp tag
- Register a new task definition
- Update the ECS service (triggers automatic rolling deployment)
- Keep all existing infrastructure (no downtime)

### What Gets Updated
- ✅ Application code
- ✅ Dependencies (from pyproject.toml)
- ✅ Environment variables (from .env file)
- ✅ Docker configuration (from Dockerfile)

### What Stays the Same
- ✅ Load balancer URL (no DNS changes)
- ✅ Security groups
- ✅ IAM roles
- ✅ VPC configuration

## Environment Variables

The deployment automatically loads environment variables from `.env`:

```bash
CLIENT_ID=your-client-id
AGENT_USERNAME=your-username
AGENT_USER_PASSWORD=your-password
AGENT_ARN=your-agent-arn
```

**Important:** After updating `.env`, run `./deploy.sh` to apply changes.

## Current Deployment

**Application URL:** http://agent-ui-alb-794854677.us-west-2.elb.amazonaws.com/

**AWS Resources:**
- Region: `us-west-2`
- Cluster: `agent-ui-cluster`
- Service: `agent-ui-service`
- ECR Repository: `agent-ui`
- Load Balancer: `agent-ui-alb`

## Useful Commands

### Check Service Status
```bash
aws ecs describe-services \
  --cluster agent-ui-cluster \
  --services agent-ui-service \
  --region us-west-2 \
  --profile "carrlos+salaunch-Admin" \
  --query 'services[0].[serviceName,status,runningCount,desiredCount]' \
  --output table
```

### View Application Logs
```bash
aws logs tail /ecs/agent-ui-task \
  --follow \
  --region us-west-2 \
  --profile "carrlos+salaunch-Admin"
```

### Force New Deployment (without code changes)
```bash
aws ecs update-service \
  --cluster agent-ui-cluster \
  --service agent-ui-service \
  --force-new-deployment \
  --region us-west-2 \
  --profile "carrlos+salaunch-Admin"
```

### List Recent Images in ECR
```bash
aws ecr describe-images \
  --repository-name agent-ui \
  --region us-west-2 \
  --profile "carrlos+salaunch-Admin" \
  --query 'sort_by(imageDetails,& imagePushedAt)[-5:].[imageTags[0],imagePushedAt]' \
  --output table
```

### Check Target Health
```bash
aws elbv2 describe-target-health \
  --target-group-arn $(aws elbv2 describe-target-groups \
    --names agent-ui-tg \
    --region us-west-2 \
    --profile "carrlos+salaunch-Admin" \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text) \
  --region us-west-2 \
  --profile "carrlos+salaunch-Admin"
```

## Troubleshooting

### Deployment Stuck or Failing

1. **Check service events:**
```bash
aws ecs describe-services \
  --cluster agent-ui-cluster \
  --services agent-ui-service \
  --region us-west-2 \
  --profile "carrlos+salaunch-Admin" \
  --query 'services[0].events[0:5].[createdAt,message]' \
  --output table
```

2. **Check task failures:**
```bash
aws ecs list-tasks \
  --cluster agent-ui-cluster \
  --service-name agent-ui-service \
  --region us-west-2 \
  --profile "carrlos+salaunch-Admin"
```

3. **View stopped tasks:**
```bash
aws ecs list-tasks \
  --cluster agent-ui-cluster \
  --desired-status STOPPED \
  --region us-west-2 \
  --profile "carrlos+salaunch-Admin"
```

### Application Not Responding

1. **Check target health** (see command above)
2. **Verify security group rules:**
```bash
aws ec2 describe-security-groups \
  --group-ids sg-0df056ab10ade82c8 \
  --region us-west-2 \
  --profile "carrlos+salaunch-Admin"
```

3. **Test direct container access** (if target is healthy but ALB fails):
   - Security group should allow ports 80 and 8000
   - Check ALB listener rules

### Image Build Failures

1. **Check Docker is running:**
```bash
docker ps
```

2. **Verify Dockerfile syntax:**
```bash
docker build --platform linux/amd64 -t test .
```

3. **Check ECR authentication:**
   - The script assumes you're already logged in via ECR plugin
   - If needed, manually login:
```bash
aws ecr get-login-password \
  --region us-west-2 \
  --profile "carrlos+salaunch-Admin" | \
  docker login --username AWS --password-stdin \
  210066870173.dkr.ecr.us-west-2.amazonaws.com
```

## Infrastructure Details

### IAM Roles

**Execution Role:** `agent-ui-task-execution-role`
- Permissions: ECS task execution, ECR pull, CloudWatch Logs

**Task Role:** `agent-ui-task-task-role`
- Permissions: Bedrock access, Bedrock AgentCore access

### Security Groups

**agent-ui-sg:**
- Inbound: Port 80 (HTTP) from 0.0.0.0/0
- Inbound: Port 8000 (Container) from 0.0.0.0/0
- Outbound: All traffic

### Load Balancer Configuration

- Type: Application Load Balancer
- Scheme: Internet-facing
- Listener: HTTP on port 80
- Target Group: IP targets on port 8000
- Health Check: Path `/`, interval 30s

### ECS Configuration

- Launch Type: Fargate
- CPU: 512 units (0.5 vCPU)
- Memory: 1024 MB (1 GB)
- Desired Count: 1 task
- Network Mode: awsvpc
- Public IP: Enabled

## Cost Optimization

Current configuration costs approximately:
- Fargate: ~$15-20/month (0.5 vCPU, 1GB RAM, 24/7)
- ALB: ~$16-20/month
- ECR: ~$0.10/GB/month for storage
- Data Transfer: Variable

**Total estimated cost:** ~$35-45/month

To reduce costs:
1. Stop the service when not in use:
```bash
aws ecs update-service \
  --cluster agent-ui-cluster \
  --service agent-ui-service \
  --desired-count 0 \
  --region us-west-2 \
  --profile "carrlos+salaunch-Admin"
```

2. Start it again:
```bash
aws ecs update-service \
  --cluster agent-ui-cluster \
  --service agent-ui-service \
  --desired-count 1 \
  --region us-west-2 \
  --profile "carrlos+salaunch-Admin"
```

## Cleanup

To delete all resources:

```bash
# Delete ECS service
aws ecs delete-service \
  --cluster agent-ui-cluster \
  --service agent-ui-service \
  --force \
  --region us-west-2 \
  --profile "carrlos+salaunch-Admin"

# Delete ECS cluster
aws ecs delete-cluster \
  --cluster agent-ui-cluster \
  --region us-west-2 \
  --profile "carrlos+salaunch-Admin"

# Delete load balancer
aws elbv2 delete-load-balancer \
  --load-balancer-arn $(aws elbv2 describe-load-balancers \
    --names agent-ui-alb \
    --region us-west-2 \
    --profile "carrlos+salaunch-Admin" \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text)

# Delete target group (wait 5 minutes after deleting ALB)
aws elbv2 delete-target-group \
  --target-group-arn $(aws elbv2 describe-target-groups \
    --names agent-ui-tg \
    --region us-west-2 \
    --profile "carrlos+salaunch-Admin" \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)

# Delete security group
aws ec2 delete-security-group \
  --group-id sg-0df056ab10ade82c8 \
  --region us-west-2 \
  --profile "carrlos+salaunch-Admin"

# Delete ECR repository (and all images)
aws ecr delete-repository \
  --repository-name agent-ui \
  --force \
  --region us-west-2 \
  --profile "carrlos+salaunch-Admin"

# Delete IAM roles
aws iam delete-role-policy \
  --role-name agent-ui-task-execution-role \
  --policy-name CloudWatchLogsPolicy \
  --profile "carrlos+salaunch-Admin"

aws iam detach-role-policy \
  --role-name agent-ui-task-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy \
  --profile "carrlos+salaunch-Admin"

aws iam delete-role \
  --role-name agent-ui-task-execution-role \
  --profile "carrlos+salaunch-Admin"

aws iam delete-role-policy \
  --role-name agent-ui-task-task-role \
  --policy-name BedrockAccess \
  --profile "carrlos+salaunch-Admin"

aws iam delete-role \
  --role-name agent-ui-task-task-role \
  --profile "carrlos+salaunch-Admin"
```
