#!/bin/bash
# Embedding Service Deployment Script - Phase 2 Clustering Overhaul
# Deploys the SentenceTransformers service to Azure Container Instances

set -e

# Configuration - Update these values for your environment
RESOURCE_GROUP="${RESOURCE_GROUP:-newsreel-rg}"
ACI_NAME="${ACI_NAME:-newsreel-embeddings}"
LOCATION="${LOCATION:-eastus}"
IMAGE_NAME="${IMAGE_NAME:-newsreel/embeddings:latest}"
CPU_CORES="${CPU_CORES:-2}"
MEMORY_GB="${MEMORY_GB:-8}" # 8GB recommended for multilingual-e5-large (Phase 3.6)
DNS_NAME_LABEL="${DNS_NAME_LABEL:-newsreel-embeddings}"

echo "🚀 Deploying Newsreel Embedding Service to Azure Container Instances"
echo "Resource Group: $RESOURCE_GROUP"
echo "ACI Name: $ACI_NAME"
echo "Location: $LOCATION"
echo "Image: $IMAGE_NAME"
echo "CPU: $CPU_CORES cores"
echo "Memory: $MEMORY_GB GB"

# Build the Docker image
echo "📦 Building Docker image..."
docker build -t $IMAGE_NAME .

# Login to Azure Container Registry (if using ACR)
if [ ! -z "$ACR_LOGIN_SERVER" ]; then
    echo "🔐 Logging into Azure Container Registry..."
    az acr login --name $ACR_LOGIN_SERVER

    # Tag and push to ACR
    ACR_IMAGE="$ACR_LOGIN_SERVER/$IMAGE_NAME"
    docker tag $IMAGE_NAME $ACR_IMAGE
    echo "📤 Pushing image to ACR..."
    docker push $ACR_IMAGE
    DEPLOY_IMAGE=$ACR_IMAGE
else
    echo "⚠️  No ACR configured, using local image (for development only)"
    DEPLOY_IMAGE=$IMAGE_NAME
fi

# Create resource group if it doesn't exist
echo "📁 Ensuring resource group exists..."
az group create --name $RESOURCE_GROUP --location $LOCATION --output none

# Deploy to Azure Container Instances
echo "🚀 Deploying to Azure Container Instances..."
az container create \
    --resource-group $RESOURCE_GROUP \
    --name $ACI_NAME \
    --image $DEPLOY_IMAGE \
    --cpu $CPU_CORES \
    --memory $MEMORY_GB \
    --ports 8080 \
    --dns-name-label $DNS_NAME_LABEL \
    --environment-variables \
        MODEL_NAME="intfloat/multilingual-e5-large" \
    --output none

# Wait for deployment to complete
echo "⏳ Waiting for deployment to complete..."
az container show --resource-group $RESOURCE_GROUP --name $ACI_NAME --query provisioningState -o tsv

# Get the public IP and FQDN
FQDN=$(az container show --resource-group $RESOURCE_GROUP --name $ACI_NAME --query ipAddress.fqdn -o tsv)
IP=$(az container show --resource-group $RESOURCE_GROUP --name $ACI_NAME --query ipAddress.ip -o tsv)

echo "✅ Deployment completed successfully!"
echo "🌐 Service URL: http://$FQDN:8080"
echo "📊 Health check: http://$FQDN:8080/health"
echo ""
echo "🔧 Update your Azure Functions configuration with:"
echo "EMBEDDINGS_SERVICE_URL=http://$FQDN:8080"
echo ""
echo "📝 To check logs: az container logs --resource-group $RESOURCE_GROUP --name $ACI_NAME"
echo "🛑 To stop: az container delete --resource-group $RESOURCE_GROUP --name $ACI_NAME"
