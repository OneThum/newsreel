#!/usr/bin/env python3
"""
Diagnostic Script: Check Clustering Pipeline Status

This script checks:
1. Are articles in raw_articles?
2. Are stories in story_clusters?
3. What are the story statuses?
4. Are change feed triggers firing?
"""

import sys
import os
import json
from datetime import datetime, timezone, timedelta

# Get Cosmos connection from environment
connection_string = os.getenv('COSMOS_CONNECTION_STRING')
database_name = os.getenv('COSMOS_DATABASE_NAME', 'newsreel-db')

if not connection_string:
    print("❌ ERROR: COSMOS_CONNECTION_STRING not set")
    print("Make sure you've configured Azure Function environment variables")
    sys.exit(1)

print("╔════════════════════════════════════════════════════════════════╗")
print("║              CLUSTERING PIPELINE DIAGNOSTIC                   ║")
print("╚════════════════════════════════════════════════════════════════╝\n")

try:
    from azure.cosmos import CosmosClient
    
    client = CosmosClient.from_connection_string(connection_string)
    db = client.get_database_client(database_name)
    
    print(f"✅ Connected to Cosmos DB: {database_name}\n")
    
    # ============================================================================
    # 1. CHECK RAW ARTICLES
    # ============================================================================
    print("┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
    print("┃ 1. RAW ARTICLES (RSS Ingestion)                             ┃")
    print("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n")
    
    try:
        raw_container = db.get_container_client("raw_articles")
        
        # Count total articles
        query = "SELECT VALUE COUNT(1) FROM c"
        count_result = list(raw_container.query_items(query=query, enable_cross_partition_query=True))
        total_articles = count_result[0] if count_result else 0
        
        print(f"Total articles in raw_articles: {total_articles}")
        
        if total_articles > 0:
            # Get recent articles
            query = "SELECT TOP 5 c.id, c.source, c.title, c.processed, c._ts FROM c ORDER BY c._ts DESC"
            recent = list(raw_container.query_items(query=query, enable_cross_partition_query=True))
            
            print("\n📋 5 Most Recent Articles:")
            for i, article in enumerate(recent, 1):
                article_id = article.get('id', 'N/A')
                source = article.get('source', 'N/A')
                title = article.get('title', 'N/A')[:60]
                processed = article.get('processed', False)
                ts = article.get('_ts', 0)
                age_seconds = (datetime.now().timestamp() - ts)
                age_minutes = int(age_seconds / 60)
                
                print(f"\n  {i}. {article_id}")
                print(f"     Source: {source}")
                print(f"     Title: {title}")
                print(f"     Processed: {processed}")
                print(f"     Age: {age_minutes} minutes ago")
            
            # Check unprocessed count
            query = "SELECT VALUE COUNT(1) FROM c WHERE c.processed != true"
            unprocessed_result = list(raw_container.query_items(query=query, enable_cross_partition_query=True))
            unprocessed_count = unprocessed_result[0] if unprocessed_result else 0
            
            print(f"\n⚠️  Unprocessed articles: {unprocessed_count}")
            print(f"✅ Processed articles: {total_articles - unprocessed_count}")
        else:
            print("❌ NO articles in raw_articles - RSS ingestion not running!")
    
    except Exception as e:
        print(f"❌ Error querying raw_articles: {e}")
    
    # ============================================================================
    # 2. CHECK STORY CLUSTERS
    # ============================================================================
    print("\n\n┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
    print("┃ 2. STORY CLUSTERS (Clustering)                             ┃")
    print("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n")
    
    try:
        story_container = db.get_container_client("story_clusters")
        
        # Count total stories
        query = "SELECT VALUE COUNT(1) FROM c"
        count_result = list(story_container.query_items(query=query, enable_cross_partition_query=True))
        total_stories = count_result[0] if count_result else 0
        
        print(f"Total stories in story_clusters: {total_stories}")
        
        if total_stories > 0:
            # Get stories by status
            query = "SELECT c.status, COUNT(1) as count FROM c GROUP BY c.status"
            status_counts = list(story_container.query_items(query=query, enable_cross_partition_query=True))
            
            print("\n📊 Stories by Status:")
            status_summary = {}
            for item in status_counts:
                status = item.get('status', 'UNKNOWN')
                count = item.get('count', 0)
                status_summary[status] = count
                print(f"  {status}: {count}")
            
            # Summary for API
            developing_count = status_summary.get('DEVELOPING', 0)
            breaking_count = status_summary.get('BREAKING', 0)
            verified_count = status_summary.get('VERIFIED', 0)
            monitoring_count = status_summary.get('MONITORING', 0)
            
            shown_count = developing_count + breaking_count + verified_count
            print(f"\n✅ Stories shown in feed: {shown_count} (DEVELOPING + BREAKING + VERIFIED)")
            print(f"❌ Stories hidden from feed: {monitoring_count} (MONITORING - only 1 source)")
            
            # Get details on a few recent stories
            query = "SELECT TOP 5 c.id, c.status, c.title, c.source_articles, c._ts FROM c ORDER BY c._ts DESC"
            recent = list(story_container.query_items(query=query, enable_cross_partition_query=True))
            
            print("\n📋 5 Most Recent Stories:")
            for i, story in enumerate(recent, 1):
                story_id = story.get('id', 'N/A')
                status = story.get('status', 'N/A')
                title = story.get('title', 'N/A')[:60]
                sources = len(story.get('source_articles', []))
                ts = story.get('_ts', 0)
                age_seconds = (datetime.now().timestamp() - ts)
                age_minutes = int(age_seconds / 60)
                
                visibility = "✅ VISIBLE" if status != 'MONITORING' else "❌ HIDDEN"
                
                print(f"\n  {i}. {story_id}")
                print(f"     Title: {title}")
                print(f"     Status: {status} ({visibility})")
                print(f"     Sources: {sources}")
                print(f"     Age: {age_minutes} minutes ago")
        else:
            print("❌ NO stories in story_clusters - clustering not running!")
    
    except Exception as e:
        print(f"❌ Error querying story_clusters: {e}")
    
    # ============================================================================
    # 3. CHECK LEASES (Change Feed Status)
    # ============================================================================
    print("\n\n┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
    print("┃ 3. CHANGE FEED LEASES (Trigger Status)                    ┃")
    print("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n")
    
    try:
        lease_container = db.get_container_client("leases")
        
        # Get all leases
        query = "SELECT TOP 10 c.id, c._ts FROM c ORDER BY c._ts DESC"
        leases = list(lease_container.query_items(query=query, enable_cross_partition_query=True))
        
        if leases:
            print(f"Found {len(leases)} change feed leases:\n")
            for lease in leases:
                lease_id = lease.get('id', 'N/A')
                ts = lease.get('_ts', 0)
                age_seconds = (datetime.now().timestamp() - ts)
                age_minutes = int(age_seconds / 60)
                
                print(f"  Lease: {lease_id}")
                print(f"  Last updated: {age_minutes} minutes ago\n")
        else:
            print("❌ NO leases found - change feed may not be running")
    
    except Exception as e:
        print(f"⚠️  Error checking leases: {e}")
    
    # ============================================================================
    # 4. DIAGNOSIS SUMMARY
    # ============================================================================
    print("\n┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
    print("┃ DIAGNOSIS SUMMARY                                          ┃")
    print("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n")
    
    if total_articles == 0:
        print("❌ CRITICAL: No articles in database")
        print("   Problem: RSS ingestion is not running or failing")
        print("   Solution: Check Azure Function App logs for RSS_Ingestion function\n")
    
    elif total_stories == 0:
        print("⚠️  Articles exist but no stories created")
        print("   Problem: Clustering change feed trigger may not be firing")
        print("   Possible causes:")
        print("     1. Leases container doesn't exist")
        print("     2. Change feed is not enabled on raw_articles")
        print("     3. Clustering function crashed")
        print("   Solution: Check Azure Function App logs\n")
    
    else:
        if shown_count == 0:
            print("⚠️  Stories exist but none are visible in API feed")
            print(f"   All {monitoring_count} stories are in MONITORING status (1 source only)")
            print("   Problem: No articles are clustering together")
            print("   Likely causes:")
            print("     1. Fingerprinting not working (all articles unique)")
            print("     2. Similarity threshold too high")
            print("     3. Topic conflict detection too strict")
            print("     4. Articles are from different RSS feeds with different topics\n")
        else:
            print(f"✅ Pipeline is working!")
            print(f"   {shown_count} stories are visible in the feed")
            print(f"   {monitoring_count} stories are still gathering sources\n")

except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("Make sure COSMOS_CONNECTION_STRING is set")
    sys.exit(1)

