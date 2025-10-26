#!/usr/bin/env python3
"""
Delete articles older than 1 hour from Cosmos DB

This script keeps only articles ingested in the last hour.
Useful for testing/development to maintain a small dataset.
"""
import os
import sys
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../functions')))

load_dotenv()

from shared.cosmos_client import CosmosDBClient


def confirm_deletion():
    """Confirmation prompt before deletion"""
    print("="*80)
    print("⚠️  DELETE OLD ARTICLES")
    print("="*80)
    print("\nThis script will delete all articles EXCEPT those from the last hour.")
    print("Articles ingested in the last hour will be kept.")
    print("\nThis operation is PERMANENT and CANNOT BE UNDONE!")
    
    response = input("\nType 'DELETE OLD' to continue (or anything else to cancel): ")
    if response != "DELETE OLD":
        print("❌ Operation cancelled.")
        return False
    
    return True


def delete_old_articles():
    """Delete articles older than 1 hour"""
    if not confirm_deletion():
        sys.exit(0)
    
    print("\n" + "="*80)
    print("Starting cleanup...")
    print("="*80 + "\n")
    
    try:
        # Connect to Cosmos DB
        client = CosmosDBClient()
        client.connect()
        print("✓ Connected to Cosmos DB\n")
        
        # Calculate cutoff time (1 hour ago)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
        cutoff_iso = cutoff_time.isoformat()
        
        print(f"⏰ Cutoff time: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"   (Keeping articles ingested after this time)\n")
        
        # Get container
        container = client._get_container("raw_articles")
        
        # Query articles older than 1 hour
        print("📊 Querying old articles...")
        query = f"SELECT c.id, c.published_date FROM c WHERE c.fetched_at < '{cutoff_iso}'"
        old_articles = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        # Query recent articles (for info)
        query_recent = f"SELECT VALUE COUNT(1) FROM c WHERE c.fetched_at >= '{cutoff_iso}'"
        recent_count = list(container.query_items(
            query=query_recent,
            enable_cross_partition_query=True
        ))[0]
        
        total_old = len(old_articles)
        print(f"Found {total_old:,} articles to delete (older than 1 hour)")
        print(f"Found {recent_count:,} recent articles to keep (last hour)\n")
        
        if total_old == 0:
            print("✓ No old articles to delete.")
            return
        
        # Confirm before proceeding
        proceed = input(f"Delete {total_old:,} old articles? (y/N): ")
        if proceed.lower() != 'y':
            print("❌ Operation cancelled.")
            return
        
        # Delete old articles
        print("\n🗑️  Deleting old articles...")
        deleted = 0
        failed = 0
        
        for article in old_articles:
            try:
                container.delete_item(
                    item=article['id'],
                    partition_key=article['published_date']
                )
                deleted += 1
                
                # Progress indicator
                if deleted % 100 == 0:
                    print(f"  Deleted {deleted:,}/{total_old:,} articles ({deleted/total_old*100:.1f}%)")
                
            except Exception as e:
                failed += 1
                if failed <= 5:  # Only print first 5 errors
                    print(f"  ⚠️  Failed to delete {article['id']}: {e}")
        
        print("\n" + "="*80)
        print("CLEANUP COMPLETE")
        print("="*80)
        print(f"✓ Deleted: {deleted:,} old articles")
        print(f"✓ Kept: {recent_count:,} recent articles (last hour)")
        if failed > 0:
            print(f"⚠️  Failed to delete: {failed:,} articles")
        print(f"\nTimestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    delete_old_articles()

