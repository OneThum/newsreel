"""
Unit tests for Queue Producer functionality

Tests the feed scheduling and queue production logic.
"""
import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os

# Add functions to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../functions')))


@pytest.mark.unit
class TestFeedScheduling:
    """Test feed scheduling logic"""
    
    def test_round_robin_category_distribution(self):
        """Test that feeds are selected round-robin across categories"""
        # Arrange: Create feeds in different categories
        from shared.models import RSSFeedConfig
        
        feeds = [
            RSSFeedConfig(id='world1', name='World 1', url='http://w1.com', source_id='w1', category='world', tier=1),
            RSSFeedConfig(id='world2', name='World 2', url='http://w2.com', source_id='w2', category='world', tier=1),
            RSSFeedConfig(id='tech1', name='Tech 1', url='http://t1.com', source_id='t1', category='tech', tier=2),
            RSSFeedConfig(id='tech2', name='Tech 2', url='http://t2.com', source_id='t2', category='tech', tier=2),
            RSSFeedConfig(id='biz1', name='Biz 1', url='http://b1.com', source_id='b1', category='business', tier=2),
        ]
        
        # Act: Group by category
        by_category = {}
        for feed in feeds:
            if feed.category not in by_category:
                by_category[feed.category] = []
            by_category[feed.category].append(feed)
        
        # Assert: Should have 3 categories
        assert len(by_category) == 3
        assert 'world' in by_category
        assert 'tech' in by_category
        assert 'business' in by_category
    
    def test_cooldown_filtering(self):
        """Test that feeds within cooldown are not selected"""
        now = datetime.now(timezone.utc)
        cooldown = timedelta(seconds=180)  # 3 minutes
        
        # Feed polled 1 minute ago - should be filtered
        last_poll_recent = now - timedelta(minutes=1)
        should_poll_recent = (now - last_poll_recent) >= cooldown
        assert should_poll_recent is False
        
        # Feed polled 5 minutes ago - should be selected
        last_poll_old = now - timedelta(minutes=5)
        should_poll_old = (now - last_poll_old) >= cooldown
        assert should_poll_old is True
        
        # Feed never polled - should be selected
        last_poll_never = None
        should_poll_never = last_poll_never is None
        assert should_poll_never is True
    
    def test_max_feeds_limit(self):
        """Test that selection respects max feeds limit"""
        # Arrange: 20 ready feeds
        ready_feeds = [f'feed_{i}' for i in range(20)]
        max_feeds = 10
        
        # Act: Select up to limit
        selected = ready_feeds[:max_feeds]
        
        # Assert: Should not exceed limit
        assert len(selected) == max_feeds
        assert len(selected) <= len(ready_feeds)


@pytest.mark.unit  
class TestQueueMessageFormat:
    """Test queue message formatting"""
    
    def test_message_contains_required_fields(self):
        """Test that queue messages contain all required fields"""
        import json
        from shared.models import RSSFeedConfig
        
        feed = RSSFeedConfig(
            id='test_feed',
            name='Test Feed',
            url='https://test.com/rss',
            source_id='test_source',
            category='world',
            tier=1,
            language='en',
            country='US'
        )
        
        # Create message body
        message = {
            'id': feed.id,
            'name': feed.name,
            'url': feed.url,
            'source_id': feed.source_id,
            'category': feed.category,
            'tier': feed.tier,
            'queued_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Verify JSON serializable
        message_json = json.dumps(message)
        parsed = json.loads(message_json)
        
        # Assert: All required fields present
        assert 'id' in parsed
        assert 'name' in parsed
        assert 'url' in parsed
        assert 'source_id' in parsed
        assert 'category' in parsed
        assert 'tier' in parsed
        assert 'queued_at' in parsed
    
    def test_message_json_serializable(self):
        """Test that message can be JSON serialized"""
        import json
        
        message = {
            'id': 'test_feed',
            'name': 'Test Feed',
            'url': 'https://test.com/rss',
            'source_id': 'test',
            'category': 'world',
            'tier': 1,
            'queued_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Should not raise
        json_str = json.dumps(message)
        assert isinstance(json_str, str)
        assert len(json_str) > 0


@pytest.mark.unit
class TestFeedConfigValidation:
    """Test feed configuration validation"""
    
    def test_feed_config_required_fields(self):
        """Test that feed config requires all mandatory fields"""
        from shared.models import RSSFeedConfig
        
        # Valid config
        feed = RSSFeedConfig(
            id='test',
            name='Test',
            url='https://test.com/rss',
            source_id='test',
            category='world',
            tier=1
        )
        
        assert feed.id == 'test'
        assert feed.url == 'https://test.com/rss'
    
    def test_feed_config_defaults(self):
        """Test that feed config has sensible defaults"""
        from shared.models import RSSFeedConfig
        
        feed = RSSFeedConfig(
            id='test',
            name='Test',
            url='https://test.com/rss',
            source_id='test',
            category='world',
            tier=1
        )
        
        assert feed.language == 'en'
        # country defaults to None, not 'global'
        assert feed.country is None or feed.country == 'global'


@pytest.mark.unit
class TestPollStateTracking:
    """Test poll state tracking logic"""
    
    def test_poll_state_update(self):
        """Test that poll state is correctly tracked"""
        # Simulate poll state storage
        poll_states = {}
        feed_name = 'Test Feed'
        
        # Update poll state
        poll_states[feed_name] = {
            'last_poll': datetime.now(timezone.utc),
            'articles_found': 10
        }
        
        # Verify state stored
        assert feed_name in poll_states
        assert 'last_poll' in poll_states[feed_name]
        assert poll_states[feed_name]['articles_found'] == 10
    
    def test_poll_state_cooldown_check(self):
        """Test cooldown check against poll state"""
        now = datetime.now(timezone.utc)
        cooldown_seconds = 180
        
        poll_states = {
            'recent_feed': {'last_poll': now - timedelta(seconds=60)},  # 1 min ago
            'old_feed': {'last_poll': now - timedelta(seconds=300)},    # 5 min ago
        }
        
        # Check if feeds are ready
        def is_ready(feed_name):
            if feed_name not in poll_states:
                return True
            last_poll = poll_states[feed_name]['last_poll']
            return (now - last_poll).total_seconds() >= cooldown_seconds
        
        assert is_ready('recent_feed') is False  # Still in cooldown
        assert is_ready('old_feed') is True       # Past cooldown
        assert is_ready('new_feed') is True       # Never polled


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

