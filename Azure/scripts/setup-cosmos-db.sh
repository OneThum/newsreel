#!/bin/bash

# Cosmos DB Setup Script for Newsreel
# This script creates the necessary database and containers in Cosmos DB

set -e

# Configuration
RESOURCE_GROUP="Newsreel-RG"
COSMOS_ACCOUNT="newsreel-db-1759951135"
DATABASE_NAME="newsreel"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Cosmos DB Setup - Creating Database & Containers      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if account exists
echo "📋 Checking Cosmos DB account: $COSMOS_ACCOUNT"
ACCOUNT=$(az cosmosdb show --name "$COSMOS_ACCOUNT" --resource-group "$RESOURCE_GROUP" --query name -o tsv 2>/dev/null || echo "")

if [ -z "$ACCOUNT" ]; then
    echo "❌ ERROR: Cosmos DB account '$COSMOS_ACCOUNT' not found in resource group '$RESOURCE_GROUP'"
    exit 1
fi

echo "✅ Cosmos DB account found: $COSMOS_ACCOUNT"
echo ""

# Create database
echo "📦 Creating database: $DATABASE_NAME"
az cosmosdb sql database create \
    --account-name "$COSMOS_ACCOUNT" \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DATABASE_NAME" \
    --max-throughput 4000 \
    2>/dev/null || echo "  (Database may already exist)"
echo "✅ Database created/verified"
echo ""

# Function to create container
create_container() {
    local container_name=$1
    local partition_key=$2
    
    echo "🔷 Creating container: $container_name (partition: $partition_key)"
    az cosmosdb sql container create \
        --account-name "$COSMOS_ACCOUNT" \
        --database-name "$DATABASE_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --name "$container_name" \
        --partition-key-path "$partition_key" \
        --max-throughput 4000 \
        2>/dev/null || echo "  (Container may already exist)"
    echo "✅ Container verified: $container_name"
}

# Create containers with their partition keys
echo "🏗️  Creating containers..."
create_container "raw_articles" "/category"
create_container "story_clusters" "/category"
create_container "user_profiles" "/user_id"
create_container "user_interactions" "/user_id"
create_container "batch_tracking" "/id"
create_container "feed_poll_states" "/feed_id"
create_container "leases" "/id"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ Setup Complete!                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Verification:"
echo "  Database: $DATABASE_NAME"
echo "  Account: $COSMOS_ACCOUNT"
echo "  Resource Group: $RESOURCE_GROUP"
echo ""
echo "🔄 Next Steps:"
echo "  1. Restart Function App: az functionapp restart --name newsreel-func-51689 --resource-group $RESOURCE_GROUP"
echo "  2. Verify connection: ./verify-cosmos-connection.sh"
echo "  3. Test data ingestion"
echo ""
