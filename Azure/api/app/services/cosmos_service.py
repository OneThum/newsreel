"""Cosmos DB Service"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
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

    async def get_latest_cluster_update(self) -> Optional[datetime]:
        """Get the timestamp of the most recently updated story cluster

        Used for ETag generation to enable caching.
        """
        try:
            container = self._get_container("story_clusters")
            # Query for the most recently updated cluster
            query = """
            SELECT TOP 1 c.last_updated
            FROM c
            WHERE c.status != 'MONITORING'
            ORDER BY c.last_updated DESC
            """

            items = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))

            if items:
                last_updated_str = items[0]['last_updated']
                # Parse the ISO string back to datetime
                if isinstance(last_updated_str, str):
                    # Handle different datetime formats
                    try:
                        return datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
                    except ValueError:
                        # Fallback for other formats
                        return datetime.strptime(last_updated_str, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)

            return None
        except Exception as e:
            logger.error(f"Error getting latest cluster update: {e}")
            return None
    
    async def get_latest_cluster_update(self) -> Optional[datetime]:
        """Get the timestamp of the most recently updated story cluster for ETag generation"""
        try:
            container = self._get_container("story_clusters")

            # Query for the most recently updated story
            query = """
                SELECT TOP 1 c.last_updated FROM c
                WHERE c.last_updated != null
                ORDER BY c.last_updated DESC
            """
            items = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))

            if items and items[0].get('last_updated'):
                # Parse the ISO datetime string
                last_updated_str = items[0]['last_updated']
                return datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
            else:
                # Fallback: return current time if no stories found
                return datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Failed to get latest cluster update: {e}")
            return None

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
                # Query only recent stories (last 7 days) for better performance
                seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
                query = f"""
                    SELECT * FROM c 
                    WHERE c.category = @category
                    AND c.last_updated >= '{seven_days_ago}'
                """
                parameters = [{"name": "@category", "value": category}]
                items = list(container.query_items(
                    query=query,
                    parameters=parameters
                ))
            else:
                # Query only recent stories (last 7 days) to avoid querying all 38,000+ stories
                seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
                query = f"""
                    SELECT * FROM c
                    WHERE c.last_updated >= '{seven_days_ago}'
                """
                items = list(container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
            
            # 🔍 DIAGNOSTIC: Log query results
            logger.info(f"✅ Query returned {len(items)} stories")
            
            # ✅ SORT IN PYTHON - Sort by last_updated DESC (newest first)
            # This is required because Cosmos DB queries don't support ORDER BY without indexes
            sorted_items = sorted(
                items,
                key=lambda s: s.get('last_updated', ''),
                reverse=True  # Newest first
            )
            
            logger.info(f"📊 After sorting: {len(sorted_items)} stories by last_updated DESC")
            return sorted_items
        except exceptions.CosmosResourceNotFoundError as e:
            # Session token error - reset connection and retry
            logger.warning(f"Session token error, resetting connection: {e}")
            self.client = None
            self._containers = {}
            self.database = None
            
            # Retry once with fresh connection
            logger.info("Retrying with fresh Cosmos DB connection...")
            try:
                self.connect()
                container = self._get_container("story_clusters")
                query = "SELECT * FROM c ORDER BY c.last_updated DESC LIMIT @limit"
                parameters = [{"name": "@limit", "value": limit}]
                items = list(container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
                logger.info(f"✅ Retry successful, returned {len(items)} stories")
                return items
            except Exception as retry_error:
                logger.error(f"Retry failed: {retry_error}")
                raise
        except Exception as e:
            logger.error(f"Error querying stories: {e}")
            raise
    
    async def query_breaking_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Query recent stories - include all recent stories, prioritizing BREAKING/DEVELOPING/VERIFIED"""
        try:
            container = self._get_container("story_clusters")
            
            # Query ALL stories from the last 24 hours to ensure fresh content shows up
            # This includes MONITORING stories so users see fresh news even if single-source
            one_day_ago = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
            
            query = f"""
                SELECT * FROM c
                WHERE c.last_updated >= '{one_day_ago}'
            """
            items = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            # 🔍 DIAGNOSTIC: Log query results
            logger.info(f"📊 [COSMOS] query_breaking_news (24h) returned {len(items)} items")
            
            # If no recent stories, fallback to VERIFIED/DEVELOPING/BREAKING from any time
            if len(items) < limit:
                logger.info(f"📊 [COSMOS] Insufficient recent stories ({len(items)}), adding verified stories")
                fallback_query = """
                    SELECT * FROM c
                    WHERE c.status IN ('BREAKING', 'DEVELOPING', 'VERIFIED')
                """
                fallback_items = list(container.query_items(
                    query=fallback_query,
                    enable_cross_partition_query=True
                ))
                
                # Add fallback items that aren't already in items
                existing_ids = {item['id'] for item in items}
                for fallback in fallback_items:
                    if fallback['id'] not in existing_ids:
                        items.append(fallback)
                
                logger.info(f"📊 [COSMOS] After fallback: {len(items)} total items")
            
            if items:
                first_item = items[0]
                logger.info(f"   [COSMOS] First item ID: {first_item.get('id')}")
                logger.info(f"   [COSMOS] First item has 'summary': {'summary' in first_item}")
                logger.info(f"   [COSMOS] First item has 'source_articles': {'source_articles' in first_item}")
                if 'source_articles' in first_item:
                    logger.info(f"   [COSMOS] First item source_articles length: {len(first_item['source_articles'])}")
            
            # Sort by last_updated in Python (newest first)
            items_sorted = sorted(items, key=lambda x: x.get('last_updated', ''), reverse=True)
            
            # Apply limit
            return items_sorted[:limit]
        except Exception as e:
            logger.error(f"Error querying recent stories: {e}")
            raise

    async def get_latest_cluster_update(self) -> Optional[datetime]:
        """Get the timestamp of the most recently updated story cluster for ETag generation"""
        try:
            container = self._get_container("story_clusters")

            # Query for the most recently updated story
            query = """
                SELECT TOP 1 c.last_updated FROM c
                WHERE c.status != 'MONITORING'
                ORDER BY c.last_updated DESC
            """
            items = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))

            if items:
                last_updated_str = items[0].get('last_updated')
                if last_updated_str:
                    # Parse the timestamp (Cosmos DB returns as string)
                    if isinstance(last_updated_str, str):
                        # Handle both ISO format and other formats
                        try:
                            return datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
                        except ValueError:
                            # Fallback parsing
                            return datetime.strptime(last_updated_str, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)

            # If no stories found, return None
            return None

        except Exception as e:
            logger.error(f"Error getting latest cluster update: {e}")
            return None

    async def get_story_sources(self, source_ids: List[str]) -> List[Dict[str, Any]]:
        """Get source articles for a story - DEDUPLICATED by source name
        
        ⚡ CRITICAL OPTIMIZATION: Uses single batch query instead of N+1 queries
        Before: 1 query per source = 817 queries for 817-source story (TIMEOUT!)
        After: 1 batch query = all sources fetched instantly
        """
        try:
            if not source_ids:
                return []
            
            container = self._get_container("raw_articles")
            
            # Build batch query to fetch all sources in ONE query
            placeholders = ', '.join([f'@id{i}' for i in range(len(source_ids))])
            query = f"SELECT * FROM c WHERE c.id IN ({placeholders})"
            
            parameters = [{'name': f'@id{i}', 'value': source_ids[i]} for i in range(len(source_ids))]
            
            # Execute single batch query (cross-partition to ensure all are found)
            sources = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            # DEDUPLICATE by source name
            seen_sources = {}
            for source in sources:
                source_name = source.get('source', '')
                if source_name:
                    seen_sources[source_name] = source
            
            deduplicated_sources = list(seen_sources.values())
            
            logger.info(f"⚡ Batch query: {len(source_ids)} IDs → {len(sources)} found → {len(deduplicated_sources)} unique")
            
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

