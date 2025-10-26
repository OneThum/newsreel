#!/bin/bash
# Deploy Batch Processing Feature
# This script sets up the batch processing infrastructure for cost-effective backfill summarization

set -e

echo "🚀 Deploying Batch Processing for Newsreel"
echo "=========================================="

# Load configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../configure-firebase-azure.sh" 2>/dev/null || true

# Get configuration
read -p "Azure Function App Name: " FUNCTION_APP_NAME
read -p "Resource Group: " RESOURCE_GROUP
read -p "Cosmos DB Account Name: " COSMOS_ACCOUNT

echo ""
echo "📦 Step 1: Creating batch_tracking container in Cosmos DB"
echo "--------------------------------------------------------"

# Check if container already exists
CONTAINER_EXISTS=$(az cosmosdb sql container show \
  --account-name "$COSMOS_ACCOUNT" \
  --database-name newsreel-db \
  --name batch_tracking \
  --resource-group "$RESOURCE_GROUP" \
  --query 'id' -o tsv 2>/dev/null || echo "")

if [ -n "$CONTAINER_EXISTS" ]; then
  echo "✅ Container 'batch_tracking' already exists"
else
  echo "Creating container 'batch_tracking'..."
  az cosmosdb sql container create \
    --account-name "$COSMOS_ACCOUNT" \
    --database-name newsreel-db \
    --name batch_tracking \
    --partition-key-path /batch_id \
    --resource-group "$RESOURCE_GROUP" \
    --throughput 400
  
  echo "✅ Container created successfully"
fi

echo ""
echo "📝 Step 2: Updating Function App settings"
echo "-----------------------------------------"

# Enable batch processing
echo "Enabling batch processing..."
az functionapp config appsettings set \
  --name "$FUNCTION_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --settings BATCH_PROCESSING_ENABLED=true \
  --output none

echo "✅ Batch processing enabled"

# Optional: Disable old backfill
read -p "Disable old backfill function? (y/n): " DISABLE_OLD
if [ "$DISABLE_OLD" = "y" ]; then
  az functionapp config appsettings set \
    --name "$FUNCTION_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --settings SUMMARIZATION_BACKFILL_ENABLED=false \
    --output none
  echo "✅ Old backfill disabled"
fi

echo ""
echo "🚢 Step 3: Deploying updated function code"
echo "------------------------------------------"

cd "$SCRIPT_DIR/../functions"

# Check if Azure Functions Core Tools is installed
if ! command -v func &> /dev/null; then
  echo "❌ Azure Functions Core Tools not found"
  echo "Please install: https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local"
  exit 1
fi

echo "Deploying functions..."
func azure functionapp publish "$FUNCTION_APP_NAME" --python

echo "✅ Functions deployed"

echo ""
echo "✅ Deployment Complete!"
echo "======================"
echo ""
echo "📊 Next Steps:"
echo "1. Monitor function logs:"
echo "   func azure functionapp logstream $FUNCTION_APP_NAME --browser"
echo ""
echo "2. Check batch submissions in 30 minutes (first scheduled run)"
echo ""
echo "3. Query batch tracking in Cosmos DB:"
echo "   Container: batch_tracking"
echo "   Query: SELECT * FROM c WHERE c.status = 'in_progress'"
echo ""
echo "4. Monitor costs in Application Insights"
echo ""
echo "📚 Documentation: docs/BATCH_PROCESSING.md"
echo ""
echo "💰 Expected Savings:"
echo "   - Real-time (Haiku 4.5): ~\$2-3/day"
echo "   - Batch (Haiku 4.5): ~\$1-1.5/day"
echo "   - Total: ~\$3-5/day (vs \$20+/day with Sonnet 4)"
echo ""

