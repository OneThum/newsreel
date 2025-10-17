"""Cosmos DB Service"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from azure.cosmos import CosmosClient, exceptions
from azure.cosmos.container import ContainerProxy
from azure.cosmos.database import DatabaseProxy
from ..config import settings

logger = logging.getLogger(__name__)


class CosmosService:
    """Service for Cosmos DB operations"""
    
    def __init__(self):
        self.client: Optional[CosmosClient] = None
        self.database: Optional[DatabaseProxy] = None
        self._containers: Dict[str, ContainerProxy] = {}
        
    def connect(self):
        """Initialize connection"""
        if not self.client:
            self.client = CosmosClient.from_connection_string(
                settings.cosmos_connection_string
            )
            self.database = self.client.get_database_client(settings.cosmos_database_name)
            logger.info(f"Connected to Cosmos DB: {settings.cosmos_database_name}")
    
    def _get_container(self, container_name: str) -> ContainerProxy:
        """Get container proxy"""
        if container_name not in self._containers:
            if not self.database:
                self.connect()
            self._containers[container_name] = self.database.get_container_client(container_name)
        return self._containers[container_name]
    
    # Story Operations
    
    async def get_story(self, story_id: str, category: str) -> Optional[Dict[str, Any]]:
        """Get story by ID"""
        try:
            container = self._get_container("story_clusters")
            item = container.read_item(item=story_id, partition_key=category)
            return item
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error getting story {story_id}: {e}")
            raise
    
    async def query_recent_stories(
        self,
        category: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Query recent stories ordered by when news broke (first_seen)"""
        try:
            container = self._get_container("story_clusters")
            
            # Query without ORDER BY to avoid Cosmos DB limitations
            # We'll sort in Python instead
            # INCLUDE all stories including MONITORING - users want fresh news!
            
            # Special handling for "top_stories" category: show breaking news when available
            if category == "top_stories":
                # For Top Stories, prioritize BREAKING and DEVELOPING stories
                query = """
                    SELECT * FROM c 
                    WHERE c.status IN ('BREAKING', 'DEVELOPING', 'VERIFIED')
                """
                items = list(container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
            elif category:
                query = """
                    SELECT * FROM c 
                    WHERE c.category = @category
                """
                parameters = [{"name": "@category", "value": category}]
                items = list(container.query_items(
                    query=query,
                    parameters=parameters
                ))
            else:
                query = """
                    SELECT * FROM c
                """
                items = list(container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
            
            # Smart sorting algorithm: BREAKING news ALWAYS first, then sort by recency
            def story_sort_key(story):
                # Base score on recency (use last_updated if significantly different from first_seen)
                first_seen = story.get('first_seen', '')
                last_updated = story.get('last_updated', first_seen)
                
                # Use the most recent timestamp for sorting
                primary_time = max(first_seen, last_updated) if last_updated else first_seen
                
                # Status weight (higher = more important)
                # CRITICAL: BREAKING news must ALWAYS be first
                status = story.get('status', 'VERIFIED')
                is_breaking = 1 if status == 'BREAKING' else 0
                
                # Secondary status weight for non-breaking stories
                status_weights = {
                    'BREAKING': 1000,  # Not used in primary sort, but kept for consistency
                    'DEVELOPING': 500,
                    'VERIFIED': 100,
                    'MONITORING': 10
                }
                status_weight = status_weights.get(status, 50)
                
                # Source count matters (more sources = more important)
                source_count = len(story.get('source_articles', []))
                source_weight = min(source_count * 10, 100)  # Cap at 100
                
                # CRITICAL CHANGE: Sort by breaking status FIRST, then by time
                # This ensures BREAKING news is ALWAYS at the top, regardless of publish time
                # Format: (is_breaking, time, status_weight, source_weight)
                # Breaking news sorted by time amongst themselves, non-breaking after
                return (is_breaking, primary_time, status_weight, source_weight)
            
            items_sorted = sorted(items, key=story_sort_key, reverse=True)
            
            # Apply offset and limit
            start = offset
            end = offset + limit
            return items_sorted[start:end]
        except Exception as e:
            logger.error(f"Error querying recent stories: {e}")
            raise
    
    async def query_breaking_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Query recent stories (BREAKING, DEVELOPING, and VERIFIED)"""
        try:
            container = self._get_container("story_clusters")
            query = """
                SELECT * FROM c
                WHERE c.status IN ('BREAKING', 'DEVELOPING', 'VERIFIED')
                ORDER BY c.last_updated DESC
                OFFSET 0 LIMIT @limit
            """
            parameters = [{"name": "@limit", "value": limit}]
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            return items
        except Exception as e:
            logger.error(f"Error querying recent stories: {e}")
            raise
    
    async def get_story_sources(self, source_ids: List[str]) -> List[Dict[str, Any]]:
        """Get source articles for a story - DEDUPLICATED by source name"""
        try:
            container = self._get_container("raw_articles")
            sources = []
            
            for source_id in source_ids:
                # Extract partition key from source ID
                parts = source_id.split('_')
                if len(parts) >= 2:
                    date_str = parts[1]
                    partition_key = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    
                    try:
                        item = container.read_item(item=source_id, partition_key=partition_key)
                        sources.append(item)
                    except exceptions.CosmosResourceNotFoundError:
                        logger.warning(f"Source article not found: {source_id}")
                        continue
            
            # DEDUPLICATE by source name before returning
            # This prevents showing "CNN, CNN, CNN..." when CNN has multiple updates
            # Keep the most recent article from each unique source
            seen_sources = {}
            for source in sources:
                source_name = source.get('source', '')
                if source_name:
                    # Overwrites older articles from same source with newer ones
                    seen_sources[source_name] = source
            
            deduplicated_sources = list(seen_sources.values())
            
            logger.info(f"📊 Deduplication: {len(sources)} articles → {len(deduplicated_sources)} unique sources")
            
            return deduplicated_sources
        except Exception as e:
            logger.error(f"Error getting story sources: {e}")
            raise
    
    # User Operations
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile"""
        try:
            container = self._get_container("user_profiles")
            item = container.read_item(item=user_id, partition_key=user_id)
            return item
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error getting user profile {user_id}: {e}")
            raise
    
    async def create_user_profile(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create user profile"""
        try:
            container = self._get_container("user_profiles")
            result = container.create_item(body=user_data)
            logger.info(f"Created user profile: {user_data['id']}")
            return result
        except Exception as e:
            logger.error(f"Error creating user profile: {e}")
            raise
    
    async def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile"""
        try:
            container = self._get_container("user_profiles")
            user = container.read_item(item=user_id, partition_key=user_id)
            user.update(updates)
            result = container.replace_item(item=user_id, body=user)
            logger.info(f"Updated user profile: {user_id}")
            return result
        except Exception as e:
            logger.error(f"Error updating user profile {user_id}: {e}")
            raise
    
    # Interaction Operations
    
    async def create_interaction(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """Create user interaction"""
        try:
            container = self._get_container("user_interactions")
            result = container.create_item(body=interaction)
            return result
        except Exception as e:
            logger.error(f"Error creating interaction: {e}")
            raise
    
    async def query_user_interactions(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query user interactions"""
        try:
            container = self._get_container("user_interactions")
            query = """
                SELECT * FROM c 
                WHERE c.user_id = @user_id 
                ORDER BY c.timestamp DESC
                OFFSET 0 LIMIT @limit
            """
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@limit", "value": limit}
            ]
            items = list(container.query_items(
                query=query,
                parameters=parameters
            ))
            return items
        except Exception as e:
            logger.error(f"Error querying user interactions: {e}")
            raise


# Global instance
cosmos_service = CosmosService()

