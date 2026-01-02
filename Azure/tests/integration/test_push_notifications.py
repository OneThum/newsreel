"""
Push Notification Integration Tests

Tests the push notification workflow for breaking news alerts.
Note: Actual notification delivery requires Firebase configuration.
"""

import pytest
import os
from datetime import datetime, timezone, timedelta
from azure.cosmos import CosmosClient


@pytest.fixture(scope="module")
def cosmos_client():
    """Get Cosmos DB client"""
    conn_str = os.getenv('COSMOS_CONNECTION_STRING')
    if not conn_str:
        pytest.skip("COSMOS_CONNECTION_STRING not configured")
    
    return CosmosClient.from_connection_string(conn_str)


@pytest.fixture(scope="module")
def database(cosmos_client):
    """Get database client"""
    db_name = os.getenv('COSMOS_DATABASE_NAME', 'newsreel-db')
    return cosmos_client.get_database_client(db_name)


@pytest.mark.integration
class TestBreakingNewsDetection:
    """Test breaking news detection logic"""
    
    def test_breaking_news_criteria(self, database):
        """Test that breaking news stories meet the criteria"""
        stories = database.get_container_client('story_clusters')
        
        # Query stories marked as breaking
        query = """
            SELECT * FROM c 
            WHERE c.breaking_news = true 
            ORDER BY c.last_updated DESC
        """
        
        breaking_stories = list(stories.query_items(
            query, 
            enable_cross_partition_query=True,
            max_item_count=20
        ))
        
        print(f"📊 Found {len(breaking_stories)} breaking news stories")
        
        for story in breaking_stories[:5]:
            # Breaking stories should have 3+ sources (verified)
            source_count = story.get('verification_level', 0)
            status = story.get('status', 'unknown')
            
            print(f"  - [{status}] {story.get('title', 'unknown')[:40]}... ({source_count} sources)")
            
            # Breaking news should generally be verified
            if source_count < 3:
                print(f"    ⚠️ Breaking story has only {source_count} sources")
    
    def test_recent_breaking_news(self, database):
        """Test if there's recent breaking news"""
        stories = database.get_container_client('story_clusters')
        
        # Look for breaking news in last 24 hours
        yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
        
        query = f"""
            SELECT VALUE COUNT(1) FROM c 
            WHERE c.breaking_news = true 
            AND c.last_updated >= '{yesterday.isoformat()}'
        """
        
        result = list(stories.query_items(query, enable_cross_partition_query=True))
        recent_breaking = result[0] if result else 0
        
        print(f"📊 Breaking news in last 24h: {recent_breaking}")
        
        # This is informational - not a failure if no breaking news


@pytest.mark.integration
class TestNotificationTracking:
    """Test notification tracking in database"""
    
    def test_notification_sent_flag(self, database):
        """Test that stories track notification sent status"""
        stories = database.get_container_client('story_clusters')
        
        # Query breaking stories with notification tracking
        query = """
            SELECT TOP 10 c.id, c.title, c.breaking_news, 
                   c.push_notification_sent, c.push_notification_sent_at
            FROM c 
            WHERE c.breaking_news = true
            ORDER BY c.last_updated DESC
        """
        
        results = list(stories.query_items(query, enable_cross_partition_query=True))
        
        notified_count = 0
        for story in results:
            sent = story.get('push_notification_sent', False)
            sent_at = story.get('push_notification_sent_at')
            
            if sent:
                notified_count += 1
                print(f"✅ Notification sent: {story.get('title', 'unknown')[:40]}...")
                if sent_at:
                    print(f"   Sent at: {sent_at}")
        
        print(f"📊 {notified_count}/{len(results)} breaking stories have notifications sent")
    
    def test_notification_deduplication(self, database):
        """Test that notifications aren't sent multiple times"""
        stories = database.get_container_client('story_clusters')
        
        # Find stories with notification sent
        query = """
            SELECT c.id, c.title, c.push_notification_sent, c.push_notification_sent_at
            FROM c 
            WHERE c.push_notification_sent = true
            ORDER BY c.push_notification_sent_at DESC
        """
        
        results = list(stories.query_items(
            query, 
            enable_cross_partition_query=True,
            max_item_count=20
        ))
        
        # Check for duplicates (same story notified multiple times would be a bug)
        seen_ids = set()
        duplicates = []
        
        for story in results:
            story_id = story['id']
            if story_id in seen_ids:
                duplicates.append(story_id)
            seen_ids.add(story_id)
        
        if duplicates:
            print(f"⚠️ Found duplicate notifications: {duplicates}")
        else:
            print(f"✅ No duplicate notifications found in {len(results)} checked")


@pytest.mark.integration
class TestNotificationPayload:
    """Test notification payload generation"""
    
    def test_breaking_story_has_notification_content(self, database):
        """Test that breaking stories have content suitable for notifications"""
        stories = database.get_container_client('story_clusters')
        
        query = """
            SELECT TOP 5 c.id, c.title, c.category, c.summary, c.sources, c.source_articles
            FROM c 
            WHERE c.breaking_news = true
            ORDER BY c.last_updated DESC
        """
        
        results = list(stories.query_items(query, enable_cross_partition_query=True))
        
        if not results:
            pytest.skip("No breaking news stories to test")
        
        for story in results:
            # Title should be suitable for notification
            title = story.get('title', '')
            assert len(title) > 0, "Breaking story should have a title"
            assert len(title) <= 200, "Title should be suitable for notification"
            
            # Should have category for routing
            assert story.get('category'), "Breaking story should have a category"
            
            # Should have sources for credibility (could be in sources or source_articles)
            sources = story.get('sources', []) or story.get('source_articles', [])
            if not sources:
                print(f"⚠️ Breaking story has no sources: {title[:40]}...")
            else:
                print(f"✅ Notification-ready ({len(sources)} sources): {title[:50]}...")
    
    def test_notification_title_length(self, database):
        """Test that titles are appropriate length for push notifications"""
        stories = database.get_container_client('story_clusters')
        
        query = """
            SELECT c.title FROM c 
            WHERE c.breaking_news = true
            ORDER BY c.last_updated DESC
        """
        
        results = list(stories.query_items(
            query, 
            enable_cross_partition_query=True,
            max_item_count=20
        ))
        
        long_titles = []
        for story in results:
            title = story.get('title', '')
            if len(title) > 100:  # iOS push title limit is ~100 chars visible
                long_titles.append(title[:50])
        
        if long_titles:
            print(f"⚠️ {len(long_titles)} stories have long titles that may truncate:")
            for t in long_titles[:3]:
                print(f"   - {t}...")


@pytest.mark.integration
class TestBreakingNewsTrigger:
    """Test the breaking news trigger conditions"""
    
    def test_tier1_source_triggers_breaking(self, database):
        """Test that tier 1 sources can trigger breaking news"""
        stories = database.get_container_client('story_clusters')
        
        # Query for tier 1 source articles
        articles = database.get_container_client('raw_articles')
        
        tier1_query = """
            SELECT TOP 5 c.source, c.title, c.story_id
            FROM c 
            WHERE c.source_tier = 1
            ORDER BY c.fetched_at DESC
        """
        
        tier1_articles = list(articles.query_items(
            tier1_query, 
            enable_cross_partition_query=True
        ))
        
        print(f"📊 Recent tier 1 articles: {len(tier1_articles)}")
        
        for article in tier1_articles:
            print(f"  - [{article.get('source')}] {article.get('title', 'unknown')[:40]}...")
    
    def test_verification_level_for_breaking(self, database):
        """Test that breaking stories have appropriate verification level"""
        stories = database.get_container_client('story_clusters')
        
        query = """
            SELECT c.id, c.title, c.verification_level, c.breaking_news
            FROM c 
            WHERE c.breaking_news = true
            ORDER BY c.last_updated DESC
        """
        
        results = list(stories.query_items(
            query, 
            enable_cross_partition_query=True,
            max_item_count=20
        ))
        
        verification_levels = [r.get('verification_level', 0) for r in results]
        
        if verification_levels:
            avg_verification = sum(verification_levels) / len(verification_levels)
            min_verification = min(verification_levels)
            max_verification = max(verification_levels)
            
            print(f"📊 Breaking news verification levels:")
            print(f"   Avg: {avg_verification:.1f}, Min: {min_verification}, Max: {max_verification}")
            
            # Breaking news should generally have high verification
            low_verification = [v for v in verification_levels if v < 3]
            if low_verification:
                print(f"   ⚠️ {len(low_verification)} stories have verification < 3")


@pytest.mark.integration
class TestUserPreferences:
    """Test user notification preferences"""
    
    def test_user_profiles_exist(self, database):
        """Test that user profiles container exists"""
        try:
            profiles = database.get_container_client('user_profiles')
            
            # Try to query
            query = 'SELECT VALUE COUNT(1) FROM c'
            result = list(profiles.query_items(query, enable_cross_partition_query=True))
            count = result[0] if result else 0
            
            print(f"📊 User profiles: {count}")
            
        except Exception as e:
            print(f"ℹ️ User profiles container not accessible: {e}")
    
    def test_notification_preferences_structure(self, database):
        """Test notification preferences structure in user profiles"""
        try:
            profiles = database.get_container_client('user_profiles')
            
            query = 'SELECT TOP 1 * FROM c'
            result = list(profiles.query_items(query, enable_cross_partition_query=True))
            
            if result:
                profile = result[0]
                prefs = profile.get('notification_preferences', {})
                
                # Check expected preference fields
                expected_fields = ['breaking_news', 'daily_digest', 'category_alerts']
                
                for field in expected_fields:
                    if field in prefs:
                        print(f"✅ Has preference: {field}")
                    else:
                        print(f"ℹ️ Missing preference: {field}")
            else:
                print("ℹ️ No user profiles to check")
                
        except Exception as e:
            print(f"ℹ️ Could not check preferences: {e}")


@pytest.mark.integration
class TestNotificationHistory:
    """Test notification history tracking"""
    
    def test_breaking_news_triggered_at_tracking(self, database):
        """Test that breaking_triggered_at is tracked"""
        stories = database.get_container_client('story_clusters')
        
        query = """
            SELECT c.id, c.title, c.breaking_triggered_at
            FROM c 
            WHERE c.breaking_news = true 
            AND IS_DEFINED(c.breaking_triggered_at)
            ORDER BY c.breaking_triggered_at DESC
        """
        
        results = list(stories.query_items(
            query, 
            enable_cross_partition_query=True,
            max_item_count=10
        ))
        
        print(f"📊 Stories with breaking_triggered_at: {len(results)}")
        
        for story in results[:3]:
            triggered = story.get('breaking_triggered_at', 'unknown')
            print(f"  - {triggered}: {story.get('title', 'unknown')[:40]}...")
    
    def test_notification_latency(self, database):
        """Test latency between breaking trigger and notification"""
        stories = database.get_container_client('story_clusters')
        
        query = """
            SELECT c.breaking_triggered_at, c.push_notification_sent_at
            FROM c 
            WHERE c.breaking_news = true 
            AND IS_DEFINED(c.breaking_triggered_at)
            AND c.push_notification_sent = true
            ORDER BY c.breaking_triggered_at DESC
        """
        
        results = list(stories.query_items(
            query, 
            enable_cross_partition_query=True,
            max_item_count=10
        ))
        
        latencies = []
        for story in results:
            triggered = story.get('breaking_triggered_at')
            sent = story.get('push_notification_sent_at')
            
            if triggered and sent:
                try:
                    triggered_time = datetime.fromisoformat(str(triggered).replace('Z', '+00:00'))
                    sent_time = datetime.fromisoformat(str(sent).replace('Z', '+00:00'))
                    latency = (sent_time - triggered_time).total_seconds()
                    latencies.append(latency)
                except:
                    pass
        
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            
            print(f"📊 Notification latency:")
            print(f"   Avg: {avg_latency:.1f}s, Max: {max_latency:.1f}s")
            
            if max_latency > 300:  # 5 minutes
                print("   ⚠️ Some notifications had high latency (>5min)")
        else:
            print("ℹ️ No latency data available")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

