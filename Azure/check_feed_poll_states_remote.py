#!/usr/bin/env python3
"""
Check RSS feed poll states by querying the API
"""

import requests
import datetime
from typing import Dict, List, Any

def check_feed_poll_states_via_api():
    print('🔍 CHECKING FEED POLL STATES VIA API')
    print('=' * 50)

    # We can't directly query Cosmos DB, but we can analyze the feed data
    # to see if new stories are being created

    # Check recent stories
    api_url = 'https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io'

    try:
        # Get Firebase token for authentication
        import sys
        sys.path.insert(0, 'tests')
        from scripts.firebase_auth_helper import FirebaseAuthHelper

        helper = FirebaseAuthHelper(verbose=False)
        token = helper.get_token()

        headers = {'Authorization': f'Bearer {token}'}

        # Get recent stories
        response = requests.get(f'{api_url}/api/stories/feed?limit=50', headers=headers)
        if response.status_code != 200:
            print(f'❌ API Error: {response.status_code}')
            return

        data = response.json()
        stories = data.get('stories', [])

        print(f'📊 Retrieved {len(stories)} stories')

        # Analyze story timestamps
        timestamps = []
        for story in stories:
            ts = story.get('last_updated', '')
            if ts:
                try:
                    # Parse ISO timestamp
                    dt = datetime.datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    timestamps.append(dt)
                except:
                    pass

        if timestamps:
            timestamps.sort(reverse=True)
            newest = timestamps[0]
            oldest = timestamps[-1]

            now = datetime.datetime.now(datetime.timezone.utc)
            newest_age = (now - newest).total_seconds() / 60  # minutes
            oldest_age = (now - oldest).total_seconds() / 60  # minutes

            print(f'\\n⏰ STORY AGE ANALYSIS:')
            print(f'   Newest story: {newest_age:.1f} minutes ago')
            print(f'   Oldest story: {oldest_age:.1f} minutes ago')

            # Check if RSS is working
            if newest_age < 15:  # Less than 15 minutes
                print('✅ RSS ingestion appears ACTIVE (recent stories)')
            elif newest_age < 60:  # Less than 1 hour
                print('⚠️  RSS ingestion appears SLOW (stories 15-60 min old)')
            else:
                print('❌ RSS ingestion appears INACTIVE (no recent stories)')

        # Analyze source diversity as additional check
        sources = {}
        for story in stories:
            for source in story.get('sources', []):
                src_name = source.get('source', '').lower().strip()
                if src_name and 'test' not in src_name:
                    sources[src_name] = sources.get(src_name, 0) + 1

        print(f'\\n🌍 SOURCE ANALYSIS:')
        print(f'   Unique sources: {len(sources)}')
        if sources:
            top_source = max(sources.items(), key=lambda x: x[1])
            print(f'   Top source: {top_source[0]} ({top_source[1]} articles)')

        return len(stories) > 0 and (newest_age < 60 if 'newest_age' in locals() else False)

    except Exception as e:
        print(f'❌ Error: {e}')
        return False

if __name__ == "__main__":
    check_feed_poll_states_via_api()
