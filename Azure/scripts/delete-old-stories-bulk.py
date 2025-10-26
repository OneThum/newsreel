#!/usr/bin/env python3
"""
Efficiently delete all stories older than 4 hours using Cosmos DB bulk operations
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

def delete_old_stories_bulk():
    """Delete all stories older than 4 hours using bulk operations"""
    
    # Calculate cutoff time (4 hours ago)
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=4)
    cutoff_iso = cutoff_time.isoformat(timespec='seconds') + 'Z'
    
    logger.info(f"Deleting stories older than {cutoff_iso}")
    
    try:
        container = get_cosmos_client()
        
        # First, get count of stories to delete
        count_query = f"SELECT VALUE COUNT(1) FROM c WHERE c.last_updated < '{cutoff_iso}'"
        total_count = list(container.query_items(query=count_query, enable_cross_partition_query=True))[0]
        
        logger.info(f"Found {total_count:,} stories older than 4 hours")
        
        if total_count == 0:
            logger.info("No old stories to delete")
            return
        
        # Delete in batches using bulk operations
        batch_size = 1000  # Larger batches for efficiency
        deleted_count = 0
        
        while deleted_count < total_count:
            # Get batch of IDs to delete
            batch_query = f"""
            SELECT c.id FROM c 
            WHERE c.last_updated < '{cutoff_iso}'
            ORDER BY c.last_updated DESC
            OFFSET {deleted_count} LIMIT {batch_size}
            """
            
            logger.info(f"Fetching batch {deleted_count//batch_size + 1}...")
            items = list(container.query_items(query=batch_query, enable_cross_partition_query=True))
            
            if not items:
                break
            
            # Delete batch
            batch_deleted = 0
            for item in items:
                try:
                    container.delete_item(item=item['id'], partition_key=item['id'])
                    batch_deleted += 1
                except CosmosResourceNotFoundError:
                    pass  # Already deleted
                except Exception as e:
                    logger.error(f"Error deleting story {item['id']}: {e}")
            
            deleted_count += batch_deleted
            logger.info(f"Deleted {deleted_count:,}/{total_count:,} stories ({batch_deleted} in this batch)")
            
            # Small delay to avoid overwhelming the database
            import time
            time.sleep(0.1)
        
        logger.info(f"✅ Successfully deleted {deleted_count:,} stories")
        
        # Verify remaining count
        remaining_query = "SELECT VALUE COUNT(1) FROM c"
        remaining_count = list(container.query_items(query=remaining_query, enable_cross_partition_query=True))[0]
        logger.info(f"Remaining stories in database: {remaining_count:,}")
        
    except Exception as e:
        logger.error(f"Error during deletion: {e}")
        raise

if __name__ == "__main__":
    try:
        delete_old_stories_bulk()
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)

