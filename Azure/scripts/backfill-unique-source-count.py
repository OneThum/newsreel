#!/usr/bin/env python3
"""
Backfill unique_source_count for existing story clusters.

This script calculates the unique_source_count field for all existing stories
based on their source_articles and updates the database.
"""

import os
import sys
from azure.cosmos import CosmosClient
from datetime import datetime, timezone

def backfill_unique_source_count():
    """Backfill unique_source_count for all stories in the database."""

    # Get Cosmos DB credentials
    COSMOS_KEY = os.popen('az cosmosdb keys list --name newsreel-db-1759951135 --resource-group newsreel-rg --query primaryMasterKey -o tsv 2>/dev/null').read().strip()
    COSMOS_ENDPOINT = 'https://newsreel-db-1759951135.documents.azure.com:443/'

    if not COSMOS_KEY:
        print("❌ Failed to get Cosmos DB key")
        return False

    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = client.get_database_client('newsreel-db')
    story_container = database.get_container_client('story_clusters')

    print('🔄 BACKFILLING UNIQUE SOURCE COUNT')
    print('='*40)

    # Get all stories that need updating (unique_source_count is missing or 0)
    query = '''
    SELECT c.id, c.source_articles, c.unique_source_count
    FROM c
    WHERE NOT IS_DEFINED(c.unique_source_count) OR c.unique_source_count = 0
    '''

    stories = list(story_container.query_items(query=query, enable_cross_partition_query=True))

    print(f'Found {len(stories)} stories that need unique_source_count backfilled')

    updated_count = 0
    error_count = 0

    for story in stories:
        story_id = story.get('id')
        source_articles = story.get('source_articles', [])
        current_count = story.get('unique_source_count', 0)

        # Calculate unique sources
        unique_sources = set()
        for article in source_articles:
            if isinstance(article, dict):
                source = article.get('source', '')
                if source:
                    unique_sources.add(source)
            else:
                # Fallback for old format (article ID strings)
                source = article.split('_')[0] if '_' in article else article
                if source:
                    unique_sources.add(source)

        calculated_count = len(unique_sources)

        # Only update if the count is different
        if calculated_count != current_count:
            try:
                # Update the story with the calculated count
                updates = {
                    'unique_source_count': calculated_count,
                    'last_updated': datetime.now(timezone.utc).isoformat()
                }

                # Use the story fingerprint (last part of ID) as partition key
                partition_key = story_id.split('_')[-1]

                story_container.patch_item(
                    item=story_id,
                    partition_key=partition_key,
                    patch_operations=[
                        {"op": "replace", "path": "/unique_source_count", "value": calculated_count},
                        {"op": "replace", "path": "/last_updated", "value": updates['last_updated']}
                    ]
                )

                print(f'✅ Updated {story_id}: {current_count} → {calculated_count} unique sources')
                updated_count += 1

            except Exception as e:
                print(f'❌ Failed to update {story_id}: {e}')
                error_count += 1
        else:
            print(f'⏭️  Skipped {story_id}: already has correct count ({current_count})')

    print()
    print('📊 BACKFILL SUMMARY')
    print('='*20)
    print(f'Total stories processed: {len(stories)}')
    print(f'Successfully updated: {updated_count}')
    print(f'Errors: {error_count}')
    print(f'Skipped (already correct): {len(stories) - updated_count - error_count}')

    # Verify the backfill worked
    print()
    print('🔍 VERIFICATION')
    print('='*15)

    # Check a few random stories
    verification_query = 'SELECT TOP 5 c.id, c.unique_source_count, c.source_articles FROM c ORDER BY c.first_seen DESC'
    verification_stories = list(story_container.query_items(query=verification_query, enable_cross_partition_query=True))

    for story in verification_stories:
        story_id = story.get('id')
        unique_count = story.get('unique_source_count', 0)
        source_articles = story.get('source_articles', [])

        # Recalculate for verification
        unique_sources = set()
        for article in source_articles:
            if isinstance(article, dict):
                source = article.get('source', '')
                if source:
                    unique_sources.add(source)
            else:
                source = article.split('_')[0] if '_' in article else article
                if source:
                    unique_sources.add(source)

        calculated_count = len(unique_sources)

        status = '✅' if unique_count == calculated_count else '❌'
        print(f'{status} {story_id}: stored={unique_count}, calculated={calculated_count}')

    return True

if __name__ == '__main__':
    success = backfill_unique_source_count()
    sys.exit(0 if success else 1)
