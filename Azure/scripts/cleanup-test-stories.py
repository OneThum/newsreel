#!/usr/bin/env python3
"""
Clean up test stories from the Newsreel database.

This script identifies and removes stories that were created during testing
and are polluting the production feed with old content.
"""

import os
import sys
import json
from datetime import datetime, timezone

# Add the functions directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'functions'))

try:
    from shared.cosmos_client import cosmos_client
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the Azure/scripts directory")
    sys.exit(1)


def is_test_story(story: dict) -> bool:
    """Determine if a story is test data that should be deleted."""

    title = story.get('title', '').lower()
    headline = story.get('headline', '').lower()
    source_articles = story.get('source_articles', [])

    # Check title patterns (case insensitive)
    test_title_patterns = [
        'breaking: major event',
        'major policy announcement',
        'test article',
        'test article 0',
        'major breakthrough in renewable energy',
        'global markets rally',
        'new climate agreement reached'
    ]

    if any(pattern in title for pattern in test_title_patterns):
        return True

    if any(pattern in headline for pattern in test_title_patterns):
        return True

    # Check for test sources
    test_source_count = 0
    for article in source_articles:
        if isinstance(article, dict):
            source = article.get('source', '').lower()
            if ('test' in source or
                source.startswith('source ') or
                source == 'test source' or
                source == 'test source 1'):
                test_source_count += 1

    # If more than half the sources are test sources, it's a test story
    if test_source_count > len(source_articles) // 2 and len(source_articles) > 0:
        return True

    # Check for unrealistic number of sources (>100 is definitely test data)
    if len(source_articles) > 100:
        return True

    # Check for stories with only test sources
    if len(source_articles) > 0 and test_source_count == len(source_articles):
        return True

    return False


def main():
    """Main cleanup function."""
    print("🧹 CLEANING UP TEST STORIES FROM NEWSREEL DATABASE")
    print("=" * 60)

    # Connect to Cosmos DB
    cosmos_client.connect()

    try:
        stories_container = cosmos_client._get_container('story_clusters')

        # Query all stories
        print("📊 Querying all stories...")
        query = 'SELECT * FROM c'
        all_stories = list(stories_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))

        print(f"Found {len(all_stories)} total stories")

        # Analyze and categorize stories
        test_stories = []
        real_stories = []

        print("🔍 Analyzing stories...")
        for story in all_stories:
            if is_test_story(story):
                test_stories.append(story)
            else:
                real_stories.append(story)

        print("\n📊 ANALYSIS COMPLETE:")
        print(f"  ✅ Real stories to keep: {len(real_stories)}")
        print(f"  🗑️  Test stories to delete: {len(test_stories)}")

        if not test_stories:
            print("🎉 No test stories found! Database is clean.")
            return

        # Show sample of test stories
        print("\n🗑️  TEST STORIES TO DELETE (first 5):")
        for i, story in enumerate(test_stories[:5]):
            story_id = story.get('id', 'unknown')
            title = story.get('title', '')[:50]
            sources_count = len(story.get('source_articles', []))
            print(f"  {i+1}. {story_id} - {title}... ({sources_count} sources)")

        if len(test_stories) > 5:
            print(f"  ... and {len(test_stories) - 5} more")

        # Confirm deletion
        print(f"\n⚠️  This will delete {len(test_stories)} test stories from the database.")
        confirm = input("Continue? (type 'yes' to proceed): ").strip().lower()

        if confirm != 'yes':
            print("❌ Cleanup cancelled.")
            return

        # Delete test stories
        print("\n🗑️  DELETING TEST STORIES...")
        deleted_count = 0

        for story in test_stories:
            try:
                story_id = story.get('id')
                category = story.get('category')
                if story_id and category:
                    # Delete by ID using category as partition key
                    stories_container.delete_item(item=story_id, partition_key=category)
                    deleted_count += 1

                    if deleted_count % 10 == 0:
                        print(f"  Deleted {deleted_count}/{len(test_stories)} stories...")

            except Exception as e:
                print(f"  ❌ Error deleting story {story.get('id')}: {e}")

        print(f"\n✅ CLEANUP COMPLETE!")
        print(f"  Deleted: {deleted_count} test stories")
        print(f"  Remaining: {len(real_stories)} real stories")
        print("\n🎉 Database is now clean! Fresh news only!")
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
