#!/usr/bin/env python3
"""Quick script to check a specific story's sources for duplicates"""

import sys
import json
from collections import Counter
from azure.cosmos import CosmosClient
import os

# Get from environment or Azure
COSMOS_KEY = os.popen('az cosmosdb keys list --name newsreel-db-1759951135 --resource-group newsreel-rg --query primaryMasterKey -o tsv 2>/dev/null').read().strip()
COSMOS_ENDPOINT = "https://newsreel-db-1759951135.documents.azure.com:443/"

# Story ID from status page
STORY_ID = "story_20251008_201007_7c5764d6d050ae41"  # National Guard story with 19 sources

print(f"🔍 Analyzing story: {STORY_ID}")
print(f"{'='*80}\n")

try:
    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = client.get_database_client("newsreel-db")
    container = database.get_container_client("story_clusters")
    
    # Query the story
    query = "SELECT * FROM c WHERE c.id = @story_id"
    items = list(container.query_items(
        query=query,
        parameters=[{"name": "@story_id", "value": STORY_ID}],
        enable_cross_partition_query=True
    ))
    
    if not items:
        print(f"❌ Story not found!")
        sys.exit(1)
    
    story = items[0]
    
    print(f"📰 Title: {story.get('title', 'N/A')}")
    print(f"📊 Status: {story.get('status', 'N/A')}")
    print(f"🔢 Verification Level: {story.get('verification_level', 0)}")
    print(f"\n{'='*80}\n")
    
    source_articles = story.get('source_articles', [])
    print(f"📋 Source Articles Array: {len(source_articles)} articles")
    print(f"\n{'='*80}\n")
    
    # Extract sources from article IDs
    sources = []
    print(f"Article IDs and extracted sources:")
    for i, art_id in enumerate(source_articles[:10], 1):  # Show first 10
        # Extract source from ID (format: source_hash or source_YYYYMMDD_...)
        source = art_id.split('_')[0]
        sources.append(source)
        print(f"  [{i}] {art_id[:60]}...")
        print(f"      Source: {source}")
    
    if len(source_articles) > 10:
        print(f"  ... and {len(source_articles) - 10} more")
    
    print(f"\n{'='*80}\n")
    
    # Count sources
    source_counts = Counter(sources)
    unique_count = len(source_counts)
    total_count = len(sources)
    
    print(f"📊 SOURCE ANALYSIS:")
    print(f"   Total articles checked: {total_count}")
    print(f"   Unique sources: {unique_count}")
    print(f"\n")
    
    if unique_count == total_count:
        print(f"✅ ALL SOURCES UNIQUE - No duplicates!")
    else:
        print(f"❌ DUPLICATES DETECTED!")
        print(f"   {total_count - unique_count} duplicate entries\n")
        
        print(f"Breakdown:")
        for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
            if count > 1:
                print(f"  🔴 {source}: appears {count} times")
            else:
                print(f"  🟢 {source}: appears once")
    
    print(f"\n{'='*80}\n")
    
    # Now fetch the actual articles to see more details
    print(f"📄 Fetching article details...")
    articles_container = database.get_container_client("raw_articles")
    
    article_details = []
    for art_id in source_articles[:5]:  # Get first 5
        # Try to determine partition key
        parts = art_id.split('_')
        if len(parts) >= 2 and len(parts[1]) == 8 and parts[1].isdigit():
            date_str = parts[1]
            partition_key = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        else:
            # New format, try recent dates
            from datetime import datetime, timedelta
            for days_ago in range(7):
                date = datetime.utcnow() - timedelta(days=days_ago)
                partition_key = date.strftime('%Y-%m-%d')
                try:
                    article = articles_container.read_item(item=art_id, partition_key=partition_key)
                    article_details.append(article)
                    break
                except:
                    continue
    
    if article_details:
        print(f"\nFirst {len(article_details)} articles:")
        for i, art in enumerate(article_details, 1):
            print(f"\n  [{i}] Source: {art.get('source', 'unknown')}")
            print(f"      Title: {art.get('title', 'N/A')[:80]}")
            print(f"      URL: {art.get('article_url', 'N/A')[:80]}")
    
    print(f"\n{'='*80}\n")
    
    # CONCLUSION
    if unique_count == len(source_articles):
        print(f"✅ CONCLUSION: Story has {len(source_articles)} UNIQUE sources")
        print(f"   Backend storage is CORRECT - no duplicates in database")
        print(f"   If iOS shows duplicates, the problem is in API or iOS decoding")
    else:
        duplicates = {k: v for k, v in source_counts.items() if v > 1}
        print(f"❌ CONCLUSION: Backend has DUPLICATE SOURCES")
        print(f"   Database contains duplicate article IDs from same sources")
        print(f"   Duplicates: {dict(duplicates)}")
        print(f"   This needs to be fixed in clustering logic (function_app.py)")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

