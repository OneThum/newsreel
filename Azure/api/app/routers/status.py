"""Simple Status Endpoint - No complex queries"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from ..services.cosmos_service import cosmos_service

router = APIRouter(tags=["status"])


@router.get("/status", response_class=HTMLResponse)
async def simple_status():
    """Extremely simple status page - just counts"""
    
    cosmos_service.connect()
    
    try:
        raw_articles = cosmos_service._get_container("raw_articles")
        stories = cosmos_service._get_container("story_clusters")
        
        # Just count - no GROUP BY, no ORDER BY
        article_count_query = list(raw_articles.query_items(
            query="SELECT VALUE COUNT(1) FROM c",
            enable_cross_partition_query=True
        ))
        article_count = article_count_query[0] if article_count_query else 0
        
        story_count_query = list(stories.query_items(
            query="SELECT VALUE COUNT(1) FROM c",
            enable_cross_partition_query=True
        ))
        story_count = story_count_query[0] if story_count_query else 0
        
        # Get recent stories (all, then sort in Python)
        sample_stories_query = list(stories.query_items(
            query="SELECT TOP 50 c.id, c.title, c.verification_level, c.last_updated, ARRAY_LENGTH(c.source_articles) as source_count FROM c",
            enable_cross_partition_query=True
        ))
        # Sort by last_updated descending to get newest
        sample_stories = sorted(sample_stories_query, key=lambda x: x.get('last_updated', ''), reverse=True)[:5]
        
        # Get unique sources
        unique_sources = list(raw_articles.query_items(
            query="SELECT DISTINCT VALUE c.source FROM c",
            enable_cross_partition_query=True
        ))
        
        # Get recent articles (filter by today, then sort in Python)
        sample_articles_query = list(raw_articles.query_items(
            query="SELECT TOP 100 c.source, c.title, c.published_at, c.processed FROM c WHERE c.published_date >= '2025-10-09'",
            enable_cross_partition_query=True
        ))
        # Sort by published_at descending to get newest
        sample_articles = sorted(sample_articles_query, key=lambda x: x.get('published_at', ''), reverse=True)[:20]
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Newsreel Backend Status</title>
    <meta http-equiv="refresh" content="10">
    <style>
        body {{ background: #0a1929; color: #fff; font-family: monospace; padding: 40px; }}
        h1 {{ color: #60a5fa; }}
        .stat {{ font-size: 48px; color: #4ade80; margin: 20px 0; }}
        .label {{ color: #94a3b8; }}
        pre {{ background: #1e293b; padding: 15px; border-radius: 8px; overflow-x: auto; }}
        .good {{ color: #4ade80; }}
        .bad {{ color: #f87171; }}
    </style>
</head>
<body>
    <h1>📊 Newsreel Backend Status</h1>
    <p class="label">Auto-refreshes every 10 seconds</p>
    
    <h2>Database Counts</h2>
    <div class="stat">{article_count}</div>
    <div class="label">Total Articles in Database</div>
    
    <div class="stat">{story_count}</div>
    <div class="label">Total Story Clusters</div>
    
    <h2>Sample Stories (Random 5)</h2>
    <pre>{''.join(f'''
ID: {s.get('id')}
Title: {s.get('title')}
Sources: {s.get('source_count', 0)} <span class="{'good' if s.get('source_count', 0) > 1 else 'bad'}">({'✓ Multi-source' if s.get('source_count', 0) > 1 else '✗ Single-source'})</span>

''' for s in sample_stories)}</pre>
    
    <h2>Latest 20 Articles (Real-time Feed)</h2>
    <pre>{''.join(f'''
{i+1}. [{a.get('source').upper()}] {a.get('title')[:70]}...
   Published: {str(a.get('published_at', ''))[:19]} | {'✓ Clustered' if a.get('processed') else '⏳ Pending'}

''' for i, a in enumerate(sample_articles))}</pre>
    
    <h2>Active Sources ({len(unique_sources)} unique)</h2>
    <pre>{', '.join(sorted(unique_sources))}</pre>
    
    <h2>Health Check</h2>
    <p class="{'good' if article_count > 100 else 'bad'}">
        Articles: {article_count} {'✓ Good' if article_count > 100 else '✗ Too few'}
    </p>
    <p class="{'good' if len(unique_sources) > 5 else 'bad'}">
        Sources: {len(unique_sources)} different feeds {'✓ Good diversity' if len(unique_sources) > 5 else '✗ Too few sources'}
    </p>
    <p class="{'good' if story_count > 20 else 'bad'}">
        Stories: {story_count} {'✓ Good' if story_count > 20 else '✗ Too few'}
    </p>
    <p class="{'good' if any(s.get('source_count', 0) > 1 for s in sample_stories) else 'bad'}">
        Multi-source: {'✓ Found in samples' if any(s.get('source_count', 0) > 1 for s in sample_stories) else '✗ None in samples'}
    </p>
    
</body>
</html>
        """
        return html
        
    except Exception as e:
        return f"""
<html>
<body style="background: #0a1929; color: #f87171; padding: 40px; font-family: monospace;">
    <h1>Error</h1>
    <pre>{str(e)}</pre>
</body>
</html>
        """

