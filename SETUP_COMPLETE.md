# ✅ EUCLOUD - CI/CD Setup Complete!

## 📦 Wat is er aangemaakt:

### 1. Docker Configuratie
- ✅ `backend/Dockerfile` - Flask backend container
- ✅ `frontend/Dockerfile` - React frontend container (met Nginx)
- ✅ `frontend/nginx.conf` - Nginx configuratie
- ✅ `docker-compose.yml` - Lokale Docker ontwikkeling

### 2. Kubernetes Manifests (k8s/)
- ✅ `namespace.yaml` - EUCLOUD namespace
- ✅ `pvc.yaml` - Persistent storage (50GB uploads, 10GB database)
- ✅ `backend-deployment.yaml` - Backend deployment (2 replicas)
- ✅ `frontend-deployment.yaml` - Frontend deployment (2 replicas)
- ✅ `services.yaml` - Kubernetes services
- ✅ `secrets.yaml` - Template voor secrets (UPDATE DEZE!)
- ✅ `ingress.yaml` - Ingress met SSL

### 3. GitHub Actions CI/CD (.github/workflows/)
- ✅ `ci-cd.yml` - Complete pipeline:
  - Test backend & frontend
  - Build Docker images
  - Push naar GitHub Container Registry
  - Deploy naar Kubernetes

### 4. Documentatie
- ✅ `README.md` - Project documentatie
- ✅ `DEPLOYMENT.md` - Volledige deployment guide
- ✅ `deploy.sh` - Automated deployment script
- ✅ `.gitignore` - Git ignore configuratie

### 5. Code
- ✅ Alle backend code (Flask API)
- ✅ Alle frontend code (React app)
- ✅ Database migratie script

## 🚀 Volgende Stappen:

### Stap 1: GitHub Repository Configureren ✅
**DONE!** Code is al gepusht naar: https://github.com/Dylan0165/EUCLOUD

### Stap 2: GitHub Secrets Instellen
Ga naar: https://github.com/Dylan0165/EUCLOUD/settings/secrets/actions

**Voeg toe:**

1. **KUBE_CONFIG** (vereist voor deployment)
   ```powershell
   # Windows PowerShell:
   $config = Get-Content ~/.kube/config -Raw
   [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($config))
   ```
   Kopieer de output en voeg toe als secret.

### Stap 3: Kubernetes Secrets Aanmaken

**BELANGRIJK:** Update `k8s/secrets.yaml` VOOR je deploy!

```powershell
# Genereer sterke secrets:
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
```

Run dit 2x en update de secrets in `k8s/secrets.yaml`.

### Stap 4: Deploy naar Kubernetes

**Optie A: Via GitHub Actions (Aanbevolen)**
```bash
git push origin main
```
De pipeline doet alles automatisch!

**Optie B: Handmatig**
```bash
# Windows (Git Bash):
chmod +x deploy.sh
./deploy.sh

# Of handmatig:
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/services.yaml
```

### Stap 5: Controleer Deployment

```bash
# Check pods
kubectl get pods -n eucloud

# Check services
kubectl get services -n eucloud

# Check logs
kubectl logs -f deployment/eucloud-backend -n eucloud
```

### Stap 6: Toegang tot Applicatie

```bash
# Get LoadBalancer IP
kubectl get service eucloud-frontend -n eucloud

# Voor Minikube:
minikube service eucloud-frontend -n eucloud --url
```

## 🔧 Configuratie Aanpassen

### Backend API URL in Frontend

Edit `k8s/frontend-deployment.yaml` en voeg environment variable toe:

```yaml
env:
- name: VITE_API_URL
  value: "http://api.eucloud.yourdomain.com"
```

### Custom Domain met SSL

1. Update `k8s/ingress.yaml` met je domain
2. Installeer cert-manager in cluster
3. Deploy ingress: `kubectl apply -f k8s/ingress.yaml`

## 📊 CI/CD Pipeline Flows

### Bij elke Push naar `main`:
1. ✅ Test backend (flake8, pytest)
2. ✅ Test frontend (lint, build)
3. ✅ Build Docker images
4. ✅ Push naar `ghcr.io/dylan0165/eucloud-*`
5. ✅ Deploy naar Kubernetes cluster
6. ✅ Rolling update deployments
7. ✅ Verify deployment health

### Bij Pull Request:
1. ✅ Test backend
2. ✅ Test frontend
3. ❌ Geen deployment (alleen testen)

## 🎯 Tips

### Lokaal Testen met Docker
```bash
docker-compose up -d
# App beschikbaar op http://localhost
```

### Database Backup (Kubernetes)
```bash
kubectl exec deployment/eucloud-backend -n eucloud -- \
  tar -czf /tmp/backup.tar.gz /app/instance
  
kubectl cp eucloud/eucloud-backend-xxx:/tmp/backup.tar.gz ./backup.tar.gz
```

### Logs Bekijken
```bash
# Backend logs
kubectl logs -f deployment/eucloud-backend -n eucloud

# Frontend logs
kubectl logs -f deployment/eucloud-frontend -n eucloud

# Alle pods
kubectl logs -f -l app=eucloud-backend -n eucloud
```

### Debugging
```bash
# Port forward backend
kubectl port-forward service/eucloud-backend 5000:5000 -n eucloud

# Port forward frontend
kubectl port-forward service/eucloud-frontend 8080:80 -n eucloud

# Shell in pod
kubectl exec -it deployment/eucloud-backend -n eucloud -- /bin/bash
```

## 🔒 Security Checklist

- [ ] Update secrets in `k8s/secrets.yaml`
- [ ] Maak GitHub Personal Access Token voor packages
- [ ] Set up RBAC in Kubernetes
- [ ] Enable network policies
- [ ] Scan Docker images voor vulnerabilities
- [ ] Use HTTPS met valid SSL certificate
- [ ] Regular backups van database

## 📈 Scaling

```bash
# Scale backend
kubectl scale deployment eucloud-backend --replicas=5 -n eucloud

# Scale frontend
kubectl scale deployment eucloud-frontend --replicas=3 -n eucloud

# Auto-scaling (HPA)
kubectl autoscale deployment eucloud-backend \
  --cpu-percent=70 --min=2 --max=10 -n eucloud
```

## 🎉 Je bent klaar!

Je hebt nu:
- ✅ Complete CI/CD pipeline
- ✅ Docker containers
- ✅ Kubernetes manifests
- ✅ Automated deployment
- ✅ Code op GitHub

**Volgende push naar `main` branch triggert automatisch de hele pipeline!**

## 📚 Meer Info

- [DEPLOYMENT.md](DEPLOYMENT.md) - Volledige deployment guide
- [README.md](README.md) - Project documentatie
- GitHub Actions: https://github.com/Dylan0165/EUCLOUD/actions
- Packages: https://github.com/Dylan0165?tab=packages

---

**Created by:** Dylan van Herpen  
**Repository:** https://github.com/Dylan0165/EUCLOUD  
**Date:** November 15, 2025
