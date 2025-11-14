# EUCLOUD Deployment Guide

## 📋 Prerequisites

Before deploying EUCLOUD, ensure you have:

1. ✅ A GitHub account
2. ✅ A Kubernetes cluster (GKE, EKS, AKS, or self-hosted)
3. ✅ `kubectl` installed and configured
4. ✅ Docker (for local testing)

## 🚀 Deployment Steps

### Step 1: Push Code to GitHub

1. **Initialize Git repository:**
```bash
cd "c:\Users\dylan\Desktop\persoonlijk project\EUCLOUD"
git init
git add .
git commit -m "Initial commit: EUCLOUD with CI/CD"
```

2. **Create GitHub repository:**
   - Go to https://github.com/new
   - Repository name: `EUCLOUD`
   - Make it public or private
   - DO NOT initialize with README (we already have one)

3. **Push to GitHub:**
```bash
git remote add origin https://github.com/Dylan0165/EUCLOUD.git
git branch -M main
git push -u origin main
```

### Step 2: Configure GitHub Secrets

Go to your repository → Settings → Secrets and variables → Actions

Add the following secrets:

#### 1. KUBE_CONFIG
Your Kubernetes config file (base64 encoded):

```bash
# On Linux/Mac:
cat ~/.kube/config | base64 | tr -d '\n'

# On Windows (PowerShell):
[Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Content ~/.kube/config -Raw)))
```

Copy the output and add as secret `KUBE_CONFIG`

### Step 3: Enable GitHub Container Registry

1. Go to your GitHub profile → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with these scopes:
   - `write:packages`
   - `read:packages`
   - `delete:packages`
3. The pipeline will automatically use this for Docker images

### Step 4: Prepare Kubernetes Cluster

#### Option A: Local Kubernetes (Minikube/Kind)

```bash
# Start minikube
minikube start

# Enable ingress
minikube addons enable ingress
```

#### Option B: Cloud Kubernetes (GKE example)

```bash
# Create GKE cluster
gcloud container clusters create eucloud-cluster \
  --zone=europe-west1-b \
  --num-nodes=2 \
  --machine-type=e2-medium

# Get credentials
gcloud container clusters get-credentials eucloud-cluster --zone=europe-west1-b
```

### Step 5: Create Kubernetes Secrets

**Important:** Update `k8s/secrets.yaml` with strong secrets BEFORE applying:

```bash
# Generate random secrets
openssl rand -hex 32  # Use for SECRET_KEY
openssl rand -hex 32  # Use for JWT_SECRET_KEY
```

Edit `k8s/secrets.yaml` and replace the placeholder values.

**NEVER commit real secrets to git!**

### Step 6: Deploy to Kubernetes

#### Automated Deployment (via GitHub Actions)

Simply push to `main` branch:
```bash
git push origin main
```

The CI/CD pipeline will:
1. ✅ Run tests
2. ✅ Build Docker images
3. ✅ Push to GitHub Container Registry
4. ✅ Deploy to Kubernetes

#### Manual Deployment

```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

Or manually:

```bash
# 1. Create namespace
kubectl apply -f k8s/namespace.yaml

# 2. Create secrets (edit first!)
kubectl apply -f k8s/secrets.yaml

# 3. Create persistent volumes
kubectl apply -f k8s/pvc.yaml

# 4. Deploy backend
kubectl apply -f k8s/backend-deployment.yaml

# 5. Deploy frontend
kubectl apply -f k8s/frontend-deployment.yaml

# 6. Create services
kubectl apply -f k8s/services.yaml

# 7. (Optional) Create ingress
kubectl apply -f k8s/ingress.yaml
```

### Step 7: Verify Deployment

```bash
# Check pods
kubectl get pods -n eucloud

# Check services
kubectl get services -n eucloud

# Check logs
kubectl logs -f deployment/eucloud-backend -n eucloud
kubectl logs -f deployment/eucloud-frontend -n eucloud
```

### Step 8: Access the Application

#### LoadBalancer (Cloud)
```bash
# Get external IP
kubectl get service eucloud-frontend -n eucloud

# Wait for EXTERNAL-IP to be assigned
# Access at http://<EXTERNAL-IP>
```

#### NodePort (Local/Minikube)
```bash
# Get service URL
minikube service eucloud-frontend -n eucloud --url
```

#### Ingress (Production)
1. Update `k8s/ingress.yaml` with your domain
2. Point DNS A record to LoadBalancer IP
3. Access at https://eucloud.yourdomain.com

## 🔄 Updating the Application

### Automated (Recommended)

1. Make code changes
2. Commit and push:
```bash
git add .
git commit -m "Your changes"
git push origin main
```

The pipeline will automatically rebuild and redeploy.

### Manual

```bash
# Build new images
docker build -t ghcr.io/dylan0165/eucloud-backend:latest ./backend
docker build -t ghcr.io/dylan0165/eucloud-frontend:latest ./frontend

# Push images
docker push ghcr.io/dylan0165/eucloud-backend:latest
docker push ghcr.io/dylan0165/eucloud-frontend:latest

# Restart deployments
kubectl rollout restart deployment/eucloud-backend -n eucloud
kubectl rollout restart deployment/eucloud-frontend -n eucloud
```

## 🐛 Troubleshooting

### Pods not starting
```bash
# Describe pod to see errors
kubectl describe pod <pod-name> -n eucloud

# Check logs
kubectl logs <pod-name> -n eucloud
```

### ImagePullBackOff error
```bash
# Make sure images are public or create imagePullSecret
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=Dylan0165 \
  --docker-password=<YOUR_GITHUB_TOKEN> \
  -n eucloud

# Update deployments to use the secret
```

### Database issues
```bash
# Check PVC
kubectl get pvc -n eucloud

# If PVC is pending, check your storage class
kubectl get storageclass
```

## 📊 Monitoring

```bash
# Watch pod status
watch kubectl get pods -n eucloud

# Stream logs
kubectl logs -f deployment/eucloud-backend -n eucloud --tail=100

# Port forward for debugging
kubectl port-forward service/eucloud-backend 5000:5000 -n eucloud
```

## 🔒 Security Checklist

- [ ] Update secrets in `k8s/secrets.yaml`
- [ ] Use HTTPS with valid SSL certificate
- [ ] Enable network policies
- [ ] Set resource limits
- [ ] Use non-root containers
- [ ] Scan images for vulnerabilities
- [ ] Enable RBAC
- [ ] Regular backups of PVCs

## 🎯 Production Recommendations

1. **Use managed database** (PostgreSQL) instead of SQLite
2. **Set up monitoring** (Prometheus + Grafana)
3. **Configure autoscaling** (HPA)
4. **Use Helm charts** for easier management
5. **Implement backup strategy** for PVCs
6. **Set up logging** (ELK stack)
7. **Use CDN** for static assets

## 📞 Support

For issues or questions, create an issue on GitHub: https://github.com/Dylan0165/EUCLOUD/issues
