"""Azure Cosmos DB client wrapper"""
import logging
from typing import List, Optional, Dict, Any
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.cosmos.container import ContainerProxy
from azure.cosmos.database import DatabaseProxy
from azure.core import MatchConditions
from .config import config
from .models import RawArticle, StoryCluster, UserProfile, UserInteraction

logger = logging.getLogger(__name__)


class CosmosDBClient:
    """Wrapper for Azure Cosmos DB operations"""
    
    def __init__(self):
        self.client: Optional[CosmosClient] = None
        self.database: Optional[DatabaseProxy] = None
        self._containers: Dict[str, ContainerProxy] = {}
        
    def connect(self):
        """Initialize Cosmos DB connection"""
        try:
            if not config.COSMOS_CONNECTION_STRING:
                raise ValueError("COSMOS_CONNECTION_STRING not configured")
                
            self.client = CosmosClient.from_connection_string(
                config.COSMOS_CONNECTION_STRING
            )
            self.database = self.client.get_database_client(config.COSMOS_DATABASE_NAME)
            logger.info(f"Connected to Cosmos DB: {config.COSMOS_DATABASE_NAME}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Cosmos DB: {e}")
            raise
    
    def _get_container(self, container_name: str) -> ContainerProxy:
        """Get or create container reference"""
        if container_name not in self._containers:
            if not self.database:
                self.connect()
            self._containers[container_name] = self.database.get_container_client(container_name)
        return self._containers[container_name]
    
    # Raw Articles Operations
    
    async def upsert_raw_article(self, article: RawArticle) -> Dict[str, Any]:
        """Create or update raw article (upsert) - implements update-in-place
        
        If article exists (same source + URL): Updates with latest title, description, content
        If article is new: Creates new record
        
        This prevents duplicate entries when a source updates the same article multiple times.
        
        Benefits:
        - 80% storage reduction (no duplicate updates)
        - Each source represented once per story
        - Faster queries (fewer records)
        - No API deduplication needed
        """
        try:
            container = self._get_container(config.CONTAINER_RAW_ARTICLES)
            
            # Upsert: Creates if new, updates if exists
            result = container.upsert_item(body=article.model_dump(mode='json'))
            
            logger.info(f"Upserted raw article: {article.id}")
            return result
        except Exception as e:
            logger.error(f"Failed to upsert raw article {article.id}: {e}")
            raise
    
    async def create_raw_article(self, article: RawArticle) -> Dict[str, Any]:
        """DEPRECATED: Use upsert_raw_article instead
        
        This method is kept for backwards compatibility but will be removed.
        """
        return await self.upsert_raw_article(article)
    
    async def get_raw_article(self, article_id: str, partition_key: str) -> Optional[Dict[str, Any]]:
        """Get raw article by ID"""
        try:
            container = self._get_container(config.CONTAINER_RAW_ARTICLES)
            item = container.read_item(item=article_id, partition_key=partition_key)
            return item
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Failed to get raw article {article_id}: {e}")
            raise
    
    async def query_unprocessed_articles(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Query unprocessed articles
        
        CRITICAL: NO ORDER BY to avoid Cosmos DB field omission bug!
        We sort in Python instead.
        """
        try:
            container = self._get_container(config.CONTAINER_RAW_ARTICLES)
            # Query without ORDER BY, sort in Python
            query = "SELECT * FROM c WHERE c.processed = false"
            items = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            # Sort in Python by published_at (descending)
            sorted_items = sorted(items, key=lambda x: x.get('published_at', ''), reverse=True)
            
            # Apply limit
            return sorted_items[:limit]
        except Exception as e:
            logger.error(f"Failed to query unprocessed articles: {e}")
            raise
    
    async def update_article_processed(self, article_id: str, partition_key: str, story_id: str):
        """Mark article as processed"""
        try:
            container = self._get_container(config.CONTAINER_RAW_ARTICLES)
            article = container.read_item(item=article_id, partition_key=partition_key)
            article['processed'] = True
            article['story_id'] = story_id
            container.replace_item(item=article_id, body=article)
            logger.info(f"Marked article as processed: {article_id}")
        except Exception as e:
            logger.error(f"Failed to update article {article_id}: {e}")
            raise
    
    async def update_article_embedding(self, article_id: str, partition_key: str, embedding: list):
        """Update article with semantic embedding
        
        Args:
            article_id: Article ID
            partition_key: Partition key (published_date)
            embedding: List of floats (1536 dimensions for text-embedding-3-small)
        """
        try:
            container = self._get_container(config.CONTAINER_RAW_ARTICLES)
            article = container.read_item(item=article_id, partition_key=partition_key)
            article['embedding'] = embedding
            container.replace_item(item=article_id, body=article)
            logger.debug(f"Updated embedding for article: {article_id}")
        except Exception as e:
            logger.error(f"Failed to update embedding for {article_id}: {e}")
            # Don't raise - embedding update is not critical for clustering to proceed
    
    # Story Cluster Operations
    
    async def create_story_cluster(self, story: StoryCluster) -> Dict[str, Any]:
        """Create a new story cluster"""
        try:
            container = self._get_container(config.CONTAINER_STORY_CLUSTERS)
            result = container.create_item(body=story.model_dump(mode='json'))
            logger.info(f"Created story cluster: {story.id}")
            return result
        except Exception as e:
            logger.error(f"Failed to create story cluster {story.id}: {e}")
            raise
    
    async def get_story_cluster(self, story_id: str, partition_key: str) -> Optional[Dict[str, Any]]:
        """Get story cluster by ID"""
        try:
            container = self._get_container(config.CONTAINER_STORY_CLUSTERS)
            item = container.read_item(item=story_id, partition_key=partition_key)
            return item
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Failed to get story cluster {story_id}: {e}")
            raise
    
    async def update_story_cluster(self, story_id: str, partition_key: str, updates: Dict[str, Any]):
        """Update story cluster with retry logic for concurrent updates"""
        max_retries = 5
        retry_delay = 0.1  # Start with 100ms
        
        for attempt in range(max_retries):
            try:
                container = self._get_container(config.CONTAINER_STORY_CLUSTERS)
                # Read current version with ETag
                story = container.read_item(item=story_id, partition_key=partition_key)
                
                # Apply updates
                story.update(updates)
                
                # Replace with ETag check (optimistic concurrency)
                result = container.replace_item(
                    item=story_id,
                    body=story,
                    etag=story.get('_etag'),
                    match_condition=MatchConditions.IfNotModified
                )
                logger.info(f"Updated story cluster: {story_id}")
                return result
                
            except exceptions.CosmosHttpResponseError as e:
                if e.status_code == 409 or e.status_code == 412:  # Conflict or Precondition Failed
                    if attempt < max_retries - 1:
                        # Retry with exponential backoff
                        import time, random
                        sleep_time = retry_delay * (2 ** attempt) + random.uniform(0, 0.1)
                        logger.warning(f"Conflict updating {story_id}, retry {attempt + 1}/{max_retries} after {sleep_time:.2f}s")
                        time.sleep(sleep_time)
                        continue
                    else:
                        logger.error(f"Failed to update {story_id} after {max_retries} retries (concurrent updates)")
                        raise
                else:
                    # Other error, don't retry
                    logger.error(f"Failed to update story cluster {story_id}: {e}")
                    raise
            except Exception as e:
                logger.error(f"Failed to update story cluster {story_id}: {e}")
                raise
    
    async def query_stories_by_fingerprint(self, fingerprint: str) -> List[Dict[str, Any]]:
        """Find stories by event fingerprint"""
        try:
            container = self._get_container(config.CONTAINER_STORY_CLUSTERS)
            query = f"SELECT * FROM c WHERE c.event_fingerprint = @fingerprint"
            parameters = [{"name": "@fingerprint", "value": fingerprint}]
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            return items
        except Exception as e:
            logger.error(f"Failed to query stories by fingerprint {fingerprint}: {e}")
            raise
    
    async def query_recent_stories(
        self, 
        category: Optional[str] = None,
        limit: int = 20,
        include_monitoring: bool = True  # Include MONITORING for semantic clustering
    ) -> List[Dict[str, Any]]:
        """Query recent stories, optionally filtered by category
        
        CRITICAL: NO ORDER BY to avoid Cosmos DB field omission bug!
        We sort in Python instead.
        
        Args:
            category: Filter by category (optional)
            limit: Maximum number of stories to return
            include_monitoring: Whether to include MONITORING status stories (for clustering)
        """
        try:
            container = self._get_container(config.CONTAINER_STORY_CLUSTERS)
            
            # For semantic clustering, we want ALL recent stories including MONITORING
            # This ensures new articles can cluster with single-source stories
            if category:
                if include_monitoring:
                    query = "SELECT * FROM c WHERE c.category = @category"
                else:
                    query = "SELECT * FROM c WHERE c.category = @category AND c.status != 'MONITORING'"
                parameters = [{"name": "@category", "value": category}]
                items = list(container.query_items(
                    query=query,
                    parameters=parameters
                ))
            else:
                if include_monitoring:
                    query = "SELECT * FROM c"
                else:
                    query = "SELECT * FROM c WHERE c.status != 'MONITORING'"
                items = list(container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
            
            # Sort in Python by last_updated (descending)
            sorted_items = sorted(items, key=lambda x: x.get('last_updated', ''), reverse=True)
            
            # Apply limit
            return sorted_items[:limit]
        except Exception as e:
            logger.error(f"Failed to query recent stories: {e}")
            raise
    
    async def query_breaking_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Query breaking news stories
        
        CRITICAL: NO ORDER BY to avoid Cosmos DB field omission bug!
        We sort in Python instead.
        """
        try:
            container = self._get_container(config.CONTAINER_STORY_CLUSTERS)
            # Query without ORDER BY, sort in Python
            query = "SELECT * FROM c WHERE c.status = 'BREAKING'"
            items = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            # Sort in Python by breaking_detected_at (descending)
            sorted_items = sorted(items, key=lambda x: x.get('breaking_detected_at', x.get('last_updated', '')), reverse=True)
            
            # Apply limit
            return sorted_items[:limit]
        except Exception as e:
            logger.error(f"Failed to query breaking news: {e}")
            raise
    
    async def query_stories_by_status(self, status: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Query stories by status (for status transition monitoring)"""
        try:
            container = self._get_container(config.CONTAINER_STORY_CLUSTERS)
            # Query stories with specific status
            query = "SELECT * FROM c WHERE c.status = @status"
            items = list(container.query_items(
                query=query,
                parameters=[{"name": "@status", "value": status}],
                enable_cross_partition_query=True
            ))
            
            # No longer need to filter feed_poll_state documents since they're in a separate container
            stories = items
            
            # Sort in Python by first_seen (newest first) for age-based transitions
            stories_sorted = sorted(stories, key=lambda x: x.get('first_seen', ''), reverse=True)
            return stories_sorted[:limit]
        except Exception as e:
            logger.error(f"Failed to query stories by status {status}: {e}")
            return []
    
    # User Profile Operations
    
    async def create_user_profile(self, user: UserProfile) -> Dict[str, Any]:
        """Create a new user profile"""
        try:
            container = self._get_container(config.CONTAINER_USER_PROFILES)
            result = container.create_item(body=user.model_dump(mode='json'))
            logger.info(f"Created user profile: {user.id}")
            return result
        except Exception as e:
            logger.error(f"Failed to create user profile {user.id}: {e}")
            raise
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by ID"""
        try:
            container = self._get_container(config.CONTAINER_USER_PROFILES)
            item = container.read_item(item=user_id, partition_key=user_id)
            return item
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Failed to get user profile {user_id}: {e}")
            raise
    
    async def update_user_profile(self, user_id: str, updates: Dict[str, Any]):
        """Update user profile"""
        try:
            container = self._get_container(config.CONTAINER_USER_PROFILES)
            user = container.read_item(item=user_id, partition_key=user_id)
            user.update(updates)
            result = container.replace_item(item=user_id, body=user)
            logger.info(f"Updated user profile: {user_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to update user profile {user_id}: {e}")
            raise
    
    # User Interaction Operations
    
    async def create_interaction(self, interaction: UserInteraction) -> Dict[str, Any]:
        """Create a new user interaction"""
        try:
            container = self._get_container(config.CONTAINER_USER_INTERACTIONS)
            result = container.create_item(body=interaction.model_dump(mode='json'))
            logger.debug(f"Created interaction: {interaction.id}")
            return result
        except Exception as e:
            logger.error(f"Failed to create interaction {interaction.id}: {e}")
            raise
    
    async def query_user_interactions(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query user interactions"""
        try:
            container = self._get_container(config.CONTAINER_USER_INTERACTIONS)
            query = "SELECT * FROM c WHERE c.user_id = @user_id ORDER BY c.timestamp DESC"
            parameters = [{"name": "@user_id", "value": user_id}]
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                max_item_count=limit
            ))
            return items
        except Exception as e:
            logger.error(f"Failed to query user interactions for {user_id}: {e}")
            raise
    
    # Feed Poll State Operations (for staggered polling)
    
    async def get_feed_poll_states(self) -> Dict[str, Dict[str, Any]]:
        """Get poll states for all feeds
        
        Returns dict of feed_name -> {last_poll: datetime, articles_found: int}
        """
        try:
            from datetime import datetime, timezone
            # Use dedicated feed_poll_states container instead of story_clusters
            container = self._get_container('feed_poll_states')
            
            # Query all documents (no need to filter by doc_type now)
            query = "SELECT * FROM c"
            items = list(container.query_items(query=query, enable_cross_partition_query=True))
            
            # Convert to dict format
            result = {}
            for item in items:
                feed_name = item.get('feed_name')
                if feed_name:
                    last_poll_str = item.get('last_poll')
                    last_poll = datetime.fromisoformat(last_poll_str) if last_poll_str else None
                    result[feed_name] = {
                        'last_poll': last_poll,
                        'articles_found': item.get('articles_found', 0)
                    }
            
            return result
        except Exception as e:
            logger.warning(f"Failed to get feed poll states (this is OK on first run): {e}")
            return {}
    
    async def update_feed_poll_state(
        self,
        feed_name: str,
        last_poll: 'datetime',
        articles_found: int
    ) -> None:
        """Update poll state for a feed"""
        try:
            # Use dedicated feed_poll_states container instead of story_clusters
            container = self._get_container('feed_poll_states')
            
            doc_id = f"feed_poll_state_{feed_name.replace(' ', '_').lower()}"
            
            document = {
                'id': doc_id,
                'feed_name': feed_name,
                'last_poll': last_poll.isoformat(),
                'articles_found': articles_found
            }
            
            # Upsert (create or update)
            container.upsert_item(document)
            
        except Exception as e:
            logger.warning(f"Failed to update feed poll state for {feed_name}: {e}")
            # Don't raise - poll state tracking is not critical
    
    # ============================================================================
    # BATCH TRACKING OPERATIONS
    # ============================================================================
    
    async def create_batch_tracking(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a batch tracking record
        
        Args:
            batch_data: Dictionary containing:
                - batch_id: Anthropic batch ID
                - status: processing status
                - story_ids: list of story IDs in this batch
                - created_at: timestamp
                - request_count: number of requests
        """
        try:
            container = self._get_container(config.CONTAINER_BATCH_TRACKING)
            result = container.create_item(body=batch_data)
            logger.info(f"Created batch tracking record: {batch_data['batch_id']}")
            return result
        except Exception as e:
            logger.error(f"Failed to create batch tracking: {e}")
            raise
    
    async def get_batch_tracking(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get batch tracking record by batch ID"""
        try:
            container = self._get_container(config.CONTAINER_BATCH_TRACKING)
            # Batch tracking uses batch_id as both id and partition key
            item = container.read_item(item=batch_id, partition_key=batch_id)
            return item
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Failed to get batch tracking {batch_id}: {e}")
            raise
    
    async def update_batch_tracking(self, batch_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update batch tracking record"""
        try:
            container = self._get_container(config.CONTAINER_BATCH_TRACKING)
            
            # Get existing record
            existing = await self.get_batch_tracking(batch_id)
            if not existing:
                raise ValueError(f"Batch tracking record not found: {batch_id}")
            
            # Apply updates
            existing.update(updates)
            
            # Upsert
            result = container.upsert_item(body=existing)
            logger.info(f"Updated batch tracking: {batch_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to update batch tracking {batch_id}: {e}")
            raise
    
    async def query_pending_batches(self) -> List[Dict[str, Any]]:
        """Query batches that are still in_progress"""
        try:
            container = self._get_container(config.CONTAINER_BATCH_TRACKING)
            query = "SELECT * FROM c WHERE c.status = 'in_progress' ORDER BY c.created_at DESC"
            items = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            return items
        except Exception as e:
            logger.error(f"Failed to query pending batches: {e}")
            return []

    # ========================================================================
    # TEST CONVENIENCE METHODS - Wrapper methods for easier testing
    # ========================================================================
    
    async def upsert_article(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convenience wrapper for upserting articles (used by integration tests)"""
        article = RawArticle(**article_data) if isinstance(article_data, dict) else article_data
        return await self.upsert_raw_article(article)
    
    async def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """Convenience wrapper for getting articles - extracts partition key from ID"""
        try:
            # Article ID format: source_YYYYMMDD_HH...
            # Try to extract date from ID
            parts = article_id.split('_')
            partition_key = None
            
            if len(parts) >= 2:
                date_str = parts[1]
                # Check if this looks like a date (8 digits: YYYYMMDD)
                if len(date_str) >= 8 and date_str[:8].isdigit():
                    partition_key = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            
            # If we extracted a partition key, try it first
            if partition_key:
                try:
                    result = await self.get_raw_article(article_id, partition_key)
                    if result:
                        return result
                except:
                    pass  # Fall through to cross-partition query
            
            # Fallback: Try cross-partition query
            container = self._get_container(config.CONTAINER_RAW_ARTICLES)
            query = f"SELECT * FROM c WHERE c.id = '{article_id}'"
            items = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            return items[0] if items else None
            
        except Exception as e:
            logger.error(f"Failed to get article {article_id}: {e}")
            return None
    
    async def upsert_story(self, story_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convenience wrapper for upserting stories (used by integration tests)"""
        story = StoryCluster(**story_data) if isinstance(story_data, dict) else story_data
        return await self.create_story_cluster(story)
    
    async def get_story(self, story_id: str) -> Optional[Dict[str, Any]]:
        """Convenience wrapper for getting stories - uses category from story data"""
        try:
            # Try default categories
            for category in ['world', 'tech', 'business', 'science', 'health', 'test', 'general']:
                try:
                    return await self.get_story_cluster(story_id, category)
                except:
                    continue
            return None
        except Exception as e:
            logger.error(f"Failed to get story {story_id}: {e}")
            return None


# Global instance
cosmos_client = CosmosDBClient()

