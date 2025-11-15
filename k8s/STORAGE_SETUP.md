# EUCLOUD Persistent Storage Setup

## Overview
EUCLOUD uses persistent storage similar to Nextcloud's approach - all data is stored on the VM's filesystem and mounted into Kubernetes pods. This ensures data survives pod crashes, restarts, and even cluster rebuilds.

## Storage Architecture

### VM Storage Locations
```
/var/eucloud/
├── database/     # SQLite database (10GB)
├── uploads/      # User files (50GB)  
└── thumbnails/   # Image thumbnails (5GB)
```

### Kubernetes Resources
- **PersistentVolume (PV)**: Maps VM directories to Kubernetes
- **PersistentVolumeClaim (PVC)**: Requests storage for pods
- **hostPath**: Direct mount from VM filesystem

## Why This Approach?

✅ **Survives pod crashes** - Data stays on VM
✅ **Survives cluster rebuilds** - Just remount existing directories
✅ **Easy backups** - Simple `rsync` or `tar` of `/var/eucloud/`
✅ **Nextcloud-style reliability** - Battle-tested pattern
✅ **No data loss** - Even if K3s completely fails

## Deployment

### First Time Setup
```bash
cd k8s/
chmod +x deploy-with-storage.sh setup-vm-storage.sh
./deploy-with-storage.sh
```

This will:
1. Create `/var/eucloud/` directories on VM
2. Set proper permissions
3. Deploy Kubernetes PVs and PVCs
4. Deploy backend and frontend pods with persistent mounts

### Verify Storage
```bash
# Check VM directories
ls -la /var/eucloud/

# Check Kubernetes PVs
kubectl get pv

# Check PVCs
kubectl get pvc -n eucloud

# Check which pods are using storage
kubectl describe pod -n eucloud | grep -A 5 Volumes
```

## Backup & Restore

### Backup Data
```bash
# On VM 192.168.124.50
sudo tar -czf eucloud-backup-$(date +%Y%m%d).tar.gz /var/eucloud/

# Or use rsync to remote location
rsync -avz /var/eucloud/ backup-server:/backups/eucloud/
```

### Restore Data
```bash
# On VM 192.168.124.50
sudo tar -xzf eucloud-backup-20250115.tar.gz -C /

# Redeploy (will use existing data)
cd k8s/
./deploy-with-storage.sh
```

## Troubleshooting

### Pod can't write to storage
```bash
# Fix permissions
sudo chown -R 1000:1000 /var/eucloud/
sudo chmod -R 755 /var/eucloud/
```

### PVC stuck in Pending
```bash
# Check if PV exists
kubectl get pv

# Delete and recreate
kubectl delete pvc <pvc-name> -n eucloud
kubectl apply -f pvc.yaml
```

### Data not persisting
```bash
# Verify hostPath mount
kubectl describe pod <pod-name> -n eucloud | grep -A 10 Mounts

# Check VM directory
ls -la /var/eucloud/uploads/
```

## Comparison with Other Approaches

| Approach | Data Survives Pod Crash | Data Survives Cluster Rebuild | Easy Backup | Used By |
|----------|------------------------|------------------------------|-------------|---------|
| **hostPath (our choice)** | ✅ Yes | ✅ Yes | ✅ Easy | Nextcloud, GitLab |
| emptyDir | ❌ No | ❌ No | ❌ No | Temporary only |
| local-path (K3s default) | ✅ Yes | ⚠️ Maybe | ⚠️ Complex | Small deployments |
| NFS/Ceph | ✅ Yes | ✅ Yes | ⚠️ Complex | Large clusters |

## Storage Monitoring

### Check disk usage
```bash
# On VM
df -h /var/eucloud/
du -sh /var/eucloud/*

# Inside pod
kubectl exec -it <backend-pod> -n eucloud -- df -h
kubectl exec -it <backend-pod> -n eucloud -- du -sh /app/uploads
```

### Monitor growth
```bash
# Create monitoring script
watch -n 60 'du -sh /var/eucloud/*'
```

## Maintenance

### Clean old thumbnails
```bash
# Find thumbnails older than 30 days
find /var/eucloud/thumbnails/ -type f -mtime +30 -delete
```

### Expand storage
```bash
# Update PV size in pvc.yaml
# Then reapply
kubectl apply -f pvc.yaml

# Note: hostPath doesn't enforce size limits,
# actual limit is VM disk space
```

## Security

- Storage directories owned by UID 1000 (pod user)
- Files not world-readable
- Database not directly exposed to network
- All access through backend API with JWT auth

## Migration from emptyDir

If you previously used emptyDir:
```bash
# 1. Copy data from running pod
kubectl cp eucloud/<old-pod>:/app/uploads /tmp/uploads-backup

# 2. Deploy new persistent storage
./deploy-with-storage.sh

# 3. Restore data
sudo cp -r /tmp/uploads-backup/* /var/eucloud/uploads/

# 4. Fix permissions
sudo chown -R 1000:1000 /var/eucloud/
```
