# Quick Start Guide

## Deploy or Update Application

```bash
cd agent/agent-ui
AWS_PROFILE="carrlos+salaunch-Admin" AWS_REGION="us-west-2" ./deploy.sh
```

That's it! The script handles everything automatically.

## What Happens

1. ✅ Builds Docker image
2. ✅ Pushes to ECR
3. ✅ Updates ECS service
4. ✅ Rolling deployment (zero downtime)

**Time:** 2-3 minutes

## Application URL

http://agent-ui-alb-794854677.us-west-2.elb.amazonaws.com/

## Common Tasks

### View Logs
```bash
aws logs tail /ecs/agent-ui-task --follow --region us-west-2 --profile "carrlos+salaunch-Admin"
```

### Check Status
```bash
aws ecs describe-services \
  --cluster agent-ui-cluster \
  --services agent-ui-service \
  --region us-west-2 \
  --profile "carrlos+salaunch-Admin" \
  --query 'services[0].[status,runningCount,desiredCount]' \
  --output table
```

### Update Environment Variables
1. Edit `.env` file
2. Run `AWS_PROFILE="carrlos+salaunch-Admin" AWS_REGION="us-west-2" ./deploy.sh`

### Stop Service (save costs)
```bash
aws ecs update-service \
  --cluster agent-ui-cluster \
  --service agent-ui-service \
  --desired-count 0 \
  --region us-west-2 \
  --profile "carrlos+salaunch-Admin"
```

### Start Service
```bash
aws ecs update-service \
  --cluster agent-ui-cluster \
  --service agent-ui-service \
  --desired-count 1 \
  --region us-west-2 \
  --profile "carrlos+salaunch-Admin"
```

## Troubleshooting

If deployment fails, check:
1. Docker is running: `docker ps`
2. Service events: See DEPLOYMENT.md
3. Application logs: See command above

## Full Documentation

See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete details.
