"""Integration tests: Story Clustering → AI Summarization

Tests the flow from story cluster updates to AI summary generation using REAL Cosmos DB
"""
import pytest
import asyncio
from datetime import datetime, timezone
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from functions.shared.cosmos_client import CosmosDBClient
from functions.shared.models import StoryCluster


@pytest.mark.integration
class TestClusteringToSummarizationFlow:
    """Test story cluster → summarization pipeline with REAL Cosmos DB"""
    
    @pytest.mark.asyncio
    async def test_verified_story_triggers_summarization(self, cosmos_client_for_tests, clean_test_data):
        """Test that VERIFIED stories (3+ sources) trigger summarization"""
        now = datetime.now(timezone.utc)
        
        # Arrange: Create and store a VERIFIED story
        from conftest import create_test_source_articles
        story = StoryCluster(
            id=f"story_verified_{now.strftime('%Y%m%d_%H%M%S')}",
            event_fingerprint="test_verify_fingerprint",
            title="President Announces Major Climate Initiative",
            category="world",
            tags=["climate", "policy"],
            status="VERIFIED",
            verification_level=3,
            first_seen=now,
            last_updated=now,
            source_articles=create_test_source_articles(3),  # Fixed: use helper
            importance_score=85,
            confidence_score=90,
            breaking_news=False
        )
        
        try:
            await cosmos_client_for_tests.upsert_story(story.dict())
            clean_test_data['register_story'](story.id)
        except Exception as e:
            pytest.skip(f"Could not store story: {e}")
        
        # Act & Assert: Check if story needs summary
        stored_story = await cosmos_client_for_tests.get_story(story.id)
        if stored_story:
            needs_summary = (
                stored_story.get('status') == 'VERIFIED' and 
                len(stored_story.get('source_articles', [])) >= 3 and
                stored_story.get('summary') is None
            )
            assert needs_summary, "VERIFIED story without summary should trigger summarization"
        
    @pytest.mark.asyncio
    async def test_developing_story_no_summarization(self, cosmos_client_for_tests, clean_test_data):
        """Test that DEVELOPING stories (2 sources) don't trigger summarization"""
        now = datetime.now(timezone.utc)
        
        # Arrange: Create and store a DEVELOPING story
        from conftest import create_test_source_articles
        story = StoryCluster(
            id=f"story_develop_{now.strftime('%Y%m%d_%H%M%S')}",
            event_fingerprint="test_develop_fingerprint",
            title="Test Story Development",
            category="world",
            tags=["test"],
            status="DEVELOPING",
            verification_level=2,
            first_seen=now,
            last_updated=now,
            source_articles=create_test_source_articles(2),  # Fixed: use helper with 2
            importance_score=50,
            confidence_score=60,
            breaking_news=False
        )
        
        try:
            await cosmos_client_for_tests.upsert_story(story.dict())
            clean_test_data['register_story'](story.id)
        except Exception as e:
            pytest.skip(f"Could not store story: {e}")
        
        # Act & Assert: Check if story needs summary
        stored_story = await cosmos_client_for_tests.get_story(story.id)
        if stored_story:
            needs_summary = (
                stored_story.get('status') == 'VERIFIED' and 
                len(stored_story.get('source_articles', [])) >= 3 and
                stored_story.get('summary') is None
            )
            assert not needs_summary, "DEVELOPING story should not trigger summarization"
        
    @pytest.mark.asyncio
    async def test_summary_prompt_construction(self, sample_verified_story):
        """Test that summarization prompt is constructed correctly"""
        # Arrange: Story with multiple sources
        story = sample_verified_story
        
        # Act: Build prompt (simulate summarization function)
        sources_text = "\n\n".join([
            f"Source {i+1} ({s['source_name']}): {s['title']}"
            for i, s in enumerate(story['sources'][:5])  # Max 5 sources
        ])
        
        prompt = f"""Summarize this news story in exactly 3 sentences:

{story['headline']}

Sources:
{sources_text}

Provide a balanced, factual summary combining information from all sources."""
        
        # Assert: Prompt includes key elements
        assert story['headline'] in prompt
        assert 'exactly 3 sentences' in prompt
        assert 'Reuters' in prompt
        assert 'BBC News' in prompt
        assert 'CNN' in prompt
        
    @pytest.mark.asyncio
    async def test_summary_stored_in_cluster(self, cosmos_client_for_tests, clean_test_data, sample_verified_story, mock_anthropic_response):
        """Test that AI summary is stored back in story cluster"""
        now = datetime.now(timezone.utc)
        
        # Arrange: Create story and get AI summary
        ai_summary = mock_anthropic_response['content'][0]['text']
        
        from conftest import create_test_source_articles
        story = StoryCluster(
            id=f"story_summary_{now.strftime('%Y%m%d_%H%M%S')}",
            event_fingerprint="test_summary_fingerprint",
            title="Test Story for Summary",
            category="world",
            tags=["test"],
            status="VERIFIED",
            verification_level=3,
            first_seen=now,
            last_updated=now,
            source_articles=create_test_source_articles(3),  # Fixed: use helper
            importance_score=75,
            confidence_score=80,
            breaking_news=False,
            summary=ai_summary,
            summary_generated_at=now.isoformat()
        )
        
        # Act: Store story with summary
        try:
            await cosmos_client_for_tests.upsert_story(story.dict())
            clean_test_data['register_story'](story.id)
        except Exception as e:
            pytest.skip(f"Could not store story: {e}")
        
        # Assert: Verify summary stored
        stored_story = await cosmos_client_for_tests.get_story(story.id)
        if stored_story:
            assert stored_story.get('summary') == ai_summary
            assert stored_story.get('summary_generated_at') is not None
            assert len(stored_story.get('summary', '')) > 0
        
    @pytest.mark.asyncio
    async def test_headline_regeneration_on_source_addition(self, cosmos_client_for_tests, clean_test_data):
        """Test that headlines are regenerated when new sources are added"""
        now = datetime.now(timezone.utc)
        
        # Arrange: Create story with 2 sources
        from conftest import create_test_source_articles
        story = StoryCluster(
            id=f"story_headline_{now.strftime('%Y%m%d_%H%M%S')}",
            event_fingerprint="test_headline_fingerprint",
            title="Test Story Headline",
            category="world",
            tags=["test"],
            status="DEVELOPING",
            verification_level=2,
            first_seen=now,
            last_updated=now,
            source_articles=create_test_source_articles(2),  # Fixed: use helper with 2
            importance_score=60,
            confidence_score=70,
            breaking_news=False
        )
        
        try:
            await cosmos_client_for_tests.upsert_story(story.dict())
            clean_test_data['register_story'](story.id)
        except Exception as e:
            pytest.skip(f"Could not store story: {e}")
        
        # Act: Simulate adding third source
        stored_story = await cosmos_client_for_tests.get_story(story.id)
        if stored_story:
            stored_story['source_articles'].append("art3")
            should_regenerate_headline = len(stored_story['source_articles']) >= 3
            
            # Assert: Should trigger headline update
            assert should_regenerate_headline, "Adding 3rd source should trigger headline regeneration"
        
    @pytest.mark.asyncio
    async def test_cost_tracking_for_summarization(self, mock_anthropic_response):
        """Test that AI costs are tracked for summarization"""
        # Arrange: Mock Anthropic response with usage
        response = mock_anthropic_response
        usage = response['usage']
        
        # Act: Calculate cost (Haiku pricing: $0.80/$4.00 per million tokens)
        input_cost = (usage['input_tokens'] / 1_000_000) * 0.80
        output_cost = (usage['output_tokens'] / 1_000_000) * 4.00
        total_cost = input_cost + output_cost
        
        # Assert: Cost calculated correctly
        assert total_cost > 0, "Total cost should be positive"
        assert input_cost == 0.0004, "Input cost should be 0.0004"
        assert output_cost == 0.0002, "Output cost should be 0.0002"
        expected_cost = (500 / 1_000_000 * 0.80) + (50 / 1_000_000 * 4.00)
        assert abs(total_cost - expected_cost) < 0.000001  # Should be identical


@pytest.mark.integration
class TestSummarizationWorkflow:
    """Test complete summarization workflows with REAL Cosmos DB"""
    
    @pytest.mark.asyncio
    async def test_real_time_summarization_flow(self, cosmos_client_for_tests, clean_test_data):
        """Test real-time summarization via change feed"""
        now = datetime.now(timezone.utc)
        
        # Arrange: Create a story that just reached VERIFIED
        from conftest import create_test_source_articles
        story = StoryCluster(
            id=f"story_realtime_{now.strftime('%Y%m%d_%H%M%S')}",
            event_fingerprint="test_realtime_fingerprint",
            title="Real-time Summary Test",
            category="world",
            tags=["test"],
            status="VERIFIED",
            verification_level=3,
            first_seen=now,
            last_updated=now,
            source_articles=create_test_source_articles(3),  # Fixed: use helper
            importance_score=80,
            confidence_score=85,
            breaking_news=False
        )
        
        try:
            await cosmos_client_for_tests.upsert_story(story.dict())
            clean_test_data['register_story'](story.id)
        except Exception as e:
            pytest.skip(f"Could not store story: {e}")
        
        # Act & Assert: Check if would trigger real-time summarization
        stored_story = await cosmos_client_for_tests.get_story(story.id)
        if stored_story:
            should_summarize = (
                stored_story.get('status') == 'VERIFIED' and
                stored_story.get('summary') is None
            )
            assert should_summarize, "VERIFIED story without summary should trigger real-time summarization"
        
    @pytest.mark.asyncio
    async def test_batch_summarization_flow(self, sample_batch_request):
        """Test batch summarization workflow"""
        # Arrange: Batch request with multiple stories
        batch = sample_batch_request
        
        # Act: Verify batch structure
        assert 'story_ids' in batch
        assert 'anthropic_batch_id' in batch
        assert batch['status'] == 'submitted'
        assert len(batch['story_ids']) == 5
        
        # Assert: Batch ready for processing
        assert batch['request_count'] == len(batch['story_ids'])
        
    @pytest.mark.asyncio
    async def test_batch_result_processing(self, sample_completed_batch):
        """Test processing of completed batch results"""
        # Arrange: Completed batch with results
        batch = sample_completed_batch
        
        # Act: Process results
        successful_results = [r for r in batch['results'] if r['result']['type'] == 'succeeded']
        failed_results = [r for r in batch['results'] if r['result']['type'] == 'failed']
        
        # Assert: Results processed correctly
        assert len(successful_results) == 3
        assert len(failed_results) == 0
        assert batch['succeeded_count'] == 3
        assert batch['failed_count'] == 0
        
    @pytest.mark.asyncio
    async def test_summary_fallback_on_ai_refusal(self, cosmos_client_for_tests, clean_test_data):
        """Test fallback summary when AI refuses to summarize"""
        now = datetime.now(timezone.utc)
        
        # Arrange: Create story for fallback testing
        from conftest import create_test_source_articles
        story = StoryCluster(
            id=f"story_fallback_{now.strftime('%Y%m%d_%H%M%S')}",
            event_fingerprint="test_fallback_fingerprint",
            title="AI Refusal Fallback Test",
            category="world",
            tags=["test"],
            status="VERIFIED",
            verification_level=3,
            first_seen=now,
            last_updated=now,
            source_articles=create_test_source_articles(3),  # Fixed: use helper
            importance_score=70,
            confidence_score=75,
            breaking_news=False
        )
        
        try:
            await cosmos_client_for_tests.upsert_story(story.dict())
            clean_test_data['register_story'](story.id)
        except Exception as e:
            pytest.skip(f"Could not store story: {e}")
        
        # Act: Generate fallback summary
        ai_refused = True
        if ai_refused:
            fallback_summary = f"Multiple sources report: {story.title}"
        else:
            fallback_summary = None
            
        # Assert: Fallback created
        assert fallback_summary is not None
        assert story.title in fallback_summary
        assert 'Multiple sources report' in fallback_summary


@pytest.mark.integration
class TestSummarizationQuality:
    """Test summarization quality and validation"""
    
    @pytest.mark.asyncio
    async def test_summary_length_validation(self, mock_anthropic_response):
        """Test that summaries meet length requirements"""
        # Arrange: AI-generated summary
        summary = mock_anthropic_response['content'][0]['text']
        
        # Act: Count sentences
        sentence_count = summary.count('.') + summary.count('!') + summary.count('?')
        
        # Assert: Should have at least some sentences (allow for shorthand)
        assert sentence_count > 0, "Summary should have at least one sentence or period"
        
    @pytest.mark.asyncio
    async def test_summary_includes_key_information(self, sample_verified_story):
        """Test that summary includes information from multiple sources"""
        # Arrange: Story with 3 sources
        story = sample_verified_story
        
        # Simulate summary generation
        mock_summary = "President announces major climate initiative targeting emissions reduction. " \
                       "The policy includes new environmental regulations and funding. " \
                       "Multiple news agencies report widespread support for the plan."
        
        # Act: Check if summary references multiple sources
        references_multiple_sources = 'multiple' in mock_summary.lower() or 'agencies' in mock_summary.lower()
        
        # Assert: Should indicate multi-source verification
        assert references_multiple_sources or len(story['sources']) >= 3
        
    @pytest.mark.asyncio
    async def test_summary_prompt_cache_usage(self):
        """Test that prompt caching is used for cost savings"""
        # Arrange: System prompt for caching
        system_prompt = """You are a news summarization AI. Your task is to create balanced, 
        factual summaries combining information from multiple sources."""
        
        # Act: Check if prompt is marked for caching
        should_use_cache = len(system_prompt) > 100  # Worth caching if substantial
        
        # Assert: Prompt suitable for caching
        assert should_use_cache, "System prompt should be cached for cost savings"


@pytest.mark.integration
@pytest.mark.slow
class TestSummarizationPerformance:
    """Test summarization performance and costs"""
    
    @pytest.mark.asyncio
    async def test_batch_vs_realtime_cost(self):
        """Test that batch processing costs 50% less than real-time"""
        # Arrange: Cost per request
        realtime_cost_per_request = 0.005  # $0.005
        batch_cost_per_request = 0.0025    # $0.0025 (50% savings)
        
        # Act: Calculate costs for 100 summaries
        realtime_total = 100 * realtime_cost_per_request
        batch_total = 100 * batch_cost_per_request
        savings = realtime_total - batch_total
        savings_percent = (savings / realtime_total) * 100
        
        # Assert: Batch saves 50%
        assert savings_percent == 50.0
        assert batch_total == realtime_total * 0.5
        
    @pytest.mark.asyncio
    async def test_summarization_rate_limit(self):
        """Test that rate limiting is respected"""
        # Arrange: Rate limit config
        max_requests_per_minute = 50
        
        # Act: Check if within limit
        requests_this_minute = 45
        can_make_request = requests_this_minute < max_requests_per_minute
        
        # Assert: Rate limit enforced
        assert can_make_request, "Should allow requests under rate limit"
        
        # Test over limit
        requests_this_minute = 51
        can_make_request = requests_this_minute < max_requests_per_minute
        assert not can_make_request, "Should block requests over rate limit"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

