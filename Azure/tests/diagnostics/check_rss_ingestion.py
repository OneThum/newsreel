#!/usr/bin/env python3
"""
RSS Ingestion Health Checker

Checks the health and performance of RSS ingestion:
- Are feeds being polled every 10 seconds?
- Are we polling 3 feeds per cycle?
- Are articles being stored correctly?
- What's the success rate per feed?
- Are there any bottlenecks or errors?
"""
import os
import sys
import asyncio
from datetime import datetime, timezone, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Any
from dotenv import load_dotenv
from colorama import Fore, Style, init
from tabulate import tabulate

# Initialize colorama for colored output
init(autoreset=True)

# Add functions to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../functions')))

load_dotenv()

from shared.config import config
from shared.cosmos_client import CosmosDBClient


class RSSIngestionChecker:
    """Check RSS ingestion health"""
    
    def __init__(self):
        self.cosmos_client = CosmosDBClient()
        self.results = {}
    
    async def check_all(self):
        """Run all checks"""
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}RSS INGESTION HEALTH CHECK")
        print(f"{Fore.CYAN}{'='*80}\n")
        
        print(f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        
        # Connect to Cosmos DB
        try:
            self.cosmos_client.connect()
            print(f"{Fore.GREEN}✓ Connected to Cosmos DB\n")
        except Exception as e:
            print(f"{Fore.RED}✗ Failed to connect to Cosmos DB: {e}\n")
            return
        
        # Run checks
        await self.check_recent_articles()
        await self.check_polling_rate()
        await self.check_feed_distribution()
        await self.check_article_quality()
        await self.check_processing_lag()
        await self.check_feed_errors()
        
        # Print summary
        self.print_summary()
    
    async def check_recent_articles(self):
        """Check if articles are being ingested recently"""
        print(f"{Fore.YELLOW}1. Checking Recent Article Ingestion...")
        print(f"   {'-'*70}")
        
        try:
            container = self.cosmos_client._get_container("raw_articles")
            
            # Check last hour
            one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
            
            query = f"SELECT VALUE COUNT(1) FROM c WHERE c.fetched_at >= '{one_hour_ago}'"
            result = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            articles_last_hour = result[0] if result else 0
            
            # Check last 10 minutes
            ten_minutes_ago = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
            query = f"SELECT VALUE COUNT(1) FROM c WHERE c.fetched_at >= '{ten_minutes_ago}'"
            result = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            articles_last_10_min = result[0] if result else 0
            
            # Get most recent article
            query = "SELECT TOP 1 c.id, c.source, c.title, c.fetched_at FROM c ORDER BY c.fetched_at DESC"
            recent_articles = list(container.query_items(
                query=query,
                enable_cross_partition_query=True,
                max_item_count=1
            ))
            
            if recent_articles:
                most_recent = recent_articles[0]
                fetched_at = datetime.fromisoformat(most_recent['fetched_at'].replace('Z', '+00:00'))
                time_since = (datetime.now(timezone.utc) - fetched_at).total_seconds()
                
                print(f"   Articles in last hour: {Fore.GREEN if articles_last_hour > 0 else Fore.RED}{articles_last_hour}")
                print(f"   Articles in last 10 minutes: {Fore.GREEN if articles_last_10_min > 0 else Fore.RED}{articles_last_10_min}")
                print(f"   Most recent article:")
                print(f"     - Source: {most_recent['source']}")
                print(f"     - Title: {most_recent['title'][:60]}...")
                print(f"     - Fetched: {int(time_since)} seconds ago")
                
                # Health check
                if time_since < 60:
                    print(f"   {Fore.GREEN}✓ RSS ingestion is active (articles within last minute)")
                    self.results['ingestion_active'] = True
                elif time_since < 300:
                    print(f"   {Fore.YELLOW}⚠ RSS ingestion may be slow (last article {int(time_since)}s ago)")
                    self.results['ingestion_active'] = 'slow'
                else:
                    print(f"   {Fore.RED}✗ RSS ingestion appears stalled (last article {int(time_since/60):.1f} minutes ago)")
                    self.results['ingestion_active'] = False
            else:
                print(f"   {Fore.RED}✗ No articles found in database")
                self.results['ingestion_active'] = False
            
            print()
            
        except Exception as e:
            print(f"   {Fore.RED}✗ Error checking recent articles: {e}\n")
            self.results['ingestion_active'] = 'error'
    
    async def check_polling_rate(self):
        """Check if feeds are being polled at the correct rate"""
        print(f"{Fore.YELLOW}2. Checking Polling Rate...")
        print(f"   {'-'*70}")
        
        try:
            container = self.cosmos_client._get_container("raw_articles")
            
            # Get articles from last 5 minutes to analyze polling pattern
            five_minutes_ago = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
            
            query = f"SELECT c.source, c.fetched_at FROM c WHERE c.fetched_at >= '{five_minutes_ago}'"
            articles = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            if not articles:
                print(f"   {Fore.RED}✗ No articles in last 5 minutes - ingestion not working")
                print()
                return
            
            # Analyze polling intervals
            sources_by_minute = defaultdict(list)
            for article in articles:
                fetched_at = datetime.fromisoformat(article['fetched_at'].replace('Z', '+00:00'))
                minute_bucket = fetched_at.strftime('%Y-%m-%d %H:%M')
                sources_by_minute[minute_bucket].append(article['source'])
            
            # Calculate articles per minute
            articles_per_minute = [len(sources) for sources in sources_by_minute.values()]
            avg_per_minute = sum(articles_per_minute) / len(articles_per_minute) if articles_per_minute else 0
            
            print(f"   Total articles in last 5 minutes: {len(articles)}")
            print(f"   Average articles per minute: {avg_per_minute:.1f}")
            print(f"   Expected (3 feeds * 6 cycles/min): ~18 articles/min")
            
            # Expected: 3 feeds per 10-second cycle = 18 feeds per minute
            # But with 3-minute cooldown, actual rate will be lower
            # More realistic: ~10-15 articles per minute with overlapping cycles
            
            if avg_per_minute >= 10:
                print(f"   {Fore.GREEN}✓ Polling rate is healthy")
                self.results['polling_rate'] = 'healthy'
            elif avg_per_minute >= 5:
                print(f"   {Fore.YELLOW}⚠ Polling rate is below expected (may be ok with cooldowns)")
                self.results['polling_rate'] = 'slow'
            else:
                print(f"   {Fore.RED}✗ Polling rate is very low - check function configuration")
                self.results['polling_rate'] = 'low'
            
            # Show per-minute breakdown
            print(f"\n   Per-minute breakdown:")
            for minute, sources in sorted(sources_by_minute.items())[-5:]:  # Last 5 minutes
                unique_sources = len(set(sources))
                print(f"     {minute}: {len(sources)} articles from {unique_sources} unique sources")
            
            print()
            
        except Exception as e:
            print(f"   {Fore.RED}✗ Error checking polling rate: {e}\n")
            self.results['polling_rate'] = 'error'
    
    async def check_feed_distribution(self):
        """Check which feeds are being polled and their distribution"""
        print(f"{Fore.YELLOW}3. Checking Feed Distribution...")
        print(f"   {'-'*70}")
        
        try:
            container = self.cosmos_client._get_container("raw_articles")
            
            # Get articles from last hour
            one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
            
            query = f"SELECT c.source FROM c WHERE c.fetched_at >= '{one_hour_ago}'"
            articles = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            if not articles:
                print(f"   {Fore.RED}✗ No articles to analyze")
                print()
                return
            
            # Count articles per source
            source_counts = Counter([article['source'] for article in articles])
            
            print(f"   Total unique sources: {len(source_counts)}")
            print(f"   Total articles: {len(articles)}")
            print(f"\n   Top 10 sources (last hour):")
            
            # Create table
            table_data = []
            for source, count in source_counts.most_common(10):
                percentage = (count / len(articles)) * 100
                table_data.append([source, count, f"{percentage:.1f}%"])
            
            print(tabulate(table_data, headers=["Source", "Articles", "% of Total"], tablefmt="simple"))
            
            # Check for source diversity
            unique_sources = len(source_counts)
            if unique_sources >= 10:
                print(f"\n   {Fore.GREEN}✓ Good source diversity ({unique_sources} sources)")
                self.results['source_diversity'] = 'good'
            elif unique_sources >= 5:
                print(f"\n   {Fore.YELLOW}⚠ Moderate source diversity ({unique_sources} sources)")
                self.results['source_diversity'] = 'moderate'
            else:
                print(f"\n   {Fore.RED}✗ Poor source diversity ({unique_sources} sources)")
                self.results['source_diversity'] = 'poor'
            
            # Check for dominance (one source > 50%)
            top_source_percentage = (source_counts.most_common(1)[0][1] / len(articles)) * 100
            if top_source_percentage > 50:
                print(f"   {Fore.YELLOW}⚠ Warning: Top source dominates ({top_source_percentage:.1f}%)")
            
            print()
            
        except Exception as e:
            print(f"   {Fore.RED}✗ Error checking feed distribution: {e}\n")
            self.results['source_diversity'] = 'error'
    
    async def check_article_quality(self):
        """Check quality of ingested articles"""
        print(f"{Fore.YELLOW}4. Checking Article Quality...")
        print(f"   {'-'*70}")
        
        try:
            container = self.cosmos_client._get_container("raw_articles")
            
            # Sample recent articles
            ten_minutes_ago = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
            
            query = f"""
                SELECT c.id, c.title, c.description, c.content, c.story_fingerprint
                FROM c 
                WHERE c.fetched_at >= '{ten_minutes_ago}'
            """
            articles = list(container.query_items(
                query=query,
                enable_cross_partition_query=True,
                max_item_count=100
            ))
            
            if not articles:
                print(f"   {Fore.YELLOW}⚠ No recent articles to analyze")
                print()
                return
            
            # Check article completeness
            complete_articles = 0
            articles_with_content = 0
            articles_with_fingerprint = 0
            
            for article in articles:
                has_title = bool(article.get('title'))
                has_description = bool(article.get('description'))
                has_content = bool(article.get('content'))
                has_fingerprint = bool(article.get('story_fingerprint'))
                
                if has_title and has_description:
                    complete_articles += 1
                if has_content:
                    articles_with_content += 1
                if has_fingerprint:
                    articles_with_fingerprint += 1
            
            completeness_rate = (complete_articles / len(articles)) * 100
            content_rate = (articles_with_content / len(articles)) * 100
            fingerprint_rate = (articles_with_fingerprint / len(articles)) * 100
            
            print(f"   Analyzed {len(articles)} recent articles:")
            print(f"   - Complete (title + description): {complete_articles}/{len(articles)} ({completeness_rate:.1f}%)")
            print(f"   - With content: {articles_with_content}/{len(articles)} ({content_rate:.1f}%)")
            print(f"   - With fingerprint: {articles_with_fingerprint}/{len(articles)} ({fingerprint_rate:.1f}%)")
            
            if completeness_rate >= 95:
                print(f"   {Fore.GREEN}✓ Article quality is good")
                self.results['article_quality'] = 'good'
            elif completeness_rate >= 80:
                print(f"   {Fore.YELLOW}⚠ Some articles missing data")
                self.results['article_quality'] = 'moderate'
            else:
                print(f"   {Fore.RED}✗ Many articles incomplete")
                self.results['article_quality'] = 'poor'
            
            print()
            
        except Exception as e:
            print(f"   {Fore.RED}✗ Error checking article quality: {e}\n")
            self.results['article_quality'] = 'error'
    
    async def check_processing_lag(self):
        """Check if articles are being processed by clustering"""
        print(f"{Fore.YELLOW}5. Checking Processing Lag...")
        print(f"   {'-'*70}")
        
        try:
            container = self.cosmos_client._get_container("raw_articles")
            
            # Check unprocessed articles
            query = "SELECT VALUE COUNT(1) FROM c WHERE c.processed = false"
            result = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            unprocessed_count = result[0] if result else 0
            
            # Get oldest unprocessed article
            query = """
                SELECT TOP 1 c.id, c.source, c.title, c.fetched_at
                FROM c 
                WHERE c.processed = false
                ORDER BY c.fetched_at ASC
            """
            oldest_unprocessed = list(container.query_items(
                query=query,
                enable_cross_partition_query=True,
                max_item_count=1
            ))
            
            print(f"   Unprocessed articles: {unprocessed_count}")
            
            if oldest_unprocessed:
                oldest = oldest_unprocessed[0]
                fetched_at = datetime.fromisoformat(oldest['fetched_at'].replace('Z', '+00:00'))
                lag_seconds = (datetime.now(timezone.utc) - fetched_at).total_seconds()
                
                print(f"   Oldest unprocessed article:")
                print(f"     - Source: {oldest['source']}")
                print(f"     - Title: {oldest['title'][:60]}...")
                print(f"     - Age: {int(lag_seconds)} seconds")
                
                if lag_seconds < 60:
                    print(f"   {Fore.GREEN}✓ Processing lag is minimal (<1 min)")
                    self.results['processing_lag'] = 'minimal'
                elif lag_seconds < 300:
                    print(f"   {Fore.YELLOW}⚠ Processing lag is moderate ({int(lag_seconds/60)} minutes)")
                    self.results['processing_lag'] = 'moderate'
                else:
                    print(f"   {Fore.RED}✗ Processing lag is high ({int(lag_seconds/60)} minutes)")
                    self.results['processing_lag'] = 'high'
            else:
                print(f"   {Fore.GREEN}✓ All articles are processed")
                self.results['processing_lag'] = 'none'
            
            print()
            
        except Exception as e:
            print(f"   {Fore.RED}✗ Error checking processing lag: {e}\n")
            self.results['processing_lag'] = 'error'
    
    async def check_feed_errors(self):
        """Check for feed errors or failures"""
        print(f"{Fore.YELLOW}6. Checking Feed Errors...")
        print(f"   {'-'*70}")
        
        try:
            # This would require Application Insights integration
            # For now, we'll check for patterns in data
            container = self.cosmos_client._get_container("raw_articles")
            
            # Check for sources that haven't updated recently
            one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
            
            query = f"SELECT DISTINCT VALUE c.source FROM c WHERE c.fetched_at >= '{one_hour_ago}'"
            active_sources = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            print(f"   Active sources in last hour: {len(active_sources)}")
            
            # Expected sources (would load from config in production)
            expected_sources = ['reuters', 'bbc', 'ap', 'cnn', 'nyt', 'guardian', 'bloomberg', 'wsj', 'ft', 'economist']
            
            missing_sources = set(expected_sources) - set(active_sources)
            
            if missing_sources:
                print(f"   {Fore.YELLOW}⚠ Some expected sources not seen recently:")
                for source in missing_sources:
                    print(f"     - {source}")
                self.results['feed_errors'] = 'some_missing'
            else:
                print(f"   {Fore.GREEN}✓ All expected major sources are active")
                self.results['feed_errors'] = 'none'
            
            print()
            
        except Exception as e:
            print(f"   {Fore.RED}✗ Error checking feed errors: {e}\n")
            self.results['feed_errors'] = 'error'
    
    def print_summary(self):
        """Print summary of all checks"""
        print(f"{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}SUMMARY")
        print(f"{Fore.CYAN}{'='*80}\n")
        
        # Overall health
        issues = sum(1 for v in self.results.values() if v in [False, 'error', 'poor', 'high', 'low'])
        warnings = sum(1 for v in self.results.values() if v in ['slow', 'moderate', 'some_missing'])
        
        if issues == 0 and warnings == 0:
            print(f"{Fore.GREEN}✓ RSS ingestion is healthy - all checks passed")
        elif issues == 0:
            print(f"{Fore.YELLOW}⚠ RSS ingestion has minor issues - {warnings} warnings")
        else:
            print(f"{Fore.RED}✗ RSS ingestion has problems - {issues} failures, {warnings} warnings")
        
        print(f"\nCheck results:")
        for check, result in self.results.items():
            if result in [True, 'healthy', 'good', 'minimal', 'none']:
                status = f"{Fore.GREEN}✓"
            elif result in ['slow', 'moderate', 'some_missing']:
                status = f"{Fore.YELLOW}⚠"
            else:
                status = f"{Fore.RED}✗"
            
            print(f"  {status} {check}: {result}")
        
        print()


async def main():
    """Main entry point"""
    checker = RSSIngestionChecker()
    await checker.check_all()


if __name__ == "__main__":
    asyncio.run(main())

