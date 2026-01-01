#!/bin/bash
#
# Deploy RSS Worker to Azure Container Apps + Service Bus
# 
# This script:
# 1. Creates Azure Service Bus namespace and queue
# 2. Creates Azure Container Registry (if needed)
# 3. Builds and pushes Docker image
# 4. Creates Container Apps environment
# 5. Deploys the RSS Worker container app
#
# Prerequisites:
# - Azure CLI installed and logged in (az login)
# - Docker installed and running
#
# Usage:
#   ./deploy.sh
#
# Cost estimate: ~$85/month for always-on worker

set -e

# Configuration
RESOURCE_GROUP='Newsreel-RG'
LOCATION='centralus'
SERVICE_BUS_NAMESPACE='newsreel-servicebus'
SERVICE_BUS_QUEUE='rss-feeds'
ACR_NAME='newsreelacr'
CONTAINER_APP_ENV='newsreel-container-env'
CONTAINER_APP_NAME='newsreel-rss-worker'

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Newsreel RSS Worker Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if logged into Azure
echo -e "\n${YELLOW}Checking Azure login...${NC}"
if ! az account show > /dev/null 2>&1; then
    echo -e "${RED}Not logged into Azure. Please run: az login${NC}"
    exit 1
fi

SUBSCRIPTION=$(az account show --query name -o tsv)
echo -e "${GREEN}✓ Logged into Azure: $SUBSCRIPTION${NC}"

# ============================================================================
# 1. CREATE SERVICE BUS NAMESPACE AND QUEUE
# ============================================================================

echo -e "\n${YELLOW}Step 1: Creating Service Bus...${NC}"

# Check if namespace exists
if az servicebus namespace show --name $SERVICE_BUS_NAMESPACE --resource-group $RESOURCE_GROUP > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Service Bus namespace already exists${NC}"
else
    echo "Creating Service Bus namespace..."
    az servicebus namespace create \
        --name $SERVICE_BUS_NAMESPACE \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --sku Standard
    echo -e "${GREEN}✓ Service Bus namespace created${NC}"
fi

# Create queue if not exists
if az servicebus queue show --name $SERVICE_BUS_QUEUE --namespace-name $SERVICE_BUS_NAMESPACE --resource-group $RESOURCE_GROUP > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Queue '$SERVICE_BUS_QUEUE' already exists${NC}"
else
    echo "Creating queue..."
    az servicebus queue create \
        --name $SERVICE_BUS_QUEUE \
        --namespace-name $SERVICE_BUS_NAMESPACE \
        --resource-group $RESOURCE_GROUP \
        --enable-dead-lettering-on-message-expiration true \
        --max-delivery-count 5 \
        --default-message-time-to-live P1D
    echo -e "${GREEN}✓ Queue created with dead-letter enabled${NC}"
fi

# Get connection string
SERVICE_BUS_CONNECTION_STRING=$(az servicebus namespace authorization-rule keys list \
    --name RootManageSharedAccessKey \
    --namespace-name $SERVICE_BUS_NAMESPACE \
    --resource-group $RESOURCE_GROUP \
    --query primaryConnectionString -o tsv)

echo -e "${GREEN}✓ Service Bus ready${NC}"

# ============================================================================
# 2. CREATE CONTAINER REGISTRY
# ============================================================================

echo -e "\n${YELLOW}Step 2: Creating Container Registry...${NC}"

# Check if ACR exists
if az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Container Registry already exists${NC}"
else
    echo "Creating Container Registry..."
    az acr create \
        --name $ACR_NAME \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --sku Basic \
        --admin-enabled true
    echo -e "${GREEN}✓ Container Registry created${NC}"
fi

# Get ACR credentials
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query loginServer -o tsv)
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query passwords[0].value -o tsv)

echo -e "${GREEN}✓ Container Registry: $ACR_LOGIN_SERVER${NC}"

# ============================================================================
# 3. BUILD AND PUSH DOCKER IMAGE
# ============================================================================

echo -e "\n${YELLOW}Step 3: Building Docker image...${NC}"

# Build image
IMAGE_TAG="$ACR_LOGIN_SERVER/rss-worker:latest"

echo "Building image: $IMAGE_TAG"
docker build -t $IMAGE_TAG .

echo "Pushing to ACR..."
az acr login --name $ACR_NAME
docker push $IMAGE_TAG

echo -e "${GREEN}✓ Docker image pushed${NC}"

# ============================================================================
# 4. CREATE CONTAINER APPS ENVIRONMENT
# ============================================================================

echo -e "\n${YELLOW}Step 4: Creating Container Apps environment...${NC}"

# Check if environment exists
if az containerapp env show --name $CONTAINER_APP_ENV --resource-group $RESOURCE_GROUP > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Container Apps environment already exists${NC}"
else
    echo "Creating Container Apps environment..."
    az containerapp env create \
        --name $CONTAINER_APP_ENV \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION
    echo -e "${GREEN}✓ Container Apps environment created${NC}"
fi

# ============================================================================
# 5. GET EXISTING SECRETS FROM KEY VAULT OR FUNCTION APP
# ============================================================================

echo -e "\n${YELLOW}Step 5: Getting existing secrets...${NC}"

# Try to get Cosmos connection string from existing function app
COSMOS_CONNECTION_STRING=$(az functionapp config appsettings list \
    --name newsreel-func-51689 \
    --resource-group $RESOURCE_GROUP \
    --query "[?name=='COSMOS_CONNECTION_STRING'].value" -o tsv 2>/dev/null || echo '')

if [ -z "$COSMOS_CONNECTION_STRING" ]; then
    echo -e "${YELLOW}⚠ Could not get COSMOS_CONNECTION_STRING from function app${NC}"
    echo "Please set COSMOS_CONNECTION_STRING environment variable and re-run"
    exit 1
fi

OPENAI_API_KEY=$(az functionapp config appsettings list \
    --name newsreel-func-51689 \
    --resource-group $RESOURCE_GROUP \
    --query "[?name=='OPENAI_API_KEY'].value" -o tsv 2>/dev/null || echo '')

echo -e "${GREEN}✓ Secrets retrieved${NC}"

# ============================================================================
# 6. DEPLOY CONTAINER APP
# ============================================================================

echo -e "\n${YELLOW}Step 6: Deploying Container App...${NC}"

# Check if app exists
if az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP > /dev/null 2>&1; then
    echo "Updating existing Container App..."
    az containerapp update \
        --name $CONTAINER_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --image $IMAGE_TAG
else
    echo "Creating Container App..."
    az containerapp create \
        --name $CONTAINER_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --environment $CONTAINER_APP_ENV \
        --image $IMAGE_TAG \
        --registry-server $ACR_LOGIN_SERVER \
        --registry-username $ACR_USERNAME \
        --registry-password $ACR_PASSWORD \
        --target-port 8080 \
        --ingress external \
        --cpu 0.5 \
        --memory 1.0Gi \
        --min-replicas 1 \
        --max-replicas 3 \
        --env-vars \
            "SERVICE_BUS_CONNECTION_STRING=$SERVICE_BUS_CONNECTION_STRING" \
            "SERVICE_BUS_QUEUE_NAME=$SERVICE_BUS_QUEUE" \
            "COSMOS_CONNECTION_STRING=$COSMOS_CONNECTION_STRING" \
            "COSMOS_DATABASE_NAME=newsreel-db" \
            "OPENAI_API_KEY=$OPENAI_API_KEY" \
            "MAX_CONCURRENT_FEEDS=10" \
            "FEED_TIMEOUT_SECONDS=30" \
            "CIRCUIT_BREAKER_THRESHOLD=3" \
            "CIRCUIT_BREAKER_TIMEOUT_MINUTES=30"
fi

echo -e "${GREEN}✓ Container App deployed${NC}"

# Get the app URL
APP_URL=$(az containerapp show \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn -o tsv)

# ============================================================================
# 7. VERIFY DEPLOYMENT
# ============================================================================

echo -e "\n${YELLOW}Step 7: Verifying deployment...${NC}"

echo "Waiting for container to start..."
sleep 10

# Check health endpoint
HEALTH_URL="https://$APP_URL/health"
echo "Checking health endpoint: $HEALTH_URL"

HTTP_STATUS=$(curl -s -o /dev/null -w '%{http_code}' $HEALTH_URL || echo '000')

if [ "$HTTP_STATUS" == "200" ]; then
    echo -e "${GREEN}✓ Health check passed!${NC}"
    curl -s $HEALTH_URL | python3 -m json.tool 2>/dev/null || curl -s $HEALTH_URL
else
    echo -e "${YELLOW}⚠ Health check returned: $HTTP_STATUS (container may still be starting)${NC}"
fi

# ============================================================================
# SUMMARY
# ============================================================================

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Resources created:"
echo "  • Service Bus: $SERVICE_BUS_NAMESPACE"
echo "  • Queue: $SERVICE_BUS_QUEUE"
echo "  • Container Registry: $ACR_LOGIN_SERVER"
echo "  • Container App: $CONTAINER_APP_NAME"
echo ""
echo "Endpoints:"
echo "  • Health: https://$APP_URL/health"
echo "  • Stats: https://$APP_URL/stats"
echo ""
echo "Next steps:"
echo "  1. Update Azure Functions to push feed URLs to Service Bus queue"
echo "  2. Monitor logs: az containerapp logs show -n $CONTAINER_APP_NAME -g $RESOURCE_GROUP"
echo "  3. Check stats: curl https://$APP_URL/stats"
echo ""
echo -e "${YELLOW}Estimated monthly cost: ~\$85 (0.5 vCPU, 1GB RAM, always-on)${NC}"
echo ""

# Save configuration for future reference
cat > .deploy-config <<EOF
# Deployment configuration - $(date)
RESOURCE_GROUP=$RESOURCE_GROUP
SERVICE_BUS_NAMESPACE=$SERVICE_BUS_NAMESPACE
SERVICE_BUS_QUEUE=$SERVICE_BUS_QUEUE
ACR_NAME=$ACR_NAME
CONTAINER_APP_ENV=$CONTAINER_APP_ENV
CONTAINER_APP_NAME=$CONTAINER_APP_NAME
APP_URL=$APP_URL
EOF

echo "Configuration saved to .deploy-config"

