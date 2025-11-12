#!/usr/bin/env python3
"""
Test RSS feed accessibility
"""

import requests
import sys
import os

# Add functions to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions'))

def test_rss_feed(url: str, name: str) -> bool:
    """Test if an RSS feed is accessible"""
    try:
        print(f"🔍 Testing {name}: {url[:60]}...")
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Newsreel-RSS-Test/1.0'})

        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            if 'xml' in content_type or 'rss' in content_type:
                print(f"  ✅ SUCCESS: {response.status_code}, {len(response.content)} bytes")
                return True
            else:
                print(f"  ⚠️  WARNING: Not XML/RSS content-type: {content_type}")
                return False
        else:
            print(f"  ❌ FAILED: {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        print("  ❌ TIMEOUT: Feed took too long to respond")
        return False
    except requests.exceptions.RequestException as e:
        print(f"  ❌ ERROR: {e}")
        return False

def test_key_feeds():
    """Test a few key RSS feeds to see if they're accessible"""
    print("🧪 TESTING RSS FEED ACCESSIBILITY")
    print("=" * 50)

    test_feeds = [
        ("BBC World News", "http://feeds.bbci.co.uk/news/world/rss.xml"),
        ("Reuters World", "https://feeds.reuters.com/reuters/worldNews"),
        ("CNN World", "http://rss.cnn.com/rss/edition_world.rss"),
        ("Sydney Morning Herald", "https://www.smh.com.au/rss/world.xml"),
        ("New York Times", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"),
        ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ]

    working_feeds = 0
    failed_feeds = 0

    for name, url in test_feeds:
        if test_rss_feed(url, name):
            working_feeds += 1
        else:
            failed_feeds += 1
        print()

    print("📊 RESULTS:")
    print(f"  ✅ Working feeds: {working_feeds}")
    print(f"  ❌ Failed feeds: {failed_feeds}")

    if failed_feeds > working_feeds:
        print("⚠️  MAJOR ISSUE: Most feeds are not accessible")
        print("   This would explain why RSS ingestion is not working")
        return False
    elif failed_feeds > 0:
        print("⚠️  SOME ISSUES: Some feeds are not accessible")
        print("   This could slow down RSS ingestion")
        return True
    else:
        print("✅ ALL FEEDS ACCESSIBLE: RSS feeds are working")
        return True

if __name__ == "__main__":
    test_key_feeds()
