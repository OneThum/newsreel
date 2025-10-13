#!/usr/bin/env python3
"""Check the actual 'source' field values in the database for a story's articles"""

import sys
from azure.cosmos import CosmosClient
from datetime import datetime, timedelta
import os

COSMOS_KEY = os.popen('az cosmosdb keys list --name newsreel-db-1759951135 --resource-group newsreel-rg --query primaryMasterKey -o tsv 2>/dev/null').read().strip()
COSMOS_ENDPOINT = "https://newsreel-db-1759951135.documents.azure.com:443/"

# The National Guard story
STORY_ID = "story_20251008_201007_7c5764d6d050ae41"

print(f"🔍 Checking actual source field values in database")
print(f"{'='*80}\n")

try:
    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = client.get_database_client("newsreel-db")
    
    # Get the story
    story_container = database.get_container_client("story_clusters")
    items = list(story_container.query_items(
        query="SELECT * FROM c WHERE c.id = @story_id",
        parameters=[{"name": "@story_id", "value": STORY_ID}],
        enable_cross_partition_query=True
    ))
    
    if not items:
        print("❌ Story not found!")
        sys.exit(1)
    
    story = items[0]
    source_articles = story.get('source_articles', [])
    
    print(f"📰 Story: {STORY_ID}")
    print(f"   Title: {story.get('title', 'N/A')}")
    print(f"   Article IDs: {len(source_articles)}\n")
    print(f"{'='*80}\n")
    
    # Get each article
    articles_container = database.get_container_client("raw_articles")
    
    print(f"Fetching article details from database...")
    print()
    
    found_articles = []
    
    for i, art_id in enumerate(source_articles, 1):
        # Try to determine partition key from ID
        parts = art_id.split('_')
        
        # Try old format (source_YYYYMMDD_timestamp_hash)
        if len(parts) >= 2 and len(parts[1]) == 8 and parts[1].isdigit():
            date_str = parts[1]
            partition_key = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            
            try:
                article = articles_container.read_item(item=art_id, partition_key=partition_key)
                found_articles.append(article)
                
                source_value = article.get('source', 'UNKNOWN')
                title = article.get('title', 'N/A')[:60]
                
                print(f"[{i}] ID: {art_id}")
                print(f"    source field: '{source_value}'")
                print(f"    title: {title}...")
                print()
                
            except Exception as e:
                print(f"[{i}] ID: {art_id}")
                print(f"    ❌ Could not fetch: {e}")
                print()
        else:
            # New format, try recent dates
            found = False
            for days_ago in range(7):
                date = datetime.utcnow() - timedelta(days=days_ago)
                partition_key = date.strftime('%Y-%m-%d')
                try:
                    article = articles_container.read_item(item=art_id, partition_key=partition_key)
                    found_articles.append(article)
                    found = True
                    
                    source_value = article.get('source', 'UNKNOWN')
                    title = article.get('title', 'N/A')[:60]
                    
                    print(f"[{i}] ID: {art_id}")
                    print(f"    source field: '{source_value}'")
                    print(f"    title: {title}...")
                    print()
                    
                    break
                except:
                    continue
            
            if not found:
                print(f"[{i}] ID: {art_id}")
                print(f"    ❌ Could not fetch from any partition")
                print()
    
    print(f"{'='*80}\n")
    
    # Analyze source fields
    source_values = [a.get('source', 'UNKNOWN') for a in found_articles]
    unique_sources = set(source_values)
    
    print(f"ANALYSIS:")
    print(f"   Total articles in story: {len(source_articles)}")
    print(f"   Successfully fetched: {len(found_articles)}")
    print(f"   Unique 'source' field values: {len(unique_sources)}")
    print(f"   Source values: {list(unique_sources)}")
    print()
    
    if len(unique_sources) == 1:
        print(f"✅ All articles have the SAME source value: '{list(unique_sources)[0]}'")
        print(f"   API deduplication SHOULD work - all have same source name")
        print(f"   → The API code must have a bug or isn't running")
    else:
        print(f"⚠️  Articles have DIFFERENT source values!")
        print(f"   This explains why API isn't deduplicating properly")
        print(f"   Each unique source value becomes a separate entry")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

