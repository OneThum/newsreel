#!/usr/bin/env python3
"""Test if API is properly deduplicating sources"""

import requests
import json

API_BASE = "https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io"

print("🔍 Testing API Deduplication")
print("="*80)
print()

# Test 1: Get feed (requires auth, will fail)
print("Test 1: GET /api/stories/feed")
response = requests.get(f"{API_BASE}/api/stories/feed?limit=5")
print(f"Status: {response.status_code}")

if response.status_code == 403:
    print("❌ Requires authentication (expected)")
    print()
else:
    stories = response.json()
    print(f"✅ Got {len(stories)} stories")
    
    for story in stories[:3]:
        story_id = story.get('id', 'unknown')
        title = story.get('title', 'N/A')[:60]
        source_count = story.get('source_count', 0)
        sources = story.get('sources', [])
        
        print(f"\n📰 Story: {story_id}")
        print(f"   Title: {title}...")
        print(f"   source_count field: {source_count}")
        print(f"   sources array length: {len(sources)}")
        
        if source_count != len(sources):
            print(f"   ⚠️  MISMATCH! source_count ({source_count}) != sources length ({len(sources)})")
        else:
            print(f"   ✅ Match!")
        
        # Check for duplicates in sources array
        if sources:
            source_names = [s.get('source', 'unknown') for s in sources]
            unique_names = len(set(source_names))
            if unique_names != len(source_names):
                print(f"   ❌ DUPLICATES in sources array!")
                print(f"      Total: {len(source_names)}, Unique: {unique_names}")
            else:
                print(f"   ✅ All {len(source_names)} sources unique")

print()
print("="*80)
print()

# Test 2: Check specific story
print("Test 2: GET specific story with sources")
# The National Guard story we know has duplicates in DB
story_id = "story_20251008_201007_7c5764d6d050ae41"

response = requests.get(f"{API_BASE}/api/stories/{story_id}")
print(f"Status: {response.status_code}")

if response.status_code == 200:
    story = response.json()
    source_count = story.get('source_count', 0)
    sources = story.get('sources', [])
    
    print(f"✅ Got story: {story.get('title', 'N/A')[:60]}...")
    print(f"   source_count field: {source_count}")
    print(f"   sources array length: {len(sources)}")
    
    if source_count != len(sources):
        print(f"   ⚠️  MISMATCH!")
    else:
        print(f"   ✅ Match!")
    
    # Check sources
    if sources:
        source_names = [s.get('source', 'unknown') for s in sources]
        unique_names = set(source_names)
        
        print(f"\n   Sources in array:")
        for i, name in enumerate(source_names[:10], 1):
            print(f"      [{i}] {name}")
        if len(source_names) > 10:
            print(f"      ... and {len(source_names) - 10} more")
        
        print(f"\n   Unique sources: {len(unique_names)}")
        print(f"   Total entries: {len(source_names)}")
        
        if len(unique_names) == len(source_names):
            print(f"   ✅ All sources unique - API deduplication WORKING!")
        else:
            print(f"   ❌ DUPLICATES - API deduplication NOT working!")
    else:
        print(f"   ⚠️  No sources array in response")
elif response.status_code == 403:
    print("❌ Requires authentication")
else:
    print(f"❌ Error: {response.text}")

print()
print("="*80)

