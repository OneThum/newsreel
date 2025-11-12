#!/usr/bin/env python3
"""Clean duplicate sources from existing stories in Cosmos DB"""

import os
import logging
from collections import defaultdict
from azure.cosmos import CosmosClient
from datetime import datetime, timezone

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cosmos DB connection
COSMOS_KEY = os.popen('az cosmosdb keys list --name newsreel-db-1759951135 --resource-group newsreel-rg --query primaryMasterKey -o tsv 2>/dev/null').read().strip()
COSMOS_ENDPOINT = "https://newsreel-db-1759951135.documents.azure.com:443/"

def clean_duplicate_sources():
    """Remove duplicate sources from existing stories"""

    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = client.get_database_client("newsreel-db")
    container = database.get_container_client("story_clusters")

    # Query all stories
    query = 'SELECT * FROM c WHERE ARRAY_LENGTH(c.source_articles) > 1'
    stories = list(container.query_items(query=query, enable_cross_partition_query=True))

    logger.info(f"Found {len(stories)} stories to check for duplicates")

    cleaned_count = 0
    total_duplicates_removed = 0

    for story in stories:
        story_id = story.get('id')
        source_articles = story.get('source_articles', [])

        if not source_articles:
            continue

        # Group articles by source to identify duplicates
        sources_seen = set()
        unique_articles = []
        duplicates_found = 0

        for art in source_articles:
            if isinstance(art, dict):
                source = art.get('source', '')
            else:
                source = art.split('_')[0] if isinstance(art, str) else ''

            if source and source not in sources_seen:
                sources_seen.add(source)
                unique_articles.append(art)
            else:
                duplicates_found += 1

        # If duplicates were found, update the story
        if duplicates_found > 0:
            logger.info(f"Cleaning {story_id}: {len(source_articles)} → {len(unique_articles)} articles ({duplicates_found} duplicates removed)")

            # Update the story with deduplicated sources
            update_data = {
                'source_articles': unique_articles,
                'verification_level': len(unique_articles),
                'last_updated': datetime.now(timezone.utc).isoformat()
            }

            # Use the story category as partition key
            category = story.get('category', 'general')
            container.upsert_item({
                **story,
                **update_data
            })

            cleaned_count += 1
            total_duplicates_removed += duplicates_found

    logger.info(f"✅ Cleanup complete: {cleaned_count} stories cleaned, {total_duplicates_removed} duplicate sources removed")

if __name__ == "__main__":
    clean_duplicate_sources()
