#!/bin/bash
set -e

# Script to delete the demo cluster

CLUSTER_NAME=${1:-"automode-demo"}

echo "🗑️  EKS Auto Mode Demo - Cleanup"
echo "================================"
echo ""
echo "Cluster to delete: ${CLUSTER_NAME}"
echo ""

# Show current cluster
echo "📊 Current cluster info:"
eksctl get cluster --name ${CLUSTER_NAME} 2>/dev/null || echo "Cluster not found or not accessible"
echo ""

# Confirm deletion
read -p "⚠️  Are you sure you want to DELETE cluster '${CLUSTER_NAME}'? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Deletion cancelled"
    exit 0
fi

echo ""
echo "🗑️  Deleting cluster ${CLUSTER_NAME}..."
echo "This will take approximately 10-15 minutes"
echo ""

# Delete the cluster
eksctl delete cluster --name ${CLUSTER_NAME} --wait

echo ""
echo "✅ Cluster deleted successfully!"
echo ""
echo "🎯 To recreate the demo:"
echo "   1. Create cluster: eksctl create cluster -f eks-automode-cluster-1.31.yaml"
echo "   2. Deploy app: kubectl apply -f python-app-workload-restrictive.yaml"
echo "   3. Upgrade cluster: bash scripts/upgrade-cluster.sh ${CLUSTER_NAME} 1.31"
echo ""
