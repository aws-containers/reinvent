# EKS Auto Mode Live Demo Guide - Zero-Downtime Upgrades

This guide walks through a live demonstration of EKS Auto Mode's automatic node rollout during cluster upgrades while maintaining application availability.

## Demo Architecture

- **Cluster 1 (1.30)**: Baseline cluster showing current version with working app
- **Cluster 2 (Control Plane: 1.31, Nodes: 1.30)**: Pre-upgraded cluster where Auto Mode is "stuck" due to restrictive PDB - demonstrates Auto Mode respecting PDBs
- **Python App**: Web application with QR code that attendees can scan to verify uptime

## The Demo Story

Cluster 2 will demonstrate a realistic scenario:
- Control plane upgraded to 1.31 (done before demo)
- Nodes still on 1.30 because Auto Mode respects the overly restrictive PDB
- During demo: Fix the PDB configuration
- Auto Mode automatically completes the node rollout
- Application stays up throughout

## Pre-Demo Setup

### 1. Build and Push the Python App

```bash
# Set your ECR repository
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=us-east-1
export ECR_REPO=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/eks-demo-app

# Create ECR repository
aws ecr create-repository --repository-name eks-demo-app --region ${AWS_REGION}

# Login to ECR
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPO}

# Build and push
cd python-app
docker build -t eks-demo-app:latest .
docker tag eks-demo-app:latest ${ECR_REPO}:latest
docker push ${ECR_REPO}:latest
cd ..
```

### 2. Create Cluster 1 (1.30) - Already Running

```bash
# This should already be provisioned
eksctl create cluster -f eks-automode-cluster.yaml

# Wait for cluster to be ready (~15-20 minutes)
```

### 3. Deploy App to Cluster 1

```bash
# Update the image in python-app-workload.yaml with your ECR repo
# Then apply
kubectl apply -f python-app-workload.yaml

# Get the LoadBalancer URL
kubectl get svc eks-demo-app-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# Update the SERVICE_URL in python-app-workload.yaml and re-apply
# Update CLUSTER_VERSION to "1.30"
kubectl apply -f python-app-workload.yaml
```

### 4. Create Cluster 2 and Set Up "Stuck" Upgrade State

```bash
# Step 1: Create cluster at 1.30
eksctl create cluster -f eks-automode-cluster.yaml --name automode-demo-131

# Wait for cluster to be ready (~15-20 minutes)
kubectl config use-context <cluster-2-context>
```

### 5. Deploy App with Restrictive PDB to Cluster 2

```bash
# Deploy with the restrictive PDB configuration
kubectl apply -f python-app-workload-restrictive.yaml

# Wait for app to be ready
kubectl wait --for=condition=available --timeout=300s deployment/eks-demo-app

# Get LoadBalancer URL and update SERVICE_URL in the manifest
LB_URL=$(kubectl get svc eks-demo-app-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "LoadBalancer URL: http://${LB_URL}"

# Update and re-apply with the correct URL
kubectl apply -f python-app-workload-restrictive.yaml

# Verify all pods are running
kubectl get pods -o wide
```

### 6. Upgrade Control Plane (Creates "Stuck" State)

```bash
# Upgrade the control plane to 1.31
# Auto Mode will TRY to upgrade nodes but will be blocked by the restrictive PDB
eksctl upgrade cluster --name automode-demo-131 --version 1.31 --approve

# Wait for control plane upgrade to complete (~15 minutes)

# Verify control plane is 1.31 but nodes are still 1.30
kubectl version --short
kubectl get nodes -o custom-columns=NAME:.metadata.name,VERSION:.status.nodeInfo.kubeletVersion

# You should see:
# - Server Version: v1.31.x (control plane)
# - Node versions: v1.30.x (nodes stuck due to PDB)
```

### 7. Verify "Stuck" State Before Demo

```bash
# Check that nodes are still on 1.30
kubectl get nodes -o wide

# Check PDB status - should show disruptions not allowed
kubectl get pdb eks-demo-app-pdb -o yaml

# Check events - you may see Auto Mode attempting but respecting PDB
kubectl get events --sort-by='.lastTimestamp' | grep -i pdb

# App should still be running fine
curl http://${LB_URL}/health
```

## Live Demo Flow

### Part 1: Show Baseline (Cluster 1 - 1.30)

```bash
# Switch to cluster 1
kubectl config use-context <cluster-1-context>

# Show cluster version
kubectl version --short

# Show nodes
kubectl get nodes -o wide

# Show app running
kubectl get pods -o wide

# Show PDB protecting the app
kubectl get pdb eks-demo-app-pdb -o yaml

# Display the app URL and QR code
# Attendees can scan and see the app running
```

**Talking Points:**
- This is our baseline cluster running Kubernetes 1.30
- Application is distributed across 3 availability zones
- PodDisruptionBudget ensures minimum 4 pods always available
- Attendees can scan the QR code to monitor uptime

### Part 2: Show the "Stuck" Upgrade (Cluster 2)

```bash
# Switch to cluster 2
kubectl config use-context <cluster-2-context>

# Show the version mismatch
echo "=== Control Plane Version ==="
kubectl version --short

echo "=== Node Versions (still on 1.30!) ==="
kubectl get nodes -o custom-columns=NAME:.metadata.name,VERSION:.status.nodeInfo.kubeletVersion,CREATED:.metadata.creationTimestamp

# Show the restrictive PDB
echo "=== Restrictive PDB Configuration ==="
kubectl get pdb eks-demo-app-pdb -o yaml

# Show the restrictive topology spread
echo "=== Restrictive Topology Spread ==="
kubectl get deployment eks-demo-app -o yaml | grep -A 10 topologySpreadConstraints

# Show pods distribution
echo "=== Current Pod Distribution ==="
kubectl get pods -o wide
```

**Talking Points:**
- Control plane is already at 1.31 (upgraded before demo)
- But nodes are STILL at 1.30 - why?
- Auto Mode is respecting our overly restrictive PDB
- PDB requires ALL 3 pods available at all times
- Topology spread requires maxSkew: 0 (all pods on different nodes)
- Auto Mode won't break your app - it respects these constraints!
- This is a common real-world scenario

### Part 3: Fix the Configuration and Watch Auto Mode Complete the Upgrade

```bash
# Open multiple terminals to watch the upgrade:

# Terminal 1: Watch nodes
kubectl get nodes -w

# Terminal 2: Watch pods
kubectl get pods -w

# Terminal 3: Monitor app health
watch -n 1 'curl -s http://<LOADBALANCER_URL>/health'

# Terminal 4: Watch events
kubectl get events -w --field-selector involvedObject.kind=PodDisruptionBudget
```

**Now fix the PDB and topology spread:**

```bash
# Apply the fixed configuration
kubectl apply -f python-app-workload-fixed.yaml

# Watch Auto Mode automatically complete the node upgrade!
```

**Talking Points:**
- We're fixing the PDB to allow 2 pods to be disrupted (minAvailable: 4 out of 6)
- We're relaxing the topology spread constraints
- Auto Mode immediately detects it can now proceed
- Watch as Auto Mode automatically upgrades the nodes!
- Old nodes are cordoned and drained gracefully
- New nodes with 1.31 come up
- Application stays available throughout - check the QR code!
- No manual intervention - Auto Mode handles everything

### Part 4: Monitor the Automatic Rollout

```bash
# Watch node transitions in real-time
kubectl get nodes --sort-by=.metadata.creationTimestamp

# Check node versions - you'll see mix of 1.30 and 1.31 during rollout
kubectl get nodes -o custom-columns=NAME:.metadata.name,VERSION:.status.nodeInfo.kubeletVersion,CREATED:.metadata.creationTimestamp

# Verify pods are rescheduled
kubectl get pods -o wide

# Check PDB status during rollout - should show disruptions allowed now
kubectl get pdb eks-demo-app-pdb -o yaml

# Verify no downtime
kubectl get events --sort-by='.lastTimestamp' | grep -i pdb
```

**Talking Points:**
- Auto Mode is now replacing nodes automatically
- It was waiting for us to fix the configuration!
- Pods are evicted gracefully respecting the NEW PDB
- Topology spread constraints are maintained
- Zero downtime achieved
- This all happens without any manual node group management!

### Part 5: Verify Completion

```bash
# Check all nodes are now on 1.31
kubectl get nodes -o wide

# Verify all nodes show v1.31
kubectl get nodes -o custom-columns=NAME:.metadata.name,VERSION:.status.nodeInfo.kubeletVersion

# Verify app is still running
kubectl get pods -o wide

# Check the app shows updated version
# Visit the LoadBalancer URL or scan QR code

# Verify cluster upgrade completed
eksctl get cluster --name automode-demo-131
```

**Talking Points:**
- All nodes successfully upgraded to 1.31
- Application never went down
- EKS Auto Mode handled everything automatically
- No manual node group management required

## Key Demo Highlights

### What This Demo Shows:

**Part 1: Auto Mode Respects Your Constraints**
- ✅ Control plane upgraded to 1.31
- ✅ Nodes stayed at 1.30 because PDB was too restrictive
- ✅ Auto Mode won't break your app - it respects PDBs!
- ✅ This is intelligent upgrade management

**Part 2: Auto Mode Completes Upgrade When Safe**
- ✅ Fixed the PDB configuration
- ✅ Auto Mode immediately detected it could proceed
- ✅ Provisioned new nodes with Kubernetes 1.31
- ✅ Cordoned old nodes
- ✅ Drained pods gracefully respecting the new PDB
- ✅ Maintained topology spread across AZs
- ✅ Terminated old nodes after successful migration
- ✅ Ensured zero downtime

### What You Didn't Have to Do:
- ❌ Create or manage node groups
- ❌ Calculate node capacity
- ❌ Manually cordon/drain nodes
- ❌ Monitor pod evictions
- ❌ Verify topology constraints
- ❌ Clean up old nodes
- ❌ Trigger any manual rollout process

## Troubleshooting

### If upgrade is stuck:

```bash
# Check cluster upgrade status
eksctl get cluster --name automode-demo-131

# Check if PDB is blocking
kubectl get pdb

# Check pod status
kubectl get pods -o wide

# Check node conditions
kubectl describe nodes

# Check Auto Mode events
kubectl get events --all-namespaces | grep -i automode
```

### If app is not accessible:

```bash
# Check service
kubectl get svc eks-demo-app-service

# Check endpoints
kubectl get endpoints eks-demo-app-service

# Check pod logs
kubectl logs -l app=eks-demo-app --tail=50
```

## Cleanup

```bash
# Delete cluster 1
eksctl delete cluster -f eks-automode-cluster.yaml

# Delete cluster 2
eksctl delete cluster -f eks-automode-cluster-1.31.yaml

# Delete ECR repository
aws ecr delete-repository --repository-name eks-demo-app --force --region us-east-1
```

## Additional Demo Ideas

### Show Upgrade Insights (Optional):

```bash
# Check for upgrade readiness
aws eks list-insights --cluster-name automode-demo-131 --region us-east-1

# Describe specific insights
aws eks describe-insight --cluster-name automode-demo-131 \
  --region us-east-1 --id <insight-id>
```

### Load Testing During Rollout:

```bash
# Generate load to show app stays responsive
kubectl run -it --rm load-generator --image=busybox --restart=Never -- \
  /bin/sh -c "while true; do wget -q -O- http://eks-demo-app-service; done"
```

### Show Cost Optimization:

```bash
# Show Auto Mode selected appropriate instance types
kubectl get nodes -o custom-columns=NAME:.metadata.name,INSTANCE:.metadata.labels.node\\.kubernetes\\.io/instance-type
```
