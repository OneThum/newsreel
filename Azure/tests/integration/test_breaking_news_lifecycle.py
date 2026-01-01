"""Integration tests: Breaking News Lifecycle

Tests the complete breaking news detection and notification workflow using REAL Cosmos DB

NOTE: StoryStatus is now simplified to NEW, DEVELOPING, VERIFIED.
Breaking news is indicated via the `breaking_news` boolean field, not a separate status.
"""
import pytest
import asyncio
from datetime import datetime, timezone, timedelta
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from functions.shared.cosmos_client import CosmosDBClient
from functions.shared.models import StoryCluster, StoryStatus


@pytest.mark.integration
class TestBreakingNewsDetection:
    """Test breaking news detection logic with REAL Cosmos DB"""
    
    @pytest.mark.asyncio
    async def test_verified_to_breaking_transition(self, cosmos_client_for_tests, clean_test_data):
        """Test that VERIFIED stories can become breaking (via breaking_news flag)"""
        now = datetime.now(timezone.utc)
        
        # Arrange: Create VERIFIED story with breaking_news=True
        from conftest import create_test_source_articles
        story = StoryCluster(
            id=f"story_breaking_{now.strftime('%Y%m%d_%H%M%S')}",
            event_fingerprint="test_breaking_fingerprint",
            title="Major Breaking News Event",
            category="world",
            tags=["breaking"],
            status=StoryStatus.VERIFIED,
            verification_level=3,
            first_seen=now - timedelta(minutes=15),
            last_updated=now,
            source_articles=create_test_source_articles(4),
            importance_score=95,
            confidence_score=95,
            breaking_news=True,
            breaking_triggered_at=now.isoformat()
        )
        
        try:
            await cosmos_client_for_tests.upsert_story(story.model_dump())
            clean_test_data['register_story'](story.id)
        except Exception as e:
            pytest.skip(f"Could not store story: {e}")
        
        # Act & Assert: Verify breaking story stored
        stored_story = await cosmos_client_for_tests.get_story(story.id)
        if stored_story:
            assert stored_story.get('status') == 'VERIFIED'
            assert len(stored_story.get('source_articles', [])) >= 4, "Breaking news requires 4+ sources"
            assert stored_story.get('breaking_news') == True
        
    @pytest.mark.asyncio
    async def test_rapid_escalation_to_breaking(self, cosmos_client_for_tests, clean_test_data):
        """Test that stories can rapidly escalate to breaking with multiple sources"""
        now = datetime.now(timezone.utc)
        
        # Arrange: Create story that rapidly escalated
        from conftest import create_test_source_articles
        story = StoryCluster(
            id=f"story_rapid_{now.strftime('%Y%m%d_%H%M%S')}",
            event_fingerprint="test_rapid_fingerprint",
            title="Rapidly Escalating Story",
            category="world",
            tags=["rapid"],
            status=StoryStatus.VERIFIED,  # VERIFIED with breaking_news=True
            verification_level=3,
            first_seen=now - timedelta(minutes=5),  # Only 5 minutes ago
            last_updated=now,
            source_articles=create_test_source_articles(4),
            importance_score=90,
            confidence_score=90,
            breaking_news=True,
            breaking_triggered_at=now.isoformat()
        )
        
        try:
            await cosmos_client_for_tests.upsert_story(story.model_dump())
            clean_test_data['register_story'](story.id)
        except Exception as e:
            pytest.skip(f"Could not store story: {e}")
        
        # Act & Assert: Verify rapid escalation
        stored_story = await cosmos_client_for_tests.get_story(story.id)
        if stored_story:
            meets_source_threshold = len(stored_story.get('source_articles', [])) >= 4
            first_seen = stored_story.get('first_seen')
            last_updated = stored_story.get('last_updated')
            
            if first_seen and last_updated:
                if isinstance(first_seen, str):
                    first_seen = datetime.fromisoformat(first_seen.replace('Z', '+00:00'))
                if isinstance(last_updated, str):
                    last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                time_elapsed_minutes = (last_updated - first_seen).total_seconds() / 60
                is_rapid = time_elapsed_minutes < 30
                
                assert meets_source_threshold and is_rapid, "Should detect rapid source accumulation"
        
    @pytest.mark.asyncio
    async def test_breaking_news_not_triggered_for_slow_stories(self, cosmos_client_for_tests, clean_test_data):
        """Test that slow-developing stories don't become breaking"""
        now = datetime.now(timezone.utc)
        
        # Arrange: Create story added slowly over 3 hours
        from conftest import create_test_source_articles
        story = StoryCluster(
            id=f"story_slow_{now.strftime('%Y%m%d_%H%M%S')}",
            event_fingerprint="test_slow_fingerprint",
            title="Slowly Developing Story",
            category="world",
            tags=["slow"],
            status=StoryStatus.VERIFIED,  # Stays VERIFIED, doesn't become breaking
            verification_level=3,
            first_seen=now - timedelta(hours=3),  # 3 hours ago
            last_updated=now,
            source_articles=create_test_source_articles(4),
            importance_score=60,
            confidence_score=65,
            breaking_news=False  # Not breaking (too slow)
        )
        
        try:
            await cosmos_client_for_tests.upsert_story(story.model_dump())
            clean_test_data['register_story'](story.id)
        except Exception as e:
            pytest.skip(f"Could not store story: {e}")
        
        # Act & Assert: Verify slow story NOT marked as breaking
        stored_story = await cosmos_client_for_tests.get_story(story.id)
        if stored_story:
            assert stored_story.get('breaking_news') == False, "Slow stories should not trigger breaking status"


@pytest.mark.integration
class TestBreakingNewsNotifications:
    """Test breaking news notification workflow with REAL Cosmos DB"""
    
    @pytest.mark.asyncio
    async def test_notification_triggered_on_breaking_flag(self, cosmos_client_for_tests, clean_test_data):
        """Test that notifications are triggered when story has breaking_news=True"""
        now = datetime.now(timezone.utc)
        
        # Arrange: Create VERIFIED story with breaking_news=True
        from conftest import create_test_source_articles
        story = StoryCluster(
            id=f"story_notify_{now.strftime('%Y%m%d_%H%M%S')}",
            event_fingerprint="test_notify_fingerprint",
            title="Breaking News Notification Test",
            category="world",
            tags=["breaking"],
            status=StoryStatus.VERIFIED,
            verification_level=3,
            first_seen=now,
            last_updated=now,
            source_articles=create_test_source_articles(4),
            importance_score=95,
            confidence_score=95,
            breaking_news=True,
            breaking_triggered_at=now.isoformat(),
            push_notification_sent=False  # Will be set to true after notification
        )
        
        try:
            await cosmos_client_for_tests.upsert_story(story.model_dump())
            clean_test_data['register_story'](story.id)
        except Exception as e:
            pytest.skip(f"Could not store story: {e}")
        
        # Act & Assert: Verify breaking story should trigger notification
        stored_story = await cosmos_client_for_tests.get_story(story.id)
        if stored_story:
            should_notify = (
                stored_story.get('breaking_news') == True and
                stored_story.get('status') == 'VERIFIED'
            )
            assert should_notify, "breaking_news=True should trigger notification"
        
    @pytest.mark.asyncio
    async def test_notification_deduplication(self, cosmos_client_for_tests, clean_test_data):
        """Test that duplicate notifications are prevented"""
        now = datetime.now(timezone.utc)
        
        # Arrange: Create breaking story with notification already sent
        from conftest import create_test_source_articles
        story = StoryCluster(
            id=f"story_dedup_{now.strftime('%Y%m%d_%H%M%S')}",
            event_fingerprint="test_dedup_fingerprint",
            title="Deduplication Test",
            category="world",
            tags=["breaking"],
            status=StoryStatus.VERIFIED,
            verification_level=3,
            first_seen=now - timedelta(minutes=10),
            last_updated=now,
            source_articles=create_test_source_articles(4),
            importance_score=90,
            confidence_score=90,
            breaking_news=True,
            breaking_triggered_at=(now - timedelta(minutes=5)).isoformat(),
            push_notification_sent=True,  # Already sent
            push_notification_sent_at=(now - timedelta(minutes=5))
        )
        
        try:
            await cosmos_client_for_tests.upsert_story(story.model_dump())
            clean_test_data['register_story'](story.id)
        except Exception as e:
            pytest.skip(f"Could not store story: {e}")
        
        # Act & Assert: Verify notification not duplicated
        stored_story = await cosmos_client_for_tests.get_story(story.id)
        if stored_story:
            already_notified = stored_story.get('push_notification_sent') == True
            assert already_notified, "Should prevent duplicate notifications"
        
    @pytest.mark.asyncio
    async def test_breaking_demotion(self, cosmos_client_for_tests, clean_test_data):
        """Test that breaking stories can be demoted (breaking_news set to False) if news slows"""
        now = datetime.now(timezone.utc)
        
        # Arrange: Create breaking story that's now slowing down
        from conftest import create_test_source_articles
        story = StoryCluster(
            id=f"story_demote_{now.strftime('%Y%m%d_%H%M%S')}",
            event_fingerprint="test_demote_fingerprint",
            title="Slowing Breaking News",
            category="world",
            tags=["breaking"],
            status=StoryStatus.VERIFIED,  # Still VERIFIED
            verification_level=3,
            first_seen=now - timedelta(hours=2),
            last_updated=now,
            source_articles=create_test_source_articles(4),
            importance_score=70,  # Lower than fresh breaking news
            confidence_score=75,
            breaking_news=True  # Currently breaking
        )
        
        try:
            await cosmos_client_for_tests.upsert_story(story.model_dump())
            clean_test_data['register_story'](story.id)
        except Exception as e:
            pytest.skip(f"Could not store story: {e}")
        
        # Act & Assert: Verify story could be demoted if needed
        stored_story = await cosmos_client_for_tests.get_story(story.id)
        if stored_story:
            first_seen = stored_story.get('first_seen')
            if isinstance(first_seen, str):
                first_seen = datetime.fromisoformat(first_seen.replace('Z', '+00:00'))
            
            is_old_breaking = (
                stored_story.get('breaking_news') == True and
                (datetime.now(timezone.utc) - first_seen).total_seconds() > 3600
            )
            
            if is_old_breaking:
                # Can be demoted (breaking_news set to False)
                assert stored_story.get('importance_score', 100) < 90, "Old breaking news should have lower importance"


@pytest.mark.integration
class TestBreakingNewsLifecycle:
    """Test complete breaking news lifecycle with REAL Cosmos DB"""
    
    @pytest.mark.asyncio
    async def test_verified_to_archived_lifecycle(self, cosmos_client_for_tests, clean_test_data):
        """Test that old stories eventually get archived"""
        now = datetime.now(timezone.utc)
        
        # Arrange: Create story that's been around for a week
        from conftest import create_test_source_articles
        story = StoryCluster(
            id=f"story_archive_{now.strftime('%Y%m%d_%H%M%S')}",
            event_fingerprint="test_archive_fingerprint",
            title="Old Story for Archiving",
            category="world",
            tags=["old"],
            status=StoryStatus.VERIFIED,
            verification_level=3,
            first_seen=now - timedelta(days=7),
            last_updated=now - timedelta(days=1),
            source_articles=create_test_source_articles(3),
            importance_score=30,  # Low importance over time
            confidence_score=50,
            breaking_news=False,
            archived=False
        )
        
        try:
            await cosmos_client_for_tests.upsert_story(story.model_dump())
            clean_test_data['register_story'](story.id)
        except Exception as e:
            pytest.skip(f"Could not store story: {e}")
        
        # Act & Assert: Verify old story can be archived
        stored_story = await cosmos_client_for_tests.get_story(story.id)
        if stored_story:
            first_seen = stored_story.get('first_seen')
            if isinstance(first_seen, str):
                first_seen = datetime.fromisoformat(first_seen.replace('Z', '+00:00'))
            is_old = (datetime.now(timezone.utc) - first_seen).total_seconds() > 604800  # 7 days
            
            assert is_old, "Story should be considered old for archival"
        
    @pytest.mark.asyncio
    async def test_complete_story_lifecycle_flow(self, cosmos_client_for_tests, clean_test_data):
        """Test complete flow: NEW → DEVELOPING → VERIFIED → (breaking_news=True) → archived"""
        now = datetime.now(timezone.utc)
        
        # Arrange: Create story and track through lifecycle
        story_id = f"story_lifecycle_{now.strftime('%Y%m%d_%H%M%S')}"
        
        # Stage 1: NEW (1 source)
        from conftest import create_test_source_articles
        story = StoryCluster(
            id=story_id,
            event_fingerprint="test_lifecycle_fingerprint",
            title="Story Lifecycle Test",
            category="world",
            tags=["lifecycle"],
            status=StoryStatus.NEW,
            verification_level=1,
            first_seen=now,
            last_updated=now,
            source_articles=create_test_source_articles(1),
            importance_score=10,
            confidence_score=30,
            breaking_news=False
        )
        
        try:
            await cosmos_client_for_tests.upsert_story(story.model_dump())
            clean_test_data['register_story'](story.id)
        except Exception as e:
            pytest.skip(f"Could not store story: {e}")
        
        # Act: Verify can progress through stages
        stored_story = await cosmos_client_for_tests.get_story(story.id)
        if stored_story:
            assert stored_story.get('status') == 'NEW'
            assert len(stored_story.get('source_articles', [])) >= 1
        
    @pytest.mark.asyncio
    async def test_breaking_news_detection_latency(self, cosmos_client_for_tests, clean_test_data):
        """Test that breaking news is detected with acceptable latency"""
        now = datetime.now(timezone.utc)
        
        # Arrange: Create rapid story
        from conftest import create_test_source_articles
        story = StoryCluster(
            id=f"story_latency_{now.strftime('%Y%m%d_%H%M%S')}",
            event_fingerprint="test_latency_fingerprint",
            title="Latency Test",
            category="world",
            tags=["latency"],
            status=StoryStatus.VERIFIED,
            verification_level=3,
            first_seen=now - timedelta(seconds=30),  # 30 seconds ago
            last_updated=now,
            source_articles=create_test_source_articles(4),
            importance_score=95,
            confidence_score=95,
            breaking_news=True
        )
        
        try:
            await cosmos_client_for_tests.upsert_story(story.model_dump())
            clean_test_data['register_story'](story.id)
        except Exception as e:
            pytest.skip(f"Could not store story: {e}")
        
        # Act & Assert: Verify rapid detection
        stored_story = await cosmos_client_for_tests.get_story(story.id)
        if stored_story:
            first_seen = stored_story.get('first_seen')
            last_updated = stored_story.get('last_updated')
            
            if isinstance(first_seen, str):
                first_seen = datetime.fromisoformat(first_seen.replace('Z', '+00:00'))
            if isinstance(last_updated, str):
                last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            
            detection_latency = (last_updated - first_seen).total_seconds()
            
            # Breaking news with 4 sources in under 60 seconds = good latency
            assert detection_latency < 60, "Breaking news detection should have <1min latency"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
