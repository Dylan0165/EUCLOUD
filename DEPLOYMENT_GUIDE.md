# 🚀 Deployment Guide - EU-CORE-BACKEND naar K3s via GitHub Actions

## Overzicht
Deze guide beschrijft hoe je de EU-CORE-BACKEND (en later EuType) automatisch deploy naar je K3s cluster via GitHub Actions CI/CD.

---

## Wat is Er Veranderd

### ✅ CI/CD Pipeline Updates
1. **Database Migratie Job** - Automatisch uitgevoerd bij deployment
2. **Multi-App Support** - Klaar voor EuType deployment
3. **SHA-tagged Images** - Unieke image tags per commit
4. **Deployment Verificatie** - Uitgebreide status rapportage

### ✅ Deployment Flow
```
Push naar GitHub (main branch)
    ↓
Test Backend (Python + Pytest)
    ↓
Test Frontend (Node + npm build)
    ↓
Build Docker Images (Backend + Frontend)
    ↓
Push naar GitHub Container Registry (ghcr.io)
    ↓
Run Database Migration (one-time job)
    ↓
Deploy to K3s (kubectl apply + rollout)
    ↓
Verify Deployment (health checks)
```

---

## Vereisten

### 1. Self-Hosted Runner op VM
Je hebt al een runner, check status:
```bash
# Op je VM
cd actions-runner
./run.sh --check
```

Als runner niet actief is:
```bash
./run.sh
```

### 2. GitHub Secrets Configureren
Check of deze secrets bestaan in je repo:
- Go to: `https://github.com/Dylan0165/EUCLOUD/settings/secrets/actions`

**Required Secrets:**
- `DOCKERHUB_USERNAME` - Je Docker Hub username
- `DOCKERHUB_TOKEN` - Docker Hub access token

**Optional (automatisch via GITHUB_TOKEN):**
- GitHub Container Registry - Automatisch via `GITHUB_TOKEN`

### 3. Kubernetes Setup op VM
Check of K3s draait:
```bash
kubectl get nodes
kubectl get namespaces
kubectl config current-context
```

---

## Deployment Stappen

### Stap 1: Commit en Push Changes
```bash
# Vanaf je Windows machine
cd "C:\Users\dylan\Desktop\persoonlijk project\EUCLOUD"

# Check status
git status

# Add alle changes
git add .

# Commit met duidelijke message
git commit -m "Transform backend to EU-CORE-BACKEND with multi-app support

- Add app_type field to File model
- Implement user-based storage (/uploads/{owner_id}/{file_id}.ext)
- Add content endpoints (GET/PUT /api/files/{id}/content) for EuType
- Update CORS for multi-app support (ports 30080, 30081)
- Add database migration script
- Update CI/CD for automatic migration on deployment
- Add comprehensive API documentation"

# Push naar GitHub (triggert automatisch CI/CD)
git push origin main
```

### Stap 2: Monitor Deployment
Open GitHub Actions:
```
https://github.com/Dylan0165/EUCLOUD/actions
```

Je ziet 4 jobs:
1. ✅ **Test Backend** - Python tests
2. ✅ **Test Frontend** - npm build
3. 🐳 **Build and Push** - Docker images
4. 🚀 **Deploy** - K3s deployment + migration

### Stap 3: Check Deployment op VM
```bash
# SSH naar je VM
ssh dylan@192.168.124.50

# Check pods (namespace: eucloud)
kubectl get pods -n eucloud

# Check services
kubectl get services -n eucloud

# Check logs van backend
kubectl logs -f deployment/eucloud-backend -n eucloud

# Check migration job (als uitgevoerd)
kubectl get jobs -n eucloud
kubectl logs job/eucloud-migration-<timestamp> -n eucloud
```

### Stap 4: Verify API
```bash
# Health check
curl http://192.168.124.50:30500/health

# API docs (open in browser)
# http://192.168.124.50:30500/docs

# Test login
curl -X POST http://192.168.124.50:30500/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"password123"}'
```

---

## Database Migration

### Automatische Migratie (CI/CD)
Bij deployment wordt automatisch een Kubernetes Job gemaakt die:
1. Checkt of `migrate_to_multiapp.py` bestaat
2. Draait de migratie in een tijdelijke pod
3. Gebruikt dezelfde PVCs als de backend (database + uploads)
4. Wacht max 2 minuten op completion
5. Cleaned up na 100 seconden

### Handmatige Migratie (indien nodig)
Als je de migratie handmatig wilt draaien:
```bash
# Op je VM
kubectl exec -it deployment/eucloud-backend -n eucloud -- python migrate_to_multiapp.py
```

### Migratie Skip
Als de migratie al gedaan is:
- Script detecteert automatisch gemigreerde files
- Skips files die al in user directories staan
- Veilig om meerdere keren te draaien

---

## Troubleshooting

### Pipeline Fails bij Build Step
**Probleem**: Docker build failed
```bash
# Check runner logs op VM
journalctl -u actions-runner -f

# Check Docker status
sudo systemctl status docker
docker ps
```

**Oplossing**:
```bash
# Restart Docker
sudo systemctl restart docker

# Restart runner
cd ~/actions-runner
./svc.sh stop
./svc.sh start
```

### Pipeline Fails bij Deploy Step
**Probleem**: kubectl command failed

```bash
# Check kubeconfig
kubectl config view
echo $KUBECONFIG

# Check runner user permissions
sudo usermod -aG docker <runner-user>
```

**Oplossing**:
```bash
# Ensure runner has kubectl access
cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
chmod 600 ~/.kube/config
```

### Migration Job Hangs
**Probleem**: Migration job niet compleet binnen 2 minuten

```bash
# Check job status
kubectl get jobs -n eucloud
kubectl describe job <job-name> -n eucloud

# Check pod logs
kubectl logs job/<job-name> -n eucloud
```

**Oplossing**:
```bash
# Handmatig migratie draaien
kubectl exec -it deployment/eucloud-backend -n eucloud -- python migrate_to_multiapp.py

# Of delete stuck job
kubectl delete job <job-name> -n eucloud
```

### Pods Crashen Na Deployment
**Probleem**: Backend pods in CrashLoopBackOff

```bash
# Check logs
kubectl logs deployment/eucloud-backend -n eucloud --previous

# Check events
kubectl get events -n eucloud --sort-by='.lastTimestamp'
```

**Oplossing**:
```bash
# Check PVC mounts
kubectl get pvc -n eucloud

# Check database file
kubectl exec -it deployment/eucloud-backend -n eucloud -- ls -la /app/instance/
kubectl exec -it deployment/eucloud-backend -n eucloud -- ls -la /app/uploads/
```

### CORS Errors from Frontend
**Probleem**: EuCloud frontend krijgt CORS errors

**Oplossing**: Check main.py CORS config:
```python
allow_origins=[
    "http://192.168.124.50:30080",  # Must match frontend URL
    "http://192.168.124.50:30081",
    ...
]
```

Re-deploy:
```bash
git add backend/main.py
git commit -m "Fix CORS configuration"
git push origin main
```

---

## Rollback Procedure

Als nieuwe deployment niet werkt:

### Option 1: Rollback via kubectl
```bash
# Rollback to previous version
kubectl rollout undo deployment/eucloud-backend -n eucloud

# Check rollout status
kubectl rollout status deployment/eucloud-backend -n eucloud
```

### Option 2: Re-deploy Specific SHA
```bash
# Find previous working commit SHA
git log --oneline

# Use kubectl to set old image
kubectl set image deployment/eucloud-backend \
  backend=ghcr.io/dylan0165/eucloud-backend:main-<OLD_SHA> \
  -n eucloud
```

### Option 3: Revert Git Commit
```bash
# On Windows
git revert HEAD
git push origin main

# CI/CD will auto-deploy reverted version
```

---

## Post-Deployment Checklist

Na succesvolle deployment:

- [ ] EuCloud frontend bereikbaar op `http://192.168.124.50:30080`
- [ ] Backend API bereikbaar op `http://192.168.124.50:30500`
- [ ] API docs beschikbaar op `http://192.168.124.50:30500/docs`
- [ ] Health check returns 200: `/health`
- [ ] Kan inloggen via EuCloud frontend
- [ ] Files lijsten werkt
- [ ] File upload werkt
- [ ] Files staan in user directories: `/app/uploads/{user_id}/`
- [ ] Content endpoints werken (test met .ty file)
- [ ] Database migratie compleet (check logs)
- [ ] Alle pods running: `kubectl get pods -n eucloud`
- [ ] Geen errors in logs: `kubectl logs -f deployment/eucloud-backend -n eucloud`

---

## Volgende Stappen

### Voor EuType Deployment
Wanneer je EuType frontend klaar hebt:

1. **Push EuType naar GitHub**:
   ```bash
   cd EUTYPE
   git push origin main
   ```

2. **Update EUCLOUD repo** (optioneel - voor unified deployment):
   - Add EuType als submodule, of
   - Deploy EuType apart met eigen CI/CD

3. **Deploy EuType met NodePort 30081**:
   ```yaml
   # k8s/eutype-service.yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: eutype-frontend
     namespace: eucloud
   spec:
     type: NodePort
     ports:
     - port: 80
       targetPort: 80
       nodePort: 30081
     selector:
       app: eutype-frontend
   ```

4. **CORS is al geconfigureerd** in EU-CORE-BACKEND voor port 30081

---

## Monitoring & Maintenance

### Daily Health Checks
```bash
# Quick status check
kubectl get all -n eucloud

# Check resource usage
kubectl top pods -n eucloud

# Check persistent volumes
kubectl get pvc -n eucloud
df -h /var/eucloud/
```

### Weekly Maintenance
```bash
# Clean up old images
docker system prune -a -f

# Check logs for errors
kubectl logs deployment/eucloud-backend -n eucloud --since=24h | grep ERROR

# Backup database
kubectl exec -it deployment/eucloud-backend -n eucloud -- \
  cp /app/instance/eucloud.db /app/instance/eucloud.db.backup
```

### Monthly Tasks
- Review storage quota usage
- Update dependencies (requirements.txt, package.json)
- Check for security updates
- Review and clean old migration jobs

---

## Environment Variables

Backend deployment gebruikt deze env vars (in `backend-deployment.yaml`):

```yaml
env:
- name: FLASK_ENV
  value: "production"
- name: SERVER_IP
  value: "192.168.124.50"
- name: SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: eucloud-secrets
      key: secret-key
- name: JWT_SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: eucloud-secrets
      key: jwt-secret-key
```

Als je secrets moet updaten:
```bash
kubectl edit secret eucloud-secrets -n eucloud
```

---

## Success Criteria ✅

Je deployment is succesvol als:

1. ✅ CI/CD pipeline compleet zonder errors
2. ✅ Backend pods running (2 replicas)
3. ✅ Frontend pods running
4. ✅ Services exposed op NodePorts 30080, 30500
5. ✅ Database migratie uitgevoerd
6. ✅ Files in user directories
7. ✅ API endpoints werken (test via /docs)
8. ✅ EuCloud frontend werkt
9. ✅ Content endpoints beschikbaar voor EuType
10. ✅ Logs tonen geen critical errors

---

## Quick Commands Reference

```bash
# Deploy
git push origin main

# Check status
kubectl get pods -n eucloud
kubectl get svc -n eucloud

# View logs
kubectl logs -f deployment/eucloud-backend -n eucloud

# Restart deployment
kubectl rollout restart deployment/eucloud-backend -n eucloud

# Scale replicas
kubectl scale deployment/eucloud-backend --replicas=3 -n eucloud

# Port forward (for local testing)
kubectl port-forward svc/eucloud-backend 5000:5000 -n eucloud

# Execute commands in pod
kubectl exec -it deployment/eucloud-backend -n eucloud -- bash

# Delete and redeploy
kubectl delete -f k8s/
kubectl apply -f k8s/

# Watch deployment
watch kubectl get pods -n eucloud
```

---

## 🎯 Ready to Deploy!

Nu kun je deployen:

```bash
cd "C:\Users\dylan\Desktop\persoonlijk project\EUCLOUD"
git add .
git commit -m "EU-CORE-BACKEND transformation complete - ready for multi-app deployment"
git push origin main
```

Monitor op: https://github.com/Dylan0165/EUCLOUD/actions

Succes! 🚀
