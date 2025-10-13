#!/bin/bash

# Remove Sponsored Content from Database
# Finds and deletes promotional/spam articles and story clusters

set -e

echo "🧹 Removing Sponsored Content from Newsreel"
echo "==========================================="
echo ""

RESOURCE_GROUP="Newsreel-RG"
COSMOS_ACCOUNT="newsreel-cosmos"
COSMOS_DB="newsreel-db"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Spam indicators to search for
SPAM_KEYWORDS=(
    "Sponsored Content"
    "Sponsored Post"
    "Paid Content"
    "Advertisement"
    "Brought to You By"
    "Advertorial"
    "Promotional Content"
)

echo "1️⃣  Searching for sponsored content in story_clusters..."
echo ""

for keyword in "${SPAM_KEYWORDS[@]}"; do
    echo "   Searching for: '$keyword'"
    
    # Query for stories with this keyword
    STORIES=$(az cosmosdb sql query \
        --account-name $COSMOS_ACCOUNT \
        --database-name $COSMOS_DB \
        --container-name story_clusters \
        --query-text "SELECT c.id, c.category, c.title FROM c WHERE CONTAINS(LOWER(c.title), LOWER('$keyword'))" \
        --resource-group $RESOURCE_GROUP 2>/dev/null | jq -r '.[].id' || echo "")
    
    if [ -n "$STORIES" ]; then
        STORY_COUNT=$(echo "$STORIES" | wc -l | tr -d ' ')
        echo -e "${YELLOW}   Found $STORY_COUNT story/stories${NC}"
        
        # List the stories
        while IFS= read -r story_id; do
            if [ -n "$story_id" ]; then
                # Get full story details
                STORY_DETAILS=$(az cosmosdb sql query \
                    --account-name $COSMOS_ACCOUNT \
                    --database-name $COSMOS_DB \
                    --container-name story_clusters \
                    --query-text "SELECT c.id, c.category, c.title FROM c WHERE c.id = '$story_id'" \
                    --resource-group $RESOURCE_GROUP 2>/dev/null | jq -r '.[0]')
                
                TITLE=$(echo "$STORY_DETAILS" | jq -r '.title')
                CATEGORY=$(echo "$STORY_DETAILS" | jq -r '.category')
                
                echo ""
                echo "   📰 Story ID: $story_id"
                echo "   📂 Category: $CATEGORY"
                echo "   📝 Title: $TITLE"
                echo ""
                
                # Ask for confirmation
                read -p "   Delete this story? (y/n): " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    # Delete from Cosmos DB
                    az cosmosdb sql query \
                        --account-name $COSMOS_ACCOUNT \
                        --database-name $COSMOS_DB \
                        --container-name story_clusters \
                        --query-text "SELECT * FROM c WHERE c.id = '$story_id'" \
                        --resource-group $RESOURCE_GROUP 2>/dev/null | \
                        jq -r '.[0] | @json' | \
                        xargs -I {} az cosmosdb sql container delete-item \
                            --account-name $COSMOS_ACCOUNT \
                            --database-name $COSMOS_DB \
                            --container-name story_clusters \
                            --partition-key-path "/category" \
                            --resource-group $RESOURCE_GROUP \
                            --id "$story_id" 2>/dev/null && \
                        echo -e "${GREEN}   ✅ Deleted${NC}" || \
                        echo -e "${RED}   ❌ Delete failed${NC}"
                else
                    echo "   ⏭️  Skipped"
                fi
            fi
        done <<< "$STORIES"
    fi
done

echo ""
echo "2️⃣  Searching for sponsored content in raw_articles..."
echo ""

for keyword in "${SPAM_KEYWORDS[@]}"; do
    echo "   Searching for: '$keyword'"
    
    # Count raw articles with this keyword
    ARTICLE_COUNT=$(az cosmosdb sql query \
        --account-name $COSMOS_ACCOUNT \
        --database-name $COSMOS_DB \
        --container-name raw_articles \
        --query-text "SELECT VALUE COUNT(1) FROM c WHERE CONTAINS(LOWER(c.title), LOWER('$keyword'))" \
        --resource-group $RESOURCE_GROUP 2>/dev/null | jq -r '.[0]' || echo "0")
    
    if [ "$ARTICLE_COUNT" -gt "0" ]; then
        echo -e "${YELLOW}   Found $ARTICLE_COUNT article(s)${NC}"
        echo "   (These will be automatically filtered on next ingestion cycle)"
    fi
done

echo ""
echo "=========================================="
echo "✅ Sponsored content cleanup complete!"
echo ""
echo "📝 Note: New sponsored content will be automatically blocked by the enhanced spam filter."
echo "   The filter now catches:"
echo "   • Sponsored Content"
echo "   • Paid Partnership"
echo "   • Advertisement"
echo "   • Promotional Content"
echo "   • And many more variants"

