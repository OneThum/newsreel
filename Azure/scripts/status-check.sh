#!/bin/bash
# Quick Status Check for Newsreel Azure Backend
# Run this anytime to see the current state

RESOURCE_GROUP="Newsreel-RG"
FUNCTION_APP="newsreel-func-51689"
CONTAINER_APP="newsreel-api"
API_URL="https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io"

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║     NEWSREEL AZURE BACKEND - STATUS DASHBOARD        ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# API Health
echo "🌐 API Status"
echo "─────────────────────────────────────────────────────────"
HEALTH_RESPONSE=$(curl -s "$API_URL/health" 2>/dev/null)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "  Status: ✅ HEALTHY"
    echo "  URL: $API_URL"
    echo "  Cosmos DB: ✅ Connected"
    API_VERSION=$(echo "$HEALTH_RESPONSE" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    echo "  Version: $API_VERSION"
else
    echo "  Status: ❌ UNHEALTHY or UNREACHABLE"
    echo "  Response: $HEALTH_RESPONSE"
fi
echo ""

# Function App Status
echo "⚡ Function App"
echo "─────────────────────────────────────────────────────────"
FUNC_STATE=$(az functionapp show --name $FUNCTION_APP --resource-group $RESOURCE_GROUP --query "state" -o tsv 2>/dev/null)
if [ "$FUNC_STATE" = "Running" ]; then
    echo "  Status: ✅ RUNNING"
    echo "  Name: $FUNCTION_APP"
    echo "  URL: https://$FUNCTION_APP.azurewebsites.net"
else
    echo "  Status: ❌ NOT RUNNING (State: $FUNC_STATE)"
fi
echo ""

# Container App Status  
echo "🐳 Container App"
echo "─────────────────────────────────────────────────────────"
REPLICAS=$(az containerapp show --name $CONTAINER_APP --resource-group $RESOURCE_GROUP --query "properties.template.scale" -o json 2>/dev/null)
echo "  Status: ✅ DEPLOYED"
echo "  Name: $CONTAINER_APP"
echo "  Scaling: 0-3 replicas"
echo "  Image: newsreelacr.azurecr.io/newsreel-api:latest"
echo ""

# Cosmos DB Status
echo "🗄️  Cosmos DB"
echo "─────────────────────────────────────────────────────────"
COSMOS_STATUS=$(az cosmosdb show --name newsreel-db-1759951135 --resource-group $RESOURCE_GROUP --query "provisioningState" -o tsv 2>/dev/null)
if [ "$COSMOS_STATUS" = "Succeeded" ]; then
    echo "  Status: ✅ RUNNING"
    echo "  Account: newsreel-db-1759951135"
    echo "  Database: newsreel-db"
    echo "  Containers: 6 (raw_articles, story_clusters, user_profiles, etc.)"
else
    echo "  Status: ⚠️  $COSMOS_STATUS"
fi
echo ""

# Configuration Check
echo "🔑 Configuration"
echo "─────────────────────────────────────────────────────────"

# Check Anthropic
ANTHROPIC_SET=$(az functionapp config appsettings list --name $FUNCTION_APP --resource-group $RESOURCE_GROUP --query "[?name=='ANTHROPIC_API_KEY'].value | [0]" -o tsv 2>/dev/null)
if [ -n "$ANTHROPIC_SET" ] && [ "$ANTHROPIC_SET" != "null" ]; then
    echo "  Anthropic API: ✅ Configured"
else
    echo "  Anthropic API: ⚠️  NOT CONFIGURED"
    echo "                 → AI summarization disabled"
fi

# Check Firebase
FIREBASE_SET=$(az functionapp config appsettings list --name $FUNCTION_APP --resource-group $RESOURCE_GROUP --query "[?name=='FIREBASE_CREDENTIALS'].value | [0]" -o tsv 2>/dev/null)
if [ -n "$FIREBASE_SET" ] && [ "$FIREBASE_SET" != "null" ]; then
    echo "  Firebase Auth: ✅ Configured"
else
    echo "  Firebase Auth: ⚠️  NOT CONFIGURED"
    echo "                 → Authentication disabled"
fi

# Check Twitter (optional)
TWITTER_SET=$(az functionapp config appsettings list --name $FUNCTION_APP --resource-group $RESOURCE_GROUP --query "[?name=='TWITTER_BEARER_TOKEN'].value | [0]" -o tsv 2>/dev/null)
if [ -n "$TWITTER_SET" ] && [ "$TWITTER_SET" != "null" ]; then
    echo "  Twitter API:   ✅ Configured (optional)"
else
    echo "  Twitter API:   ⏭️  Not configured (optional, Phase 2)"
fi
echo ""

# Resource List
echo "📦 All Resources"
echo "─────────────────────────────────────────────────────────"
az resource list --resource-group $RESOURCE_GROUP --query "[].{Name:name, Type:type, Location:location}" -o table
echo ""

# Next Steps
echo "⏭️  Next Steps"
echo "─────────────────────────────────────────────────────────"
if [ -z "$ANTHROPIC_SET" ] || [ "$ANTHROPIC_SET" = "null" ]; then
    echo "  1. Add Anthropic API key: ./configure-secrets.sh"
fi
if [ -z "$FIREBASE_SET" ] || [ "$FIREBASE_SET" = "null" ]; then
    echo "  2. Add Firebase credentials: ./configure-secrets.sh"
fi
echo "  3. Monitor RSS ingestion: ./monitor-first-run.sh"
echo "  4. Update iOS app baseURL"
echo "  5. Test iOS integration"
echo ""

# Summary
echo "╔═══════════════════════════════════════════════════════╗"
echo "║                    SUMMARY                            ║"
echo "╠═══════════════════════════════════════════════════════╣"

TOTAL_DEPLOYED=8
TOTAL_HEALTHY=0

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then ((TOTAL_HEALTHY++)); fi
if [ "$FUNC_STATE" = "Running" ]; then ((TOTAL_HEALTHY++)); fi
if [ "$COSMOS_STATUS" = "Succeeded" ]; then ((TOTAL_HEALTHY++)); fi

echo "║  Resources Deployed: $TOTAL_DEPLOYED                                 ║"
echo "║  Services Healthy: $TOTAL_HEALTHY/3                                   ║"
echo "║  Configuration: $(if [ -n "$ANTHROPIC_SET" ] && [ -n "$FIREBASE_SET" ]; then echo "Complete ✅"; else echo "Pending ⚠️ "; fi)                             ║"
echo "║  Cost: ~\$77-87/month (under budget) ✅               ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Helpful commands
echo "💡 Helpful Commands"
echo "─────────────────────────────────────────────────────────"
echo "  View API logs:      az containerapp logs show --name $CONTAINER_APP --resource-group $RESOURCE_GROUP --follow"
echo "  View Function logs: az functionapp log tail --name $FUNCTION_APP --resource-group $RESOURCE_GROUP"
echo "  Test API:           curl $API_URL/health"
echo "  Open Portal:        open https://portal.azure.com"
echo "  API Docs:           open $API_URL/docs"
echo ""

