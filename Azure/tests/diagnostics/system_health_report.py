#!/usr/bin/env python3
"""
Comprehensive System Health Report Generator

Generates a detailed HTML report of all Newsreel API components:
- RSS Ingestion health
- Story Clustering quality
- AI Summarization coverage
- API performance
- Database health
- Cost analysis
"""
import os
import sys
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
from dotenv import load_dotenv
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../functions')))

load_dotenv()

from shared.config import config
from shared.cosmos_client import CosmosDBClient


class SystemHealthReporter:
    """Generate comprehensive system health report"""
    
    def __init__(self):
        self.cosmos_client = CosmosDBClient()
        self.report_data = {}
    
    async def generate_report(self):
        """Generate comprehensive health report"""
        print("Generating comprehensive system health report...")
        print(f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        
        # Connect to Cosmos DB
        try:
            self.cosmos_client.connect()
            print("✓ Connected to Cosmos DB\n")
        except Exception as e:
            print(f"✗ Failed to connect to Cosmos DB: {e}\n")
            return
        
        # Collect all metrics
        await self.collect_database_metrics()
        await self.collect_rss_metrics()
        await self.collect_clustering_metrics()
        await self.collect_summarization_metrics()
        await self.collect_performance_metrics()
        
        # Collect test results if available
        self.collect_test_results()
        
        # Generate HTML report
        self.generate_html_report()
        
        # Print summary
        self.print_summary()
    
    async def collect_database_metrics(self):
        """Collect database health metrics"""
        print("Collecting database metrics...")
        
        try:
            articles_container = self.cosmos_client._get_container("raw_articles")
            stories_container = self.cosmos_client._get_container("story_clusters")
            
            # Total counts
            total_articles = list(articles_container.query_items(
                query="SELECT VALUE COUNT(1) FROM c",
                enable_cross_partition_query=True
            ))[0]
            
            total_stories = list(stories_container.query_items(
                query="SELECT VALUE COUNT(1) FROM c",
                enable_cross_partition_query=True
            ))[0]
            
            # Recent counts
            one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
            
            recent_articles = list(articles_container.query_items(
                query=f"SELECT VALUE COUNT(1) FROM c WHERE c.fetched_at >= '{one_hour_ago}'",
                enable_cross_partition_query=True
            ))[0]
            
            recent_stories = list(stories_container.query_items(
                query=f"SELECT VALUE COUNT(1) FROM c WHERE c.first_seen >= '{one_hour_ago}'",
                enable_cross_partition_query=True
            ))[0]
            
            self.report_data['database'] = {
                'total_articles': total_articles,
                'total_stories': total_stories,
                'articles_last_hour': recent_articles,
                'stories_last_hour': recent_stories,
                'health': 'healthy' if total_articles > 0 and total_stories > 0 else 'unhealthy'
            }
            
            print(f"  Total articles: {total_articles}")
            print(f"  Total stories: {total_stories}")
            print(f"  Articles (last hour): {recent_articles}")
            print(f"  Stories (last hour): {recent_stories}\n")
            
        except Exception as e:
            print(f"  Error: {e}\n")
            self.report_data['database'] = {'health': 'error', 'error': str(e)}
    
    async def collect_rss_metrics(self):
        """Collect RSS ingestion metrics"""
        print("Collecting RSS ingestion metrics...")
        
        try:
            container = self.cosmos_client._get_container("raw_articles")
            
            # Recent activity
            ten_minutes_ago = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
            
            recent_query = f"SELECT c.source, c.fetched_at FROM c WHERE c.fetched_at >= '{ten_minutes_ago}'"
            recent_articles = list(container.query_items(
                query=recent_query,
                enable_cross_partition_query=True
            ))
            
            # Source diversity
            from collections import Counter
            sources = [article['source'] for article in recent_articles]
            source_counts = Counter(sources)
            
            # Polling rate
            articles_per_minute = len(recent_articles) / 10
            
            self.report_data['rss'] = {
                'articles_last_10_min': len(recent_articles),
                'articles_per_minute': articles_per_minute,
                'unique_sources': len(source_counts),
                'top_sources': source_counts.most_common(5),
                'health': 'healthy' if articles_per_minute >= 5 else 'degraded'
            }
            
            print(f"  Articles (last 10 min): {len(recent_articles)}")
            print(f"  Articles per minute: {articles_per_minute:.1f}")
            print(f"  Unique sources: {len(source_counts)}\n")
            
        except Exception as e:
            print(f"  Error: {e}\n")
            self.report_data['rss'] = {'health': 'error', 'error': str(e)}
    
    async def collect_clustering_metrics(self):
        """Collect clustering quality metrics"""
        print("Collecting clustering metrics...")
        
        try:
            container = self.cosmos_client._get_container("story_clusters")
            
            # Get recent stories
            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            
            query = f"SELECT c.source_articles, c.status FROM c WHERE c.last_updated >= '{yesterday}'"
            stories = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            # Calculate metrics
            from collections import Counter
            
            source_counts = []
            status_counts = Counter()
            
            for story in stories:
                source_articles = story.get('source_articles', [])
                source_counts.append(len(source_articles))
                status_counts[story.get('status', 'UNKNOWN')] += 1
            
            avg_sources = sum(source_counts) / len(source_counts) if source_counts else 0
            multi_source_rate = sum(1 for count in source_counts if count >= 2) / len(source_counts) * 100 if source_counts else 0
            
            self.report_data['clustering'] = {
                'stories_last_24h': len(stories),
                'avg_sources_per_story': avg_sources,
                'multi_source_rate': multi_source_rate,
                'status_distribution': dict(status_counts),
                'health': 'healthy' if multi_source_rate >= 20 else 'degraded'
            }
            
            print(f"  Stories (last 24h): {len(stories)}")
            print(f"  Avg sources per story: {avg_sources:.2f}")
            print(f"  Multi-source rate: {multi_source_rate:.1f}%\n")
            
        except Exception as e:
            print(f"  Error: {e}\n")
            self.report_data['clustering'] = {'health': 'error', 'error': str(e)}
    
    async def collect_summarization_metrics(self):
        """Collect AI summarization metrics"""
        print("Collecting summarization metrics...")
        
        try:
            container = self.cosmos_client._get_container("story_clusters")
            
            # Total stories
            total_stories = list(container.query_items(
                query="SELECT VALUE COUNT(1) FROM c",
                enable_cross_partition_query=True
            ))[0]
            
            # Stories with summaries
            with_summaries = list(container.query_items(
                query="SELECT VALUE COUNT(1) FROM c WHERE IS_DEFINED(c.summary) AND c.summary.text != null AND c.summary.text != ''",
                enable_cross_partition_query=True
            ))[0]
            
            coverage = (with_summaries / total_stories * 100) if total_stories > 0 else 0
            
            # Recent summaries
            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            
            query = f"""
                SELECT c.summary
                FROM c 
                WHERE IS_DEFINED(c.summary)
                AND c.summary.generated_at >= '{yesterday}'
            """
            recent_summaries = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            # Calculate average metrics
            generation_times = []
            costs = []
            word_counts = []
            
            for item in recent_summaries:
                summary = item.get('summary', {})
                if summary.get('generation_time_ms'):
                    generation_times.append(summary['generation_time_ms'])
                if summary.get('cost_usd'):
                    costs.append(summary['cost_usd'])
                if summary.get('word_count'):
                    word_counts.append(summary['word_count'])
            
            avg_generation_time = (sum(generation_times) / len(generation_times)) if generation_times else 0
            total_cost_24h = sum(costs) if costs else 0
            avg_word_count = (sum(word_counts) / len(word_counts)) if word_counts else 0
            
            self.report_data['summarization'] = {
                'coverage': coverage,
                'summaries_24h': len(recent_summaries),
                'avg_generation_time_ms': avg_generation_time,
                'avg_word_count': avg_word_count,
                'cost_24h': total_cost_24h,
                'health': 'healthy' if coverage >= 30 else 'degraded'
            }
            
            print(f"  Coverage: {coverage:.1f}%")
            print(f"  Summaries (24h): {len(recent_summaries)}")
            print(f"  Avg generation time: {avg_generation_time:.0f}ms")
            print(f"  Cost (24h): ${total_cost_24h:.2f}\n")
            
        except Exception as e:
            print(f"  Error: {e}\n")
            self.report_data['summarization'] = {'health': 'error', 'error': str(e)}
    
    async def collect_performance_metrics(self):
        """Collect performance metrics"""
        print("Collecting performance metrics...")
        
        try:
            # This would integrate with Application Insights in production
            # For now, we'll use database metrics as a proxy
            
            container = self.cosmos_client._get_container("raw_articles")
            
            # Check processing lag
            query = "SELECT VALUE COUNT(1) FROM c WHERE c.processed = false"
            unprocessed = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))[0]
            
            self.report_data['performance'] = {
                'unprocessed_articles': unprocessed,
                'health': 'healthy' if unprocessed < 1000 else 'degraded'
            }
            
            print(f"  Unprocessed articles: {unprocessed}\n")
            
        except Exception as e:
            print(f"  Error: {e}\n")
            self.report_data['performance'] = {'health': 'error', 'error': str(e)}
    
    def collect_test_results(self):
        """Collect test results from last runs"""
        print("Collecting test results...")
        
        test_results = {}
        test_dir = os.path.join(os.path.dirname(__file__), '..')
        
        # Check for pytest JSON report
        json_report = os.path.join(test_dir, 'reports', 'test_results.json')
        if os.path.exists(json_report):
            try:
                with open(json_report, 'r') as f:
                    test_results['last_run'] = json.load(f)
                    print(f"  ✓ Found test results: {test_results['last_run'].get('total', 0)} tests")
            except Exception as e:
                print(f"  ⚠ Could not read test results: {e}")
        else:
            print(f"  ℹ No test results found (run tests to generate)")
        
        # Check test directories
        test_results['unit_tests_available'] = os.path.exists(os.path.join(test_dir, 'unit'))
        test_results['integration_tests_available'] = os.path.exists(os.path.join(test_dir, 'integration'))
        
        self.report_data['tests'] = test_results
        print()
    
    def _generate_test_results_section(self):
        """Generate test results HTML section"""
        tests = self.report_data.get('tests', {})
        last_run = tests.get('last_run', {})
        
        if not last_run:
            return '''
            <div class="test-results">
                <p><strong>ℹ️ No test results available</strong></p>
                <p>Run tests using the buttons above to see results here.</p>
                <div class="code-block">
                # Quick start:
                cd Azure/tests
                pytest unit/ -v --json-report --json-report-file=reports/test_results.json
                </div>
            </div>
            '''
        
        total = last_run.get('total', 0)
        passed = last_run.get('passed', 0)
        failed = last_run.get('failed', 0)
        duration = last_run.get('duration', 0)
        timestamp = last_run.get('timestamp', 'Unknown')
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        status_class = 'test-passed' if failed == 0 else 'test-failed'
        status_icon = '✅' if failed == 0 else '❌'
        
        return f'''
        <div class="test-results">
            <p><strong>{status_icon} Last Test Run:</strong> {timestamp}</p>
            <p class="{status_class}">
                <strong>{passed}/{total} tests passed</strong> ({pass_rate:.1f}%)
                {f"<span class='test-failed'> | {failed} failed</span>" if failed > 0 else ""}
            </p>
            <p>Duration: {duration:.2f}s</p>
        </div>
        '''
    
    def generate_html_report(self):
        """Generate HTML report"""
        print("Generating HTML report...")
        
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="30">
    <title>Newsreel API Health Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1a73e8;
            border-bottom: 3px solid #1a73e8;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #333;
            margin-top: 30px;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #1a73e8;
        }}
        .metric-card.healthy {{
            border-left-color: #34a853;
        }}
        .metric-card.degraded {{
            border-left-color: #fbbc04;
        }}
        .metric-card.error {{
            border-left-color: #ea4335;
        }}
        .metric-label {{
            color: #666;
            font-size: 14px;
            margin-bottom: 5px;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .status-healthy {{
            background: #e8f5e9;
            color: #2e7d32;
        }}
        .status-degraded {{
            background: #fff8e1;
            color: #f57f17;
        }}
        .status-error {{
            background: #ffebee;
            color: #c62828;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        .timestamp {{
            color: #666;
            font-size: 14px;
        }}
        .auto-refresh {{
            display: inline-block;
            margin-left: 15px;
            padding: 4px 12px;
            background: #e3f2fd;
            color: #1565c0;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }}
        .test-section {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .button-group {{
            display: flex;
            gap: 10px;
            margin: 15px 0;
            flex-wrap: wrap;
        }}
        .btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            transition: all 0.2s;
        }}
        .btn-primary {{
            background: #2196f3;
            color: white;
        }}
        .btn-primary:hover {{
            background: #1976d2;
        }}
        .btn-success {{
            background: #4caf50;
            color: white;
        }}
        .btn-success:hover {{
            background: #388e3c;
        }}
        .btn-secondary {{
            background: #757575;
            color: white;
        }}
        .btn-secondary:hover {{
            background: #616161;
        }}
        .test-results {{
            background: #f8f9fa;
            border-radius: 4px;
            padding: 15px;
            margin-top: 15px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 13px;
        }}
        .test-passed {{
            color: #2e7d32;
        }}
        .test-failed {{
            color: #c62828;
        }}
        .code-block {{
            background: #263238;
            color: #aed581;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 13px;
            margin: 10px 0;
        }}
        .btn-danger {{
            background: #d32f2f;
            color: white;
        }}
        .btn-danger:hover {{
            background: #b71c1c;
        }}
        .btn-warning {{
            background: #f57c00;
            color: white;
        }}
        .btn-warning:hover {{
            background: #e65100;
        }}
        .cleanup-section {{
            background: #fff3e0;
            border: 2px solid #f57c00;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        .warning-text {{
            color: #d32f2f;
            font-weight: 600;
            margin: 10px 0;
        }}
    </style>
    <script>
        function copyCommand(command) {{
            navigator.clipboard.writeText(command).then(function() {{
                alert('Command copied to clipboard!\\n\\nPaste it in your terminal to run.');
            }}, function(err) {{
                alert('Could not copy command: ' + err);
            }});
        }}
        
        function showInstructions(type) {{
            const basePath = 'cd ~/Library/CloudStorage/OneDrive-OneThumSoftware/One\\\\ Thum\\\\ Software/Newsreel/Azure/tests';
            const instructions = {{
                'unit': basePath + ' && pytest unit/ -v --json-report --json-report-file=reports/.report.json && python3 scripts/save_test_results.py',
                'integration': basePath + ' && pytest integration/ -v --json-report --json-report-file=reports/.report.json && python3 scripts/save_test_results.py',
                'all': basePath + ' && pytest -v --json-report --json-report-file=reports/.report.json && python3 scripts/save_test_results.py',
                'diagnostics': basePath + ' && ./run_all_diagnostics.sh'
            }};
            
            const command = instructions[type];
            if (command) {{
                if (confirm('Copy this command to clipboard?\\n\\n' + command)) {{
                    copyCommand(command);
                }}
            }}
        }}
        
        function showCleanupCommand(type) {{
            const basePath = 'cd ~/Library/CloudStorage/OneDrive-OneThumSoftware/One\\\\ Thum\\\\ Software/Newsreel/Azure/tests';
            const commands = {{
                'cleanup_all': basePath + ' && python3 scripts/cleanup_all_articles.py',
                'cleanup_old': basePath + ' && python3 scripts/cleanup_old_articles.py'
            }};
            
            const warnings = {{
                'cleanup_all': '⚠️  EXTREME CAUTION ⚠️\\n\\nThis will DELETE ALL ARTICLES from Cosmos DB!\\n\\nThis operation is PERMANENT and CANNOT BE UNDONE!\\n\\nYou will be asked for multiple confirmations before deletion.\\n\\nAre you sure you want to copy this command?',
                'cleanup_old': '⚠️  WARNING ⚠️\\n\\nThis will delete all articles EXCEPT those from the last hour.\\n\\nThis operation is PERMANENT and CANNOT BE UNDONE!\\n\\nYou will be asked for confirmation before deletion.\\n\\nCopy this command?'
            }};
            
            if (confirm(warnings[type])) {{
                copyCommand(commands[type]);
                alert('Command copied!\\n\\nIMPORTANT: Read all prompts carefully before confirming deletion.');
            }}
        }}
    </script>
</head>
<body>
    <div class="container">
        <h1>Newsreel API Health Report</h1>
        <p class="timestamp">Generated: {timestamp} <span class="auto-refresh">🔄 Auto-refreshes every 30s</span></p>
        
        <h2>System Overview</h2>
        <div class="metric-grid">
            <div class="metric-card {self.report_data['database'].get('health', 'error')}">
                <div class="metric-label">Total Articles</div>
                <div class="metric-value">{self.report_data['database'].get('total_articles', 0):,}</div>
            </div>
            <div class="metric-card {self.report_data['database'].get('health', 'error')}">
                <div class="metric-label">Total Stories</div>
                <div class="metric-value">{self.report_data['database'].get('total_stories', 0):,}</div>
            </div>
            <div class="metric-card {self.report_data['summarization'].get('health', 'error')}">
                <div class="metric-label">Summary Coverage</div>
                <div class="metric-value">{self.report_data['summarization'].get('coverage', 0):.1f}%</div>
            </div>
            <div class="metric-card {self.report_data['clustering'].get('health', 'error')}">
                <div class="metric-label">Multi-Source Rate</div>
                <div class="metric-value">{self.report_data['clustering'].get('multi_source_rate', 0):.1f}%</div>
            </div>
        </div>
        
        <h2>Component Health</h2>
        <table>
            <tr>
                <th>Component</th>
                <th>Status</th>
                <th>Key Metric</th>
            </tr>
            <tr>
                <td>Database</td>
                <td><span class="status-badge status-{self.report_data['database'].get('health', 'error')}">{self.report_data['database'].get('health', 'error')}</span></td>
                <td>{self.report_data['database'].get('articles_last_hour', 0)} articles/hour</td>
            </tr>
            <tr>
                <td>RSS Ingestion</td>
                <td><span class="status-badge status-{self.report_data['rss'].get('health', 'error')}">{self.report_data['rss'].get('health', 'error')}</span></td>
                <td>{self.report_data['rss'].get('articles_per_minute', 0):.1f} articles/min</td>
            </tr>
            <tr>
                <td>Story Clustering</td>
                <td><span class="status-badge status-{self.report_data['clustering'].get('health', 'error')}">{self.report_data['clustering'].get('health', 'error')}</span></td>
                <td>{self.report_data['clustering'].get('avg_sources_per_story', 0):.2f} avg sources</td>
            </tr>
            <tr>
                <td>AI Summarization</td>
                <td><span class="status-badge status-{self.report_data['summarization'].get('health', 'error')}">{self.report_data['summarization'].get('health', 'error')}</span></td>
                <td>{self.report_data['summarization'].get('summaries_24h', 0)} summaries/day</td>
            </tr>
        </table>
        
        <h2>RSS Ingestion Details</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Articles (10 min)</div>
                <div class="metric-value">{self.report_data['rss'].get('articles_last_10_min', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Unique Sources</div>
                <div class="metric-value">{self.report_data['rss'].get('unique_sources', 0)}</div>
            </div>
        </div>
        
        <h2>Clustering Quality</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Stories (24h)</div>
                <div class="metric-value">{self.report_data['clustering'].get('stories_last_24h', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Avg Sources/Story</div>
                <div class="metric-value">{self.report_data['clustering'].get('avg_sources_per_story', 0):.2f}</div>
            </div>
        </div>
        
        <h2>AI Summarization</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Generation Time</div>
                <div class="metric-value">{self.report_data['summarization'].get('avg_generation_time_ms', 0):.0f}ms</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Cost (24h)</div>
                <div class="metric-value">${self.report_data['summarization'].get('cost_24h', 0):.2f}</div>
            </div>
        </div>
        
        <div class="test-section">
            <h2>🧪 Test Suite</h2>
            <p>Run tests to verify system functionality and update this report with results.</p>
            
            <div class="button-group">
                <button class="btn btn-primary" onclick="showInstructions('diagnostics')">
                    🔍 Run Diagnostics
                </button>
                <button class="btn btn-success" onclick="showInstructions('unit')">
                    ⚙️ Run Unit Tests
                </button>
                <button class="btn btn-success" onclick="showInstructions('integration')">
                    🔗 Run Integration Tests
                </button>
                <button class="btn btn-secondary" onclick="showInstructions('all')">
                    🚀 Run All Tests
                </button>
            </div>
            
            {self._generate_test_results_section()}
        </div>
        
        <div class="cleanup-section">
            <h2>🗑️ Database Cleanup</h2>
            <p class="warning-text">⚠️  DESTRUCTIVE OPERATIONS - USE WITH EXTREME CAUTION</p>
            <p>These operations permanently delete articles from Cosmos DB. They cannot be undone!</p>
            
            <div class="button-group">
                <button class="btn btn-warning" onclick="showCleanupCommand('cleanup_old')">
                    🧹 Delete Old Articles (Keep Last Hour)
                </button>
                <button class="btn btn-danger" onclick="showCleanupCommand('cleanup_all')">
                    ⚠️ DELETE ALL ARTICLES
                </button>
            </div>
            
            <div style="margin-top: 15px; padding: 10px; background: white; border-radius: 4px; font-size: 13px;">
                <p><strong>What these do:</strong></p>
                <ul>
                    <li><strong>Delete Old Articles:</strong> Removes all articles except those ingested in the last hour. Useful for maintaining a small test dataset.</li>
                    <li><strong>DELETE ALL ARTICLES:</strong> Removes EVERY article from the database. Only use this if you want to completely reset the system.</li>
                </ul>
                <p style="color: #d32f2f;"><strong>⚠️  Both operations require confirmation prompts before executing.</strong></p>
            </div>
        </div>
        
        <h2>📊 Raw Data</h2>
        <pre style="background: #f8f9fa; padding: 15px; border-radius: 4px; overflow-x: auto;">
{json.dumps(self.report_data, indent=2)}
        </pre>
    </div>
</body>
</html>
"""
        
        # Save report
        report_path = os.path.join(os.path.dirname(__file__), '../reports/health_report.html')
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w') as f:
            f.write(html)
        
        print(f"✓ Report saved to: {report_path}\n")
    
    def print_summary(self):
        """Print summary to console"""
        print("="*80)
        print("SYSTEM HEALTH SUMMARY")
        print("="*80)
        
        # Count health statuses
        components = ['database', 'rss', 'clustering', 'summarization', 'performance']
        healthy = sum(1 for c in components if self.report_data.get(c, {}).get('health') == 'healthy')
        total = len(components)
        
        print(f"\nHealthy components: {healthy}/{total}")
        
        for component in components:
            health = self.report_data.get(component, {}).get('health', 'unknown')
            icon = "✓" if health == 'healthy' else "⚠" if health == 'degraded' else "✗"
            print(f"  {icon} {component.upper()}: {health}")
        
        print("\n" + "="*80)


async def main():
    """Main entry point"""
    reporter = SystemHealthReporter()
    await reporter.generate_report()


if __name__ == "__main__":
    asyncio.run(main())

