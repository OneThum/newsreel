"""
Story Clustering Function
Triggered by Cosmos DB change feed on raw_articles container
Groups related articles into story clusters
"""
import azure.functions as func
import logging
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import config
from shared.cosmos_client import cosmos_client
from shared.models import (
    RawArticle, StoryCluster, StoryStatus, VersionHistory,
    SummaryVersion, Entity
)
from shared.utils import (
    generate_event_fingerprint,
    calculate_text_similarity
)

logger = logging.getLogger(__name__)
app = func.FunctionApp()


class StoryClusterer:
    """Story clustering logic"""
    
    def __init__(self):
        self.similarity_threshold = config.STORY_FINGERPRINT_SIMILARITY_THRESHOLD
    
    async def find_matching_story(self, article: RawArticle) -> Optional[Dict[str, Any]]:
        """Find existing story cluster that matches this article"""
        
        # First, try exact fingerprint match
        stories = await cosmos_client.query_stories_by_fingerprint(article.story_fingerprint)
        
        if stories:
            # Find the most recent story with this fingerprint
            stories_sorted = sorted(stories, key=lambda s: s.get('last_updated', ''), reverse=True)
            
            # Check if story is still recent (within 7 days)
            most_recent = stories_sorted[0]
            last_updated = datetime.fromisoformat(most_recent['last_updated'].replace('Z', '+00:00'))
            
            if datetime.now(timezone.utc) - last_updated < timedelta(days=7):
                return most_recent
        
        # If no exact match, try fuzzy matching on title similarity
        # Query recent stories in the same category
        recent_stories = await cosmos_client.query_recent_stories(
            category=article.category,
            limit=50
        )
        
        best_match = None
        best_similarity = 0.0
        
        for story in recent_stories:
            # Calculate title similarity
            similarity = calculate_text_similarity(article.title, story.get('title', ''))
            
            if similarity > self.similarity_threshold and similarity > best_similarity:
                best_similarity = similarity
                best_match = story
        
        return best_match
    
    async def create_new_story(self, article: RawArticle) -> StoryCluster:
        """Create a new story cluster from an article"""
        
        story_id = f"story_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{article.story_fingerprint}"
        
        # Determine initial status
        status = StoryStatus.MONITORING  # Only 1 source so far
        
        # Calculate importance score (placeholder algorithm)
        importance_score = 50
        if article.source_tier == 1:
            importance_score += 20
        
        story = StoryCluster(
            id=story_id,
            event_fingerprint=article.story_fingerprint,
            title=article.title,
            category=article.category,
            tags=article.tags,
            status=status,
            verification_level=1,
            first_seen=article.published_at,
            last_updated=datetime.now(timezone.utc),
            source_articles=[article.id],
            importance_score=importance_score,
            confidence_score=40,  # Low confidence with only 1 source
            breaking_news=False
        )
        
        # Store in Cosmos DB
        await cosmos_client.create_story_cluster(story)
        logger.info(f"Created new story cluster: {story_id}")
        
        return story
    
    async def update_existing_story(
        self,
        story: Dict[str, Any],
        article: RawArticle
    ) -> Dict[str, Any]:
        """Update existing story cluster with new article"""
        
        story_id = story['id']
        partition_key = story['category']
        
        # Add article to source list if not already present
        source_articles = story.get('source_articles', [])
        if article.id not in source_articles:
            source_articles.append(article.id)
        
        verification_level = len(source_articles)
        
        # Determine status based on source count and recency
        status = story.get('status')
        first_seen = datetime.fromisoformat(story['first_seen'].replace('Z', '+00:00'))
        time_since_first = datetime.now(timezone.utc) - first_seen
        
        if verification_level == 1:
            status = StoryStatus.MONITORING.value
        elif verification_level == 2:
            status = StoryStatus.DEVELOPING.value
        elif verification_level >= 3:
            if time_since_first < timedelta(minutes=config.BREAKING_NEWS_WINDOW_MINUTES):
                status = StoryStatus.BREAKING.value
            else:
                status = StoryStatus.VERIFIED.value
        
        # Update breaking news flag
        breaking_news = (status == StoryStatus.BREAKING.value)
        breaking_detected_at = story.get('breaking_detected_at')
        
        if breaking_news and not story.get('breaking_news'):
            # Just became breaking news
            breaking_detected_at = datetime.now(timezone.utc).isoformat()
            logger.info(f"Story {story_id} upgraded to BREAKING status")
        
        # Calculate updated confidence score
        confidence_score = min(40 + (verification_level * 15), 99)
        
        # Update importance score based on tier of new source
        importance_score = story.get('importance_score', 50)
        if article.source_tier == 1:
            importance_score = min(importance_score + 10, 100)
        
        # Prepare updates
        updates = {
            'source_articles': source_articles,
            'verification_level': verification_level,
            'status': status,
            'confidence_score': confidence_score,
            'importance_score': importance_score,
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'update_count': story.get('update_count', 0) + 1,
            'breaking_news': breaking_news
        }
        
        if breaking_detected_at:
            updates['breaking_detected_at'] = breaking_detected_at
        
        # Update in Cosmos DB
        result = await cosmos_client.update_story_cluster(story_id, partition_key, updates)
        
        logger.info(f"Updated story cluster {story_id}: now {verification_level} sources, status={status}")
        
        return result
    
    async def process_article(self, article_data: Dict[str, Any]):
        """Process a single article for clustering"""
        try:
            # Parse article data
            article = RawArticle(**article_data)
            
            # Skip if already processed
            if article.processed:
                logger.debug(f"Article {article.id} already processed, skipping")
                return
            
            # Find matching story
            matching_story = await self.find_matching_story(article)
            
            if matching_story:
                # Update existing story
                updated_story = await self.update_existing_story(matching_story, article)
                story_id = updated_story['id']
            else:
                # Create new story
                new_story = await self.create_new_story(article)
                story_id = new_story.id
            
            # Mark article as processed
            await cosmos_client.update_article_processed(
                article.id,
                article.published_date,
                story_id
            )
            
            logger.info(f"Article {article.id} clustered into story {story_id}")
            
        except Exception as e:
            logger.error(f"Error processing article for clustering: {e}", exc_info=True)
            raise


@app.function_name(name="StoryClusteringChangeFeed")
@app.cosmos_db_trigger(
    arg_name="documents",
    database_name="%COSMOS_DATABASE_NAME%",
    container_name="raw_articles",
    connection="COSMOS_CONNECTION_STRING",
    lease_container_name="leases",
    create_lease_container_if_not_exists=True
)
async def story_clustering_changefeed(documents: func.DocumentList) -> None:
    """
    Cosmos DB Change Feed trigger
    Processes new articles for story clustering
    """
    
    if not documents:
        return
    
    logger.info(f"Processing {len(documents)} documents from change feed")
    
    # Connect to Cosmos DB
    cosmos_client.connect()
    
    # Create clusterer
    clusterer = StoryClusterer()
    
    # Process each document
    for doc in documents:
        try:
            article_data = json.loads(doc.to_json())
            await clusterer.process_article(article_data)
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            # Continue with next document
    
    logger.info(f"Completed processing {len(documents)} documents")

