#!/usr/bin/env python3
"""
Comprehensive RSS ingestion diagnostic
"""

import sys
import os
import datetime
import requests

# Add functions to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions'))

def diagnose_rss_ingestion():
    print("🔍 COMPREHENSIVE RSS INGESTION DIAGNOSTIC")
    print("=" * 60)

    issues_found = []
    recommendations = []

    # 1. Check API accessibility
    print("1️⃣ CHECKING API ACCESSIBILITY")
    try:
        sys.path.insert(0, 'tests')
        from scripts.firebase_auth_helper import FirebaseAuthHelper

        helper = FirebaseAuthHelper(verbose=False)
        token = helper.get_token()
        headers = {'Authorization': f'Bearer {token}'}

        api_url = 'https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io'
        response = requests.get(f'{api_url}/api/stories/feed?limit=10', headers=headers)

        if response.status_code == 200:
            print("✅ API is accessible and responding")
        else:
            print(f"❌ API error: {response.status_code}")
            issues_found.append("API not responding correctly")
            recommendations.append("Check API deployment and authentication")

    except Exception as e:
        print(f"❌ API access failed: {e}")
        issues_found.append("Cannot access API")
        recommendations.append("Check Firebase authentication and API deployment")

    print()

    # 2. Check story freshness
    print("2️⃣ CHECKING STORY FRESHNESS")
    try:
        data = response.json()
        stories = data.get('stories', [])

        if stories:
            latest_story = max(stories, key=lambda s: s.get('last_updated', ''))
            last_updated = latest_story.get('last_updated', '')

            if last_updated:
                dt = datetime.datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                now = datetime.datetime.now(datetime.timezone.utc)
                age_minutes = (now - dt).total_seconds() / 60

                print(f"📅 Latest story: {age_minutes:.1f} minutes ago")

                if age_minutes < 10:
                    print("✅ RSS ingestion is ACTIVE")
                elif age_minutes < 60:
                    print("⚠️  RSS ingestion is SLOW")
                    issues_found.append("RSS ingestion running slowly")
                    recommendations.append("Check feed polling frequency and errors")
                else:
                    print("❌ RSS ingestion appears INACTIVE")
                    issues_found.append("RSS ingestion not running")
                    recommendations.append("Check function app timer triggers and logs")
            else:
                print("❌ No timestamp data")
                issues_found.append("Missing story timestamps")
        else:
            print("❌ No stories found")
            issues_found.append("No stories in feed")
            recommendations.append("Check if RSS ingestion ever ran successfully")

    except Exception as e:
        print(f"❌ Story freshness check failed: {e}")

    print()

    # 3. Check source diversity
    print("3️⃣ CHECKING SOURCE DIVERSITY")
    try:
        sources = {}
        total_articles = 0

        for story in stories:
            for source in story.get('sources', []):
                src_name = source.get('source', '').lower().strip()
                if src_name and 'test' not in src_name:
                    sources[src_name] = sources.get(src_name, 0) + 1
                    total_articles += 1

        print(f"📊 Unique sources: {len(sources)}")
        if sources:
            top_source = max(sources.items(), key=lambda x: x[1])
            top_percentage = (top_source[1] / total_articles) * 100 if total_articles > 0 else 0
            print(f"🥇 Top source: {top_source[0]} ({top_source[1]} articles, {top_percentage:.1f}%)")

            if top_percentage > 60:
                print("❌ CRITICAL: Extreme source concentration")
                issues_found.append("Unhealthy source concentration")
                recommendations.append("Add more diverse RSS feeds")
            elif top_percentage > 30:
                print("⚠️  HIGH: Significant source concentration")
                issues_found.append("High source concentration")
                recommendations.append("Monitor new feed processing")

        if len(sources) < 5:
            print("❌ LOW: Insufficient source diversity")
            issues_found.append("Low source diversity")
            recommendations.append("Add more RSS feeds to working_feeds.py")

    except Exception as e:
        print(f"❌ Source diversity check failed: {e}")

    print()

    # 4. Check RSS feed accessibility
    print("4️⃣ CHECKING RSS FEED ACCESSIBILITY")
    test_feeds = [
        ("BBC World", "http://feeds.bbci.co.uk/news/world/rss.xml"),
        ("CNN World", "http://rss.cnn.com/rss/edition_world.rss"),
        ("Reuters World", "https://feeds.reuters.com/reuters/worldNews"),
        ("NYT World", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"),
    ]

    working_feeds = 0
    failed_feeds = 0

    for name, url in test_feeds:
        try:
            response = requests.get(url, timeout=10, headers={'User-Agent': 'Newsreel-Diagnostic/1.0'})
            if response.status_code == 200:
                print(f"✅ {name}: OK")
                working_feeds += 1
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
                failed_feeds += 1
        except Exception as e:
            print(f"❌ {name}: {str(e)[:50]}...")
            failed_feeds += 1

    if failed_feeds > working_feeds:
        print("❌ MAJOR: Most RSS feeds inaccessible")
        issues_found.append("RSS feeds not accessible")
        recommendations.append("Check network connectivity and feed URLs")
    elif failed_feeds > 0:
        print("⚠️  MINOR: Some RSS feeds inaccessible")
        recommendations.append("Monitor feed accessibility")

    print()

    # 5. Check working_feeds.py configuration
    print("5️⃣ CHECKING FEED CONFIGURATION")
    try:
        from functions.shared.working_feeds import get_verified_working_feeds
        feeds = get_verified_working_feeds()

        print(f"📊 Configured feeds: {len(feeds)}")

        categories = {}
        sources = set()

        for feed in feeds:
            cat = getattr(feed, 'category', 'unknown')
            src = getattr(feed, 'source_id', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
            sources.add(src)

        print(f"📂 Categories: {dict(categories)}")
        print(f"📰 Unique sources: {len(sources)}")

        if len(feeds) < 10:
            print("⚠️  LOW: Few feeds configured")
            recommendations.append("Add more RSS feeds to increase diversity")
        else:
            print("✅ GOOD: Sufficient feeds configured")

    except Exception as e:
        print(f"❌ Feed configuration check failed: {e}")

    print()

    # SUMMARY
    print("📋 DIAGNOSTIC SUMMARY")
    print("=" * 30)

    if not issues_found:
        print("✅ NO ISSUES FOUND - RSS ingestion appears healthy")
        print("🎉 All systems operational!")
    else:
        print(f"❌ ISSUES FOUND: {len(issues_found)}")
        for i, issue in enumerate(issues_found, 1):
            print(f"   {i}. {issue}")

        print(f"\\n💡 RECOMMENDATIONS: {len(recommendations)}")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")

    return len(issues_found) == 0

if __name__ == "__main__":
    diagnose_rss_ingestion()




