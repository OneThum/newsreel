"""Diagnostics API Router - For debugging backend state"""
import logging
from fastapi import APIRouter
from ..services.cosmos_service import cosmos_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])


@router.get("/database-stats")
async def get_database_stats():
    """
    Get statistics about what's in the database
    Helps diagnose clustering and RSS issues
    """
    
    cosmos_service.connect()
    
    try:
        # Get raw articles (query_items returns iterator, not awaitable)
        raw_articles_iter = cosmos_service._get_container("raw_articles").query_items(
            query="SELECT c.source, COUNT(1) as count FROM c GROUP BY c.source",
            enable_cross_partition_query=True
        )
        articles_by_source = {item['source']: item['count'] for item in raw_articles_iter}
        
        # Get total article count
        total_articles_iter = cosmos_service._get_container("raw_articles").query_items(
            query="SELECT VALUE COUNT(1) FROM c",
            enable_cross_partition_query=True
        )
        total_articles = list(total_articles_iter)[0] if total_articles_iter else 0
        
        # Get story clusters
        total_stories_iter = cosmos_service._get_container("story_clusters").query_items(
            query="SELECT VALUE COUNT(1) FROM c",
            enable_cross_partition_query=True
        )
        total_stories = list(total_stories_iter)[0] if total_stories_iter else 0
        
        # Get stories by source count
        stories_by_source_iter = cosmos_service._get_container("story_clusters").query_items(
            query="SELECT c.verification_level, COUNT(1) as count FROM c GROUP BY c.verification_level",
            enable_cross_partition_query=True
        )
        source_distribution = {item['verification_level']: item['count'] for item in stories_by_source_iter}
        
        # Get stories with summaries
        stories_with_summary_iter = cosmos_service._get_container("story_clusters").query_items(
            query="SELECT VALUE COUNT(1) FROM c WHERE IS_DEFINED(c.summary)",
            enable_cross_partition_query=True
        )
        summary_count = list(stories_with_summary_iter)[0] if stories_with_summary_iter else 0
        
        return {
            "status": "ok",
            "raw_articles": {
                "total": total_articles,
                "by_source": articles_by_source
            },
            "story_clusters": {
                "total": total_stories,
                "with_summaries": summary_count,
                "by_source_count": source_distribution
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/recent-stories")
async def get_recent_story_details():
    """Get details of most recent stories to diagnose issues"""
    
    cosmos_service.connect()
    
    try:
        # Get 5 most recent stories
        recent = await cosmos_service.query_recent_stories(limit=5)
        
        # Simplify for readability
        story_summaries = []
        for story in recent:
            story_summaries.append({
                "id": story.get('id'),
                "title": story.get('title'),
                "first_seen": story.get('first_seen'),
                "last_updated": story.get('last_updated'),
                "source_count": len(story.get('source_articles', [])),
                "source_article_ids": story.get('source_articles', []),
                "has_summary": story.get('summary') is not None,
                "status": story.get('status')
            })
        
        return {
            "status": "ok",
            "recent_stories": story_summaries
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

