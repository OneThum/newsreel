"""Simple JSON Dashboard - No HTML, just data"""
import logging
from fastapi import APIRouter
from ..services.cosmos_service import cosmos_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def get_simple_stats():
    """Simple statistics endpoint - returns JSON"""
    
    cosmos_service.connect()
    
    try:
        raw_articles_container = cosmos_service._get_container("raw_articles")
        stories_container = cosmos_service._get_container("story_clusters")
        
        # Simple counts - no ORDER BY
        articles_by_source = list(raw_articles_container.query_items(
            query="SELECT c.source, COUNT(1) as count FROM c GROUP BY c.source",
            enable_cross_partition_query=True
        ))
        
        stories_by_level = list(stories_container.query_items(
            query="SELECT c.verification_level, COUNT(1) as count FROM c GROUP BY c.verification_level",
            enable_cross_partition_query=True
        ))
        
        # Get sample stories
        sample_stories = list(stories_container.query_items(
            query="SELECT TOP 5 c.id, c.title, c.verification_level, c.source_articles, c.summary FROM c",
            enable_cross_partition_query=True
        ))
        
        # Get sample articles
        sample_articles = list(raw_articles_container.query_items(
            query="SELECT TOP 10 c.id, c.source, c.title, c.processed FROM c",
            enable_cross_partition_query=True
        ))
        
        return {
            "status": "ok",
            "timestamp": "2025-10-09T03:00:00Z",
            "articles": {
                "total": sum(x['count'] for x in articles_by_source),
                "by_source": {x['source']: x['count'] for x in articles_by_source},
                "source_count": len(articles_by_source)
            },
            "stories": {
                "total": sum(x['count'] for x in stories_by_level),
                "by_verification_level": {x['verification_level']: x['count'] for x in stories_by_level},
                "with_summaries": sum(1 for s in sample_stories if s.get('summary'))
            },
            "samples": {
                "stories": [
                    {
                        "title": s.get('title'),
                        "source_count": len(s.get('source_articles', [])),
                        "has_summary": s.get('summary') is not None
                    } for s in sample_stories
                ],
                "articles": [
                    {
                        "source": a.get('source'),
                        "title": a.get('title')[:50],
                        "processed": a.get('processed')
                    } for a in sample_articles
                ]
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

