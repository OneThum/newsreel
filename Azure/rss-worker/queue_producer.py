"""
Queue Producer - Lightweight Azure Function that pushes feed URLs to Service Bus Queue

This replaces the heavy RSS fetching logic in the timer trigger with a simple
queue producer. The actual feed fetching is done by the Container App worker.

Architecture:
    Timer (every 10s) -> Queue Producer -> Service Bus Queue -> Container App Worker
                                                                        |
                                                                    Cosmos DB
"""

import json
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage
from azure.cosmos import CosmosClient

from config import get_all_feeds, get_feed_by_category, FeedConfig, config

logger = logging.getLogger('queue-producer')


class FeedScheduler:
    """
    Smart feed scheduler that distributes feed polling evenly across time.
    Uses round-robin across categories for diverse content flow.
    """
    
    def __init__(self, cosmos_client: CosmosClient):
        self.cosmos_client = cosmos_client
        self.database = cosmos_client.get_database_client(config.COSMOS_DATABASE_NAME)
        self.poll_states_container = self.database.get_container_client('feed_poll_states')
        
        # Category rotation index
        self.category_index = 0
    
    def get_poll_states(self) -> Dict[str, datetime]:
        """Get last poll time for all feeds"""
        try:
            items = list(self.poll_states_container.query_items(
                query='SELECT * FROM c',
                enable_cross_partition_query=True
            ))
            
            return {
                item['feed_name']: datetime.fromisoformat(item['last_poll'])
                for item in items
                if item.get('last_poll')
            }
        except Exception as e:
            logger.warning(f'Could not get poll states: {e}')
            return {}
    
    def update_poll_state(self, feed_name: str, poll_time: datetime):
        """Update last poll time for a feed"""
        try:
            doc_id = f'feed_poll_state_{feed_name.replace(" ", "_").lower()}'
            self.poll_states_container.upsert_item({
                'id': doc_id,
                'feed_name': feed_name,
                'last_poll': poll_time.isoformat()
            })
        except Exception as e:
            logger.warning(f'Could not update poll state for {feed_name}: {e}')
    
    def get_feeds_to_poll(self) -> List[FeedConfig]:
        """
        Select feeds that are due for polling using round-robin across categories.
        This ensures diverse content flow rather than polling all world news first.
        """
        now = datetime.now(timezone.utc)
        poll_states = self.get_poll_states()
        feeds_by_category = get_feed_by_category()
        
        # Filter to feeds that need polling (past cooldown period)
        cooldown = timedelta(seconds=config.FEED_POLL_INTERVAL_SECONDS)
        
        ready_by_category = {}
        for category, feeds in feeds_by_category.items():
            ready_feeds = []
            for feed in feeds:
                last_poll = poll_states.get(feed.name)
                if not last_poll or (now - last_poll) >= cooldown:
                    ready_feeds.append(feed)
            if ready_feeds:
                ready_by_category[category] = ready_feeds
        
        if not ready_by_category:
            return []
        
        # Round-robin selection across categories
        selected = []
        categories = list(ready_by_category.keys())
        
        while len(selected) < config.FEEDS_PER_BATCH and ready_by_category:
            # Get next category
            category = categories[self.category_index % len(categories)]
            
            if category in ready_by_category and ready_by_category[category]:
                feed = ready_by_category[category].pop(0)
                selected.append(feed)
                
                # Remove empty category
                if not ready_by_category[category]:
                    del ready_by_category[category]
                    categories = list(ready_by_category.keys())
            
            self.category_index = (self.category_index + 1) % max(len(categories), 1)
        
        return selected


async def push_feeds_to_queue(feeds: List[FeedConfig], servicebus_client: ServiceBusClient):
    """Push feed configurations to Service Bus queue"""
    if not feeds:
        logger.info('No feeds to push')
        return 0
    
    async with servicebus_client:
        sender = servicebus_client.get_queue_sender(queue_name=config.SERVICE_BUS_QUEUE_NAME)
        
        async with sender:
            messages = []
            for feed in feeds:
                message_body = json.dumps({
                    'id': feed.id,
                    'name': feed.name,
                    'url': feed.url,
                    'source_id': feed.source_id,
                    'category': feed.category,
                    'tier': feed.tier,
                    'queued_at': datetime.now(timezone.utc).isoformat()
                })
                messages.append(ServiceBusMessage(message_body))
            
            await sender.send_messages(messages)
            logger.info(f'Pushed {len(messages)} feeds to queue')
            
            return len(messages)


async def main():
    """
    Main function - can be called from Azure Functions timer trigger
    or run standalone for testing.
    """
    logger.info('Feed queue producer starting...')
    
    # Initialize clients
    cosmos_client = CosmosClient.from_connection_string(config.COSMOS_CONNECTION_STRING)
    servicebus_client = ServiceBusClient.from_connection_string(config.SERVICE_BUS_CONNECTION_STRING)
    
    # Get feeds to poll
    scheduler = FeedScheduler(cosmos_client)
    feeds = scheduler.get_feeds_to_poll()
    
    if feeds:
        # Push to queue
        count = await push_feeds_to_queue(feeds, servicebus_client)
        
        # Update poll states
        now = datetime.now(timezone.utc)
        for feed in feeds:
            scheduler.update_poll_state(feed.name, now)
        
        logger.info(f'Queued {count} feeds for processing')
        
        # Log category distribution
        categories = {}
        for feed in feeds:
            categories[feed.category] = categories.get(feed.category, 0) + 1
        logger.info(f'Category distribution: {categories}')
    else:
        logger.info('No feeds need polling this cycle')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

