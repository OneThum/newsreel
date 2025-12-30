#!/usr/bin/env python3
"""
Monitor RSS feed expansion progress
"""

import os
import time
from datetime import datetime, timezone
from azure.cosmos import CosmosClient

def get_cosmos_client():
    COSMOS_KEY = os.popen('az cosmosdb keys list --name newsreel-db-1759951135 --resource-group newsreel-rg --query primaryMasterKey -o tsv 2>/dev/null').read().strip()
    COSMOS_ENDPOINT = 'https://newsreel-db-1759951135.documents.azure.com:443/'
    return CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)

def monitor_rss_expansion():
    client = get_cosmos_client()
    database = client.get_database_client('newsreel-db')
    container = database.get_container_client('raw_articles')
    
    print("🔍 MONITORING RSS FEED EXPANSION")
    print("=" * 50)
    
    # Check recent articles (last 30 minutes)
    since_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    query = f'SELECT * FROM c WHERE c.published_at > "{since_time[:-4]}Z" ORDER BY c.published_at DESC'
    
    try:
        articles = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        # Group by source
        sources = {}
        for article in articles:
            source = article.get('source', 'unknown')
            if source not in sources:
                sources[source] = []
            sources[source].append(article)
        
        print(f"📄 Recent articles: {len(articles)}")
        print()
        
        # European sources
        european_sources = {
            'bbc', 'guardian', 'reuters', 'euronews', 'france24', 'dw', 'ansa', 'nos', 
            'vrt', 'rtbf', 'swi', 'orf', 'nrk', 'svt', 'dr', 'yle', 'tvp', 'ct24', 
            'agerpres', 'rtp', 'ert', 'lrt', 'lsm', 'err', 'ukrinform', 'anadolu', 'ruv'
        }
        
        # US sources
        us_sources = {
            'cnn', 'ap', 'npr', 'pbs', 'cbs', 'abc', 'nbc', 'usatoday', 'yahoo', 
            'axios', 'politico', 'the_verge', 'techcrunch'
        }
        
        european_count = sum(len(articles) for source, articles in sources.items() 
                           if any(es in source.lower() for es in european_sources))
        us_count = sum(len(articles) for source, articles in sources.items() 
                     if any(us in source.lower() for us in us_sources))
        
        print(f"🇪🇺 European sources: {european_count} articles")
        print(f"🇺�� US sources: {us_count} articles")
        print(f"🌍 Total new sources: {len(sources)}")
        print()
        
        if european_count > 0:
            print("🎉 SUCCESS! New European RSS feeds are active!")
            
            # Show sample European articles
            european_articles = []
            for source, articles in sources.items():
                if any(es in source.lower() for es in european_sources):
                    european_articles.extend(articles[:2])  # 2 per source
            
            print("📋 Sample European articles:")
            for i, article in enumerate(european_articles[:5], 1):
                title = article.get('title', '')[:60]
                source = article.get('source', 'unknown')
                print(f"  {i}. [{source}] {title}...")
        else:
            print("⏳ Waiting for European RSS feeds to activate...")
            
        return len(articles) > 0 and european_count > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = monitor_rss_expansion()
    if not success:
        print("\n💡 Next steps:")
        print("  1. RSS ingestion runs every 10 minutes")
        print("  2. Check Azure Function logs for issues")
        print("  3. Verify RSS_USE_ALL_FEEDS=true is set")
        print("  4. Test individual RSS feed URLs manually")
