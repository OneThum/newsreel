#!/usr/bin/env python3
"""
Check RSS feed poll states in Cosmos DB
"""

import os
import sys
import datetime

# Add functions to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions'))

from functions.shared.cosmos_client import CosmosDBClient

def check_feed_poll_states():
    print('🔍 CHECKING COSMOS DB FEED POLL STATES')
    print('=' * 50)

    try:
        cosmos_client = CosmosDBClient()
        cosmos_client.connect()

        # Check if the feed poll states container exists and has data
        try:
            container = cosmos_client._get_container('feed_poll_states')
            items = list(container.query_items(
                query='SELECT * FROM c',
                enable_cross_partition_query=True
            ))

            print(f'📊 Found {len(items)} feed poll state records')

            if items:
                print('\n🔍 SAMPLE FEED POLL STATES:')
                for i, item in enumerate(items[:10]):  # Show first 10
                    feed_name = item.get('feed_name', 'unknown')
                    last_poll = item.get('last_poll', 'never')
                    print(f'  {i+1}. {feed_name}: {last_poll}')

            # Check for recent activity (last hour)
            one_hour_ago = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)).isoformat()

            recent_polls = [item for item in items if item.get('last_poll', '') > one_hour_ago]
            print(f'\n⏰ RECENT POLLS (last hour): {len(recent_polls)} feeds')

            if len(recent_polls) == 0:
                print('⚠️  NO FEEDS POLLED IN LAST HOUR')
                print('   This confirms RSS ingestion is not running')
                return False
            else:
                print('✅ RSS ingestion is active')
                return True

        except Exception as e:
            print(f'❌ Error accessing feed_poll_states container: {e}')
            print('   Container may not exist or be accessible')
            return False

    except Exception as e:
        print(f'❌ Error connecting to Cosmos DB: {e}')
        return False

if __name__ == "__main__":
    check_feed_poll_states()




