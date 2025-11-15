# GitHub Actions Secrets Setup

## Required Secrets

Voor de CI/CD pipeline heb je de volgende secrets nodig in je GitHub repository:

### 1. Docker Hub Credentials
- `DOCKERHUB_USERNAME`: Je Docker Hub gebruikersnaam
- `DOCKERHUB_TOKEN`: Docker Hub access token

### 2. Kubernetes Cluster Access
- `KUBE_SERVER`: K3s API server URL
- `KUBE_TOKEN`: ServiceAccount token voor deployment
- `KUBE_NAMESPACE`: Kubernetes namespace (meestal "eucloud")

## Setup Instructies

### Stap 1: Docker Hub Token

1. Ga naar https://hub.docker.com/settings/security
2. Klik "New Access Token"
3. Naam: "GitHub Actions EUCLOUD"
4. Permissions: Read, Write, Delete
5. Kopieer de token

### Stap 2: Kubernetes ServiceAccount Token

Op je K3s VM (192.168.124.50):

```bash
# 1. Maak ServiceAccount voor GitHub Actions
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: github-deployer
  namespace: eucloud
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: github-deployer-role
  namespace: eucloud
rules:
- apiGroups: ["", "apps", "networking.k8s.io"]
  resources: ["*"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: github-deployer-binding
  namespace: eucloud
subjects:
- kind: ServiceAccount
  name: github-deployer
  namespace: eucloud
roleRef:
  kind: Role
  name: github-deployer-role
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: v1
kind: Secret
metadata:
  name: github-deployer-token
  namespace: eucloud
  annotations:
    kubernetes.io/service-account.name: github-deployer
type: kubernetes.io/service-account-token
EOF

# 2. Wacht even tot de token wordt aangemaakt
sleep 5

# 3. Haal de token op
kubectl get secret github-deployer-token -n eucloud -o jsonpath='{.data.token}' | base64 -d
# Kopieer deze token!

# 4. Haal de K3s server URL op
kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}'
# Meestal: https://192.168.124.50:6443
```

### Stap 3: GitHub Secrets Toevoegen

1. Ga naar je GitHub repository
2. Settings → Secrets and variables → Actions
3. Klik "New repository secret"

Voeg toe:

| Name | Value | Example |
|------|-------|---------|
| `DOCKERHUB_USERNAME` | Je Docker Hub username | `dylan0165` |
| `DOCKERHUB_TOKEN` | Token uit stap 1 | `dckr_pat_xxx...` |
| `KUBE_SERVER` | K3s API server URL | `https://192.168.124.50:6443` |
| `KUBE_TOKEN` | Token uit stap 2 | `eyJhbGciOiJSUzI1NiIsImtpZCI6Ikp...` |
| `KUBE_NAMESPACE` | Namespace | `eucloud` |

### Stap 4: Test de Pipeline

```bash
# Commit en push een kleine wijziging
git commit --allow-empty -m "Test CI/CD pipeline"
git push
```

Ga naar je repository → Actions tab en bekijk de workflow run.

## Troubleshooting

### "Error: Unauthorized" tijdens kubectl commando's

Controleer of:
- `KUBE_TOKEN` correct is (geen extra spaties/newlines)
- ServiceAccount bestaat: `kubectl get sa github-deployer -n eucloud`
- Role binding correct is: `kubectl get rolebinding github-deployer-binding -n eucloud`

Opnieuw token ophalen:
```bash
kubectl get secret github-deployer-token -n eucloud -o jsonpath='{.data.token}' | base64 -d
```

### "Error: Server not found"

Controleer `KUBE_SERVER` URL:
```bash
# Op K3s node
kubectl config view --minify
```

Zorg dat de URL bereikbaar is vanaf de GitHub Actions runner.

### Self-signed certificate errors

De workflow gebruikt `--insecure-skip-tls-verify=true` voor self-signed certificates.

Voor productie, voeg het CA certificate toe:
```bash
# Haal CA cert op
kubectl config view --raw -o jsonpath='{.clusters[0].cluster.certificate-authority-data}' | base64 -d > ca.crt

# Voeg toe aan workflow met base64 encoded CA cert als secret
```

## Security Best Practices

1. **Token Rotation**: Roteer de ServiceAccount token regelmatig
2. **Least Privilege**: De Role geeft alleen rechten binnen de `eucloud` namespace
3. **Token Expiry**: Overweeg tokens met expiry datum te gebruiken
4. **Audit Logs**: Monitor kubectl actions in K3s audit logs

## Alternative: Self-hosted Runner with Kubeconfig

Als je al een self-hosted runner hebt op de K3s node:

```yaml
- name: Deploy to Kubernetes
  env:
    KUBECONFIG: /etc/rancher/k3s/k3s.yaml
  run: |
    kubectl apply -f k8s/
```

Dit is eenvoudiger maar minder flexibel (runner moet op K3s node draaien).
