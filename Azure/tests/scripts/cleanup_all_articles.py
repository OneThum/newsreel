#!/usr/bin/env python3
"""
⚠️  DESTRUCTIVE OPERATION ⚠️
Delete ALL articles from Cosmos DB

This script will permanently delete every article in the raw_articles container.
USE WITH EXTREME CAUTION - This cannot be undone!
"""
import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../functions')))

load_dotenv()

from shared.cosmos_client import CosmosDBClient


def confirm_deletion():
    """Multiple confirmation prompts before deletion"""
    print("="*80)
    print("⚠️  WARNING: DESTRUCTIVE OPERATION ⚠️")
    print("="*80)
    print("\nThis script will DELETE ALL ARTICLES from Cosmos DB!")
    print("This operation is PERMANENT and CANNOT BE UNDONE!")
    print("\nYou are about to delete:")
    print("  • ALL raw articles")
    print("  • ALL ingestion history")
    print("  • ALL processing metadata")
    print("\n" + "="*80)
    
    # First confirmation
    response1 = input("\nType 'DELETE ALL ARTICLES' to continue (or anything else to cancel): ")
    if response1 != "DELETE ALL ARTICLES":
        print("❌ Operation cancelled.")
        return False
    
    # Second confirmation
    print("\n⚠️  Are you absolutely sure?")
    response2 = input("Type 'YES I AM SURE' to proceed: ")
    if response2 != "YES I AM SURE":
        print("❌ Operation cancelled.")
        return False
    
    # Final confirmation with countdown
    print("\n⚠️  FINAL WARNING")
    print("This will delete ALL articles. This cannot be undone.")
    response3 = input("Type 'CONFIRM DELETE' to proceed: ")
    if response3 != "CONFIRM DELETE":
        print("❌ Operation cancelled.")
        return False
    
    return True


def delete_all_articles():
    """Delete all articles from Cosmos DB"""
    if not confirm_deletion():
        sys.exit(0)
    
    print("\n" + "="*80)
    print("Starting deletion process...")
    print("="*80 + "\n")
    
    try:
        # Connect to Cosmos DB
        client = CosmosDBClient()
        client.connect()
        print("✓ Connected to Cosmos DB\n")
        
        # Get container
        container = client._get_container("raw_articles")
        
        # Query all articles (ID and partition key only for efficiency)
        print("📊 Querying articles...")
        query = "SELECT c.id, c.published_date FROM c"
        articles = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        total = len(articles)
        print(f"Found {total:,} articles to delete\n")
        
        if total == 0:
            print("✓ No articles to delete. Database is already empty.")
            return
        
        # Final chance to abort
        print(f"⚠️  About to delete {total:,} articles...")
        proceed = input("Press ENTER to continue or Ctrl+C to abort: ")
        
        # Delete articles
        print("\n🗑️  Deleting articles...")
        deleted = 0
        failed = 0
        
        for article in articles:
            try:
                container.delete_item(
                    item=article['id'],
                    partition_key=article['published_date']
                )
                deleted += 1
                
                # Progress indicator
                if deleted % 100 == 0:
                    print(f"  Deleted {deleted:,}/{total:,} articles ({deleted/total*100:.1f}%)")
                
            except Exception as e:
                failed += 1
                if failed <= 5:  # Only print first 5 errors
                    print(f"  ⚠️  Failed to delete {article['id']}: {e}")
        
        print("\n" + "="*80)
        print("DELETION COMPLETE")
        print("="*80)
        print(f"✓ Successfully deleted: {deleted:,} articles")
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
    delete_all_articles()

