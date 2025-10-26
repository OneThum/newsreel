#!/bin/bash

# Cosmos DB Connection Verification Script
# Verifies that the Function App can connect to Cosmos DB and containers exist

set -e

# Configuration
RESOURCE_GROUP="Newsreel-RG"
COSMOS_ACCOUNT="newsreel-db-1759951135"
DATABASE_NAME="newsreel"
FUNCTION_APP="newsreel-func-51689"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           Cosmos DB Connection Verification                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Get connection string
echo "📋 Retrieving Cosmos DB connection string..."
CONNECTION_STRING=$(az cosmosdb keys list --name "$COSMOS_ACCOUNT" --resource-group "$RESOURCE_GROUP" --type connection-strings --query 'connectionStrings[0].connectionString' -o tsv 2>/dev/null || echo "")

if [ -z "$CONNECTION_STRING" ]; then
    echo "❌ ERROR: Could not retrieve connection string"
    exit 1
fi

echo "✅ Connection string retrieved"
echo ""

# Check if database exists
echo "🔍 Checking database: $DATABASE_NAME"
DATABASES=$(az cosmosdb sql database list --account-name "$COSMOS_ACCOUNT" --resource-group "$RESOURCE_GROUP" --query "[].name" -o tsv 2>/dev/null || echo "")

if echo "$DATABASES" | grep -q "$DATABASE_NAME"; then
    echo "✅ Database exists: $DATABASE_NAME"
else
    echo "❌ ERROR: Database not found: $DATABASE_NAME"
    exit 1
fi

echo ""

# Check containers
echo "🔍 Checking containers..."
CONTAINERS=$(az cosmosdb sql container list --account-name "$COSMOS_ACCOUNT" --database-name "$DATABASE_NAME" --resource-group "$RESOURCE_GROUP" --query "[].name" -o tsv 2>/dev/null || echo "")

REQUIRED_CONTAINERS=("raw_articles" "story_clusters" "user_profiles" "user_interactions" "batch_tracking" "feed_poll_states" "leases")

for container in "${REQUIRED_CONTAINERS[@]}"; do
    if echo "$CONTAINERS" | grep -q "$container"; then
        echo "  ✅ $container"
    else
        echo "  ❌ $container (missing)"
    fi
done

echo ""

# Check Function App configuration
echo "🔍 Checking Function App configuration..."
COSMOS_ENV=$(az functionapp config appsettings list --name "$FUNCTION_APP" --resource-group "$RESOURCE_GROUP" --query "[?name=='COSMOS_CONNECTION_STRING'].value" -o tsv 2>/dev/null || echo "")

if [ -n "$COSMOS_ENV" ]; then
    echo "  ✅ COSMOS_CONNECTION_STRING is set"
else
    echo "  ❌ COSMOS_CONNECTION_STRING is not set"
fi

DB_NAME_ENV=$(az functionapp config appsettings list --name "$FUNCTION_APP" --resource-group "$RESOURCE_GROUP" --query "[?name=='COSMOS_DATABASE_NAME'].value" -o tsv 2>/dev/null || echo "")

if [ -n "$DB_NAME_ENV" ]; then
    echo "  ✅ COSMOS_DATABASE_NAME is set to: $DB_NAME_ENV"
else
    echo "  ⚠️  COSMOS_DATABASE_NAME may not be set (defaults to env var)"
fi

echo ""

# Test Python connection
echo "🧪 Testing Python connection to Cosmos DB..."
python3 - <<'PYTHON_EOF' "$CONNECTION_STRING" "$DATABASE_NAME"
import sys
from azure.cosmos import CosmosClient

try:
    connection_string = sys.argv[1]
    database_name = sys.argv[2]
    
    client = CosmosClient.from_connection_string(connection_string)
    database = client.get_database_client(database_name)
    
    # Try to access a container
    container = database.get_container_client('raw_articles')
    
    # Simple test query
    query = "SELECT TOP 1 * FROM c"
    items = list(container.query_items(query))
    
    print(f"✅ Successfully connected to database '{database_name}'")
    print(f"✅ raw_articles container is accessible")
    print(f"   Items in container: {len(items)}")
    
except Exception as e:
    print(f"❌ Connection failed: {str(e)}")
    sys.exit(1)

PYTHON_EOF

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ Verification Complete!                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "🔄 Next Steps:"
echo "  1. Restart Function App to ensure it picks up the database"
echo "  2. Monitor Function App logs for RSS ingestion"
echo "  3. Check raw_articles container for incoming data"
echo ""
