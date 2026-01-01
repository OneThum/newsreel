"""
Queue Producer for Azure Functions

This module provides the functionality to push feed URLs to Service Bus queue
instead of doing direct RSS fetching in the Azure Function.

The Container App worker handles the actual feed fetching for reliability.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from azure.servicebus import ServiceBusClient, ServiceBusMessage
from .config import config
from .rss_feeds import get_all_feeds, get_initial_feeds
from .models import RSSFeedConfig

logger = logging.getLogger(__name__)


class FeedQueueProducer:
    """
    Produces feed polling jobs to Service Bus queue.
    
    Features:
    - Round-robin distribution across categories
    - Cooldown tracking to prevent over-polling
    - Batch message sending for efficiency
    """
    
    def __init__(self, cosmos_client):
        """
        Args:
            cosmos_client: CosmosDBClient instance for poll state tracking
        """
        self.cosmos_client = cosmos_client
        self.servicebus_client: Optional[ServiceBusClient] = None
        self.category_index = 0
        
        # Get Service Bus connection from config
        self.connection_string = config.SERVICE_BUS_CONNECTION_STRING if hasattr(config, 'SERVICE_BUS_CONNECTION_STRING') else ''
        self.queue_name = config.SERVICE_BUS_QUEUE_NAME if hasattr(config, 'SERVICE_BUS_QUEUE_NAME') else 'rss-feeds'
    
    def connect(self):
        """Initialize Service Bus connection"""
        if not self.connection_string:
            raise ValueError('SERVICE_BUS_CONNECTION_STRING not configured')
        
        self.servicebus_client = ServiceBusClient.from_connection_string(
            self.connection_string
        )
        logger.info('Connected to Service Bus')
    
    async def get_feeds_to_poll(
        self,
        use_all_feeds: bool = False,
        max_feeds: int = 10,
        cooldown_seconds: int = 180
    ) -> List[RSSFeedConfig]:
        """
        Get feeds that are due for polling using round-robin across categories.
        
        Args:
            use_all_feeds: If True, use all feeds; otherwise use initial MVP feeds
            max_feeds: Maximum feeds to return per batch
            cooldown_seconds: Minimum time between polling same feed
            
        Returns:
            List of feed configs to poll
        """
        # Get all feed configs
        all_feeds = get_all_feeds() if use_all_feeds else get_initial_feeds()
        
        # Get current poll states
        poll_states = await self.cosmos_client.get_feed_poll_states()
        now = datetime.now(timezone.utc)
        cooldown = timedelta(seconds=cooldown_seconds)
        
        # Group feeds by category
        ready_by_category: Dict[str, List[RSSFeedConfig]] = {}
        
        for feed in all_feeds:
            # Check if feed is past cooldown
            last_poll = poll_states.get(feed.name, {}).get('last_poll')
            
            if not last_poll or (now - last_poll) >= cooldown:
                category = feed.category
                if category not in ready_by_category:
                    ready_by_category[category] = []
                ready_by_category[category].append(feed)
        
        if not ready_by_category:
            return []
        
        # Round-robin selection across categories
        selected: List[RSSFeedConfig] = []
        categories = list(ready_by_category.keys())
        
        while len(selected) < max_feeds and ready_by_category:
            # Get next category in rotation
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
    
    def push_feeds_to_queue(self, feeds: List[RSSFeedConfig]) -> int:
        """
        Push feed configurations to Service Bus queue.
        
        Args:
            feeds: List of feed configs to queue
            
        Returns:
            Number of messages sent
        """
        if not feeds:
            return 0
        
        if not self.servicebus_client:
            self.connect()
        
        with self.servicebus_client:
            sender = self.servicebus_client.get_queue_sender(queue_name=self.queue_name)
            
            with sender:
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
                
                # Send as batch for efficiency
                sender.send_messages(messages)
                
                logger.info(f'Pushed {len(messages)} feeds to queue')
                return len(messages)
    
    async def push_and_track(
        self,
        use_all_feeds: bool = False,
        max_feeds: int = 10,
        cooldown_seconds: int = 180
    ) -> Dict[str, Any]:
        """
        Main method: Get feeds to poll, push to queue, update tracking.
        
        Returns:
            Dict with stats about what was queued
        """
        # Get feeds ready for polling
        feeds = await self.get_feeds_to_poll(
            use_all_feeds=use_all_feeds,
            max_feeds=max_feeds,
            cooldown_seconds=cooldown_seconds
        )
        
        if not feeds:
            return {
                'feeds_queued': 0,
                'message': 'No feeds ready for polling'
            }
        
        # Push to queue
        count = self.push_feeds_to_queue(feeds)
        
        # Update poll states
        now = datetime.now(timezone.utc)
        for feed in feeds:
            await self.cosmos_client.update_feed_poll_state(
                feed_name=feed.name,
                last_poll=now,
                articles_found=0  # Will be updated by worker
            )
        
        # Calculate category distribution
        categories = {}
        feed_names = []
        for feed in feeds:
            categories[feed.category] = categories.get(feed.category, 0) + 1
            feed_names.append(f'{feed.name} ({feed.category})')
        
        return {
            'feeds_queued': count,
            'categories': categories,
            'feeds': feed_names
        }


# Module-level helper for use in function_app.py
_producer: Optional[FeedQueueProducer] = None


def get_queue_producer(cosmos_client) -> FeedQueueProducer:
    """Get or create queue producer instance"""
    global _producer
    if _producer is None:
        _producer = FeedQueueProducer(cosmos_client)
    return _producer

