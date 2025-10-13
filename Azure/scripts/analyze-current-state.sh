#!/bin/bash
#
# Analyze Current State - Direct Azure CLI queries
# Bypasses authentication issues by using Azure CLI
#

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "🔍 ANALYZING CURRENT NEWSREEL STATE"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# Get story count
echo "📊 Querying story clusters..."
story_count=$(az cosmosdb sql container throughput show \
    --account-name newsreel-db-1759951135 \
    --resource-group newsreel-rg \
    --database-name newsreel-db \
    --name story_clusters \
    --query "resource.minimumThroughput" -o tsv 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "✅ Story clusters container accessible"
else
    echo "⚠️  Could not access story clusters"
fi

# Check API directly (will fail due to auth, but we can see the error)
echo ""
echo "📡 Testing API endpoint..."
response=$(curl -s "https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/api/health" 2>&1)
echo "API Health: $response"

echo ""
echo "🔍 Checking API status page..."
status_page=$(curl -s "https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/status" 2>&1 | head -50)
echo "$status_page"

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"

