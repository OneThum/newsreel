#!/usr/bin/env python3
"""
Test script to compare feed vs breaking endpoints

This script:
1. Calls both /api/stories/feed and /api/stories/breaking endpoints
2. Compares the responses
3. Identifies where summaries and sources are missing
4. Provides detailed diagnostic output

Usage:
    python test-feed-vs-breaking.py <firebase_token>
"""

import os
import sys
import json
import requests
from datetime import datetime

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


def get_feed(token):
    """Get feed endpoint response"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_BASE_URL}/api/stories/feed?limit=5",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print_error(f"Failed to fetch feed: {e}")
        return None


def get_breaking(token):
    """Get breaking endpoint response"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_BASE_URL}/api/stories/breaking?limit=5",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print_error(f"Failed to fetch breaking: {e}")
        return None


def analyze_story(story, endpoint_name):
    """Analyze a single story response"""
    print(f"\n{BOLD}Story:{RESET} {story.get('title', 'N/A')[:60]}")
    print(f"{BOLD}ID:{RESET} {story.get('id')}")
    
    # Check summary
    summary = story.get('summary')
    if summary:
        print(f"{GREEN}✅ Summary present:{RESET} {len(summary.get('text', ''))} chars")
    else:
        print(f"{RED}❌ Summary is NULL{RESET}")
    
    # Check sources
    source_count = story.get('source_count', 0)
    sources = story.get('sources', [])
    
    print(f"{BOLD}source_count field:{RESET} {source_count}")
    print(f"{BOLD}sources array length:{RESET} {len(sources)}")
    
    if source_count == 0 and len(sources) == 0:
        print(f"{RED}❌ NO SOURCES (source_count=0, sources=[]){RESET}")
    elif source_count == 0 and len(sources) > 0:
        print(f"{YELLOW}⚠️  Mismatch: source_count=0 but sources has {len(sources)} items{RESET}")
    elif source_count > 0 and len(sources) == 0:
        print(f"{RED}❌ CRITICAL: source_count={source_count} but sources array is empty!{RESET}")
    else:
        print(f"{GREEN}✅ source_count and sources array match{RESET}")
    
    if sources:
        print(f"{BOLD}First 3 sources:{RESET}")
        for i, source in enumerate(sources[:3], 1):
            print(f"  [{i}] {source.get('source')} - {source.get('title', 'N/A')[:40]}")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print_error("Firebase token required as argument")
        print(f"Usage: {sys.argv[0]} <firebase_token>")
        sys.exit(1)
    
    token = sys.argv[1]
    
    print_header("🔍 FEED vs BREAKING ENDPOINT COMPARISON")
    
    # Fetch both endpoints
    print_info("Fetching /api/stories/feed...")
    feed_stories = get_feed(token)
    
    print_info("Fetching /api/stories/breaking...")
    breaking_stories = get_breaking(token)
    
    if not feed_stories or not breaking_stories:
        print_error("Failed to fetch both endpoints")
        sys.exit(1)
    
    # Ensure we have arrays
    if not isinstance(feed_stories, list):
        feed_stories = [feed_stories]
    if not isinstance(breaking_stories, list):
        breaking_stories = [breaking_stories]
    
    # Analyze feed endpoint
    print_header("📰 FEED ENDPOINT ANALYSIS")
    print_success(f"Returned {len(feed_stories)} stories")
    
    feed_with_summary = 0
    feed_with_sources = 0
    
    for i, story in enumerate(feed_stories[:3], 1):
        print(f"\n{BOLD}Story {i}:{RESET}")
        analyze_story(story, "feed")
        
        if story.get('summary'):
            feed_with_summary += 1
        if story.get('source_count', 0) > 0 or story.get('sources', []):
            feed_with_sources += 1
    
    print(f"\n{BOLD}Summary:{RESET} {feed_with_summary}/{min(3, len(feed_stories))} stories have summaries")
    print(f"{BOLD}Summary:{RESET} {feed_with_sources}/{min(3, len(feed_stories))} stories have sources")
    
    # Analyze breaking endpoint
    print_header("📺 BREAKING ENDPOINT ANALYSIS")
    print_success(f"Returned {len(breaking_stories)} stories")
    
    breaking_with_summary = 0
    breaking_with_sources = 0
    
    for i, story in enumerate(breaking_stories[:3], 1):
        print(f"\n{BOLD}Story {i}:{RESET}")
        analyze_story(story, "breaking")
        
        if story.get('summary'):
            breaking_with_summary += 1
        if story.get('source_count', 0) > 0 or story.get('sources', []):
            breaking_with_sources += 1
    
    print(f"\n{BOLD}Summary:{RESET} {breaking_with_summary}/{min(3, len(breaking_stories))} stories have summaries")
    print(f"{BOLD}Summary:{RESET} {breaking_with_sources}/{min(3, len(breaking_stories))} stories have sources")
    
    # Comparison
    print_header("🔄 COMPARISON")
    
    if feed_with_summary == 0 and breaking_with_summary > 0:
        print_error("FEED ENDPOINT HAS NO SUMMARIES but BREAKING does!")
        print_info("This indicates a backend issue in the feed query or personalization")
    elif feed_with_summary == breaking_with_summary:
        print_success("Both endpoints have same summary coverage")
    
    if feed_with_sources == 0 and breaking_with_sources > 0:
        print_error("FEED ENDPOINT HAS NO SOURCES but BREAKING does!")
        print_info("This indicates a backend issue in the feed query or personalization")
    elif feed_with_sources == breaking_with_sources:
        print_success("Both endpoints have same source coverage")
    
    print("\n")


if __name__ == "__main__":
    main()
