#!/usr/bin/env python3
"""
Delete all stories older than 4 hours from Cosmos DB
This will clean up old broken clusters and give the new clustering algorithm a fresh start.
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_cosmos_client():
    """Get Cosmos DB client"""
    connection_string = os.getenv("COSMOS_CONNECTION_STRING")
    if not connection_string:
        raise ValueError("COSMOS_CONNECTION_STRING environment variable not set")
    
    database_name = os.getenv("COSMOS_DATABASE_NAME", "newsreel-db")
    container_name = os.getenv("COSMOS_CONTAINER_NAME", "story_clusters")
    
    client = CosmosClient.from_connection_string(connection_string)
    database = client.get_database_client(database_name)
    container = database.get_container_client(container_name)
    
    return container

def delete_old_stories():
    """Delete all stories older than 4 hours"""
    
    # Calculate cutoff time (4 hours ago)
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=4)
    cutoff_iso = cutoff_time.isoformat(timespec='seconds') + 'Z'
    
    logger.info(f"Deleting stories older than {cutoff_iso}")
    
    try:
        container = get_cosmos_client()
        
        # Query for stories older than 4 hours
        query = f"""
        SELECT c.id, c.title, c.last_updated, c.status, ARRAY_LENGTH(c.source_articles) as source_count
        FROM c 
        WHERE c.last_updated < '{cutoff_iso}'
        ORDER BY c.last_updated DESC
        """
        
        logger.info("Querying for old stories...")
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        total_stories = len(items)
        logger.info(f"Found {total_stories} stories older than 4 hours")
        
        if total_stories == 0:
            logger.info("No old stories to delete")
            return
        
        # Show sample of what will be deleted
        logger.info("Sample of stories to be deleted:")
        for i, item in enumerate(items[:5]):
            logger.info(f"  {i+1}. [{item['status']}] {item['title'][:60]}... ({item['source_count']} sources, {item['last_updated']})")
        
        if total_stories > 5:
            logger.info(f"  ... and {total_stories - 5} more stories")
        
        # Auto-confirm deletion for automation
        confirm = "yes"
        
        # Delete stories in batches
        deleted_count = 0
        batch_size = 100
        
        for i in range(0, total_stories, batch_size):
            batch = items[i:i + batch_size]
            
            for item in batch:
                try:
                    container.delete_item(item=item['id'], partition_key=item['id'])
                    deleted_count += 1
                    
                    if deleted_count % 50 == 0:
                        logger.info(f"Deleted {deleted_count}/{total_stories} stories...")
                        
                except CosmosResourceNotFoundError:
                    logger.warning(f"Story {item['id']} not found (may have been deleted already)")
                except Exception as e:
                    logger.error(f"Error deleting story {item['id']}: {e}")
        
        logger.info(f"✅ Successfully deleted {deleted_count} stories")
        
        # Query remaining stories to verify
        remaining_query = "SELECT VALUE COUNT(1) FROM c"
        remaining_count = list(container.query_items(query=remaining_query, enable_cross_partition_query=True))[0]
        logger.info(f"Remaining stories in database: {remaining_count}")
        
    except Exception as e:
        logger.error(f"Error during deletion: {e}")
        raise

if __name__ == "__main__":
    try:
        delete_old_stories()
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)
