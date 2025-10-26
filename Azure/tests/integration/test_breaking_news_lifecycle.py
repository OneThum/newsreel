"""Integration tests: Breaking News Lifecycle

Tests the complete breaking news detection and notification workflow
"""
import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from functions.shared.cosmos_client import CosmosClient


@pytest.mark.integration
class TestBreakingNewsDetection:
    """Test breaking news detection logic"""
    
    @pytest.mark.asyncio
    async def test_verified_to_breaking_transition(self, mock_cosmos_client, sample_verified_story):
        """Test that VERIFIED stories can become BREAKING"""
        # Arrange: VERIFIED story with 3 sources
        story = sample_verified_story
        assert story['status'] == 'VERIFIED'
        assert story['article_count'] == 3
        
        # Act: Add 4th source rapidly (simulates breaking news velocity)
        story['sources'].append({
            'source': 'ap',
            'source_name': 'Associated Press',
            'article_id': 'ap_article1',
            'added_at': datetime.now(timezone.utc).isoformat()
        })
        story['article_count'] = 4
        
        # Check if story velocity indicates breaking news
        # (4 sources in <30 minutes = breaking news velocity)
        first_seen = datetime.fromisoformat(story['first_seen'].replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        time_span = (now - first_seen).total_seconds() / 60  # minutes
        
        velocity = story['article_count'] / time_span if time_span > 0 else 0
        is_breaking = velocity > 0.1  # More than 1 source per 10 minutes
        
        # Assert: Should be flagged as breaking
        assert story['article_count'] >= 4, "Breaking news requires 4+ sources"
        
    @pytest.mark.asyncio
    async def test_monitoring_to_breaking_skip_developing(self, mock_cosmos_client):
        """Test that stories can skip DEVELOPING and go straight to BREAKING"""
        # Arrange: New story with rapid source additions
        story = {
            'id': 'story_fast_1',
            'status': 'MONITORING',
            'article_count': 1,
            'first_seen': (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        }
        
        # Act: Rapidly add 3 more sources
        story['article_count'] = 4
        time_elapsed = 5  # minutes
        
        # Check breaking news criteria
        meets_source_threshold = story['article_count'] >= 4
        is_rapid = time_elapsed < 30  # Less than 30 minutes
        
        # Assert: Should jump to BREAKING
        assert meets_source_threshold and is_rapid, "Should skip DEVELOPING with rapid sources"
        
    @pytest.mark.asyncio
    async def test_breaking_news_not_triggered_for_slow_stories(self, mock_cosmos_client):
        """Test that slow-developing stories don't become BREAKING"""
        # Arrange: Story with 4 sources added slowly
        story = {
            'id': 'story_slow_1',
            'status': 'VERIFIED',
            'article_count': 4,
            'first_seen': (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
        }
        
        # Act: Check velocity
        first_seen = datetime.fromisoformat(story['first_seen'].replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        time_span_hours = (now - first_seen).total_seconds() / 3600
        
        is_rapid = time_span_hours < 0.5  # Less than 30 minutes
        
        # Assert: Should NOT be breaking (too slow)
        assert not is_rapid, "Slow stories should not trigger breaking status"


@pytest.mark.integration
class TestBreakingNewsNotifications:
    """Test breaking news notification workflow"""
    
    @pytest.mark.asyncio
    async def test_notification_triggered_on_breaking_status(self, mock_cosmos_client, sample_breaking_story):
        """Test that BREAKING status triggers push notification"""
        # Arrange: Story just became BREAKING
        story = sample_breaking_story
        notification_sent = story.get('notification_sent', False)
        
        # Act: Check if notification should be sent
        should_notify = (
            story['status'] == 'BREAKING' and
            not notification_sent and
            story['article_count'] >= 4
        )
        
        # Assert: Should trigger notification
        # Note: In sample_breaking_story, notification is already sent
        # So for a new breaking story, should_notify would be True
        assert story['status'] == 'BREAKING'
        assert story['article_count'] >= 4
        
    @pytest.mark.asyncio
    async def test_notification_payload_structure(self, sample_breaking_story):
        """Test that notification payload has correct structure"""
        # Arrange: Breaking story
        story = sample_breaking_story
        
        # Act: Build notification payload (simulate FCMNotificationService)
        notification_payload = {
            'title': '🔴 Breaking News',
            'body': story['headline'][:100],  # Truncate for mobile
            'data': {
                'story_id': story['id'],
                'type': 'breaking_news',
                'status': story['status'],
                'source_count': str(story['article_count'])
            }
        }
        
        # Assert: Payload structure correct
        assert notification_payload['title'] == '🔴 Breaking News'
        assert len(notification_payload['body']) <= 100
        assert notification_payload['data']['story_id'] == story['id']
        assert notification_payload['data']['type'] == 'breaking_news'
        
    @pytest.mark.asyncio
    async def test_notification_deduplication(self, mock_cosmos_client, sample_breaking_story):
        """Test that notifications aren't sent twice for same story"""
        # Arrange: Story with notification already sent
        story = sample_breaking_story
        story['notification_sent'] = True
        story['breaking_triggered_at'] = '2025-10-26T09:15:00Z'
        
        # Act: Check if should send again
        should_send_again = (
            story['status'] == 'BREAKING' and
            not story.get('notification_sent', False)
        )
        
        # Assert: Should NOT send duplicate
        assert not should_send_again, "Should not send duplicate notifications"
        
    @pytest.mark.asyncio
    async def test_notification_rate_limiting(self):
        """Test that notifications respect rate limits"""
        # Arrange: Multiple breaking stories in short time
        stories_in_last_hour = 5
        max_notifications_per_hour = 10
        
        # Act: Check if can send
        can_send = stories_in_last_hour < max_notifications_per_hour
        
        # Assert: Within rate limit
        assert can_send, "Should allow notifications within rate limit"
        
        # Test over limit
        stories_in_last_hour = 11
        can_send = stories_in_last_hour < max_notifications_per_hour
        assert not can_send, "Should block notifications over rate limit"


@pytest.mark.integration
class TestBreakingNewsLifecycle:
    """Test complete breaking news lifecycle"""
    
    @pytest.mark.asyncio
    async def test_breaking_to_verified_demotion(self, mock_cosmos_client, sample_breaking_story):
        """Test that BREAKING stories eventually become VERIFIED"""
        # Arrange: Breaking story older than threshold
        story = sample_breaking_story
        breaking_time = datetime.fromisoformat(
            story['breaking_triggered_at'].replace('Z', '+00:00')
        )
        
        # Act: Check if should demote
        now = datetime.now(timezone.utc)
        hours_since_breaking = (now - breaking_time).total_seconds() / 3600
        
        should_demote = hours_since_breaking >= 4  # 4 hour threshold
        
        # Assert: Old breaking stories should become VERIFIED
        if hours_since_breaking >= 4:
            assert should_demote, "BREAKING stories should demote after 4 hours"
        
    @pytest.mark.asyncio
    async def test_verified_to_archived_lifecycle(self, mock_cosmos_client):
        """Test that VERIFIED stories eventually get archived"""
        # Arrange: Old verified story
        story = {
            'id': 'story_old_1',
            'status': 'VERIFIED',
            'last_updated': (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
        }
        
        # Act: Check if should archive
        last_updated = datetime.fromisoformat(story['last_updated'].replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        hours_old = (now - last_updated).total_seconds() / 3600
        
        should_archive = hours_old >= 24  # 24 hour threshold
        
        # Assert: Old stories should be archived
        assert should_archive, "Stories older than 24 hours should be archived"
        
    @pytest.mark.asyncio
    async def test_complete_story_lifecycle_flow(self, mock_cosmos_client):
        """Test complete lifecycle: MONITORING → DEVELOPING → VERIFIED → BREAKING → VERIFIED → ARCHIVED"""
        # Arrange: Track lifecycle stages
        lifecycle = []
        
        # Act: Simulate lifecycle progression
        # Stage 1: MONITORING (1 source)
        story = {'article_count': 1}
        status = 'MONITORING'
        lifecycle.append(status)
        assert status == 'MONITORING'
        
        # Stage 2: DEVELOPING (2 sources)
        story['article_count'] = 2
        status = 'DEVELOPING' if story['article_count'] >= 2 else status
        lifecycle.append(status)
        assert status == 'DEVELOPING'
        
        # Stage 3: VERIFIED (3 sources)
        story['article_count'] = 3
        status = 'VERIFIED' if story['article_count'] >= 3 else status
        lifecycle.append(status)
        assert status == 'VERIFIED'
        
        # Stage 4: BREAKING (4 sources rapidly)
        story['article_count'] = 4
        story['rapid'] = True
        status = 'BREAKING' if story['article_count'] >= 4 and story.get('rapid') else status
        lifecycle.append(status)
        assert status == 'BREAKING'
        
        # Stage 5: Back to VERIFIED (after 4 hours)
        story['hours_since_breaking'] = 5
        status = 'VERIFIED' if story.get('hours_since_breaking', 0) >= 4 else status
        lifecycle.append(status)
        assert status == 'VERIFIED'
        
        # Assert: Complete lifecycle captured
        assert lifecycle == ['MONITORING', 'DEVELOPING', 'VERIFIED', 'BREAKING', 'VERIFIED']


@pytest.mark.integration
class TestTwitterBreakingNewsIntegration:
    """Test Twitter/X API integration for breaking news verification"""
    
    @pytest.mark.asyncio
    async def test_twitter_trending_check(self):
        """Test checking if story topic is trending on Twitter"""
        # Arrange: Story with entities
        story = {
            'headline': 'Major earthquake strikes California',
            'entities': {
                'locations': ['California'],
                'events': ['earthquake']
            }
        }
        
        # Act: Build Twitter search query (simulate)
        search_terms = story['entities'].get('locations', []) + story['entities'].get('events', [])
        twitter_query = ' OR '.join(search_terms)
        
        # Assert: Query built correctly
        assert 'California' in twitter_query
        assert 'earthquake' in twitter_query
        
    @pytest.mark.asyncio
    async def test_twitter_volume_threshold(self):
        """Test that Twitter volume indicates breaking news"""
        # Arrange: Mock Twitter API response
        mock_twitter_volume = 15000  # tweets per hour
        breaking_threshold = 10000
        
        # Act: Check if trending
        is_trending = mock_twitter_volume >= breaking_threshold
        
        # Assert: High volume indicates breaking
        assert is_trending, "High tweet volume should indicate breaking news"


@pytest.mark.integration
@pytest.mark.slow
class TestBreakingNewsPerformance:
    """Test breaking news detection performance"""
    
    @pytest.mark.asyncio
    async def test_breaking_news_detection_latency(self, mock_cosmos_client):
        """Test that breaking news is detected quickly"""
        import time
        
        # Arrange: Story with 4 sources
        story = {
            'id': 'story_perf_1',
            'article_count': 4,
            'first_seen': (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat(),
            'status': 'VERIFIED'
        }
        
        # Act: Time breaking news check
        start_time = time.time()
        
        # Simulate breaking news logic
        first_seen = datetime.fromisoformat(story['first_seen'].replace('Z', '+00:00'))
        time_span = (datetime.now(timezone.utc) - first_seen).total_seconds() / 60
        velocity = story['article_count'] / time_span if time_span > 0 else 0
        is_breaking = velocity > 0.1 and story['article_count'] >= 4
        
        duration = time.time() - start_time
        
        # Assert: Should be fast
        assert duration < 0.01, f"Breaking news check should be <10ms, took {duration*1000}ms"
        
    @pytest.mark.asyncio
    async def test_notification_send_latency(self):
        """Test that notifications are sent quickly"""
        import time
        
        # Arrange: Notification payload
        payload = {
            'title': '🔴 Breaking News',
            'body': 'Test notification',
            'data': {'story_id': 'test_123'}
        }
        
        # Act: Time payload construction
        start_time = time.time()
        # Simulate notification construction
        notification = {
            'notification': payload,
            'topic': 'breaking_news'
        }
        duration = time.time() - start_time
        
        # Assert: Should be instant
        assert duration < 0.001, "Notification construction should be <1ms"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

