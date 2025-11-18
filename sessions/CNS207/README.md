# CNS207 | Accelerate container migrations with Amazon EKS Auto Mode

As organizations migrate containerized workloads, they often face operational challenges and disruptions. Amazon EKS Auto Mode simplifies this transition, addressing common hurdles when moving to Amazon EKS. This session demonstrates how Auto Mode streamlines the shift from traditional environments or alternative orchestration solutions. Through practical examples, learn how Amazon EKS Auto Mode automates cluster provisioning, scaling, and management, enabling your team to seamlessly migrate applications rather than be tied down by infrastructure operations. Discover how to leverage these capabilities to accelerate your container migration initiatives, reduce operational overhead, and achieve a smooth transition to Amazon EKS without disrupting existing workloads.

# EKS Auto Mode Demo - Zero-Downtime Upgrades

Live demonstration of EKS Auto Mode's intelligent node rollout during cluster upgrades, showcasing how Auto Mode respects PodDisruptionBudgets while maintaining application availability.

## 🎯 Demo Overview

This demo shows:
- **Control plane upgrade** from Kubernetes 1.30 to 1.31
- **Auto Mode respecting PDBs** - nodes stay at 1.30 when PDB is too restrictive
- **Live visual monitoring** - Interactive Python web app with real-time cluster topology
- **Zero-downtime rollout** - fixing PDB allows Auto Mode to complete the upgrade automatically

### 📱 Visual Demo Application

The demo includes a **custom-built Python web application** that provides:
- **Real-time cluster visualization** - See nodes and pods as visual boxes
- **Version tracking** - Control plane and node versions displayed prominently
- **QR code access** - Scan with your phone to monitor during the demo
- **Auto-refresh** - Updates every 3 seconds to show live changes
- **Mobile-responsive design** - Perfect for audience members to follow along

**Access the app at:** `http://<LOADBALANCER_URL>` (obtained after deployment)

## 📋 Prerequisites

```bash
# Install required tools
brew install eksctl docker

# Verify AWS credentials
aws sts get-caller-identity

# Ensure Docker is running
docker ps
```

## 🚀 Quick Start

### 1. Build and Push the Demo App

```bash
# Build the Python app and push to ECR
export AWS_REGION=us-east-1
bash scripts/build-and-push.sh
```

### 2. Create the Cluster

```bash
# Create EKS 1.30 cluster with Auto Mode
eksctl create cluster -f eks-automode-cluster.yaml

# Wait ~15-20 minutes for cluster creation
```

### 3. Deploy the Application with Restrictive PDB

```bash
# Deploy app with restrictive PDB that blocks upgrades
kubectl apply -f python-app-workload-restrictive.yaml

# Wait for pods to be ready
kubectl get pods -o wide

# Get the LoadBalancer URL for the visual demo app
LB_URL=$(kubectl get svc eks-demo-app-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "🌐 Demo App URL: http://${LB_URL}"
echo "📱 Share this URL or QR code with your audience!"
```

**Open the URL in your browser** to see the live cluster visualization!

### 4. Upgrade the Cluster (Pre-Demo)

```bash
# Upgrade control plane to 1.31
bash scripts/upgrade-cluster.sh automode-demo 1.31

# This upgrades the control plane but nodes stay at 1.30 (blocked by PDB)
```

## 🎬 Live Demo Flow

### Part 1: Show the "Stuck" Upgrade

**Display the visual app on screen** - Open the LoadBalancer URL in your browser

```bash
# Show cluster status
kubectl version
kubectl get nodes -o custom-columns=NAME:.metadata.name,VERSION:.status.nodeInfo.kubeletVersion

# Show PDB blocking
kubectl get pdb eks-demo-app-pdb

# Show Auto Mode events
kubectl get events --all-namespaces --sort-by='.lastTimestamp' | grep -i "failed.*drain"
```

**Key Points:**
- **Visual app shows:** Control plane v1.31, Nodes v1.30
- PDB shows 0 allowed disruptions
- Auto Mode events show "Failed to drain node"
- **Audience can scan QR code** to monitor on their phones

### Part 2: Fix the Configuration

```bash
# Apply the fixed manifest with relaxed PDB
kubectl apply -f python-app-workload-fixed.yaml

# Watch Auto Mode complete the rollout
watch -n 2 'kubectl get nodes -o custom-columns=NAME:.metadata.name,VERSION:.status.nodeInfo.kubeletVersion'
```

**Key Points:**
- PDB now allows 2 disruptions (minAvailable: 4 out of 6)
- Auto Mode immediately starts draining old nodes
- New v1.31 nodes come up
- Pods migrate gracefully
- Application stays available throughout

### Part 3: Watch the Visual App Update in Real-Time

**Keep the app visible on screen throughout the demo:**
- See nodes change from v1.30 to v1.31 in real-time
- Watch pods migrate between nodes
- Observe the cluster topology evolve
- Verify zero downtime - app never stops responding
- **Audience members** can follow along on their phones via QR code

## 📱 Visual Demo Application

The custom-built Python web app is the **centerpiece of this demo**, providing real-time visualization:

### Features
- **🎨 Visual Cluster Topology** - Node boxes with pods inside, color-coded by status
- **📊 Version Tracking** - Control plane and node versions displayed at the top
- **🔄 Real-time Updates** - Auto-refreshes every 3 seconds to show live changes
- **📱 QR Code** - Audience can scan to monitor on their phones
- **📲 Mobile-Responsive** - Perfect viewing on any device
- **🖥️ Node Details** - Each node shows its Kubernetes version
- **🔷 Pod Status** - See which pods are running on which nodes

### What Audience Members Will See
1. **Before upgrade:** All nodes showing v1.30
2. **During upgrade:** Control plane v1.31, nodes still v1.30 (blocked)
3. **After fix:** Nodes gradually changing to v1.31
4. **Throughout:** Application stays green and responsive

### Technical Details
- Built with Flask and Python
- Uses Kubernetes API to fetch real-time cluster state
- Generates QR code dynamically based on LoadBalancer URL
- Requires RBAC permissions to read nodes and pods (included in manifests)

## 🛠️ Automation Scripts

### `scripts/build-and-push.sh`
Builds the Docker image for the visual demo app and pushes to ECR
```bash
bash scripts/build-and-push.sh
```

### `scripts/upgrade-cluster.sh`
Upgrades the cluster control plane with safety checks and status display
```bash
bash scripts/upgrade-cluster.sh <cluster-name> <version>
# Example: bash scripts/upgrade-cluster.sh automode-demo-131 1.31
```

### `scripts/cleanup-cluster.sh`
Deletes the demo cluster and cleans up resources
```bash
bash scripts/cleanup-cluster.sh <cluster-name>
# Example: bash scripts/cleanup-cluster.sh automode-demo-131
```

## 🔑 Key Configuration Details

### Restrictive PDB (Blocks Upgrade)
- **Replicas**: 6 pods
- **minAvailable**: 6 (all pods must be available)
- **Topology Spread**: maxSkew: 3 (spreads across 2+ nodes)
- **Result**: Auto Mode cannot drain any node

### Fixed PDB (Allows Upgrade)
- **Replicas**: 6 pods
- **minAvailable**: 4 (allows 2 pods to be disrupted)
- **Topology Spread**: Same as restrictive
- **Result**: Auto Mode can drain nodes one at a time

### Load Balancer Health Checks
- **Interval**: 5 seconds
- **Timeout**: 3 seconds
- **Healthy threshold**: 2 checks
- **Registration time**: ~10 seconds (fast!)

### Pod Lifecycle
- **Termination grace period**: 60 seconds
- **preStop hook**: 15 second sleep for LB deregistration
- **Rolling update**: maxSurge: 2, maxUnavailable: 1

## 🎯 Key Auto Mode Benefits Demonstrated

✅ **Respects PodDisruptionBudgets** - Won't break your app  
✅ **Automatic node provisioning** - No manual node group management  
✅ **Intelligent rollout** - Detects when it can proceed  
✅ **Zero downtime** - Application stays available throughout  
✅ **Graceful draining** - Respects termination grace periods  
✅ **Topology awareness** - Maintains pod distribution  
✅ **Fewer add-ons to manage** - Auto Mode includes essential add-ons automatically (VPC CNI, kube-proxy, CoreDNS, AWS Load Balancer Controller, EBS CSI driver, etc.)  

## 🧹 Cleanup

```bash
# Delete the cluster
bash scripts/cleanup-cluster.sh automode-demo-131

# Delete ECR repository (optional)
aws ecr delete-repository --repository-name eks-demo-app --force --region us-east-1
```

## 📚 Additional Resources

- [EKS Auto Mode Documentation](https://docs.aws.amazon.com/eks/latest/userguide/automode.html)
- [PodDisruptionBudget Best Practices](https://kubernetes.io/docs/tasks/run-application/configure-pdb/)
- [EKS Cluster Upgrades](https://docs.aws.amazon.com/eks/latest/userguide/update-cluster.html)

## 🐛 Troubleshooting

### Pods not spreading across nodes
Check topology spread constraints and ensure enough nodes are available.

### LoadBalancer not accessible
Verify security groups and that the service annotation includes `internet-facing`.

### Auto Mode not upgrading nodes
Check PDB status with `kubectl get pdb` and events with `kubectl get events`.

### Image pull errors
Ensure ECR repository exists and pods have proper IAM permissions.
