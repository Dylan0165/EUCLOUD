# Kubernetes Setup Instructies voor EUCLOUD

## 🔧 KUBECONFIG Configuratie

De CI/CD pipeline heeft toegang nodig tot je Kubernetes cluster. Dit verschilt per setup.

## 📋 Setup per Kubernetes Type

### 1️⃣ **Standard Kubernetes (GKE, EKS, AKS, Minikube)**

#### Huidige Workflow Setup:
De workflow gebruikt: `KUBECONFIG: $HOME/.kube/config`

Dit werkt voor:
- ✅ Google Kubernetes Engine (GKE)
- ✅ Amazon EKS
- ✅ Azure AKS
- ✅ Minikube
- ✅ Standard kubectl configs

#### GitHub Secret Setup:
```bash
# Get je kubeconfig (base64 encoded)
cat ~/.kube/config | base64 | tr -d '\n'
```

Voeg toe als `KUBE_CONFIG` secret in GitHub.

---

### 2️⃣ **K3s/K3d Setup**

Als je **K3s** gebruikt, is de kubeconfig meestal op: `/etc/rancher/k3s/k3s.yaml`

#### Optie A: Verander Workflow (Aanbevolen voor Self-Hosted Runners)

Edit `.github/workflows/ci-cd.yml`:

```yaml
- name: Deploy to Kubernetes
  env:
    KUBECONFIG: /etc/rancher/k3s/k3s.yaml
  run: |
    kubectl apply -f k8s/namespace.yaml
    # ... rest van commands
```

#### Optie B: Kopieer K3s Config naar Standard Locatie

Op je K3s server:
```bash
mkdir -p $HOME/.kube
sudo cp /etc/rancher/k3s/k3s.yaml $HOME/.kube/config
sudo chown $USER:$USER $HOME/.kube/config
```

Dan gebruik je de standaard workflow (huidige setup).

#### GitHub Secret voor K3s:
```bash
# Op je K3s server:
sudo cat /etc/rancher/k3s/k3s.yaml | base64 | tr -d '\n'
```

⚠️ **Let op**: Update `server:` in de config van `127.0.0.1` naar je publieke IP/hostname!

---

### 3️⃣ **Self-Hosted GitHub Runner**

Als je een **self-hosted runner** gebruikt op je Kubernetes cluster:

#### Optie A: Direct Kubeconfig
```yaml
- name: Deploy to Kubernetes
  env:
    KUBECONFIG: /etc/rancher/k3s/k3s.yaml  # Of jouw pad
  run: |
    kubectl apply -f k8s/namespace.yaml
```

#### Optie B: In-Cluster Authentication
```yaml
- name: Deploy to Kubernetes
  run: |
    # No KUBECONFIG needed - runner runs in cluster
    kubectl apply -f k8s/namespace.yaml
```

---

## 🔍 Welke Setup Heb Je?

### Check je Kubernetes Type:

```bash
# Check versie
kubectl version --short

# K3s check
kubectl version 2>&1 | grep k3s

# Standard Kubernetes
kubectl version 2>&1 | grep -v k3s
```

### Check je Kubeconfig Locatie:

```bash
# Standard locatie
ls -la ~/.kube/config

# K3s locatie
ls -la /etc/rancher/k3s/k3s.yaml

# Huidige KUBECONFIG
echo $KUBECONFIG
```

---

## 📝 Workflow Aanpassen voor Jouw Setup

### Huidige Workflow (Standaard):

```yaml
- name: Deploy to Kubernetes
  env:
    KUBECONFIG: $HOME/.kube/config
  run: |
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/pvc.yaml
    kubectl apply -f k8s/secrets.yaml
    kubectl apply -f k8s/backend-deployment.yaml
    kubectl apply -f k8s/frontend-deployment.yaml
    kubectl apply -f k8s/services.yaml
```

### Voor K3s (Self-Hosted Runner):

```yaml
- name: Deploy to Kubernetes
  env:
    KUBECONFIG: /etc/rancher/k3s/k3s.yaml
  run: |
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/pvc.yaml
    kubectl apply -f k8s/secrets.yaml
    kubectl apply -f k8s/backend-deployment.yaml
    kubectl apply -f k8s/frontend-deployment.yaml
    kubectl apply -f k8s/services.yaml
```

### Voor Cloud Kubernetes (GitHub Hosted):

Gebruik de huidige setup met `KUBE_CONFIG` secret.

---

## 🚀 GitHub Secret Setup

### Stap 1: Get Kubeconfig

**Standard Kubernetes:**
```bash
cat ~/.kube/config | base64 | tr -d '\n'
```

**K3s:**
```bash
# Kopieer eerst config
sudo cp /etc/rancher/k3s/k3s.yaml /tmp/k3s.yaml
sudo chown $USER /tmp/k3s.yaml

# Edit: Verander 127.0.0.1 naar je server IP
nano /tmp/k3s.yaml
# Zoek: server: https://127.0.0.1:6443
# Verander naar: server: https://YOUR_SERVER_IP:6443

# Base64 encode
cat /tmp/k3s.yaml | base64 | tr -d '\n'

# Cleanup
rm /tmp/k3s.yaml
```

### Stap 2: Voeg toe aan GitHub

1. Ga naar: `https://github.com/Dylan0165/EUCLOUD/settings/secrets/actions`
2. Click **New repository secret**
3. Name: `KUBE_CONFIG`
4. Value: *plak de base64 string*
5. Click **Add secret**

---

## ✅ Test je Setup

### Lokaal Testen:

```bash
# Test kubectl werkt
kubectl get nodes

# Test EUCLOUD namespace
kubectl get all -n eucloud

# Dry-run deployment
kubectl apply -f k8s/namespace.yaml --dry-run=client
```

### Pipeline Testen:

1. Maak kleine wijziging in README
2. Commit en push naar `main`
3. Check GitHub Actions: `https://github.com/Dylan0165/EUCLOUD/actions`
4. Bekijk logs voor eventuele errors

---

## 🐛 Troubleshooting

### Error: "The connection to the server localhost:8080 was refused"

**Oplossing**: KUBECONFIG is niet correct ingesteld.

```yaml
# Voeg toe aan deploy step:
env:
  KUBECONFIG: /path/to/your/kubeconfig
```

### Error: "error: You must be logged in to the server (Unauthorized)"

**Oplossing**: Kubeconfig heeft geen valid credentials.

```bash
# Check je secret
echo "$KUBE_CONFIG" | base64 -d

# Re-generate secret
kubectl config view --raw | base64 | tr -d '\n'
```

### Error: "unable to recognize k8s/xxx.yaml: no matches for kind"

**Oplossing**: Kubernetes versie mismatch of CRD niet installed.

```bash
# Check je k8s version
kubectl version

# Check manifest is geldig
kubectl apply -f k8s/namespace.yaml --dry-run=server
```

---

## 📚 Meer Informatie

- **Kubernetes Docs**: https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/
- **K3s Docs**: https://docs.k3s.io/cluster-access
- **GitHub Actions**: https://docs.github.com/en/actions/deployment/deploying-to-your-cloud-provider/deploying-to-kubernetes

---

**Gemaakt voor EUCLOUD**  
Repository: https://github.com/Dylan0165/EUCLOUD
