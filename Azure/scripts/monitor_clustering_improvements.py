#!/usr/bin/env python3
"""
Monitor clustering improvements with new breaking news feeds
"""

import os
import time
from datetime import datetime, timezone, timedelta
from azure.cosmos import CosmosClient

def get_cosmos_client():
    COSMOS_KEY = os.popen('az cosmosdb keys list --name newsreel-db-1759951135 --resource-group newsreel-rg --query primaryMasterKey -o tsv 2>/dev/null').read().strip()
    COSMOS_ENDPOINT = 'https://newsreel-db-1759951135.documents.azure.com:443/'
    return CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)

def monitor_clustering():
    client = get_cosmos_client()
    database = client.get_database_client('newsreel-db')
    story_container = database.get_container_client('story_clusters')
    
    print("🔍 MONITORING CLUSTERING IMPROVEMENTS")
    print("="*50)
    
    # Get current stats
    total_stories = list(story_container.query_items('SELECT VALUE COUNT(1) FROM c', enable_cross_partition_query=True))[0]
    
    # Count by source distribution
    stories = list(story_container.query_items('SELECT TOP 1000 c.source_articles FROM c ORDER BY c.first_seen DESC', enable_cross_partition_query=True))
    
    source_counts = {}
    for story in stories:
        sources = story.get('source_articles', [])
        count = len(sources)
        source_counts[count] = source_counts.get(count, 0) + 1
    
    # Get multi-source stories
    multi_source_stories = list(story_container.query_items('''
        SELECT TOP 10 c.id, c.title, c.source_articles, c.first_seen
        FROM c 
        WHERE ARRAY_LENGTH(c.source_articles) >= 3
        ORDER BY c.first_seen DESC
    ''', enable_cross_partition_query=True))
    
    print(f"📊 Current Stats:")
    print(f"  Total stories: {total_stories:,}")
    print(f"  Multi-source stories (3+): {len(multi_source_stories)}")
    print()
    
    print("📈 Source Distribution (last 1000 stories):")
    total_sampled = sum(source_counts.values())
    for count in sorted(source_counts.keys()):
        pct = (source_counts[count] / total_sampled) * 100
        print(f"  {count} sources: {source_counts[count]} stories ({pct:.1f}%)")
    
    print()
    print("🎯 Recent Multi-Source Stories:")
    for i, story in enumerate(multi_source_stories[:5], 1):
        sources = story.get('source_articles', [])
        source_names = list(set(s.get('source', '') for s in sources if isinstance(s, dict)))
        title = story.get('title', '')[:60]
        
        print(f"  {i}. {len(source_names)} sources: {', '.join(source_names[:4])}")
        print(f"     \"{title}...\"")
    
    print()
    print("💡 Monitoring breaking news feeds for improved clustering...")
    
    return len(multi_source_stories)

if __name__ == "__main__":
    baseline = monitor_clustering()
    print(f"\n📈 Baseline: {baseline} multi-source stories")
    print("Will monitor for increases as breaking news occurs...")
