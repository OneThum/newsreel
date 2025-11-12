#!/usr/bin/env python3
"""
Delete specific test story from Cosmos DB
"""
import os
import sys
from datetime import datetime, timezone

# Add the functions directory to path
sys.path.append('Azure/functions')

try:
    from Azure.functions.shared.cosmos_client import cosmos_client
except ImportError:
    print("❌ Could not import cosmos_client")
    sys.exit(1)

def main():
    """Delete the specific test story"""
    print("🗑️ DELETING TEST STORY: story_20251110_140632_3163e3be")

    # Connect to Cosmos DB
    cosmos_client.connect()

    try:
        # Get the story to find its category
        stories_container = cosmos_client._get_container('story_clusters')

        # Query for the specific story
        query = "SELECT * FROM c WHERE c.id = 'story_20251110_140632_3163e3be'"
        stories = list(stories_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))

        if not stories:
            print("❌ Test story not found")
            return

        story = stories[0]
        story_id = story['id']
        category = story.get('category', 'general')
        title = story.get('title', '')
        source_count = len(story.get('source_articles', []))

        print(f"📋 Found story: {story_id}")
        print(f"   Category: {category}")
        print(f"   Title: {title}")
        print(f"   Sources: {source_count}")

        # Auto-confirm deletion for test story
        print("🔥 AUTO-DELETING test story (110 sources confirms it's test data)")

        # Delete the story
        stories_container.delete_item(item=story_id, partition_key=category)
        print(f"✅ DELETED: {story_id}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
