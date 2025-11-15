#!/bin/bash
# Migration script: Switch from local-path to manual (hostPath) storage
# This script safely migrates existing PVCs to the new persistent storage setup

set -e

echo "🔄 Migrating EUCLOUD storage from local-path to manual (hostPath)..."
echo ""

# Step 1: Backup current data (if pods are running)
echo "📦 Step 1/6: Backing up current data from pods..."
BACKEND_POD=$(kubectl get pods -n eucloud -l app=eucloud-backend -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [ -n "$BACKEND_POD" ]; then
  echo "Found backend pod: $BACKEND_POD"
  echo "Creating backup directory..."
  mkdir -p /tmp/eucloud-migration-backup
  
  echo "Copying uploads..."
  kubectl exec -n eucloud $BACKEND_POD -- tar czf - -C /app uploads 2>/dev/null | tar xzf - -C /tmp/eucloud-migration-backup/ || echo "No uploads to backup"
  
  echo "Copying database..."
  kubectl exec -n eucloud $BACKEND_POD -- tar czf - -C /app instance 2>/dev/null | tar xzf - -C /tmp/eucloud-migration-backup/ || echo "No database to backup"
  
  echo "✅ Backup completed to /tmp/eucloud-migration-backup/"
else
  echo "⚠️  No running backend pod found, skipping backup"
fi
echo ""

# Step 2: Scale down deployments
echo "⏸️  Step 2/6: Scaling down deployments..."
kubectl scale deployment eucloud-backend -n eucloud --replicas=0 2>/dev/null || echo "Backend deployment not found"
kubectl scale deployment eucloud-frontend -n eucloud --replicas=0 2>/dev/null || echo "Frontend deployment not found"
echo "Waiting for pods to terminate..."
sleep 10
echo "✅ Deployments scaled down"
echo ""

# Step 3: Delete old PVCs and PVs
echo "🗑️  Step 3/6: Removing old PVCs and PVs..."
kubectl delete pvc eucloud-database-pvc -n eucloud --ignore-not-found=true --wait=true
kubectl delete pvc eucloud-uploads-pvc -n eucloud --ignore-not-found=true --wait=true
kubectl delete pvc eucloud-thumbnails-pvc -n eucloud --ignore-not-found=true --wait=true

# Also delete auto-created PVs from local-path provisioner
kubectl get pv | grep eucloud | awk '{print $1}' | xargs -r kubectl delete pv --wait=false 2>/dev/null || true

echo "Waiting for PVCs to be fully deleted..."
sleep 5
echo "✅ Old storage removed"
echo ""

# Step 4: Setup VM storage directories
echo "📁 Step 4/6: Setting up persistent storage on VM..."
sudo mkdir -p /var/eucloud/database
sudo mkdir -p /var/eucloud/uploads
sudo mkdir -p /var/eucloud/thumbnails

sudo chown -R 1000:1000 /var/eucloud/
sudo chmod -R 755 /var/eucloud/
echo "✅ VM storage directories created"
echo ""

# Step 5: Restore backup to VM storage
if [ -d "/tmp/eucloud-migration-backup/uploads" ]; then
  echo "📥 Step 5/6: Restoring data to VM storage..."
  
  if [ -d "/tmp/eucloud-migration-backup/uploads" ]; then
    echo "Restoring uploads..."
    sudo cp -r /tmp/eucloud-migration-backup/uploads/* /var/eucloud/uploads/ 2>/dev/null || echo "No uploads to restore"
  fi
  
  if [ -d "/tmp/eucloud-migration-backup/instance" ]; then
    echo "Restoring database..."
    sudo cp -r /tmp/eucloud-migration-backup/instance/* /var/eucloud/database/ 2>/dev/null || echo "No database to restore"
  fi
  
  sudo chown -R 1000:1000 /var/eucloud/
  echo "✅ Data restored"
else
  echo "⏭️  Step 5/6: No backup to restore, skipping..."
fi
echo ""

# Step 6: Apply new PVs and PVCs
echo "⚙️  Step 6/6: Creating new persistent volumes..."
kubectl apply -f k8s/pvc.yaml
echo "Waiting for PVs to be created..."
sleep 5

# Verify PVs are available
echo ""
echo "Checking PV status..."
kubectl get pv | grep eucloud || echo "⚠️  No PVs found yet"
echo ""

# Scale deployments back up
echo "▶️  Scaling deployments back up..."
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

echo ""
echo "⏳ Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=eucloud-backend -n eucloud --timeout=300s || echo "⚠️  Backend pods not ready yet"
kubectl wait --for=condition=ready pod -l app=eucloud-frontend -n eucloud --timeout=300s || echo "⚠️  Frontend pods not ready yet"

echo ""
echo "✅ Migration complete!"
echo ""
echo "📊 Current status:"
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
echo "💾 VM Storage:"
ls -lah /var/eucloud/
echo ""
du -sh /var/eucloud/*
echo ""
echo "🎉 EUCLOUD is now using persistent hostPath storage!"
echo "   Data location: /var/eucloud/"
echo "   Your data will now survive pod crashes and K3s restarts!"
echo ""
echo "🧹 Cleanup: You can now remove the backup:"
echo "   sudo rm -rf /tmp/eucloud-migration-backup/"
