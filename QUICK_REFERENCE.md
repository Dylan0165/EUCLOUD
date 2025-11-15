# 🚀 EUCLOUD - Quick Reference

## 📦 Repository
**GitHub**: https://github.com/Dylan0165/EUCLOUD

## 🔑 GitHub Secrets Nodig

Ga naar: https://github.com/Dylan0165/EUCLOUD/settings/secrets/actions

### 1. KUBE_CONFIG (Verplicht voor deployment)

**Voor Standard Kubernetes (GKE/EKS/AKS/Minikube):**
```bash
cat ~/.kube/config | base64 | tr -d '\n'
```

**Voor K3s:**
```bash
sudo cat /etc/rancher/k3s/k3s.yaml | base64 | tr -d '\n'
```
⚠️ **Let op**: Verander `127.0.0.1` naar je server IP in de config!

## 🛠️ Kubernetes Setup

### Standard Kubernetes
De workflow is al correct geconfigureerd ✅

### K3s Self-Hosted Runner
Edit `.github/workflows/ci-cd.yml`:
```yaml
env:
  KUBECONFIG: /etc/rancher/k3s/k3s.yaml
```

Zie: [KUBERNETES_SETUP.md](KUBERNETES_SETUP.md) voor details

## 📋 Update Secrets in Kubernetes

**BELANGRIJK**: Voor je deploy!

```bash
# Genereer sterke secrets
openssl rand -hex 32  # Voor SECRET_KEY
openssl rand -hex 32  # Voor JWT_SECRET_KEY
```

Edit `k8s/secrets.yaml` en vervang placeholders.

## 🚀 Deployment Commands

### Via GitHub Actions (Automatisch)
```bash
git push origin main
```

### Handmatig
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/services.yaml
```

### Met Script
```bash
chmod +x deploy.sh
./deploy.sh
```

## 🔍 Status Checken

```bash
# Pods
kubectl get pods -n eucloud

# Services
kubectl get svc -n eucloud

# Logs backend
kubectl logs -f deployment/eucloud-backend -n eucloud

# Logs frontend
kubectl logs -f deployment/eucloud-frontend -n eucloud

# Alle resources
kubectl get all -n eucloud
```

## 🌐 Toegang tot Applicatie

### LoadBalancer (Cloud)
```bash
kubectl get svc eucloud-frontend -n eucloud
# Gebruik EXTERNAL-IP
```

### NodePort (Minikube)
```bash
minikube service eucloud-frontend -n eucloud --url
```

### Port Forward (Development)
```bash
# Frontend
kubectl port-forward svc/eucloud-frontend 8080:80 -n eucloud

# Backend
kubectl port-forward svc/eucloud-backend 5000:5000 -n eucloud
```

## 🔄 Updates

```bash
# Code wijzigen
git add .
git commit -m "Your changes"
git push origin main

# Pipeline doet automatisch:
# ✅ Tests
# ✅ Build images
# ✅ Push to GHCR
# ✅ Deploy to K8s
```

## 🐛 Troubleshooting

### Pod crasht
```bash
kubectl describe pod <pod-name> -n eucloud
kubectl logs <pod-name> -n eucloud
```

### ImagePullBackOff
```bash
# Check image exists
docker pull ghcr.io/dylan0165/eucloud-backend:latest

# Create pull secret
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=Dylan0165 \
  --docker-password=<GITHUB_TOKEN> \
  -n eucloud
```

### Database reset
```bash
kubectl delete pvc eucloud-database-pvc -n eucloud
kubectl apply -f k8s/pvc.yaml
kubectl rollout restart deployment/eucloud-backend -n eucloud
```

## 📊 Pipeline Status

GitHub Actions: https://github.com/Dylan0165/EUCLOUD/actions

Workflow file: `.github/workflows/ci-cd.yml`

## 🔒 Security Checklist

- [ ] Update `k8s/secrets.yaml` met sterke secrets
- [ ] Verander GitHub KUBE_CONFIG secret
- [ ] Enable HTTPS (ingress + cert-manager)
- [ ] Review resource limits in deployments
- [ ] Regular backups van PVCs

## 📚 Documentatie

- [README.md](README.md) - Project overview
- [DEPLOYMENT.md](DEPLOYMENT.md) - Volledige deployment guide
- [KUBERNETES_SETUP.md](KUBERNETES_SETUP.md) - Kubernetes configuratie
- [SETUP_COMPLETE.md](SETUP_COMPLETE.md) - Setup checklist

## 💡 Tips

**Lokaal testen:**
```bash
docker-compose up
```

**Scale replicas:**
```bash
kubectl scale deployment eucloud-backend --replicas=5 -n eucloud
```

**Database backup:**
```bash
kubectl exec deployment/eucloud-backend -n eucloud -- \
  tar -czf /tmp/backup.tar.gz /app/instance
kubectl cp eucloud/eucloud-backend-xxx:/tmp/backup.tar.gz ./backup.tar.gz
```

**Delete everything:**
```bash
kubectl delete namespace eucloud
```

---

**Quick Start**: Push naar main → GitHub Actions doet de rest! 🚀
