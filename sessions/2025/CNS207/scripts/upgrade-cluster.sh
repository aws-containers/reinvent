#!/bin/bash
set -e

# Script to upgrade the EKS cluster control plane
# This will upgrade the control plane to 1.31, but nodes will stay at 1.30 due to restrictive PDB

CLUSTER_NAME=${1:-"automode-demo-131"}
TARGET_VERSION=${2:-"1.31"}

echo "🚀 EKS Auto Mode Upgrade Demo"
echo "================================"
echo ""
echo "Cluster: ${CLUSTER_NAME}"
echo "Target Version: ${TARGET_VERSION}"
echo ""

# Check current cluster version
echo "📊 Current cluster status:"
CURRENT_VERSION=$(kubectl version -o json 2>/dev/null | grep -o '"gitVersion":"[^"]*"' | head -2 | tail -1 | cut -d'"' -f4)
echo "Control Plane Version: ${CURRENT_VERSION}"
echo ""

# Show current node versions
echo "📊 Current node versions:"
kubectl get nodes -o custom-columns=NAME:.metadata.name,VERSION:.status.nodeInfo.kubeletVersion
echo ""

# Show PDB status
echo "📊 PodDisruptionBudget status:"
kubectl get pdb eks-demo-app-pdb
echo ""

# Show pod distribution
echo "📊 Pod distribution:"
kubectl get pods -o wide | grep eks-demo-app | awk '{print $7}' | sort | uniq -c
echo ""

# Confirm upgrade
read -p "⚠️  Ready to upgrade control plane to ${TARGET_VERSION}? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Upgrade cancelled"
    exit 0
fi

echo ""
echo "🔄 Starting control plane upgrade..."
echo "This will take approximately 15-20 minutes"
echo ""

# Upgrade the cluster
eksctl upgrade cluster --name ${CLUSTER_NAME} --version ${TARGET_VERSION} --approve

echo ""
echo "✅ Control plane upgrade complete!"
echo ""
echo "📊 Checking cluster status..."
kubectl version -o json | grep -o '"gitVersion":"[^"]*"' | head -2
echo ""

echo "📊 Node versions (should still be at 1.30):"
kubectl get nodes -o custom-columns=NAME:.metadata.name,VERSION:.status.nodeInfo.kubeletVersion
echo ""

echo "📊 PDB status (should show 0 allowed disruptions):"
kubectl get pdb eks-demo-app-pdb
echo ""

echo "📊 Checking Auto Mode events (looking for node rollout attempts):"
kubectl get events --all-namespaces --sort-by='.lastTimestamp' | grep -i "node\|drain\|evict" | tail -10
echo ""

echo "📊 Check for Auto Mode compute logs:"
kubectl logs -n kube-system -l app.kubernetes.io/name=eks-pod-identity-agent --tail=20 2>/dev/null || echo "No Auto Mode specific logs available via kubectl"
echo ""

echo "✅ Upgrade complete!"
echo ""
echo "🎯 Demo Status:"
echo "  ✅ Control Plane: ${TARGET_VERSION}"
echo "  ✅ Nodes: Still at 1.30 (blocked by PDB)"
echo "  ✅ Application: Still running"
echo ""
echo "📱 Check the app URL to see the version mismatch:"
LB_URL=$(kubectl get svc eks-demo-app-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "   http://${LB_URL}"
echo ""
echo "🎬 Next step for demo:"
echo "   Apply the fixed manifest to allow Auto Mode to complete the rollout:"
echo "   kubectl apply -f python-app-workload-fixed.yaml"
echo ""
