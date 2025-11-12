#!/usr/bin/env python3
"""
Manual cleanup script for test data in Newsreel database.
Run this in Azure Cloud Shell or with proper Azure credentials.
"""

import os
from azure.cosmos import CosmosClient

# Azure Cosmos DB connection
COSMOS_CONNECTION_STRING = os.getenv("COSMOS_CONNECTION_STRING")
DATABASE_NAME = "newsreel-db"

def cleanup_test_stories():
    """Remove test stories from the database"""
    
    if not COSMOS_CONNECTION_STRING:
        print("❌ COSMOS_CONNECTION_STRING not set")
        return
    
    # Connect to Cosmos DB
    client = CosmosClient.from_connection_string(COSMOS_CONNECTION_STRING)
    database = client.get_database_client(DATABASE_NAME)
    container = database.get_container_client("story_clusters")
    
    # Query all stories
    print("📊 Querying stories...")
    query = "SELECT * FROM c"
    stories = list(container.query_items(query=query, enable_cross_partition_query=True))
    
    print(f"Found {len(stories)} total stories")
    
    # Identify test stories
    test_stories = []
    for story in stories:
        story_id = story.get('id', '')
        title = story.get('title', '').lower()
        source_articles = story.get('source_articles', [])
        
        is_test = False
        
        # Test title patterns
        if any(pattern in title for pattern in [
            'breaking: major event',
            'major policy announcement', 
            'test article',
            'major breakthrough in renewable energy',
            'global markets rally',
            'new climate agreement reached'
        ]):
            is_test = True
        
        # Check for test sources
        if not is_test:
            test_sources = 0
            for article in source_articles:
                if isinstance(article, dict):
                    source = article.get('source', '').lower()
                    if ('test' in source or 
                        source.startswith('source ') or 
                        source == 'test source' or 
                        source == 'test source 1'):
                        test_sources += 1
            
            if test_sources > len(source_articles) // 2 and len(source_articles) > 0:
                is_test = True
        
        # Unrealistic number of sources
        if len(source_articles) > 100:
            is_test = True
            
        if is_test:
            test_stories.append(story_id)
    
    print(f"🗑️ Found {len(test_stories)} test stories to delete")
    
    # Confirm
    if input(f"Delete {len(test_stories)} test stories? (yes/no): ").lower() != 'yes':
        print("❌ Cancelled")
        return
    
    # Delete test stories
    deleted = 0
    for story_id in test_stories:
        try:
            container.delete_item(item=story_id, partition_key=story_id)
            deleted += 1
            print(f"  Deleted: {story_id}")
        except Exception as e:
            print(f"  ❌ Failed to delete {story_id}: {e}")
    
    print(f"✅ Cleanup complete! Deleted {deleted} test stories")

if __name__ == '__main__':
    cleanup_test_stories()
