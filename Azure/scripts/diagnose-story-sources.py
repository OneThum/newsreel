#!/usr/bin/env python3
"""
Diagnostic script to investigate story sources and duplicates

This script queries Cosmos DB directly to inspect:
1. Story cluster data (how many source_articles)
2. Raw article data (are there duplicate URLs?)
3. Source diversity (same source appearing multiple times?)
4. API response (what does the API actually return?)

Usage:
    python diagnose-story-sources.py <story_id>
    python diagnose-story-sources.py --latest  # Check latest BREAKING story
"""

import os
import sys
import json
from datetime import datetime, timezone
from collections import Counter
from azure.cosmos import CosmosClient
import requests

# Azure Cosmos DB configuration
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT", "https://newsreel-cosmos.documents.azure.com:443/")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = "newsreel_db"
CONTAINER_STORY_CLUSTERS = "story_clusters"
CONTAINER_RAW_ARTICLES = "raw_articles"

# API configuration
API_BASE_URL = "https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io"

# ANSI color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'


def print_header(text):
    """Print a section header"""
    print(f"\n{BOLD}{CYAN}{'='*80}{RESET}")
    print(f"{BOLD}{CYAN}{text}{RESET}")
    print(f"{BOLD}{CYAN}{'='*80}{RESET}\n")


def print_success(text):
    """Print success message"""
    print(f"{GREEN}✅ {text}{RESET}")


def print_warning(text):
    """Print warning message"""
    print(f"{YELLOW}⚠️  {text}{RESET}")


def print_error(text):
    """Print error message"""
    print(f"{RED}❌ {text}{RESET}")


def print_info(text):
    """Print info message"""
    print(f"{BLUE}ℹ️  {text}{RESET}")


def get_cosmos_client():
    """Initialize Cosmos DB client"""
    if not COSMOS_KEY:
        print_error("COSMOS_KEY environment variable not set")
        sys.exit(1)
    
    return CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)


def get_latest_breaking_story(client):
    """Get the latest BREAKING story"""
    database = client.get_database_client(DATABASE_NAME)
    container = database.get_container_client(CONTAINER_STORY_CLUSTERS)
    
    # Query without ORDER BY (Cosmos DB limitation)
    query = """
    SELECT * FROM c 
    WHERE c.status = 'BREAKING'
    """
    
    items = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    
    # Filter out feed_poll_state documents
    items = [item for item in items if item.get('doc_type') != 'feed_poll_state']
    
    if not items:
        print_error("No BREAKING stories found")
        sys.exit(1)
    
    # Sort in Python to get newest first
    items_sorted = sorted(items, key=lambda x: x.get('first_seen', ''), reverse=True)
    return items_sorted[0]


def get_story_cluster(client, story_id):
    """Get story cluster by ID"""
    database = client.get_database_client(DATABASE_NAME)
    container = database.get_container_client(CONTAINER_STORY_CLUSTERS)
    
    # Try to read directly (need partition key)
    # Partition key for stories is the date from the ID: story_YYYYMMDD_*
    try:
        parts = story_id.split('_')
        if len(parts) >= 2:
            date_str = parts[1]  # YYYYMMDD
            partition_key = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            
            try:
                story = container.read_item(item=story_id, partition_key=partition_key)
                return story
            except Exception:
                pass
    except Exception:
        pass
    
    # Fallback: query
    query = "SELECT * FROM c WHERE c.id = @story_id"
    items = list(container.query_items(
        query=query,
        parameters=[{"name": "@story_id", "value": story_id}],
        enable_cross_partition_query=True
    ))
    
    if not items:
        print_error(f"Story not found: {story_id}")
        sys.exit(1)
    
    return items[0]


def get_raw_articles(client, article_ids):
    """Get raw articles by IDs"""
    database = client.get_database_client(DATABASE_NAME)
    container = database.get_container_client(CONTAINER_RAW_ARTICLES)
    
    articles = []
    for article_id in article_ids:
        # Extract partition key from article ID
        # Format: source_YYYYMMDD_HHMMSS_hash or source_hash (new format)
        parts = article_id.split('_')
        
        if len(parts) >= 2 and len(parts[1]) == 8 and parts[1].isdigit():
            # Old format with timestamp: source_YYYYMMDD_*
            date_str = parts[1]
            partition_key = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        else:
            # New format without timestamp: source_hash
            # Use today's date as partition key (articles are ingested daily)
            today = datetime.now(timezone.utc)
            partition_key = today.strftime('%Y-%m-%d')
        
        try:
            article = container.read_item(item=article_id, partition_key=partition_key)
            articles.append(article)
        except Exception as e:
            # Try querying if direct read fails
            try:
                query = "SELECT * FROM c WHERE c.id = @article_id"
                items = list(container.query_items(
                    query=query,
                    parameters=[{"name": "@article_id", "value": article_id}],
                    enable_cross_partition_query=True,
                    max_item_count=1
                ))
                if items:
                    articles.append(items[0])
                else:
                    print_warning(f"Article not found: {article_id}")
            except Exception as e2:
                print_warning(f"Failed to fetch article {article_id}: {e2}")
    
    return articles


def check_api_response(story_id):
    """Check what the API returns for this story"""
    try:
        # Try the feed endpoint (returns sources)
        response = requests.get(
            f"{API_BASE_URL}/api/stories/feed?limit=100",
            timeout=10
        )
        response.raise_for_status()
        stories = response.json()
        
        # Find our story
        for story in stories:
            if story['id'] == story_id:
                return story
        
        print_warning(f"Story {story_id} not found in feed response")
        return None
        
    except Exception as e:
        print_error(f"Failed to fetch from API: {e}")
        return None


def analyze_story(story_id=None):
    """Analyze a story's sources for duplicates"""
    print_header(f"🔍 STORY SOURCE ANALYSIS")
    
    client = get_cosmos_client()
    
    # Get story
    if not story_id:
        print_info("No story ID provided, fetching latest BREAKING story...")
        story = get_latest_breaking_story(client)
        story_id = story['id']
        print_success(f"Found latest BREAKING story: {story_id}")
    else:
        story = get_story_cluster(client, story_id)
    
    print(f"\n{BOLD}Story:{RESET} {story.get('title', 'N/A')}")
    print(f"{BOLD}ID:{RESET} {story_id}")
    print(f"{BOLD}Status:{RESET} {story.get('status', 'N/A')}")
    print(f"{BOLD}First Seen:{RESET} {story.get('first_seen', 'N/A')}")
    print(f"{BOLD}Last Updated:{RESET} {story.get('last_updated', 'N/A')}")
    
    # Get source articles
    source_articles = story.get('source_articles', [])
    verification_level = story.get('verification_level', 0)
    
    print(f"\n{BOLD}Verification Level:{RESET} {verification_level}")
    print(f"{BOLD}Source Articles Count:{RESET} {len(source_articles)}")
    
    if len(source_articles) == 0:
        print_error("No source articles!")
        return
    
    # Fetch raw articles
    print_header("📰 FETCHING RAW ARTICLES")
    articles = get_raw_articles(client, source_articles)
    print_success(f"Fetched {len(articles)}/{len(source_articles)} articles")
    
    # Analyze sources
    print_header("🔍 SOURCE ANALYSIS")
    
    sources = [a.get('source', 'UNKNOWN') for a in articles]
    source_counts = Counter(sources)
    
    print(f"\n{BOLD}Unique Sources:{RESET} {len(source_counts)}")
    print(f"{BOLD}Total Articles:{RESET} {len(articles)}")
    
    # Check for duplicates
    duplicates = {k: v for k, v in source_counts.items() if v > 1}
    
    if duplicates:
        print_error(f"\n❌ DUPLICATES DETECTED! ({len(duplicates)} sources with duplicates)")
        print("\nDuplicate breakdown:")
        for source, count in sorted(duplicates.items(), key=lambda x: -x[1]):
            print(f"  {RED}{source}:{RESET} {count} times")
    else:
        print_success("\n✅ NO DUPLICATES - All sources unique!")
    
    # Show all sources
    print(f"\n{BOLD}All Sources:{RESET}")
    for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        if count > 1:
            print(f"  {RED}• {source} (×{count}){RESET}")
        else:
            print(f"  {GREEN}• {source}{RESET}")
    
    # Analyze URLs
    print_header("🔗 URL ANALYSIS")
    
    urls = [a.get('article_url', 'UNKNOWN') for a in articles]
    url_counts = Counter(urls)
    duplicate_urls = {k: v for k, v in url_counts.items() if v > 1}
    
    if duplicate_urls:
        print_error(f"❌ DUPLICATE URLs DETECTED! ({len(duplicate_urls)} URLs)")
        for url, count in sorted(duplicate_urls.items(), key=lambda x: -x[1])[:5]:
            print(f"  {count}×: {url}")
    else:
        print_success("✅ All URLs unique")
    
    # Show article details
    print_header("📋 ARTICLE DETAILS")
    
    # Group by source
    articles_by_source = {}
    for article in articles:
        source = article.get('source', 'UNKNOWN')
        if source not in articles_by_source:
            articles_by_source[source] = []
        articles_by_source[source].append(article)
    
    for source, source_articles_list in sorted(articles_by_source.items()):
        if len(source_articles_list) > 1:
            print(f"\n{RED}{BOLD}{source} ({len(source_articles_list)} articles):{RESET}")
        else:
            print(f"\n{GREEN}{BOLD}{source}:{RESET}")
        
        for i, article in enumerate(source_articles_list, 1):
            print(f"  [{i}] ID: {article.get('id')}")
            print(f"      Title: {article.get('title', 'N/A')[:80]}")
            print(f"      URL: {article.get('article_url', 'N/A')[:80]}")
            print(f"      Published: {article.get('published_at', 'N/A')}")
            if 'fetched_at' in article:
                print(f"      Fetched: {article.get('fetched_at', 'N/A')}")
            if 'updated_at' in article:
                print(f"      Updated: {article.get('updated_at', 'N/A')}")
    
    # Check API response
    print_header("🌐 API RESPONSE CHECK")
    
    api_story = check_api_response(story_id)
    if api_story:
        api_sources = api_story.get('sources', [])
        api_source_count = api_story.get('source_count', 0)
        
        print(f"{BOLD}API source_count field:{RESET} {api_source_count}")
        print(f"{BOLD}API sources array length:{RESET} {len(api_sources)}")
        
        if len(api_sources) == 0:
            print_error("❌ API returned EMPTY sources array!")
            print_warning("   This means the API is not including sources in the response")
        elif api_source_count != len(api_sources):
            print_warning(f"⚠️  Mismatch: source_count={api_source_count} but sources has {len(api_sources)} items")
        else:
            print_success("✅ API response looks correct")
        
        if api_sources:
            print(f"\n{BOLD}API Sources:{RESET}")
            api_source_names = [s.get('source', 'UNKNOWN') for s in api_sources]
            api_source_counts = Counter(api_source_names)
            
            api_duplicates = {k: v for k, v in api_source_counts.items() if v > 1}
            if api_duplicates:
                print_error(f"❌ API response has DUPLICATES! ({len(api_duplicates)} sources)")
                for source, count in sorted(api_duplicates.items(), key=lambda x: -x[1]):
                    print(f"  {RED}{source}: {count} times{RESET}")
            else:
                print_success(f"✅ All {len(api_source_counts)} sources unique in API response")
            
            # Show first 5
            print(f"\n{BOLD}First 5 sources in API response:{RESET}")
            for i, source in enumerate(api_sources[:5], 1):
                print(f"  [{i}] {source.get('source', 'UNKNOWN')}")
                print(f"      ID: {source.get('id', 'N/A')}")
                print(f"      Title: {source.get('title', 'N/A')[:60]}")
    
    # Summary
    print_header("📊 SUMMARY")
    
    print(f"Database: {len(articles)} articles from {len(source_counts)} unique sources")
    if duplicates:
        print(f"  {RED}❌ {len(duplicates)} sources appear multiple times{RESET}")
    else:
        print(f"  {GREEN}✅ No duplicate sources{RESET}")
    
    if api_story:
        api_sources = api_story.get('sources', [])
        api_source_names = [s.get('source', 'UNKNOWN') for s in api_sources]
        api_unique = len(set(api_source_names))
        
        print(f"\nAPI: {len(api_sources)} sources ({api_unique} unique)")
        if len(api_sources) == 0:
            print(f"  {RED}❌ API not returning sources!{RESET}")
        elif api_unique < len(api_sources):
            print(f"  {RED}❌ API has {len(api_sources) - api_unique} duplicates{RESET}")
        else:
            print(f"  {GREEN}✅ API deduplication working{RESET}")
    
    print("\n")


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--latest":
            analyze_story(None)
        elif arg.startswith("--"):
            print_error(f"Unknown option: {arg}")
            print("Usage: python diagnose-story-sources.py [story_id | --latest]")
            sys.exit(1)
        else:
            analyze_story(arg)
    else:
        analyze_story(None)


if __name__ == "__main__":
    main()

