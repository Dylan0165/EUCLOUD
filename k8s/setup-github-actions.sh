#!/bin/bash
# Setup ServiceAccount for GitHub Actions deployment
# Run this on your K3s cluster (192.168.124.50)

set -e

echo "🔐 Setting up GitHub Actions ServiceAccount for EUCLOUD deployment..."
echo ""

# Create namespace if not exists
kubectl create namespace eucloud --dry-run=client -o yaml | kubectl apply -f -

# Create ServiceAccount, Role, and RoleBinding
echo "📝 Creating ServiceAccount and RBAC permissions..."
cat <<EOF | kubectl apply -f -
---
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
- apiGroups: [""]
  resources: ["pods", "pods/log", "services", "persistentvolumeclaims", "secrets", "configmaps"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "statefulsets"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["networking.k8s.io"]
  resources: ["ingresses"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
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

echo "✅ ServiceAccount created"
echo ""

# Wait for token to be generated
echo "⏳ Waiting for token generation..."
sleep 5

# Get the token
echo ""
echo "🔑 ServiceAccount Token (save this as KUBE_TOKEN secret):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
kubectl get secret github-deployer-token -n eucloud -o jsonpath='{.data.token}' | base64 -d
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Get server URL
echo "🌐 Kubernetes API Server URL (save this as KUBE_SERVER secret):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}'
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Namespace
echo "📦 Namespace (save this as KUBE_NAMESPACE secret):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "eucloud"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Summary
echo "📋 Summary - Add these to GitHub Secrets:"
echo ""
echo "1. Go to: https://github.com/Dylan0165/EUCLOUD/settings/secrets/actions"
echo "2. Click 'New repository secret'"
echo "3. Add the following secrets:"
echo ""
echo "   Name: KUBE_TOKEN"
echo "   Value: <token from above>"
echo ""
echo "   Name: KUBE_SERVER"
echo "   Value: <server URL from above>"
echo ""
echo "   Name: KUBE_NAMESPACE"
echo "   Value: eucloud"
echo ""
echo "   Name: DOCKERHUB_USERNAME"
echo "   Value: <your Docker Hub username>"
echo ""
echo "   Name: DOCKERHUB_TOKEN"
echo "   Value: <your Docker Hub access token>"
echo ""
echo "✅ Setup complete! You can now use GitHub Actions to deploy to this cluster."
echo ""

# Verify
echo "🔍 Verification:"
kubectl get sa github-deployer -n eucloud
kubectl get role github-deployer-role -n eucloud
kubectl get rolebinding github-deployer-binding -n eucloud
kubectl get secret github-deployer-token -n eucloud
