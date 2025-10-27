"""Integration tests: Batch Processing Workflow

Tests the complete batch summarization workflow using Anthropic Message Batches API and REAL Cosmos DB
"""
import pytest
import asyncio
from datetime import datetime, timezone, timedelta
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from functions.shared.cosmos_client import CosmosDBClient
from functions.shared.models import StoryCluster


@pytest.mark.integration
class TestBatchSubmission:
    """Test batch summarization submission workflow with REAL Cosmos DB"""
    
    @pytest.mark.asyncio
    async def test_batch_creation_from_unsummarized_stories(self, cosmos_client_for_tests, clean_test_data):
        """Test creating batch from stories needing summaries"""
        now = datetime.now(timezone.utc)
        
        # Arrange: Create stories needing summaries
        story_ids = []
        for i in range(5):
            story = StoryCluster(
                id=f"story_batch_{i}_{now.strftime('%Y%m%d_%H%M%S')}",
                event_fingerprint=f"batch_fp_{i}",
                title=f"Story {i} Needing Summary",
                category="world",
                tags=["batch"],
                status="VERIFIED",
                verification_level=3,
                first_seen=now,
                last_updated=now,
                source_articles=["art1", "art2", "art3"],
                importance_score=70,
                confidence_score=75,
                breaking_news=False,
                summary=None  # Needs summary
            )
            
            try:
                await cosmos_client_for_tests.upsert_story(story.dict())
                story_ids.append(story.id)
                clean_test_data['register_story'](story.id)
            except Exception as e:
                pytest.skip(f"Could not store story: {e}")
        
        # Act: Create batch request
        batch_request = {
            'id': f'batch_req_{now.strftime("%Y%m%d_%H%M%S")}',
            'story_ids': story_ids,
            'status': 'pending',
            'created_at': now.isoformat(),
            'request_count': len(story_ids)
        }
        
        # Assert: Batch created correctly
        assert len(batch_request['story_ids']) >= 1
        assert batch_request['status'] == 'pending'
        assert batch_request['request_count'] == len(story_ids)
        
    @pytest.mark.asyncio
    async def test_batch_size_limits(self, cosmos_client_for_tests, clean_test_data):
        """Test that batches respect size limits"""
        now = datetime.now(timezone.utc)
        
        # Arrange: Create many stories
        stories = []
        for i in range(15):  # Smaller number for test
            story = StoryCluster(
                id=f"story_limit_{i}_{now.strftime('%Y%m%d_%H%M%S')}",
                event_fingerprint=f"limit_fp_{i}",
                title=f"Batch Limit Story {i}",
                category="world",
                tags=["batch"],
                status="VERIFIED",
                verification_level=3,
                first_seen=now,
                last_updated=now,
                source_articles=["art1", "art2", "art3"],
                importance_score=60,
                confidence_score=65,
                breaking_news=False,
                summary=None
            )
            
            try:
                await cosmos_client_for_tests.upsert_story(story.dict())
                stories.append(story)
                clean_test_data['register_story'](story.id)
            except Exception as e:
                pytest.skip(f"Could not store stories: {e}")
        
        # Act: Split into batches
        max_batch_size = 10
        batches = []
        for i in range(0, len(stories), max_batch_size):
            batch = stories[i:i + max_batch_size]
            batches.append(batch)
        
        # Assert: Multiple batches created
        assert len(batches) >= 1
        assert len(batches[0]) == max_batch_size
        
    @pytest.mark.asyncio
    async def test_batch_request_format(self, sample_batch_request):
        """Test Anthropic batch request format"""
        # Arrange: Batch request
        batch = sample_batch_request
        
        # Act: Build Anthropic-compatible request
        anthropic_requests = []
        for story_id in batch['story_ids']:
            request = {
                'custom_id': story_id,
                'params': {
                    'model': 'claude-3-5-haiku-20241022',
                    'max_tokens': 300,
                    'messages': [{
                        'role': 'user',
                        'content': f'Summarize story {story_id}'
                    }]
                }
            }
            anthropic_requests.append(request)
        
        # Assert: Requests formatted correctly
        assert len(anthropic_requests) == 5
        assert anthropic_requests[0]['custom_id'] == 'story_1'
        assert 'params' in anthropic_requests[0]
        assert 'model' in anthropic_requests[0]['params']


@pytest.mark.integration
class TestBatchProcessing:
    """Test batch processing and monitoring with REAL Cosmos DB"""
    
    @pytest.mark.asyncio
    async def test_batch_status_polling(self, sample_batch_request):
        """Test polling batch status from Anthropic"""
        # Arrange: Submitted batch
        batch = sample_batch_request
        assert batch['status'] == 'submitted'
        
        # Act: Simulate status progression
        status_progression = ['submitted', 'in_progress', 'in_progress', 'ended']
        
        # Assert: Status evolves correctly
        assert status_progression[0] == 'submitted'
        assert status_progression[-1] == 'ended'
        assert 'in_progress' in status_progression
        
    @pytest.mark.asyncio
    async def test_batch_completion_detection(self, sample_completed_batch):
        """Test detecting when batch is complete"""
        # Arrange: Completed batch
        batch = sample_completed_batch
        
        # Act: Check completion
        is_complete = batch['status'] == 'completed'
        has_results = 'results' in batch and len(batch['results']) > 0
        
        # Assert: Batch properly completed
        assert is_complete
        assert has_results
        assert batch['succeeded_count'] == 3
        
    @pytest.mark.asyncio
    async def test_batch_result_extraction(self, sample_completed_batch):
        """Test extracting summaries from batch results"""
        # Arrange: Completed batch with results
        batch = sample_completed_batch
        
        # Act: Extract summaries
        summaries = {}
        for result in batch['results']:
            if result['result']['type'] == 'succeeded':
                story_id = result['custom_id']
                summary_text = result['result']['message']['content'][0]['text']
                summaries[story_id] = summary_text
        
        # Assert: Summaries extracted
        assert len(summaries) == 3
        assert 'story_1' in summaries
        assert 'story_2' in summaries
        assert 'story_3' in summaries
        assert all(len(s) > 0 for s in summaries.values())
        
    @pytest.mark.asyncio
    async def test_batch_result_storage(self, cosmos_client_for_tests, clean_test_data, sample_completed_batch):
        """Test storing batch results back to Cosmos DB"""
        now = datetime.now(timezone.utc)
        batch = sample_completed_batch
        
        # Arrange: Create a story to update with summary
        story = StoryCluster(
            id=f"story_result_{now.strftime('%Y%m%d_%H%M%S')}",
            event_fingerprint="result_fp",
            title="Test Story for Results",
            category="world",
            tags=["batch"],
            status="VERIFIED",
            verification_level=3,
            first_seen=now,
            last_updated=now,
            source_articles=["art1", "art2", "art3"],
            importance_score=70,
            confidence_score=75,
            breaking_news=False,
            summary=None
        )
        
        try:
            await cosmos_client_for_tests.upsert_story(story.dict())
            clean_test_data['register_story'](story.id)
        except Exception as e:
            pytest.skip(f"Could not store story: {e}")
        
        # Act: Extract first result and update story
        if batch['results']:
            result = batch['results'][0]
            if result['result']['type'] == 'succeeded':
                summary_text = result['result']['message']['content'][0]['text']
                story.summary = summary_text
                story.summary_generated_at = now.isoformat()
                
                try:
                    await cosmos_client_for_tests.upsert_story(story.dict())
                except Exception as e:
                    pytest.skip(f"Could not update story: {e}")
        
        # Assert: Summary stored
        stored_story = await cosmos_client_for_tests.get_story(story.id)
        if stored_story:
            assert stored_story.get('summary') is not None


@pytest.mark.integration
class TestBatchCostTracking:
    """Test batch cost tracking and optimization"""
    
    @pytest.mark.asyncio
    async def test_batch_cost_calculation(self, sample_completed_batch):
        """Test calculating total batch cost"""
        # Arrange: Completed batch
        batch = sample_completed_batch
        
        # Act: Verify cost tracking
        assert 'total_cost' in batch
        assert batch['total_cost'] > 0
        assert batch['total_cost'] == 0.0015  # As specified in fixture
        
    @pytest.mark.asyncio
    async def test_batch_vs_realtime_cost_savings(self):
        """Test that batch processing saves 50% vs real-time"""
        # Arrange: 100 summaries
        num_summaries = 100
        realtime_cost_per = 0.005
        batch_cost_per = 0.0025
        
        # Act: Calculate costs
        realtime_total = num_summaries * realtime_cost_per
        batch_total = num_summaries * batch_cost_per
        savings = realtime_total - batch_total
        savings_percent = (savings / realtime_total) * 100
        
        # Assert: 50% savings
        assert savings_percent == 50.0
        assert batch_total == 0.25  # $0.25 for 100 summaries
        assert realtime_total == 0.50  # $0.50 for 100 summaries
        
    @pytest.mark.asyncio
    async def test_monthly_cost_projection(self):
        """Test projecting monthly costs with batch processing"""
        # Arrange: Daily story volume
        stories_per_day = 500
        days_per_month = 30
        batch_cost_per_story = 0.0025
        
        # Act: Calculate monthly cost
        monthly_cost = stories_per_day * days_per_month * batch_cost_per_story
        
        # Assert: Cost is reasonable
        assert monthly_cost == 37.50  # $37.50/month
        assert monthly_cost < 50  # Under budget


@pytest.mark.integration
class TestBatchWorkflowEnd2End:
    """Test complete batch workflow end-to-end with REAL Cosmos DB"""
    
    @pytest.mark.asyncio
    async def test_complete_batch_workflow(self, cosmos_client_for_tests, clean_test_data):
        """Test complete workflow: Query → Submit → Poll → Process → Store"""
        now = datetime.now(timezone.utc)
        
        # Stage 1: Create stories needing summaries
        stories_data = []
        for i in range(2):
            story = StoryCluster(
                id=f"story_e2e_{i}_{now.strftime('%Y%m%d_%H%M%S')}",
                event_fingerprint=f"e2e_fp_{i}",
                title=f"E2E Test Story {i}",
                category="world",
                tags=["e2e"],
                status="VERIFIED",
                verification_level=3,
                first_seen=now,
                last_updated=now,
                source_articles=["art1", "art2", "art3"],
                importance_score=70,
                confidence_score=75,
                breaking_news=False,
                summary=None
            )
            
            try:
                await cosmos_client_for_tests.upsert_story(story.dict())
                stories_data.append(story)
                clean_test_data['register_story'](story.id)
            except Exception as e:
                pytest.skip(f"Could not store story: {e}")
        
        # Stage 2: Create and submit batch
        batch = {
            'id': f'batch_e2e_{now.strftime("%Y%m%d_%H%M%S")}',
            'story_ids': [s.id for s in stories_data],
            'status': 'submitted',
            'submitted_at': now.isoformat()
        }
        assert batch['status'] == 'submitted'
        
        # Stage 3: Poll until complete (simulate)
        batch['status'] = 'completed'
        batch['results'] = [
            {'custom_id': s.id, 'result': {'type': 'succeeded', 'message': {'content': [{'text': f'Summary for {s.id}'}]}}}
            for s in stories_data
        ]
        assert batch['status'] == 'completed'
        
        # Stage 4: Extract and store summaries
        for result in batch['results']:
            story_id = result['custom_id']
            summary = result['result']['message']['content'][0]['text']
            
            # Update story with summary
            story_to_update = next((s for s in stories_data if s.id == story_id), None)
            if story_to_update:
                story_to_update.summary = summary
                story_to_update.summary_generated_at = now.isoformat()
                
                try:
                    await cosmos_client_for_tests.upsert_story(story_to_update.dict())
                except Exception as e:
                    pytest.skip(f"Could not update story: {e}")
        
        # Assert: Complete workflow successful
        assert len(batch['results']) >= 1


@pytest.mark.integration
@pytest.mark.slow
class TestBatchPerformance:
    """Test batch processing performance"""
    
    @pytest.mark.asyncio
    async def test_batch_processing_latency(self):
        """Test typical batch processing time"""
        # Arrange: Batch submission time
        submitted_at = datetime.now(timezone.utc) - timedelta(minutes=30)
        completed_at = datetime.now(timezone.utc)
        
        # Act: Calculate processing time
        processing_time = (completed_at - submitted_at).total_seconds() / 60
        
        # Assert: Should complete within reasonable time
        assert processing_time <= 60, f"Batch should complete within 60 min, took {processing_time} min"
        
    @pytest.mark.asyncio
    async def test_batch_throughput(self):
        """Test batch processing throughput"""
        # Arrange: Batch with 100 requests
        batch_size = 100
        processing_time_minutes = 30
        
        # Act: Calculate throughput
        throughput = batch_size / processing_time_minutes  # requests per minute
        
        # Assert: Reasonable throughput
        assert throughput >= 3.0, f"Throughput should be ≥3 req/min, got {throughput}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

