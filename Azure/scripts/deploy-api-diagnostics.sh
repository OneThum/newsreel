#!/bin/bash

# Deploy API with Diagnostic Logging
# This script builds and deploys the updated API with comprehensive diagnostic logging

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📊 NEWSREEL API DEPLOYMENT - DIAGNOSTIC LOGGING${NC}"
echo -e "${BLUE}================================================${NC}\n"

# Check if logged into Azure
echo -e "${YELLOW}Checking Azure login...${NC}"
if ! az account show > /dev/null 2>&1; then
    echo -e "${RED}❌ Not logged into Azure${NC}"
    echo "Run: az login"
    exit 1
fi

# Get current subscription
SUBSCRIPTION=$(az account show --query "name" -o tsv)
echo -e "${GREEN}✅ Logged in to: $SUBSCRIPTION${NC}\n"

# Build Docker image
echo -e "${YELLOW}🐳 Building Docker image...${NC}"
cd "$(dirname "$0")/../api"

# Build image using Azure Container Registry
ACR_NAME="newsreelacr"
IMAGE_TAG="latest"
IMAGE_NAME="newsreel-api:$IMAGE_TAG"

echo -e "   Registry: $ACR_NAME"
echo -e "   Image: $IMAGE_NAME"
echo -e "   Build context: $(pwd)\n"

az acr build \
    --registry "$ACR_NAME" \
    --image "$IMAGE_NAME" \
    --file Dockerfile \
    .

echo -e "${GREEN}✅ Image built successfully${NC}\n"

# Deploy to Container Apps
echo -e "${YELLOW}🚀 Deploying to Container Apps...${NC}"

CONTAINER_APP="newsreel-api"
RESOURCE_GROUP="Newsreel-RG"
ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name "$ACR_NAME" --query "username" -o tsv)
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)

# Set registry credentials first
az containerapp registry set \
    --name "$CONTAINER_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --server "$ACR_LOGIN_SERVER" \
    --username "$ACR_USERNAME" \
    --password "$ACR_PASSWORD"

# Update container app with new image
az containerapp update \
    --name "$CONTAINER_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --image "$ACR_LOGIN_SERVER/$IMAGE_NAME"

echo -e "${GREEN}✅ Container App updated${NC}\n"

# Wait for deployment to complete
echo -e "${YELLOW}⏳ Waiting for deployment to complete...${NC}"
sleep 10

# Check deployment status
STATUS=$(az containerapp show -n "$CONTAINER_APP" -g "$RESOURCE_GROUP" --query "properties.provisioningState" -o tsv)
echo -e "   Status: $STATUS\n"

# Show useful commands
echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${BLUE}✅ DEPLOYMENT COMPLETE${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}\n"

echo -e "${YELLOW}📊 To Monitor Logs:${NC}"
echo -e "   az containerapp logs show -n $CONTAINER_APP -g $RESOURCE_GROUP --follow\n"

echo -e "${YELLOW}🧪 To Test Feed Endpoint:${NC}"
echo -e "   # Get Firebase token first, then:"
echo -e "   curl -H \"Authorization: Bearer YOUR_TOKEN\" \\"
echo -e "     \"https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/api/stories/feed?limit=5\"\n"

echo -e "${YELLOW}🧪 To Compare Feed vs Breaking:${NC}"
echo -e "   python Azure/scripts/test-feed-vs-breaking.py YOUR_TOKEN\n"

echo -e "${YELLOW}📖 For Full Diagnostic Guide:${NC}"
echo -e "   See: FEED_ENDPOINT_DIAGNOSTIC.md\n"

echo -e "${GREEN}✅ Ready to collect diagnostics!${NC}\n"
