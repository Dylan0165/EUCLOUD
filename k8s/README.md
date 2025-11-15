# EUCLOUD Kubernetes Deployment Scripts

## Quick Start

### Automated Deployment (Recommended)
The GitHub Actions workflow automatically handles deployment with persistent storage.
Just push to main branch and it deploys automatically.

### Manual Deployment

#### First Time Setup
```bash
cd k8s/
chmod +x deploy-persistent.sh
./deploy-persistent.sh
```

#### Migration from Existing Setup
If you already have EUCLOUD running with `local-path` storage:
```bash
cd k8s/
chmod +x migrate-to-persistent-storage.sh
./migrate-to-persistent-storage.sh
```

This will:
- ✅ Backup your existing data
- ✅ Delete old PVCs with local-path
- ✅ Create new hostPath PVs on VM
- ✅ Restore your data
- ✅ Redeploy with persistent storage

## Scripts Overview

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `deploy-persistent.sh` | Quick deployment with auto-migration | CI/CD, first time setup, updates |
| `migrate-to-persistent-storage.sh` | Full migration with backup/restore | Manual migration, data preservation |
| `setup-vm-storage.sh` | Only create VM directories | Manual setup, troubleshooting |
| `deploy-with-storage.sh` | Complete setup from scratch | Clean installation |

## Storage Locations

After deployment, data is stored on VM at:
```
/var/eucloud/
├── database/     # SQLite database (10GB)
├── uploads/      # User files (50GB)
└── thumbnails/   # Image thumbnails (5GB)
```

## Troubleshooting

### PVC Stuck in Pending
```bash
# Check PV status
kubectl get pv

# Verify VM directories exist
ls -la /var/eucloud/

# Check permissions
sudo chown -R 1000:1000 /var/eucloud/
sudo chmod -R 755 /var/eucloud/
```

### Migration Failed
```bash
# Check if old PVCs are deleted
kubectl get pvc -n eucloud

# Force delete stuck PVCs
kubectl delete pvc eucloud-database-pvc eucloud-uploads-pvc -n eucloud --grace-period=0 --force

# Re-run deployment
./deploy-persistent.sh
```

### Error: spec is immutable
This means old PVCs exist with different storage class.
Run the migration script:
```bash
./migrate-to-persistent-storage.sh
```

Or manually delete and recreate:
```bash
kubectl scale deployment eucloud-backend eucloud-frontend -n eucloud --replicas=0
kubectl delete pvc --all -n eucloud
./deploy-persistent.sh
```

## Verification

```bash
# Check all resources
kubectl get all -n eucloud

# Check PVs and PVCs
kubectl get pv,pvc -n eucloud

# Check pod mounts
kubectl describe pod -n eucloud | grep -A 10 Mounts

# Check VM storage
ls -lah /var/eucloud/
du -sh /var/eucloud/*
```

## Backup & Restore

### Backup
```bash
# On VM
sudo tar -czf eucloud-backup-$(date +%Y%m%d).tar.gz /var/eucloud/
```

### Restore
```bash
# On VM
sudo tar -xzf eucloud-backup-20250115.tar.gz -C /
sudo chown -R 1000:1000 /var/eucloud/

# Restart pods to pick up data
kubectl rollout restart deployment -n eucloud
```
