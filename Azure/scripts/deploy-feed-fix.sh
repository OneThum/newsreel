#!/bin/bash

# Deploy Feed Endpoint Fix
# Fixes the issue where feed endpoint returns summary:null and source_count:0

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀 DEPLOYING FEED ENDPOINT FIX${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

# Verify Azure login
echo -e "${YELLOW}Checking Azure login...${NC}"
if ! az account show > /dev/null 2>&1; then
    echo -e "${RED}❌ Not logged into Azure${NC}"
    echo "Run: az login"
    exit 1
fi

SUBSCRIPTION=$(az account show --query "name" -o tsv)
echo -e "${GREEN}✅ Logged in to: $SUBSCRIPTION${NC}\n"

# Build Docker image
echo -e "${YELLOW}🐳 Building Docker image...${NC}"
cd "$(dirname "$0")/.."

az acr build \
    --registry newsreelacr \
    --image newsreel-api:latest \
    --file Dockerfile \
    .

echo -e "${GREEN}✅ Docker image built${NC}\n"

# Deploy to Container Apps
echo -e "${YELLOW}🚀 Deploying to Azure Container Apps...${NC}"

CONTAINER_APP="newsreel-api"
RESOURCE_GROUP="Newsreel-RG"

# Get current image
CURRENT_IMAGE=$(az containerapp show -n "$CONTAINER_APP" -g "$RESOURCE_GROUP" --query "properties.template.containers[0].image" -o tsv)
echo -e "   Current image: $CURRENT_IMAGE"

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name newsreelacr --query "username" -o tsv)
ACR_PASSWORD=$(az acr credential show --name newsreelacr --query "passwords[0].value" -o tsv)

# Update container app
az containerapp update \
    --name "$CONTAINER_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --image "newsreelacr.azurecr.io/newsreel-api:latest" \
    --registry-login-server "newsreelacr.azurecr.io" \
    --registry-username "$ACR_USERNAME" \
    --registry-password "$ACR_PASSWORD"

echo -e "${GREEN}✅ Container App updated${NC}\n"

# Wait for deployment
echo -e "${YELLOW}⏳ Waiting for deployment to complete...${NC}"
sleep 15

# Check status
STATUS=$(az containerapp show -n "$CONTAINER_APP" -g "$RESOURCE_GROUP" --query "properties.provisioningState" -o tsv)
echo -e "   Status: $STATUS\n"

# Show test commands
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

echo -e "${YELLOW}📊 To Test the Fix:${NC}\n"

echo -e "${BLUE}1. Monitor logs:${NC}"
echo -e "   az containerapp logs show -n $CONTAINER_APP -g $RESOURCE_GROUP --follow\n"

echo -e "${BLUE}2. Get a Firebase token, then test feed endpoint:${NC}"
echo -e "   curl -H \"Authorization: Bearer TOKEN\" \\"
echo -e "     \"https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/api/stories/feed?limit=5\" \\"
echo -e "     | jq '.[] | {summary: .summary.text, source_count, sources: (.sources | length)}'\n"

echo -e "${BLUE}3. Compare with breaking endpoint:${NC}"
echo -e "   curl -H \"Authorization: Bearer TOKEN\" \\"
echo -e "     \"https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/api/stories/breaking?limit=5\" \\"
echo -e "     | jq '.[] | {summary: .summary.text, source_count, sources: (.sources | length)}'\n"

echo -e "${BLUE}4. Run automatic test:${NC}"
echo -e "   python Azure/scripts/test-feed-vs-breaking.py TOKEN\n"

echo -e "${GREEN}✅ Feed endpoint should now return summaries and sources!${NC}\n"
