#!/bin/bash
# Deploy EUCLOUD with persistent storage to K3s
# Run this script on your VM at 192.168.124.50

set -e

echo "🚀 Deploying EUCLOUD to K3s with persistent storage..."
echo ""

# Step 1: Setup VM storage directories
echo "📁 Step 1/4: Setting up persistent storage on VM..."
chmod +x ./setup-vm-storage.sh
./setup-vm-storage.sh
echo ""

# Step 2: Delete old PVCs to recreate with new configuration
echo "🗑️  Step 2/4: Cleaning up old storage (if exists)..."
kubectl delete pvc eucloud-database-pvc -n eucloud --ignore-not-found=true
kubectl delete pvc eucloud-uploads-pvc -n eucloud --ignore-not-found=true
kubectl delete pvc eucloud-thumbnails-pvc -n eucloud --ignore-not-found=true
kubectl delete pv eucloud-database-pv --ignore-not-found=true
kubectl delete pv eucloud-uploads-pv --ignore-not-found=true
kubectl delete pv eucloud-thumbnails-pv --ignore-not-found=true
echo "✅ Old storage cleaned up"
echo ""

# Step 3: Apply new configuration
echo "⚙️  Step 3/4: Applying Kubernetes manifests..."
kubectl apply -f namespace.yaml
kubectl apply -f secrets.yaml
kubectl apply -f pvc.yaml
sleep 5  # Wait for PVs to bind

kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f services.yaml
kubectl apply -f ingress.yaml
echo "✅ Manifests applied"
echo ""

# Step 4: Wait for pods to be ready
echo "⏳ Step 4/4: Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=eucloud-backend -n eucloud --timeout=300s
kubectl wait --for=condition=ready pod -l app=eucloud-frontend -n eucloud --timeout=300s
echo "✅ All pods ready!"
echo ""

# Show status
echo "📊 Deployment Status:"
echo ""
echo "Persistent Volumes:"
kubectl get pv | grep eucloud
echo ""
echo "Persistent Volume Claims:"
kubectl get pvc -n eucloud
echo ""
echo "Pods:"
kubectl get pods -n eucloud
echo ""
echo "Services:"
kubectl get svc -n eucloud
echo ""
echo "🎉 EUCLOUD deployed successfully!"
echo ""
echo "📍 Access your application at: http://192.168.124.50:30080"
echo "💾 Data is stored persistently on VM at /var/eucloud/"
echo ""
echo "🔍 Verify persistent storage:"
echo "   ls -la /var/eucloud/"
