#!/usr/bin/env python3
"""Check if RECENT stories (after today's fix) have duplicate sources"""

import sys
import json
from collections import Counter
from azure.cosmos import CosmosClient
from datetime import datetime, timezone
import os

COSMOS_KEY = os.popen('az cosmosdb keys list --name newsreel-db-1759951135 --resource-group newsreel-rg --query primaryMasterKey -o tsv 2>/dev/null').read().strip()
COSMOS_ENDPOINT = "https://newsreel-db-1759951135.documents.azure.com:443/"

print(f"🔍 Checking RECENT stories (created after 09:45 UTC today)")
print(f"   Fix deployed at: 2025-10-13T09:45:00Z")
print(f"{'='*80}\n")

try:
    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = client.get_database_client("newsreel-db")
    container = database.get_container_client("story_clusters")
    
    # Query recent stories
    cutoff_time = "2025-10-13T09:45:00Z"
    query = f"""
    SELECT * FROM c 
    WHERE c.first_seen > '{cutoff_time}'
    AND ARRAY_LENGTH(c.source_articles) > 1
    """
    
    items = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    
    # Filter out feed_poll_state
    stories = [item for item in items if item.get('doc_type') != 'feed_poll_state']
    
    print(f"📊 Found {len(stories)} stories created after the fix\n")
    
    if not stories:
        print(f"ℹ️  No recent stories with multiple sources yet")
        print(f"   This is normal - stories need time to accumulate sources")
        print(f"   The fix will prevent duplicates in NEW stories")
        sys.exit(0)
    
    issues_found = 0
    
    for story in stories[:5]:  # Check first 5
        story_id = story.get('id', 'unknown')
        title = story.get('title', 'N/A')[:80]
        source_articles = story.get('source_articles', [])
        
        print(f"📰 Story: {story_id}")
        print(f"   Title: {title}")
        print(f"   Created: {story.get('first_seen', 'N/A')}")
        print(f"   Articles: {len(source_articles)}")
        
        # Extract sources
        sources = [art_id.split('_')[0] for art_id in source_articles]
        source_counts = Counter(sources)
        unique_count = len(source_counts)
        
        if unique_count == len(sources):
            print(f"   ✅ All {len(sources)} sources UNIQUE\n")
        else:
            issues_found += 1
            duplicates = {k: v for k, v in source_counts.items() if v > 1}
            print(f"   ❌ DUPLICATES FOUND: {dict(duplicates)}")
            print(f"   Article IDs:")
            for i, art_id in enumerate(source_articles[:5], 1):
                print(f"      [{i}] {art_id}")
            print()
    
    print(f"{'='*80}\n")
    
    if issues_found == 0:
        print(f"✅ SUCCESS! No duplicates in recent stories")
        print(f"   The update-in-place fix is WORKING")
        print(f"   Old stories (before fix) will have duplicates, but new ones won't")
    else:
        print(f"❌ PROBLEM! {issues_found} recent stories have duplicates")
        print(f"   The update-in-place fix is NOT working")
        print(f"   Need to investigate why new articles are still creating duplicates")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

