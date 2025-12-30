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

# Check if ACR image already exists
if [ ! -z "$ACR_LOGIN_SERVER" ]; then
    ACR_IMAGE="$ACR_LOGIN_SERVER/$IMAGE_NAME"
    echo "🔍 Checking if ACR image exists: $ACR_IMAGE"

    # Check if the linux/amd64 image exists in ACR
    IMAGE_EXISTS=$(az acr manifest show-metadata --name $ACR_LOGIN_SERVER --registry $ACR_LOGIN_SERVER --image $IMAGE_NAME:latest --query "architecture=='amd64' and os=='linux'" -o tsv 2>/dev/null || echo "not_found")

    if [ "$IMAGE_EXISTS" = "True" ]; then
        echo "✅ ACR image exists, using existing image: $ACR_IMAGE"
        DEPLOY_IMAGE=$ACR_IMAGE
    else
        echo "📦 Building Docker image with linux/amd64 platform..."
        docker build --platform linux/amd64 -t $IMAGE_NAME .

        echo "🔐 Logging into Azure Container Registry..."
        az acr login --name $ACR_LOGIN_SERVER

        # Tag and push to ACR
        echo "🏷️  Tagging image: $IMAGE_NAME -> $ACR_IMAGE"
        docker tag $IMAGE_NAME $ACR_IMAGE
        echo "📤 Pushing image to ACR..."
        docker push $ACR_IMAGE
        DEPLOY_IMAGE=$ACR_IMAGE
        echo "✅ Using ACR image for deployment: $DEPLOY_IMAGE"
    fi
else
    echo "⚠️  No ACR configured, building local image (for development only)"
    docker build -t $IMAGE_NAME .
    DEPLOY_IMAGE=$IMAGE_NAME
    echo "✅ Using local image for deployment: $DEPLOY_IMAGE"
fi

# Create resource group if it doesn't exist
echo "📁 Ensuring resource group exists..."
az group create --name $RESOURCE_GROUP --location $LOCATION --output none

# Deploy to Azure Container Apps (more reliable than ACI)
echo "🚀 Deploying to Azure Container Apps..."

# Use existing container app environment
echo "📦 Using existing Container App environment: newsreel-env"

# Create the container app
echo "📦 Creating Container App..."
az containerapp create \
    --name $ACI_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment newsreel-env \
    --image $DEPLOY_IMAGE \
    --registry-server $ACR_NAME.azurecr.io \
    --registry-username $(az acr credential show --name $ACR_NAME --query username -o tsv) \
    --registry-password $(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv) \
    --cpu 2.0 \
    --memory 4.0Gi \
    --min-replicas 1 \
    --max-replicas 1 \
    --target-port 8080 \
    --ingress external \
    --env-vars MODEL_NAME="intfloat/multilingual-e5-large" \
    --output none

# Wait for deployment to complete
echo "⏳ Waiting for deployment to complete..."
sleep 30
STATUS=$(az containerapp show --name $ACI_NAME --resource-group $RESOURCE_GROUP --query provisioningState -o tsv)

# Get the service URL
FQDN=$(az containerapp show --name $ACI_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn -o tsv)

echo "✅ Deployment completed successfully!"
echo "🌐 Service URL: http://$FQDN:8080"
echo "📊 Health check: http://$FQDN:8080/health"
echo ""
echo "🔧 Update your Azure Functions configuration with:"
echo "EMBEDDINGS_SERVICE_URL=http://$FQDN:8080"
echo ""
echo "📝 To check logs: az container logs --resource-group $RESOURCE_GROUP --name $ACI_NAME"
echo "🛑 To stop: az container delete --resource-group $RESOURCE_GROUP --name $ACI_NAME"
