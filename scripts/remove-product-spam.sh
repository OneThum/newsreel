#!/bin/bash

# Remove product listicle spam from Cosmos DB
# This script identifies and removes promotional product content from the news feed

set -e

COSMOS_ACCOUNT="newsreel-db-1759951135"
RESOURCE_GROUP="Newsreel-RG"
DATABASE="newsreel"
CONTAINER="story_clusters"

echo "🧹 Scanning for product listicle spam..."
echo "================================================"

# Get Cosmos DB endpoint and key
COSMOS_ENDPOINT=$(az cosmosdb show --name $COSMOS_ACCOUNT --resource-group $RESOURCE_GROUP --query documentEndpoint -o tsv)
COSMOS_KEY=$(az cosmosdb keys list --name $COSMOS_ACCOUNT --resource-group $RESOURCE_GROUP --query primaryMasterKey -o tsv)

echo "✅ Connected to Cosmos DB: $COSMOS_ACCOUNT"
echo ""

# Python script to find and remove spam
python3 << 'EOF'
import os
import sys
import re
from azure.cosmos import CosmosClient, PartitionKey

# Get credentials from environment
endpoint = os.environ.get('COSMOS_ENDPOINT')
key = os.environ.get('COSMOS_KEY')

if not endpoint or not key:
    print("❌ Missing Cosmos DB credentials")
    sys.exit(1)

client = CosmosClient(endpoint, key)
database = client.get_database_client('newsreel')
container = database.get_container_client('story_clusters')

# Spam patterns (matching our updated filter)
spam_patterns = [
    r'\d+\s+(?:of the|the)?.*(?:products|items|things).*(?:you can|to).*(?:buy|shop|get)',
    r'\d+\s+.*products.*(?:buy|shop).*(?:amazon|walmart|target)',
    r'\d+\s+.*(?:useful|essential|must-have).*products',
    r'\d+\s+best.*(?:deals|products|buys|items)',
    r'amazon\s+deals',
    r'gift guide',
    r'products you can buy',
    r'things to buy',
    r'products worth buying',
]

print("🔍 Searching for spam stories...")
print("")

# Query all stories
query = "SELECT * FROM c"
items = list(container.query_items(
    query=query,
    enable_cross_partition_query=True
))

spam_found = []

for item in items:
    title = item.get('title', '').lower()
    
    # Check if title matches any spam pattern
    for pattern in spam_patterns:
        if re.search(pattern, title):
            spam_found.append({
                'id': item['id'],
                'category': item.get('category', 'unknown'),
                'title': item.get('title', '')[:100],
                'source_count': len(item.get('source_articles', []))
            })
            break

if not spam_found:
    print("✅ No spam stories found!")
    sys.exit(0)

print(f"🎯 Found {len(spam_found)} spam stories:")
print("")

for idx, story in enumerate(spam_found, 1):
    print(f"{idx}. [{story['source_count']} sources] {story['title']}")
    print(f"   ID: {story['id']}")
    print(f"   Category: {story['category']}")
    print("")

print("")
response = input(f"❓ Delete these {len(spam_found)} spam stories? (yes/no): ")

if response.lower() != 'yes':
    print("❌ Cancelled")
    sys.exit(0)

print("")
print("🗑️  Deleting spam stories...")

deleted = 0
for story in spam_found:
    try:
        container.delete_item(
            item=story['id'],
            partition_key=story['category']
        )
        deleted += 1
        print(f"   ✓ Deleted: {story['title'][:60]}...")
    except Exception as e:
        print(f"   ✗ Failed to delete {story['id']}: {e}")

print("")
print(f"✅ Successfully deleted {deleted}/{len(spam_found)} spam stories")

EOF

echo ""
echo "================================================"
echo "✅ Cleanup complete!"

