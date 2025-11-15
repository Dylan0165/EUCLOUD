#!/bin/bash
# Quick deployment script for CI/CD
# Handles PVC deletion and recreation automatically

set -e

echo "🚀 Deploying EUCLOUD with persistent storage..."

# Check if we need to migrate from old storage
NEEDS_MIGRATION=false
if kubectl get pvc eucloud-database-pvc -n eucloud 2>/dev/null | grep -q "local-path"; then
  NEEDS_MIGRATION=true
  echo "⚠️  Detected old local-path storage - migration needed"
fi

if [ "$NEEDS_MIGRATION" = true ]; then
  echo "🔄 Running storage migration..."
  
  # Scale down
  echo "Scaling down deployments..."
  kubectl scale deployment eucloud-backend -n eucloud --replicas=0 --timeout=60s 2>/dev/null || true
  kubectl scale deployment eucloud-frontend -n eucloud --replicas=0 --timeout=60s 2>/dev/null || true
  sleep 5
  
  # Delete old PVCs
  echo "Deleting old PVCs..."
  kubectl delete pvc eucloud-database-pvc eucloud-uploads-pvc -n eucloud --ignore-not-found=true --wait=true --timeout=60s
  kubectl delete pvc eucloud-thumbnails-pvc -n eucloud --ignore-not-found=true --wait=false 2>/dev/null || true
  
  # Clean up orphaned PVs
  kubectl get pv | grep "eucloud" | grep "Released\|Available" | awk '{print $1}' | xargs -r kubectl delete pv 2>/dev/null || true
  
  sleep 3
fi

# Setup VM directories
echo "📁 Setting up VM storage directories..."
sudo mkdir -p /var/eucloud/{database,uploads,thumbnails}
sudo chown -R 1000:1000 /var/eucloud/
sudo chmod -R 755 /var/eucloud/

# Apply configuration
echo "⚙️  Applying Kubernetes manifests..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/pvc.yaml

echo "Waiting for PVs to bind..."
sleep 5

kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/services.yaml
kubectl apply -f k8s/ingress.yaml

echo "⏳ Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=eucloud-backend -n eucloud --timeout=180s || true
kubectl wait --for=condition=ready pod -l app=eucloud-frontend -n eucloud --timeout=180s || true

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Status:"
kubectl get pods -n eucloud
echo ""
kubectl get pvc -n eucloud
echo ""
echo "💾 Storage on VM:"
du -sh /var/eucloud/* 2>/dev/null || echo "Empty (new installation)"
