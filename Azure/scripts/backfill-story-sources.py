#!/usr/bin/env python3
"""
Backfill script to populate source_articles for existing stories
This script finds all stories with empty source_articles and populates them
by finding matching raw articles based on the story's fingerprint and title
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'functions'))

from shared.cosmos_client import cosmos_client
from shared.config import config
from shared.utils import calculate_text_similarity
from datetime import datetime, timezone

async def backfill_story_sources():
    """Backfill source_articles for stories that don't have them"""
    cosmos_client.connect()
    
    # Get all stories
    print("Fetching all stories...")
    stories = await cosmos_client.query_recent_stories(limit=1000)
    print(f"Found {len(stories)} stories")
    
    # Filter stories with no source_articles
    stories_to_fix = [s for s in stories if not s.get('source_articles') or len(s.get('source_articles', [])) == 0]
    print(f"Found {len(stories_to_fix)} stories with no source_articles")
    
    if not stories_to_fix:
        print("No stories need fixing!")
        return
    
    fixed_count = 0
    skipped_count = 0
    
    for i, story in enumerate(stories_to_fix, 1):
        story_id = story['id']
        title = story.get('title', '')
        fingerprint = story.get('event_fingerprint', '')
        category = story.get('category', 'general')
        
        print(f"\n[{i}/{len(stories_to_fix)}] Processing story: {story_id}")
        print(f"  Title: {title[:60]}...")
        
        # Find matching articles by fingerprint first
        matching_articles = []
        
        # Try to find articles by fingerprint
        if fingerprint:
            print(f"  Searching for articles with fingerprint: {fingerprint}")
            # Query raw articles with matching fingerprint
            # Note: We'll need to query across all partitions
            try:
                query = f"SELECT * FROM c WHERE c.story_fingerprint = '{fingerprint}'"
                container = cosmos_client._get_container(config.CONTAINER_RAW_ARTICLES)
                items = container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                )
                for item in items:
                    matching_articles.append(item)
                print(f"  Found {len(matching_articles)} articles by fingerprint")
            except Exception as e:
                print(f"  Error querying by fingerprint: {e}")
        
        # If no fingerprint matches, try fuzzy title matching
        if not matching_articles:
            print(f"  No fingerprint matches, trying fuzzy title matching...")
            try:
                # Get recent articles in same category
                query = f"SELECT * FROM c WHERE c.category = '{category}' ORDER BY c.published_at DESC OFFSET 0 LIMIT 500"
                container = cosmos_client._get_container(config.CONTAINER_RAW_ARTICLES)
                items = container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                )
                
                best_match = None
                best_similarity = 0.0
                
                for item in items:
                    article_title = item.get('title', '')
                    similarity = calculate_text_similarity(title, article_title)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = item
                    
                    # If similarity is high enough, consider it a match
                    if similarity > 0.60:  # 60% threshold
                        matching_articles.append(item)
                
                print(f"  Found {len(matching_articles)} articles by fuzzy matching (best: {best_similarity:.2f})")
            except Exception as e:
                print(f"  Error in fuzzy matching: {e}")
        
        if matching_articles:
            # Update story with source_articles
            source_article_ids = [article['id'] for article in matching_articles]
            
            try:
                # Update the story
                story['source_articles'] = source_article_ids
                story['verification_level'] = len(source_article_ids)
                story['last_updated'] = datetime.now(timezone.utc).isoformat()
                
                # Update in database
                container = cosmos_client._get_container(config.CONTAINER_STORY_CLUSTERS)
                container.upsert_item(body=story)
                
                print(f"  ✅ Updated story with {len(source_article_ids)} source articles")
                fixed_count += 1
                
                # Mark articles as processed
                for article in matching_articles:
                    try:
                        article['processed'] = True
                        article['story_id'] = story_id
                        article_container = cosmos_client._get_container(config.CONTAINER_RAW_ARTICLES)
                        article_container.upsert_item(body=article)
                    except Exception as e:
                        print(f"  Warning: Could not mark article {article['id']} as processed: {e}")
                
            except Exception as e:
                print(f"  ❌ Error updating story: {e}")
                skipped_count += 1
        else:
            print(f"  ⚠️  No matching articles found, skipping")
            skipped_count += 1
    
    print(f"\n\n=== BACKFILL COMPLETE ===")
    print(f"Fixed: {fixed_count} stories")
    print(f"Skipped: {skipped_count} stories")
    print(f"Total processed: {len(stories_to_fix)} stories")

if __name__ == "__main__":
    asyncio.run(backfill_story_sources())

