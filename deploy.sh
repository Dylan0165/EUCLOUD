#!/bin/bash

# EUCLOUD Deployment Script
# This script deploys EUCLOUD to Kubernetes

set -e

echo "🚀 Starting EUCLOUD Deployment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="eucloud"
KUBECTL="kubectl"

# Function to check if kubectl is installed
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        echo "❌ kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    echo "✅ kubectl is installed"
}

# Function to check cluster connection
check_cluster() {
    if ! kubectl cluster-info &> /dev/null; then
        echo "❌ Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    echo "✅ Connected to Kubernetes cluster"
}

# Create namespace
create_namespace() {
    echo -e "${YELLOW}Creating namespace...${NC}"
    kubectl apply -f k8s/namespace.yaml
    echo -e "${GREEN}✅ Namespace created${NC}"
}

# Create secrets (if not exists)
create_secrets() {
    echo -e "${YELLOW}Creating secrets...${NC}"
    
    # Check if secrets already exist
    if kubectl get secret eucloud-secrets -n $NAMESPACE &> /dev/null; then
        echo "⚠️  Secrets already exist. Skipping..."
    else
        # Generate random secrets
        SECRET_KEY=$(openssl rand -hex 32)
        JWT_SECRET=$(openssl rand -hex 32)
        
        kubectl create secret generic eucloud-secrets \
            --from-literal=secret-key=$SECRET_KEY \
            --from-literal=jwt-secret-key=$JWT_SECRET \
            -n $NAMESPACE
        
        echo -e "${GREEN}✅ Secrets created${NC}"
    fi
}

# Deploy persistent volumes
deploy_pvc() {
    echo -e "${YELLOW}Deploying persistent volume claims...${NC}"
    kubectl apply -f k8s/pvc.yaml
    echo -e "${GREEN}✅ PVCs deployed${NC}"
}

# Deploy backend
deploy_backend() {
    echo -e "${YELLOW}Deploying backend...${NC}"
    kubectl apply -f k8s/backend-deployment.yaml
    echo -e "${GREEN}✅ Backend deployed${NC}"
}

# Deploy frontend
deploy_frontend() {
    echo -e "${YELLOW}Deploying frontend...${NC}"
    kubectl apply -f k8s/frontend-deployment.yaml
    echo -e "${GREEN}✅ Frontend deployed${NC}"
}

# Deploy services
deploy_services() {
    echo -e "${YELLOW}Deploying services...${NC}"
    kubectl apply -f k8s/services.yaml
    echo -e "${GREEN}✅ Services deployed${NC}"
}

# Deploy ingress (optional)
deploy_ingress() {
    read -p "Do you want to deploy ingress? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Deploying ingress...${NC}"
        kubectl apply -f k8s/ingress.yaml
        echo -e "${GREEN}✅ Ingress deployed${NC}"
    fi
}

# Wait for deployments
wait_for_deployments() {
    echo -e "${YELLOW}Waiting for deployments to be ready...${NC}"
    kubectl rollout status deployment/eucloud-backend -n $NAMESPACE
    kubectl rollout status deployment/eucloud-frontend -n $NAMESPACE
    echo -e "${GREEN}✅ All deployments are ready${NC}"
}

# Display status
show_status() {
    echo -e "\n${GREEN}📊 Deployment Status:${NC}"
    echo -e "\n${YELLOW}Pods:${NC}"
    kubectl get pods -n $NAMESPACE
    
    echo -e "\n${YELLOW}Services:${NC}"
    kubectl get services -n $NAMESPACE
    
    echo -e "\n${YELLOW}PVCs:${NC}"
    kubectl get pvc -n $NAMESPACE
}

# Main deployment flow
main() {
    echo "🔍 Checking prerequisites..."
    check_kubectl
    check_cluster
    
    echo -e "\n📦 Starting deployment..."
    create_namespace
    create_secrets
    deploy_pvc
    deploy_backend
    deploy_frontend
    deploy_services
    deploy_ingress
    
    echo -e "\n⏳ Waiting for services to be ready..."
    wait_for_deployments
    
    show_status
    
    echo -e "\n${GREEN}🎉 EUCLOUD deployment completed successfully!${NC}"
    
    # Get LoadBalancer IP
    echo -e "\n${YELLOW}Getting service URL...${NC}"
    kubectl get service eucloud-frontend -n $NAMESPACE
}

# Run main function
main
