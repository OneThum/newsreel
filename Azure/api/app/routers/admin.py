"""Admin API Router - Comprehensive system metrics"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..services.cosmos_service import cosmos_service
from ..middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Admin email whitelist
ADMIN_EMAILS = ["david@mclauchlan.com", "dave@onethum.com"]


def require_admin(user: Dict[str, Any] = Depends(get_current_user)):
    """Verify user is an admin"""
    email = user.get("email", "")
    if email not in ADMIN_EMAILS:
        logger.warning(f"Unauthorized admin access attempt by {email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


# Response Models

class SystemHealth(BaseModel):
    overall_status: str
    api_health: str
    functions_health: str
    database_health: str


class StoryStatusCount(BaseModel):
    status: str
    count: int


class DatabaseStats(BaseModel):
    total_articles: int
    total_stories: int
    stories_with_summaries: int
    unique_sources: int
    stories_by_status: List[StoryStatusCount]


class SourceCount(BaseModel):
    source: str
    count: int


class RSSIngestionStats(BaseModel):
    total_feeds: int
    last_run: datetime
    articles_per_hour: int
    success_rate: float
    top_sources: List[SourceCount]


class ClusteringStats(BaseModel):
    match_rate: float
    avg_sources_per_story: float
    stories_created_24h: int
    stories_updated_24h: int


class SummarizationStats(BaseModel):
    coverage: float
    avg_generation_time: float
    summaries_generated_24h: int
    avg_word_count: int
    cost_24h: float


class FeedQualityStats(BaseModel):
    rating: str
    source_diversity: float
    unique_sources: int
    categorization_confidence: float


class AzureResourceInfo(BaseModel):
    resource_group: str
    location: str
    subscription_name: str
    container_app_status: str
    functions_status: str
    cosmos_db_status: str


class AdminMetrics(BaseModel):
    timestamp: datetime
    system_health: SystemHealth
    database: DatabaseStats
    rss_ingestion: RSSIngestionStats
    clustering: ClusteringStats
    summarization: SummarizationStats
    feed_quality: FeedQualityStats
    azure: AzureResourceInfo


@router.get("/metrics", response_model=AdminMetrics)
async def get_admin_metrics(user: Dict[str, Any] = Depends(require_admin)):
    """
    Get comprehensive system metrics
    
    Admin-only endpoint providing full visibility into:
    - System health
    - Database statistics
    - RSS ingestion performance
    - Story clustering metrics
    - AI summarization stats
    - Feed quality scores
    - Azure resource status
    """
    
    logger.info(f"Admin metrics requested by {user.get('email')}")
    
    try:
        cosmos_service.connect()
        
        # ==================================================================
        # DATABASE STATS
        # ==================================================================
        
        raw_articles_container = cosmos_service._get_container("raw_articles")
        stories_container = cosmos_service._get_container("story_clusters")
        
        # Total articles
        total_articles_query = list(raw_articles_container.query_items(
            query="SELECT VALUE COUNT(1) FROM c",
            enable_cross_partition_query=True
        ))
        total_articles = total_articles_query[0] if total_articles_query else 0
        
        # Total stories
        total_stories_query = list(stories_container.query_items(
            query="SELECT VALUE COUNT(1) FROM c",
            enable_cross_partition_query=True
        ))
        total_stories = total_stories_query[0] if total_stories_query else 0
        
        # Stories with summaries
        with_summaries_query = list(stories_container.query_items(
            query="SELECT VALUE COUNT(1) FROM c WHERE IS_DEFINED(c.summary) AND c.summary != null AND c.summary.text != null AND c.summary.text != ''",
            enable_cross_partition_query=True
        ))
        stories_with_summaries = with_summaries_query[0] if with_summaries_query else 0
        
        # Unique sources
        unique_sources_query = list(raw_articles_container.query_items(
            query="SELECT DISTINCT VALUE c.source FROM c",
            enable_cross_partition_query=True
        ))
        unique_sources = len(unique_sources_query)
        
        # Stories by status (aggregate in Python - serverless Cosmos doesn't support GROUP BY)
        all_stories_status = list(stories_container.query_items(
            query="SELECT c.status FROM c",
            enable_cross_partition_query=True
        ))
        status_counts: Dict[str, int] = {}
        for story in all_stories_status:
            status = story.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        stories_by_status = [
            StoryStatusCount(status=status, count=count)
            for status, count in status_counts.items()
        ]
        
        # ==================================================================
        # RSS INGESTION STATS
        # ==================================================================
        
        # Recent articles (last 24h)
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        recent_articles_query = list(raw_articles_container.query_items(
            query=f"SELECT c.source FROM c WHERE c.published_at >= '{yesterday}'",
            enable_cross_partition_query=True
        ))
        
        articles_24h = len(recent_articles_query)
        articles_per_hour = articles_24h // 24 if articles_24h > 0 else 0
        
        # Top sources (24h)
        source_counts: Dict[str, int] = {}
        for article in recent_articles_query:
            source = article.get('source', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        top_sources = [
            SourceCount(source=source, count=count)
            for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # ==================================================================
        # CLUSTERING STATS
        # ==================================================================
        
        # Average sources per story
        stories_with_sources = list(stories_container.query_items(
            query="SELECT ARRAY_LENGTH(c.source_articles) as source_count FROM c",
            enable_cross_partition_query=True
        ))
        
        source_counts_list = [item['source_count'] for item in stories_with_sources if 'source_count' in item]
        avg_sources = sum(source_counts_list) / len(source_counts_list) if source_counts_list else 1.0
        
        # Stories created/updated in last 24h
        stories_24h = list(stories_container.query_items(
            query=f"""
                SELECT c.first_seen, c.last_updated
                FROM c 
                WHERE c.first_seen >= '{yesterday}' OR c.last_updated >= '{yesterday}'
            """,
            enable_cross_partition_query=True
        ))
        
        created_24h = sum(1 for s in stories_24h if s.get('first_seen', '') >= yesterday)
        updated_24h = sum(1 for s in stories_24h if s.get('last_updated', '') >= yesterday and s.get('first_seen', '') < yesterday)
        
        # Estimated match rate (stories with 2+ sources / total stories)
        multi_source_stories = sum(1 for count in source_counts_list if count >= 2)
        match_rate = multi_source_stories / len(source_counts_list) if source_counts_list else 0.0
        
        # ==================================================================
        # SUMMARIZATION STATS
        # ==================================================================
        
        coverage = stories_with_summaries / total_stories if total_stories > 0 else 0.0
        
        # Get summary stats from recent summaries
        recent_summaries = list(stories_container.query_items(
            query=f"""
                SELECT c.summary 
                FROM c 
                WHERE IS_DEFINED(c.summary) 
                AND c.summary.generated_at >= '{yesterday}'
            """,
            enable_cross_partition_query=True
        ))
        
        summaries_24h = len(recent_summaries)
        
        # Calculate average generation time and word count
        generation_times = []
        word_counts = []
        costs_24h = []
        
        for item in recent_summaries:
            summary = item.get('summary', {})
            if summary.get('generation_time_ms'):
                generation_times.append(summary['generation_time_ms'])
            if summary.get('word_count'):
                word_counts.append(summary['word_count'])
            if summary.get('cost_usd'):
                costs_24h.append(summary['cost_usd'])
        
        avg_generation_time = (sum(generation_times) / len(generation_times) / 1000) if generation_times else 0.0
        avg_word_count = int(sum(word_counts) / len(word_counts)) if word_counts else 0
        total_cost_24h = sum(costs_24h) if costs_24h else 0.0
        
        # ==================================================================
        # FEED QUALITY STATS
        # ==================================================================
        
        # Source diversity in recent feed
        recent_stories = list(stories_container.query_items(
            query="SELECT TOP 20 c.source_articles FROM c ORDER BY c.last_updated DESC",
            enable_cross_partition_query=True
        ))
        
        feed_sources = set()
        for story in recent_stories:
            for article_id in story.get('source_articles', []):
                # Extract source from article ID (format: source_timestamp_hash)
                source = article_id.split('_')[0]
                feed_sources.add(source)
        
        feed_unique_sources = len(feed_sources)
        feed_diversity = feed_unique_sources / 20 if recent_stories else 0.0
        
        # Determine quality rating
        if feed_diversity > 0.6:
            quality_rating = "Excellent"
        elif feed_diversity > 0.4:
            quality_rating = "Good"
        elif feed_diversity > 0.2:
            quality_rating = "Fair"
        else:
            quality_rating = "Poor"
        
        # Categorization confidence (placeholder - would come from logs in production)
        categorization_confidence = 0.65  # 65% default estimate
        
        # ==================================================================
        # SYSTEM HEALTH
        # ==================================================================
        
        # Check if we can query database
        database_health = "healthy" if total_stories > 0 else "degraded"
        
        # API health (if we got here, API is working)
        api_health = "healthy"
        
        # Functions health (check if articles are recent)
        most_recent_article = list(raw_articles_container.query_items(
            query="SELECT TOP 1 c.published_at FROM c ORDER BY c.published_at DESC",
            enable_cross_partition_query=True
        ))
        
        if most_recent_article:
            last_article_time = datetime.fromisoformat(most_recent_article[0]['published_at'].replace('Z', '+00:00'))
            time_since_last = (datetime.now(timezone.utc) - last_article_time).total_seconds() / 60
            functions_health = "healthy" if time_since_last < 15 else "degraded"  # < 15 min
        else:
            functions_health = "degraded"
        
        overall_status = "healthy" if all([
            database_health == "healthy",
            api_health == "healthy",
            functions_health == "healthy"
        ]) else "degraded"
        
        # ==================================================================
        # AZURE RESOURCE INFO
        # ==================================================================
        
        azure_info = AzureResourceInfo(
            resource_group="newsreel-rg",
            location="Central US",
            subscription_name="Newsreel Subscription",
            container_app_status="running",
            functions_status="running" if functions_health == "healthy" else "degraded",
            cosmos_db_status="running" if database_health == "healthy" else "degraded"
        )
        
        # ==================================================================
        # ASSEMBLE RESPONSE
        # ==================================================================
        
        metrics = AdminMetrics(
            timestamp=datetime.now(timezone.utc),
            system_health=SystemHealth(
                overall_status=overall_status,
                api_health=api_health,
                functions_health=functions_health,
                database_health=database_health
            ),
            database=DatabaseStats(
                total_articles=total_articles,
                total_stories=total_stories,
                stories_with_summaries=stories_with_summaries,
                unique_sources=unique_sources,
                stories_by_status=stories_by_status
            ),
            rss_ingestion=RSSIngestionStats(
                total_feeds=10,  # MVP mode
                last_run=last_article_time if most_recent_article else datetime.now(timezone.utc),
                articles_per_hour=articles_per_hour,
                success_rate=0.95,  # Estimated
                top_sources=top_sources
            ),
            clustering=ClusteringStats(
                match_rate=match_rate,
                avg_sources_per_story=avg_sources,
                stories_created_24h=created_24h,
                stories_updated_24h=updated_24h
            ),
            summarization=SummarizationStats(
                coverage=coverage,
                avg_generation_time=avg_generation_time,
                summaries_generated_24h=summaries_24h,
                avg_word_count=avg_word_count,
                cost_24h=total_cost_24h
            ),
            feed_quality=FeedQualityStats(
                rating=quality_rating,
                source_diversity=feed_diversity,
                unique_sources=feed_unique_sources,
                categorization_confidence=categorization_confidence
            ),
            azure=azure_info
        )
        
        logger.info(f"Admin metrics generated: {total_stories} stories, {total_articles} articles, quality={quality_rating}")
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error generating admin metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate metrics: {str(e)}"
        )

