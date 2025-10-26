#!/usr/bin/env python3
"""
Clear all data from Cosmos DB for a fresh start
This script deletes all articles and stories from the database
"""
import os
import sys
from azure.cosmos import CosmosClient
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_cosmos_client():
    """Get Cosmos DB client and containers"""
    connection_string = os.getenv("COSMOS_CONNECTION_STRING")
    if not connection_string:
        raise ValueError("COSMOS_CONNECTION_STRING environment variable not set")
    
    database_name = os.getenv("COSMOS_DATABASE_NAME", "newsreel-db")
    
    client = CosmosClient.from_connection_string(connection_string)
    database = client.get_database_client(database_name)
    
    articles_container = database.get_container_client("raw_articles")
    stories_container = database.get_container_client("story_clusters")
    
    return articles_container, stories_container

def clear_all_data():
    """Clear all articles and stories from the database"""
    
    logger.info("🗑️  Starting database cleanup...")
    logger.info("This will delete ALL articles and stories from the database")
    
    try:
        articles_container, stories_container = get_cosmos_client()
        
        # Count items before deletion
        articles_count = list(articles_container.query_items(
            query="SELECT VALUE COUNT(1) FROM c",
            enable_cross_partition_query=True
        ))[0]
        
        stories_count = list(stories_container.query_items(
            query="SELECT VALUE COUNT(1) FROM c",
            enable_cross_partition_query=True
        ))[0]
        
        logger.info(f"Found {articles_count:,} articles and {stories_count:,} stories")
        
        if articles_count == 0 and stories_count == 0:
            logger.info("✅ Database is already empty")
            return
        
        # Delete all articles
        if articles_count > 0:
            logger.info(f"\n📰 Deleting {articles_count:,} articles...")
            deleted_articles = 0
            
            items = list(articles_container.query_items(
                query="SELECT c.id, c.published_date FROM c",
                enable_cross_partition_query=True
            ))
            
            for item in items:
                try:
                    partition_key = item.get('published_date', item['id'].split('_')[1][:10])
                    articles_container.delete_item(
                        item=item['id'],
                        partition_key=partition_key
                    )
                    deleted_articles += 1
                    
                    if deleted_articles % 100 == 0:
                        logger.info(f"  Deleted {deleted_articles:,}/{articles_count:,} articles...")
                except Exception as e:
                    logger.error(f"Error deleting article {item['id']}: {e}")
            
            logger.info(f"✅ Deleted {deleted_articles:,} articles")
        
        # Delete all stories
        if stories_count > 0:
            logger.info(f"\n📚 Deleting {stories_count:,} stories...")
            deleted_stories = 0
            
            items = list(stories_container.query_items(
                query="SELECT c.id, c.category FROM c",
                enable_cross_partition_query=True
            ))
            
            for item in items:
                try:
                    partition_key = item.get('category', item['id'])
                    stories_container.delete_item(
                        item=item['id'],
                        partition_key=partition_key
                    )
                    deleted_stories += 1
                    
                    if deleted_stories % 100 == 0:
                        logger.info(f"  Deleted {deleted_stories:,}/{stories_count:,} stories...")
                except Exception as e:
                    logger.error(f"Error deleting story {item['id']}: {e}")
            
            logger.info(f"✅ Deleted {deleted_stories:,} stories")
        
        # Verify deletion
        logger.info("\n📊 Verifying deletion...")
        remaining_articles = list(articles_container.query_items(
            query="SELECT VALUE COUNT(1) FROM c",
            enable_cross_partition_query=True
        ))[0]
        
        remaining_stories = list(stories_container.query_items(
            query="SELECT VALUE COUNT(1) FROM c",
            enable_cross_partition_query=True
        ))[0]
        
        logger.info(f"Remaining articles: {remaining_articles}")
        logger.info(f"Remaining stories: {remaining_stories}")
        
        if remaining_articles == 0 and remaining_stories == 0:
            logger.info("\n✅ Database successfully cleared!")
            logger.info("The system will start fresh on the next RSS ingestion cycle")
        else:
            logger.warning(f"\n⚠️  Some items remain: {remaining_articles} articles, {remaining_stories} stories")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise

if __name__ == "__main__":
    try:
        clear_all_data()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Cleanup interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
