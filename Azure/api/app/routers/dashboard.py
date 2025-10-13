"""Dashboard Router - Real-time visibility into backend operations"""
import logging
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from ..services.cosmos_service import cosmos_service
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/", response_class=HTMLResponse)
async def dashboard_home():
    """Real-time dashboard for monitoring Newsreel backend"""
    
    cosmos_service.connect()
    
    try:
        # Get database statistics
        raw_articles_container = cosmos_service._get_container("raw_articles")
        stories_container = cosmos_service._get_container("story_clusters")
        
        # Count articles by source
        articles_by_source_query = list(raw_articles_container.query_items(
            query="""
                SELECT c.source, COUNT(1) as count 
                FROM c 
                WHERE c.published_date >= '2025-10-09'
                GROUP BY c.source
            """,
            enable_cross_partition_query=True
        ))
        
        # Sort in Python instead of SQL
        articles_by_source_query.sort(key=lambda x: x['count'], reverse=True)
        
        # Count total articles
        total_articles = sum(item['count'] for item in articles_by_source_query)
        
        # Get stories by verification level
        stories_by_level = list(stories_container.query_items(
            query="""
                SELECT c.verification_level, COUNT(1) as count 
                FROM c 
                GROUP BY c.verification_level
            """,
            enable_cross_partition_query=True
        ))
        
        # Sort in Python
        stories_by_level.sort(key=lambda x: x['verification_level'])
        
        # Count stories with summaries
        with_summaries = list(stories_container.query_items(
            query="SELECT VALUE COUNT(1) FROM c WHERE IS_DEFINED(c.summary) AND c.summary != null",
            enable_cross_partition_query=True
        ))
        summary_count = with_summaries[0] if with_summaries else 0
        
        # Get total stories
        total_stories = sum(item['count'] for item in stories_by_level)
        
        # Get recent stories (simple query without ORDER BY)
        recent_stories_query = list(stories_container.query_items(
            query="SELECT TOP 20 * FROM c",
            enable_cross_partition_query=True
        ))
        
        # Sort in Python
        recent_stories = sorted(recent_stories_query, key=lambda x: x.get('last_updated', ''), reverse=True)[:10]
        
        # Get recent articles (Cosmos DB doesn't support ORDER BY without index)
        recent_articles_query = list(raw_articles_container.query_items(
            query="""
                SELECT TOP 50 c.id, c.source, c.title, c.published_at, c.category, c.processed
                FROM c
                WHERE c.published_date >= '2025-10-09'
            """,
            enable_cross_partition_query=True
        ))
        
        # Sort in Python by published_at
        recent_articles_query.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        recent_articles_query = recent_articles_query[:20]  # Take top 20
        
        # Build HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Newsreel Backend Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #0a1929;
            color: #fff;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            color: #60a5fa;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #94a3b8;
            margin-bottom: 30px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #1e293b;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #334155;
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
            color: #60a5fa;
        }}
        .stat-label {{
            color: #94a3b8;
            margin-top: 5px;
        }}
        .section {{
            background: #1e293b;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #334155;
            margin-bottom: 20px;
        }}
        .section h2 {{
            color: #60a5fa;
            margin-top: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #334155;
        }}
        th {{
            color: #60a5fa;
            font-weight: 600;
        }}
        .good {{
            color: #4ade80;
        }}
        .warning {{
            color: #fbbf24;
        }}
        .error {{
            color: #f87171;
        }}
        .timestamp {{
            color: #94a3b8;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 Newsreel Backend Dashboard</h1>
        <p class="subtitle">Real-time monitoring • Auto-refreshes every 30 seconds</p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total_articles}</div>
                <div class="stat-label">Total Articles (Today)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(articles_by_source_query)}</div>
                <div class="stat-label">Different Sources</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_stories}</div>
                <div class="stat-label">Story Clusters</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary_count}</div>
                <div class="stat-label">AI Summaries</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📰 Articles by Source (Today)</h2>
            <table>
                <tr>
                    <th>Source</th>
                    <th>Article Count</th>
                    <th>Status</th>
                </tr>
                {''.join(f'''
                <tr>
                    <td>{item["source"]}</td>
                    <td>{item["count"]}</td>
                    <td class="good">✓ Active</td>
                </tr>
                ''' for item in articles_by_source_query[:20])}
            </table>
            <p class="timestamp">Expected: 40-60 different sources. Current: {len(articles_by_source_query)}</p>
        </div>
        
        <div class="section">
            <h2>🔗 Stories by Source Count</h2>
            <table>
                <tr>
                    <th>Source Count</th>
                    <th>Story Count</th>
                    <th>Status</th>
                </tr>
                {''.join(f'''
                <tr>
                    <td>{item["verification_level"]} sources</td>
                    <td>{item["count"]}</td>
                    <td class="{'good' if item['verification_level'] > 1 else 'warning'}">
                        {'✓ Multi-source' if item['verification_level'] > 1 else '⚠ Single-source'}
                    </td>
                </tr>
                ''' for item in stories_by_level)}
            </table>
            <p class="timestamp">Expected: 30-50% of stories with 2+ sources</p>
        </div>
        
        <div class="section">
            <h2>📝 Recent Stories</h2>
            <table>
                <tr>
                    <th>Title</th>
                    <th>Sources</th>
                    <th>Summary</th>
                    <th>Age</th>
                </tr>
                {''.join(f'''
                <tr>
                    <td>{story.get('title', 'Unknown')[:60]}...</td>
                    <td class="{'good' if len(story.get('source_articles', [])) > 1 else 'warning'}">
                        {len(story.get('source_articles', []))} sources
                    </td>
                    <td class="{'good' if story.get('summary') else 'error'}">
                        {'✓ Has summary' if story.get('summary') else '✗ No summary'}
                    </td>
                    <td class="timestamp">{story.get('first_seen', 'Unknown')}</td>
                </tr>
                ''' for story in recent_stories[:10])}
            </table>
        </div>
        
        <div class="section">
            <h2>📥 Recent Articles</h2>
            <table>
                <tr>
                    <th>Source</th>
                    <th>Title</th>
                    <th>Category</th>
                    <th>Processed</th>
                    <th>Published</th>
                </tr>
                {''.join(f'''
                <tr>
                    <td><strong>{article.get('source', 'Unknown')}</strong></td>
                    <td>{article.get('title', 'Unknown')[:50]}...</td>
                    <td>{article.get('category', 'general')}</td>
                    <td class="{'good' if article.get('processed') else 'warning'}">
                        {'✓ Clustered' if article.get('processed') else '⏳ Pending'}
                    </td>
                    <td class="timestamp">{str(article.get('published_at', 'Unknown'))[:19]}</td>
                </tr>
                ''' for article in recent_articles_query)}
            </table>
        </div>
        
        <div class="section">
            <h2>🔍 System Health</h2>
            <table>
                <tr>
                    <th>Component</th>
                    <th>Status</th>
                    <th>Details</th>
                </tr>
                <tr>
                    <td>RSS Feeds</td>
                    <td class="{'good' if len(articles_by_source_query) > 20 else 'error'}">
                        {'✓ Working' if len(articles_by_source_query) > 20 else '✗ Limited sources'}
                    </td>
                    <td>{len(articles_by_source_query)} of 100 feeds active</td>
                </tr>
                <tr>
                    <td>Story Clustering</td>
                    <td class="{'good' if any(s['verification_level'] > 1 for s in stories_by_level) else 'error'}">
                        {'✓ Multi-source stories' if any(s['verification_level'] > 1 for s in stories_by_level) else '✗ All single-source'}
                    </td>
                    <td>{sum(s['count'] for s in stories_by_level if s['verification_level'] > 1)} multi-source stories</td>
                </tr>
                <tr>
                    <td>AI Summarization</td>
                    <td class="{'good' if summary_count > 0 else 'error'}">
                        {'✓ Generating' if summary_count > 0 else '✗ No summaries'}
                    </td>
                    <td>{summary_count} summaries generated</td>
                </tr>
            </table>
        </div>
        
        <p class="timestamp">Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC • Auto-refreshes every 30 seconds</p>
    </div>
</body>
</html>
        """
        
        return html
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return f"""
<!DOCTYPE html>
<html>
<head><title>Dashboard Error</title></head>
<body style="background: #0a1929; color: #fff; font-family: sans-serif; padding: 40px;">
    <h1>Dashboard Error</h1>
    <p>Error loading dashboard: {str(e)}</p>
    <p>Check Container App logs for details.</p>
</body>
</html>
        """

