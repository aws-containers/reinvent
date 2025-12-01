# Kubernetes Manifests for EKS Auto Mode Deployment

This directory contains Kubernetes manifests for deploying the Insurance Agent ChatBot services to an EKS Auto Mode cluster using Kustomize for configuration management.

## Directory Structure

```
manifests/
├── README.md                    # This file
├── deploy-with-ecr.sh           # Script to deploy with ECR images
├── base/                        # Base configurations
│   ├── kustomization.yaml       # Base kustomization with ECR image references
│   ├── customer-server/
│   │   ├── deployment.yaml      # Customer service deployment (port 8001)
│   │   ├── service.yaml         # Customer service ClusterIP
│   │   └── ingress.yaml         # Customer service ALB ingress
│   ├── appointment-server/
│   │   ├── deployment.yaml      # Appointment service deployment (port 8002)
│   │   ├── service.yaml         # Appointment service ClusterIP
│   │   └── ingress.yaml         # Appointment service ALB ingress
│   └── technician-server/
│       ├── deployment.yaml      # Technician service deployment (port 8003)
│       ├── service.yaml         # Technician service ClusterIP
│       └── ingress.yaml         # Technician service ALB ingress
└── overlays/                    # Environment-specific overlays
    ├── development/
    │   └── kustomization.yaml   # Dev-specific overrides (1 replica each)
    └── production/
        └── kustomization.yaml   # Prod-specific overrides (3 replicas each)
```

## ECR Integration

The manifests are configured to use ECR repositories created by Terraform. The image references use placeholder values that need to be replaced with actual ECR repository URIs.

### ECR Repository Pattern

The ECR repositories follow this naming pattern:
- `{ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com/agentcore-gateway/customer-server`
- `{ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com/agentcore-gateway/appointment-server`
- `{ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com/agentcore-gateway/technician-server`

### Updating Image References

After deploying the Terraform infrastructure, update the manifests with actual ECR URIs:

```bash
# Deploy to development environment
make deploy-dev-ecr

# Deploy to production environment
make deploy-prod-ecr
```

The script will:
1. Extract ECR repository URIs from Terraform outputs
2. Replace placeholder values in all Kustomize files
3. Update base and overlay configurations

## Deployment Environments

### Base Configuration
- **Namespace**: `default`
- **Replicas**: 2 per service
- **Image Tags**: `latest`
- **Resources**: CPU 100m-500m, Memory 128Mi-512Mi

### Development Environment
- **Namespace**: `development`
- **Replicas**: 1 per service
- **Image Tags**: `latest`
- **Name Suffix**: `-dev`

### Production Environment
- **Namespace**: `production`
- **Replicas**: 3 per service
- **Image Tags**: `latest` (consider using specific versions)
- **Name Suffix**: `-prod`

## Deployment Commands

```bash
# Deploy base configuration
kubectl apply -k base/

# Deploy to development
kubectl apply -k overlays/development/

# Deploy to production
kubectl apply -k overlays/production/

# Or use Makefile targets
make deploy-manifests    # Base configuration
make deploy-dev         # Development environment
make deploy-prod        # Production environment
```

## Service Configuration

Each service is configured with:

### Health Checks
- **Liveness Probe**: `GET /health` on service port
- **Readiness Probe**: `GET /health` on service port
- **Initial Delay**: 30s (liveness), 5s (readiness)

### Networking
- **Service Type**: ClusterIP (internal cluster communication)
- **Ingress Class**: `alb` (EKS Auto Mode ALB controller)
- **Target Type**: `ip` (direct pod routing)
- **Scheme**: `internet-facing`

### Ports
- **Customer Server**: 8001
- **Appointment Server**: 8002
- **Technician Server**: 8003

## ALB Ingress Configuration

Each service gets its own Application Load Balancer with:
- Internet-facing scheme
- IP target type for direct pod routing
- Health checks pointing to `/health` endpoint
- Default path routing (`/`) to the service

## Security

- **Non-root containers**: All containers run as user 1000
- **Dropped capabilities**: All Linux capabilities dropped
- **No privilege escalation**: Security contexts prevent privilege escalation
- **ECR scanning**: All images scanned for vulnerabilities on push

## Monitoring and Troubleshooting

```bash
# Check deployment status
kubectl get deployments -n default

# Check pod health
kubectl get pods -n default -o wide

# Check service endpoints
kubectl get services -n default

# Check ingress status and ALB URLs
kubectl get ingress -n default

# View pod logs
kubectl logs -l app=customer-server -n default

# Describe ingress for ALB details
kubectl describe ingress customer-server-ingress -n default
```

## Complete Workflow

1. **Deploy Infrastructure**:
   ```bash
   make terraform-apply
   ```

2. **Configure kubectl**:
   ```bash
   # Follow instructions from terraform output
   export KUBECONFIG="/tmp/eks-cluster"
   aws eks --region us-west-2 update-kubeconfig --name eks-cluster
   ```

3. **Deploy with ECR Images**:
   ```bash
   # Deploy to development
   make deploy-dev-ecr

   # Or deploy to production
   make deploy-prod-ecr
   ```

4. **Build and Push Container Images**:
   ```bash
   make build-and-push
   ```

5. **Deploy Applications**:
   ```bash
   make deploy-manifests
   ```

6. **Test Deployment**:
   ```bash
   make test-all-eks
   ```

7. **Access Services**:
   ```bash
   kubectl get ingress
   # Use the ALB URLs to access your services
   ```

## Notes

- The manifests use Kustomize for configuration management
- ECR repositories are created and managed by Terraform
- Each service gets its own ALB for external access
- Auto Mode handles node provisioning and scaling automatically
- Health checks ensure pods are ready before receiving traffic
