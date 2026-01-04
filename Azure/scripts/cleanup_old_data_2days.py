#!/usr/bin/env python3
"""
Clean up database: Delete all stories and articles older than 2 days
This improves clustering performance and keeps the database lean.

Usage:
    export COSMOS_CONNECTION_STRING='...'
    python cleanup_old_data_2days.py [--dry-run]
"""

import os
import sys
import time
import argparse
from datetime import datetime, timezone, timedelta
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_cosmos_connection():
    """Get Cosmos DB connection"""
    connection_string = os.getenv('COSMOS_CONNECTION_STRING')
    if not connection_string:
        raise ValueError('COSMOS_CONNECTION_STRING environment variable not set')
    
    database_name = os.getenv('COSMOS_DATABASE_NAME', 'newsreel-db')
    
    client = CosmosClient.from_connection_string(connection_string)
    database = client.get_database_client(database_name)
    
    return database


def delete_old_stories(database, cutoff_iso: str, dry_run: bool = False) -> int:
    """Delete old stories from story_clusters container
    
    IMPORTANT: Partition key for story_clusters is 'category', not 'id'
    """
    container = database.get_container_client('story_clusters')
    
    # Query for old stories - include category for partition key
    query = f"""
    SELECT c.id, c.category, c.title, c.first_seen, c.last_updated
    FROM c 
    WHERE c.first_seen < '{cutoff_iso}'
    """
    
    logger.info('Querying for old stories (first_seen < 2 days ago)...')
    items = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    
    total = len(items)
    logger.info(f'Found {total:,} stories older than 2 days')
    
    if total == 0:
        return 0
    
    # Show sample
    logger.info('Sample of stories to delete:')
    for item in items[:5]:
        title = item.get('title', 'No title')[:50]
        first_seen = item.get('first_seen', 'Unknown')
        logger.info(f'  - [{item.get("category")}] {title}... (first_seen: {first_seen})')
    
    if total > 5:
        logger.info(f'  ... and {total - 5} more')
    
    if dry_run:
        logger.info('[DRY RUN] Would delete these stories')
        return 0
    
    # Delete stories - use category as partition key
    deleted = 0
    errors = 0
    
    for i, item in enumerate(items):
        try:
            # CRITICAL: Partition key is 'category', not 'id'
            container.delete_item(
                item=item['id'],
                partition_key=item['category']
            )
            deleted += 1
            
            if deleted % 100 == 0:
                logger.info(f'Deleted {deleted:,}/{total:,} stories...')
                time.sleep(0.05)  # Small delay to avoid throttling
                
        except CosmosResourceNotFoundError:
            # Already deleted
            pass
        except Exception as e:
            errors += 1
            if errors < 10:  # Only log first few errors
                logger.error(f'Error deleting story {item["id"]}: {e}')
    
    logger.info(f'✅ Deleted {deleted:,} stories ({errors} errors)')
    return deleted


def delete_old_articles(database, cutoff_iso: str, dry_run: bool = False) -> int:
    """Delete old articles from raw_articles container
    
    IMPORTANT: Partition key for raw_articles is 'published_date' (YYYY-MM-DD format)
    """
    container = database.get_container_client('raw_articles')
    
    # Query for old articles - include all potential partition keys
    query = f"""
    SELECT c.id, c.source, c.title, c.fetched_at, c.published_at, c.published_date, c.category
    FROM c 
    WHERE c.fetched_at < '{cutoff_iso}'
    """
    
    logger.info('Querying for old articles (fetched_at < 2 days ago)...')
    items = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    
    total = len(items)
    logger.info(f'Found {total:,} articles older than 2 days')
    
    if total == 0:
        return 0
    
    # Show sample
    logger.info('Sample of articles to delete:')
    for item in items[:5]:
        title = item.get('title', 'No title')[:50]
        fetched = item.get('fetched_at', 'Unknown')
        logger.info(f'  - [{item.get("source")}] {title}... (fetched: {fetched})')
    
    if total > 5:
        logger.info(f'  ... and {total - 5} more')
    
    if dry_run:
        logger.info('[DRY RUN] Would delete these articles')
        return 0
    
    # Delete articles - try multiple partition key strategies
    deleted = 0
    errors = 0
    
    for i, item in enumerate(items):
        item_id = item['id']
        
        # Try different partition key strategies
        partition_keys_to_try = []
        
        # Strategy 1: published_date (YYYY-MM-DD)
        if item.get('published_date'):
            partition_keys_to_try.append(item['published_date'])
        
        # Strategy 2: category
        if item.get('category'):
            partition_keys_to_try.append(item['category'])
        
        # Strategy 3: Extract date from fetched_at
        fetched = item.get('fetched_at', '')
        if fetched and len(fetched) >= 10:
            partition_keys_to_try.append(fetched[:10])
        
        success = False
        for pk in partition_keys_to_try:
            try:
                container.delete_item(item=item_id, partition_key=pk)
                deleted += 1
                success = True
                break
            except CosmosResourceNotFoundError:
                # Try next partition key
                continue
            except Exception as e:
                # Try next partition key
                continue
        
        if not success:
            errors += 1
            if errors < 5:
                logger.warning(f'Could not delete article {item_id} with any partition key')
        
        if deleted % 500 == 0 and deleted > 0:
            logger.info(f'Deleted {deleted:,}/{total:,} articles...')
            time.sleep(0.05)  # Small delay to avoid throttling
    
    logger.info(f'✅ Deleted {deleted:,} articles ({errors} errors)')
    return deleted


def get_database_stats(database):
    """Get current database statistics"""
    stories_container = database.get_container_client('story_clusters')
    articles_container = database.get_container_client('raw_articles')
    
    # Count stories
    story_count = list(stories_container.query_items(
        query='SELECT VALUE COUNT(1) FROM c',
        enable_cross_partition_query=True
    ))[0]
    
    # Count articles
    article_count = list(articles_container.query_items(
        query='SELECT VALUE COUNT(1) FROM c',
        enable_cross_partition_query=True
    ))[0]
    
    return story_count, article_count


def main():
    parser = argparse.ArgumentParser(description='Clean up old stories and articles from database')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without actually deleting')
    parser.add_argument('--stories-only', action='store_true', help='Only delete stories, not articles')
    parser.add_argument('--articles-only', action='store_true', help='Only delete articles, not stories')
    args = parser.parse_args()
    
    # Calculate cutoff time (2 days ago)
    cutoff_time = datetime.now(timezone.utc) - timedelta(days=2)
    cutoff_iso = cutoff_time.isoformat()
    
    logger.info('=' * 60)
    logger.info('DATABASE CLEANUP - Delete data older than 2 days')
    logger.info('=' * 60)
    logger.info(f'Cutoff time: {cutoff_iso}')
    if args.dry_run:
        logger.info('MODE: DRY RUN (no changes will be made)')
    logger.info('')
    
    try:
        database = get_cosmos_connection()
        
        # Show current stats
        logger.info('Current database statistics:')
        story_count, article_count = get_database_stats(database)
        logger.info(f'  Stories: {story_count:,}')
        logger.info(f'  Articles: {article_count:,}')
        logger.info('')
        
        total_deleted_stories = 0
        total_deleted_articles = 0
        
        # Delete old stories
        if not args.articles_only:
            logger.info('-' * 40)
            logger.info('STEP 1: Cleaning up old stories')
            logger.info('-' * 40)
            total_deleted_stories = delete_old_stories(database, cutoff_iso, args.dry_run)
            logger.info('')
        
        # Delete old articles
        if not args.stories_only:
            logger.info('-' * 40)
            logger.info('STEP 2: Cleaning up old articles')
            logger.info('-' * 40)
            total_deleted_articles = delete_old_articles(database, cutoff_iso, args.dry_run)
            logger.info('')
        
        # Show final stats
        if not args.dry_run:
            logger.info('-' * 40)
            logger.info('FINAL DATABASE STATISTICS')
            logger.info('-' * 40)
            story_count, article_count = get_database_stats(database)
            logger.info(f'  Stories: {story_count:,}')
            logger.info(f'  Articles: {article_count:,}')
        
        logger.info('')
        logger.info('=' * 60)
        logger.info('CLEANUP COMPLETE')
        logger.info(f'  Deleted {total_deleted_stories:,} stories')
        logger.info(f'  Deleted {total_deleted_articles:,} articles')
        logger.info('=' * 60)
        
    except Exception as e:
        logger.error(f'Script failed: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

