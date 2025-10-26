#!/usr/bin/env python3
"""
Story Clustering Quality Checker

Checks the quality of story clustering:
- Are articles being clustered correctly?
- Are duplicate sources being prevented?
- What's the false positive/negative rate?
- Are status transitions working properly?
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

init(autoreset=True)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../functions')))

load_dotenv()

from shared.config import config
from shared.cosmos_client import CosmosDBClient
from shared.utils import calculate_text_similarity


class ClusteringQualityChecker:
    """Check story clustering quality"""
    
    def __init__(self):
        self.cosmos_client = CosmosDBClient()
        self.results = {}
    
    async def check_all(self):
        """Run all checks"""
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}STORY CLUSTERING QUALITY CHECK")
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
        await self.check_story_creation_rate()
        await self.check_source_clustering()
        await self.check_duplicate_sources()
        await self.check_status_distribution()
        await self.check_clustering_accuracy()
        await self.check_fingerprint_collisions()
        
        # Print summary
        self.print_summary()
    
    async def check_story_creation_rate(self):
        """Check how many stories are being created"""
        print(f"{Fore.YELLOW}1. Checking Story Creation Rate...")
        print(f"   {'-'*70}")
        
        try:
            container = self.cosmos_client._get_container("story_clusters")
            
            # Stories created in last hour
            one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
            
            query = f"SELECT VALUE COUNT(1) FROM c WHERE c.first_seen >= '{one_hour_ago}'"
            result = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            stories_last_hour = result[0] if result else 0
            
            # Total stories
            query = "SELECT VALUE COUNT(1) FROM c"
            result = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            total_stories = result[0] if result else 0
            
            print(f"   Total stories in database: {total_stories}")
            print(f"   Stories created in last hour: {stories_last_hour}")
            
            # Expected rate: with 1900 articles/hour and ~50% clustering rate, ~900-1000 stories/hour
            # With better clustering (75% threshold), maybe 500-700 stories/hour
            
            if stories_last_hour > 0:
                print(f"   {Fore.GREEN}✓ Stories are being created")
                self.results['story_creation'] = 'active'
            else:
                print(f"   {Fore.RED}✗ No stories created in last hour")
                self.results['story_creation'] = 'inactive'
            
            print()
            
        except Exception as e:
            print(f"   {Fore.RED}✗ Error checking story creation: {e}\n")
            self.results['story_creation'] = 'error'
    
    async def check_source_clustering(self):
        """Check how articles are being clustered together"""
        print(f"{Fore.YELLOW}2. Checking Source Clustering...")
        print(f"   {'-'*70}")
        
        try:
            container = self.cosmos_client._get_container("story_clusters")
            
            # Get stories from last 24 hours
            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            
            query = f"SELECT c.id, c.source_articles, c.status FROM c WHERE c.last_updated >= '{yesterday}'"
            stories = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            if not stories:
                print(f"   {Fore.RED}✗ No recent stories to analyze")
                print()
                return
            
            # Analyze source counts
            source_counts = Counter()
            stories_by_source_count = defaultdict(int)
            
            for story in stories:
                source_articles = story.get('source_articles', [])
                num_sources = len(source_articles)
                source_counts[num_sources] += 1
                stories_by_source_count[num_sources] += 1
            
            print(f"   Analyzed {len(stories)} stories from last 24 hours:")
            print(f"\n   Stories by source count:")
            
            table_data = []
            for num_sources in sorted(stories_by_source_count.keys()):
                count = stories_by_source_count[num_sources]
                percentage = (count / len(stories)) * 100
                table_data.append([num_sources, count, f"{percentage:.1f}%"])
            
            print(tabulate(table_data, headers=["Sources", "Stories", "% of Total"], tablefmt="simple"))
            
            # Calculate statistics
            multi_source_stories = sum(count for num_sources, count in stories_by_source_count.items() if num_sources >= 2)
            multi_source_rate = (multi_source_stories / len(stories)) * 100 if stories else 0
            
            avg_sources = sum(num_sources * count for num_sources, count in stories_by_source_count.items()) / len(stories) if stories else 0
            
            print(f"\n   Multi-source stories: {multi_source_stories}/{len(stories)} ({multi_source_rate:.1f}%)")
            print(f"   Average sources per story: {avg_sources:.2f}")
            
            if multi_source_rate >= 30:
                print(f"   {Fore.GREEN}✓ Good clustering rate (≥30% multi-source)")
                self.results['clustering_rate'] = 'good'
            elif multi_source_rate >= 20:
                print(f"   {Fore.YELLOW}⚠ Moderate clustering rate (20-30% multi-source)")
                self.results['clustering_rate'] = 'moderate'
            else:
                print(f"   {Fore.RED}✗ Low clustering rate (<20% multi-source)")
                self.results['clustering_rate'] = 'low'
            
            print()
            
        except Exception as e:
            print(f"   {Fore.RED}✗ Error checking source clustering: {e}\n")
            self.results['clustering_rate'] = 'error'
    
    async def check_duplicate_sources(self):
        """Check for duplicate sources in stories"""
        print(f"{Fore.YELLOW}3. Checking for Duplicate Sources...")
        print(f"   {'-'*70}")
        
        try:
            container = self.cosmos_client._get_container("story_clusters")
            
            # Get recent stories with 2+ sources
            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            
            query = f"""
                SELECT c.id, c.title, c.source_articles
                FROM c 
                WHERE c.last_updated >= '{yesterday}'
                AND ARRAY_LENGTH(c.source_articles) >= 2
            """
            stories = list(container.query_items(
                query=query,
                enable_cross_partition_query=True,
                max_item_count=500
            ))
            
            if not stories:
                print(f"   {Fore.YELLOW}⚠ No multi-source stories to check")
                print()
                return
            
            # Check for duplicates
            stories_with_duplicates = []
            total_duplicate_count = 0
            
            for story in stories:
                source_articles = story.get('source_articles', [])
                
                # Extract sources
                sources = []
                for article in source_articles:
                    if isinstance(article, dict):
                        source = article.get('source', article.get('id', '').split('_')[0])
                    else:
                        source = article.split('_')[0]
                    sources.append(source)
                
                # Count duplicates
                source_counts = Counter(sources)
                duplicates = {source: count for source, count in source_counts.items() if count > 1}
                
                if duplicates:
                    stories_with_duplicates.append({
                        'id': story['id'],
                        'title': story.get('title', 'N/A')[:60],
                        'duplicates': duplicates,
                        'total_sources': len(sources),
                        'unique_sources': len(set(sources))
                    })
                    total_duplicate_count += sum(count - 1 for count in duplicates.values())
            
            print(f"   Analyzed {len(stories)} multi-source stories:")
            print(f"   Stories with duplicate sources: {len(stories_with_duplicates)}")
            print(f"   Total duplicate instances: {total_duplicate_count}")
            
            if len(stories_with_duplicates) > 0:
                duplicate_rate = (len(stories_with_duplicates) / len(stories)) * 100
                print(f"   Duplicate rate: {duplicate_rate:.1f}%")
                
                if duplicate_rate > 10:
                    print(f"   {Fore.RED}✗ High duplicate rate (>{10}%)")
                    self.results['duplicate_prevention'] = 'failing'
                elif duplicate_rate > 5:
                    print(f"   {Fore.YELLOW}⚠ Some duplicates found ({duplicate_rate:.1f}%)")
                    self.results['duplicate_prevention'] = 'partial'
                else:
                    print(f"   {Fore.GREEN}✓ Low duplicate rate (<5%)")
                    self.results['duplicate_prevention'] = 'working'
                
                # Show examples
                if stories_with_duplicates[:3]:
                    print(f"\n   Example stories with duplicates:")
                    for story in stories_with_duplicates[:3]:
                        print(f"     - {story['title']}...")
                        print(f"       ID: {story['id']}")
                        print(f"       Sources: {story['total_sources']} total, {story['unique_sources']} unique")
                        print(f"       Duplicates: {story['duplicates']}")
            else:
                print(f"   {Fore.GREEN}✓ No duplicate sources found")
                self.results['duplicate_prevention'] = 'working'
            
            print()
            
        except Exception as e:
            print(f"   {Fore.RED}✗ Error checking duplicates: {e}\n")
            self.results['duplicate_prevention'] = 'error'
    
    async def check_status_distribution(self):
        """Check distribution of story statuses"""
        print(f"{Fore.YELLOW}4. Checking Status Distribution...")
        print(f"   {'-'*70}")
        
        try:
            container = self.cosmos_client._get_container("story_clusters")
            
            # Get all story statuses
            query = "SELECT c.status FROM c"
            stories = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            if not stories:
                print(f"   {Fore.RED}✗ No stories found")
                print()
                return
            
            # Count by status
            status_counts = Counter([story.get('status', 'UNKNOWN') for story in stories])
            
            print(f"   Total stories: {len(stories)}")
            print(f"\n   Status distribution:")
            
            table_data = []
            for status in ['BREAKING', 'DEVELOPING', 'VERIFIED', 'MONITORING']:
                count = status_counts.get(status, 0)
                percentage = (count / len(stories)) * 100
                table_data.append([status, count, f"{percentage:.1f}%"])
            
            print(tabulate(table_data, headers=["Status", "Count", "% of Total"], tablefmt="simple"))
            
            # Check for unhealthy distributions
            monitoring_rate = (status_counts.get('MONITORING', 0) / len(stories)) * 100
            
            if monitoring_rate > 50:
                print(f"\n   {Fore.YELLOW}⚠ High percentage of MONITORING stories ({monitoring_rate:.1f}%)")
                print(f"   This suggests many single-source stories not being clustered")
                self.results['status_distribution'] = 'high_monitoring'
            elif monitoring_rate > 30:
                print(f"\n   {Fore.YELLOW}⚠ Moderate MONITORING stories ({monitoring_rate:.1f}%)")
                self.results['status_distribution'] = 'moderate'
            else:
                print(f"\n   {Fore.GREEN}✓ Healthy status distribution")
                self.results['status_distribution'] = 'healthy'
            
            print()
            
        except Exception as e:
            print(f"   {Fore.RED}✗ Error checking status distribution: {e}\n")
            self.results['status_distribution'] = 'error'
    
    async def check_clustering_accuracy(self):
        """Check clustering accuracy by sampling story matches"""
        print(f"{Fore.YELLOW}5. Checking Clustering Accuracy (Sample)...")
        print(f"   {'-'*70}")
        
        try:
            container = self.cosmos_client._get_container("story_clusters")
            
            # Get recent multi-source stories
            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            
            query = f"""
                SELECT TOP 20 c.id, c.title, c.source_articles
                FROM c 
                WHERE c.last_updated >= '{yesterday}'
                AND ARRAY_LENGTH(c.source_articles) >= 2
            """
            stories = list(container.query_items(
                query=query,
                enable_cross_partition_query=True,
                max_item_count=20
            ))
            
            if not stories:
                print(f"   {Fore.YELLOW}⚠ No recent multi-source stories to sample")
                print()
                return
            
            print(f"   Sampled {len(stories)} multi-source stories:")
            print(f"\n   Similarity analysis:")
            
            # For each story, fetch source articles and check similarity
            good_matches = 0
            questionable_matches = 0
            
            for story in stories[:5]:  # Check first 5 in detail
                story_title = story.get('title', 'N/A')
                source_articles = story.get('source_articles', [])
                
                if len(source_articles) < 2:
                    continue
                
                # Fetch first two source articles
                articles_container = self.cosmos_client._get_container("raw_articles")
                article_titles = []
                
                for article_ref in source_articles[:2]:
                    try:
                        if isinstance(article_ref, dict):
                            article_id = article_ref.get('id')
                        else:
                            article_id = article_ref
                        
                        # Extract partition key from ID
                        parts = article_id.split('_')
                        if len(parts) >= 2:
                            date_str = parts[1]
                            partition_key = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                            article = articles_container.read_item(item=article_id, partition_key=partition_key)
                            article_titles.append(article.get('title', ''))
                    except:
                        pass
                
                if len(article_titles) >= 2:
                    similarity = calculate_text_similarity(article_titles[0], article_titles[1])
                    
                    print(f"\n   Story: {story_title[:60]}...")
                    print(f"   Sources: {len(source_articles)}")
                    print(f"   Title similarity: {similarity:.3f}")
                    
                    if similarity >= 0.70:
                        print(f"   {Fore.GREEN}✓ Good match (≥0.70)")
                        good_matches += 1
                    elif similarity >= 0.50:
                        print(f"   {Fore.YELLOW}⚠ Questionable match (0.50-0.70)")
                        questionable_matches += 1
                    else:
                        print(f"   {Fore.RED}✗ Poor match (<0.50)")
            
            if good_matches >= 4:
                print(f"\n   {Fore.GREEN}✓ Clustering accuracy appears good")
                self.results['clustering_accuracy'] = 'good'
            elif good_matches >= 2:
                print(f"\n   {Fore.YELLOW}⚠ Clustering accuracy is moderate")
                self.results['clustering_accuracy'] = 'moderate'
            else:
                print(f"\n   {Fore.RED}✗ Clustering accuracy may be poor")
                self.results['clustering_accuracy'] = 'poor'
            
            print()
            
        except Exception as e:
            print(f"   {Fore.RED}✗ Error checking clustering accuracy: {e}\n")
            self.results['clustering_accuracy'] = 'error'
    
    async def check_fingerprint_collisions(self):
        """Check for fingerprint collisions"""
        print(f"{Fore.YELLOW}6. Checking Fingerprint Collisions...")
        print(f"   {'-'*70}")
        
        try:
            container = self.cosmos_client._get_container("story_clusters")
            
            # Get all fingerprints
            query = "SELECT c.event_fingerprint FROM c"
            stories = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            if not stories:
                print(f"   {Fore.RED}✗ No stories to check")
                print()
                return
            
            fingerprints = [story.get('event_fingerprint') for story in stories if story.get('event_fingerprint')]
            
            # Count duplicates
            fingerprint_counts = Counter(fingerprints)
            collisions = {fp: count for fp, count in fingerprint_counts.items() if count > 1}
            
            print(f"   Total stories: {len(stories)}")
            print(f"   Unique fingerprints: {len(fingerprint_counts)}")
            print(f"   Fingerprint collisions: {len(collisions)}")
            
            if collisions:
                total_collisions = sum(count - 1 for count in collisions.values())
                collision_rate = (total_collisions / len(stories)) * 100
                
                print(f"   Collision rate: {collision_rate:.2f}%")
                
                if collision_rate < 1:
                    print(f"   {Fore.GREEN}✓ Very low collision rate (<1%)")
                    self.results['fingerprint_collisions'] = 'low'
                elif collision_rate < 5:
                    print(f"   {Fore.YELLOW}⚠ Moderate collision rate (1-5%)")
                    self.results['fingerprint_collisions'] = 'moderate'
                else:
                    print(f"   {Fore.RED}✗ High collision rate (>5%)")
                    self.results['fingerprint_collisions'] = 'high'
            else:
                print(f"   {Fore.GREEN}✓ No fingerprint collisions")
                self.results['fingerprint_collisions'] = 'none'
            
            print()
            
        except Exception as e:
            print(f"   {Fore.RED}✗ Error checking fingerprint collisions: {e}\n")
            self.results['fingerprint_collisions'] = 'error'
    
    def print_summary(self):
        """Print summary of all checks"""
        print(f"{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}SUMMARY")
        print(f"{Fore.CYAN}{'='*80}\n")
        
        # Overall health
        issues = sum(1 for v in self.results.values() if v in ['inactive', 'error', 'poor', 'failing', 'low', 'high'])
        warnings = sum(1 for v in self.results.values() if v in ['moderate', 'partial', 'questionable', 'high_monitoring'])
        
        if issues == 0 and warnings == 0:
            print(f"{Fore.GREEN}✓ Story clustering is healthy - all checks passed")
        elif issues == 0:
            print(f"{Fore.YELLOW}⚠ Story clustering has minor issues - {warnings} warnings")
        else:
            print(f"{Fore.RED}✗ Story clustering has problems - {issues} failures, {warnings} warnings")
        
        print(f"\nCheck results:")
        for check, result in self.results.items():
            if result in ['active', 'working', 'good', 'healthy', 'none', 'low']:
                status = f"{Fore.GREEN}✓"
            elif result in ['moderate', 'partial', 'questionable', 'high_monitoring']:
                status = f"{Fore.YELLOW}⚠"
            else:
                status = f"{Fore.RED}✗"
            
            print(f"  {status} {check}: {result}")
        
        print()


async def main():
    """Main entry point"""
    checker = ClusteringQualityChecker()
    await checker.check_all()


if __name__ == "__main__":
    asyncio.run(main())

