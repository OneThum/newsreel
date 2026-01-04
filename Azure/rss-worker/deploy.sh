#!/bin/bash
# Deploy RSS Worker to Azure Container Apps
# This creates a reliable, always-on RSS polling service

set -e

# Configuration
RESOURCE_GROUP="Newsreel-RG"
LOCATION="australiaeast"
CONTAINER_APP_NAME="newsreel-rss-worker"
CONTAINER_APP_ENV="newsreel-container-env"
ACR_NAME="newsreelacr"
IMAGE_NAME="rss-worker"
IMAGE_TAG="latest"

echo "=========================================="
echo "Deploying RSS Worker to Azure Container Apps"
echo "=========================================="

# Get existing secrets from Azure
echo "Fetching configuration from Azure..."
COSMOS_CONNECTION=$(az cosmosdb keys list --name newsreel-cosmos --resource-group $RESOURCE_GROUP --type connection-strings --query "connectionStrings[0].connectionString" -o tsv)
OPENAI_KEY=$(az keyvault secret show --vault-name newsreel-kv --name openai-api-key --query value -o tsv 2>/dev/null || echo "")

if [ -z "$COSMOS_CONNECTION" ]; then
    echo "ERROR: Could not fetch Cosmos DB connection string"
    exit 1
fi

# Create Container Apps Environment if it doesn't exist
echo "Checking Container Apps Environment..."
if ! az containerapp env show --name $CONTAINER_APP_ENV --resource-group $RESOURCE_GROUP &>/dev/null; then
    echo "Creating Container Apps Environment..."
    az containerapp env create \
        --name $CONTAINER_APP_ENV \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION
else
    echo "Container Apps Environment already exists"
fi

# Build and push Docker image
echo "Building Docker image..."
az acr build \
    --registry $ACR_NAME \
    --image $IMAGE_NAME:$IMAGE_TAG \
    --file Dockerfile \
    .

# Deploy or update Container App
echo "Deploying Container App..."
FULL_IMAGE="${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${IMAGE_TAG}"

# Check if container app exists
if az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP &>/dev/null; then
    echo "Updating existing Container App..."
    az containerapp update \
        --name $CONTAINER_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --image $FULL_IMAGE \
        --set-env-vars \
            COSMOS_CONNECTION_STRING="$COSMOS_CONNECTION" \
            COSMOS_DATABASE_NAME=newsreel-db \
            OPENAI_API_KEY="$OPENAI_KEY" \
            FEEDS_PER_CYCLE=10 \
            POLL_INTERVAL_SECONDS=10 \
            FEED_TIMEOUT_SECONDS=30 \
            FEED_COOLDOWN_MINUTES=5
else
    echo "Creating new Container App..."
    az containerapp create \
        --name $CONTAINER_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --environment $CONTAINER_APP_ENV \
        --image $FULL_IMAGE \
        --registry-server ${ACR_NAME}.azurecr.io \
        --registry-identity system \
        --target-port 8080 \
        --ingress external \
        --min-replicas 1 \
        --max-replicas 1 \
        --cpu 0.25 \
        --memory 0.5Gi \
        --env-vars \
            COSMOS_CONNECTION_STRING="$COSMOS_CONNECTION" \
            COSMOS_DATABASE_NAME=newsreel-db \
            OPENAI_API_KEY="$OPENAI_KEY" \
            FEEDS_PER_CYCLE=10 \
            POLL_INTERVAL_SECONDS=10 \
            FEED_TIMEOUT_SECONDS=30 \
            FEED_COOLDOWN_MINUTES=5
fi

# Get the Container App URL
APP_URL=$(az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv)

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo "Container App URL: https://${APP_URL}"
echo "Health Endpoint: https://${APP_URL}/health"
echo "Stats Endpoint: https://${APP_URL}/stats"
echo ""
echo "Configuration:"
echo "  - Polls 10 feeds every 10 seconds"
echo "  - 52 verified working feeds"
echo "  - Circuit breaker: 3 failures, 30 min timeout"
echo "  - Feed cooldown: 5 minutes"
echo ""
echo "Testing health endpoint..."
sleep 5
curl -s "https://${APP_URL}/health" | python -m json.tool || echo "Health check pending..."
