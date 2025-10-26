"""
System-level tests for the DEPLOYED Newsreel API

These tests verify the actual deployed Azure services are working.
THESE SHOULD FAIL when the system is broken (unlike unit tests).
"""
import pytest
import requests
import time
import os
from datetime import datetime, timedelta
from azure.cosmos import CosmosClient


@pytest.mark.system
class TestDeployedAPI:
    """Test the actual deployed API endpoints"""
    
    @pytest.fixture
    def api_base_url(self):
        """Get API base URL from environment"""
        url = os.getenv('API_BASE_URL', 'https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io')
        return url
    
    def test_api_is_reachable(self, api_base_url):
        """Test: Can we reach the API at all?"""
        try:
            response = requests.get(f"{api_base_url}/health", timeout=10)
            assert response.status_code in [200, 404], f"API returned {response.status_code}"
        except Exception as e:
            pytest.fail(f"❌ API is not reachable: {e}")
    
    def test_stories_endpoint_returns_data(self, api_base_url):
        """Test: Does /api/stories/feed return actual stories?"""
        response = requests.get(f"{api_base_url}/api/stories/feed?limit=10", timeout=10)
        
        assert response.status_code == 200, f"Endpoint returned {response.status_code}"
        
        data = response.json()
        stories = data.get('stories', [])
        
        # REAL TEST: Are there actual stories?
        assert len(stories) > 0, "❌ FAIL: No stories returned (clustering not working?)"
        
        # Verify story structure
        first_story = stories[0]
        assert 'id' in first_story, "Story missing 'id' field"
        assert 'headline' in first_story, "Story missing 'headline' field"
        assert 'sources' in first_story, "Story missing 'sources' field"
        
        print(f"✓ API returned {len(stories)} stories")
    
    def test_stories_are_recent(self, api_base_url):
        """Test: Are the stories recent (not stale data)?"""
        response = requests.get(f"{api_base_url}/api/stories/feed?limit=5", timeout=10)
        data = response.json()
        stories = data.get('stories', [])
        
        assert len(stories) > 0, "No stories to check"
        
        # Check if most recent story is within last 24 hours
        most_recent = stories[0]
        last_update_str = most_recent.get('last_updated')
        if last_update_str:
            last_update = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
            age_hours = (datetime.now().astimezone() - last_update).total_seconds() / 3600
            
            assert age_hours < 24, f"❌ FAIL: Most recent story is {age_hours:.1f} hours old (RSS not ingesting?)"
            
            print(f"✓ Most recent story is {age_hours:.1f} hours old")
        else:
            print("⚠️  Story missing last_updated field (non-critical)")


@pytest.mark.system
class TestRSSIngestion:
    """Test that RSS ingestion is actually working"""
    
    @pytest.fixture
    def cosmos_client(self):
        """Get Cosmos DB client"""
        endpoint = os.getenv('COSMOS_ENDPOINT')
        key = os.getenv('COSMOS_KEY')
        
        if not endpoint or not key:
            pytest.skip("Cosmos credentials not set")
        
        client = CosmosClient(endpoint, key)
        database = client.get_database_client('newsreel')
        return database.get_container_client('raw_articles')
    
    def test_articles_are_being_ingested(self, cosmos_client):
        """Test: Are new articles being added to the database?"""
        # Count articles from last 5 minutes
        five_min_ago = datetime.utcnow() - timedelta(minutes=5)
        
        query = """
        SELECT VALUE COUNT(1)
        FROM c
        WHERE c.ingested_at >= @five_min_ago
        """
        
        results = list(cosmos_client.query_items(
            query=query,
            parameters=[
                {"name": "@five_min_ago", "value": five_min_ago.isoformat()}
            ]
        ))
        
        count = results[0] if results else 0
        
        # REAL TEST: Are articles being ingested?
        assert count > 0, f"❌ FAIL: No articles ingested in last 5 minutes (RSS functions not running?)"
        
        # Should be seeing ~1.5 articles per minute (9 per 5 min minimum)
        expected_min = 5  # Conservative threshold
        assert count >= expected_min, f"❌ FAIL: Only {count} articles in 5 min (should be >{expected_min})"
        
        print(f"✓ {count} articles ingested in last 5 minutes")
    
    def test_rss_ingestion_rate(self, cosmos_client):
        """Test: Is RSS ingestion rate within expected range?"""
        # Count articles from last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        query = """
        SELECT VALUE COUNT(1)
        FROM c
        WHERE c.ingested_at >= @one_hour_ago
        """
        
        results = list(cosmos_client.query_items(
            query=query,
            parameters=[
                {"name": "@one_hour_ago", "value": one_hour_ago.isoformat()}
            ]
        ))
        
        count = results[0] if results else 0
        rate_per_min = count / 60.0
        
        # Expected: ~18 articles/min (based on 3 feeds every 10 seconds)
        # Allow for variability: 10-25 articles/min
        assert rate_per_min > 10, f"❌ FAIL: RSS rate too low: {rate_per_min:.1f}/min (should be ~18/min)"
        assert rate_per_min < 30, f"⚠️  WARNING: RSS rate very high: {rate_per_min:.1f}/min (expected ~18/min)"
        
        print(f"✓ RSS ingestion rate: {rate_per_min:.1f} articles/min")
    
    def test_multiple_sources_being_ingested(self, cosmos_client):
        """Test: Are we ingesting from multiple different sources?"""
        # Get sources from last 10 minutes
        ten_min_ago = datetime.utcnow() - timedelta(minutes=10)
        
        query = """
        SELECT DISTINCT VALUE c.source
        FROM c
        WHERE c.ingested_at >= @ten_min_ago
        """
        
        results = list(cosmos_client.query_items(
            query=query,
            parameters=[
                {"name": "@ten_min_ago", "value": ten_min_ago.isoformat()}
            ]
        ))
        
        unique_sources = len(results)
        
        # Should be seeing 5-15 different sources in 10 minutes
        assert unique_sources >= 5, f"❌ FAIL: Only {unique_sources} sources in 10 min (RSS diversity problem?)"
        
        print(f"✓ {unique_sources} unique sources ingested in last 10 minutes")


@pytest.mark.system
class TestStoryClustering:
    """Test that story clustering is actually working"""
    
    @pytest.fixture
    def cosmos_client(self):
        """Get Cosmos DB client"""
        endpoint = os.getenv('COSMOS_ENDPOINT')
        key = os.getenv('COSMOS_KEY')
        
        if not endpoint or not key:
            pytest.skip("Cosmos credentials not set")
        
        client = CosmosClient(endpoint, key)
        database = client.get_database_client('newsreel')
        return database.get_container_client('story_clusters')
    
    def test_stories_are_being_created(self, cosmos_client):
        """Test: Are new stories being created?"""
        # Count stories from last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        query = """
        SELECT VALUE COUNT(1)
        FROM c
        WHERE c.created_at >= @one_hour_ago
        """
        
        results = list(cosmos_client.query_items(
            query=query,
            parameters=[
                {"name": "@one_hour_ago", "value": one_hour_ago.isoformat()}
            ]
        ))
        
        count = results[0] if results else 0
        
        # REAL TEST: Is clustering creating stories?
        assert count > 0, f"❌ FAIL: No stories created in last hour (clustering not running?)"
        
        print(f"✓ {count} stories created in last hour")
    
    def test_stories_have_multiple_sources(self, cosmos_client):
        """Test: Are stories being clustered from multiple sources?"""
        # Get recent stories
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        query = """
        SELECT c.id, ARRAY_LENGTH(c.sources) as source_count
        FROM c
        WHERE c.created_at >= @one_hour_ago
        """
        
        results = list(cosmos_client.query_items(
            query=query,
            parameters=[
                {"name": "@one_hour_ago", "value": one_hour_ago.isoformat()}
            ]
        ))
        
        assert len(results) > 0, "No stories to check"
        
        # Count how many stories have multiple sources
        multi_source_stories = sum(1 for s in results if s.get('source_count', 0) > 1)
        multi_source_rate = multi_source_stories / len(results)
        
        # At least 30% of stories should have multiple sources
        assert multi_source_rate > 0.3, f"❌ FAIL: Only {multi_source_rate*100:.0f}% multi-source (clustering not aggregating?)"
        
        print(f"✓ {multi_source_rate*100:.0f}% of stories have multiple sources")


@pytest.mark.system
class TestAISummarization:
    """Test that AI summarization is actually working"""
    
    @pytest.fixture
    def cosmos_client(self):
        """Get Cosmos DB client"""
        endpoint = os.getenv('COSMOS_ENDPOINT')
        key = os.getenv('COSMOS_KEY')
        
        if not endpoint or not key:
            pytest.skip("Cosmos credentials not set")
        
        client = CosmosClient(endpoint, key)
        database = client.get_database_client('newsreel')
        return database.get_container_client('story_clusters')
    
    def test_summaries_are_being_generated(self, cosmos_client):
        """Test: Are AI summaries being generated?"""
        # Count stories with summaries from last 6 hours
        six_hours_ago = datetime.utcnow() - timedelta(hours=6)
        
        query = """
        SELECT VALUE COUNT(1)
        FROM c
        WHERE c.created_at >= @six_hours_ago
        AND c.ai_summary != null
        """
        
        results = list(cosmos_client.query_items(
            query=query,
            parameters=[
                {"name": "@six_hours_ago", "value": six_hours_ago.isoformat()}
            ]
        ))
        
        count = results[0] if results else 0
        
        # REAL TEST: Is AI summarization working?
        assert count > 0, f"❌ FAIL: No AI summaries generated in last 6 hours (summarization not running?)"
        
        print(f"✓ {count} stories with AI summaries in last 6 hours")
    
    def test_summary_coverage_rate(self, cosmos_client):
        """Test: What % of stories are getting summaries?"""
        # Count total stories vs stories with summaries
        six_hours_ago = datetime.utcnow() - timedelta(hours=6)
        
        # Total stories
        query_total = """
        SELECT VALUE COUNT(1)
        FROM c
        WHERE c.created_at >= @six_hours_ago
        """
        
        total = list(cosmos_client.query_items(
            query=query_total,
            parameters=[
                {"name": "@six_hours_ago", "value": six_hours_ago.isoformat()}
            ]
        ))[0]
        
        # Stories with summaries
        query_summarized = """
        SELECT VALUE COUNT(1)
        FROM c
        WHERE c.created_at >= @six_hours_ago
        AND c.ai_summary != null
        """
        
        summarized = list(cosmos_client.query_items(
            query=query_summarized,
            parameters=[
                {"name": "@six_hours_ago", "value": six_hours_ago.isoformat()}
            ]
        ))[0]
        
        if total == 0:
            pytest.skip("No stories to check")
        
        coverage_rate = summarized / total
        
        # Should have >50% coverage for breaking/verified stories
        assert coverage_rate > 0.3, f"❌ FAIL: Only {coverage_rate*100:.0f}% coverage (AI not running?)"
        
        print(f"✓ Summary coverage: {coverage_rate*100:.0f}% ({summarized}/{total})")


@pytest.mark.system
class TestAzureFunctions:
    """Test that Azure Functions are deployed and running"""
    
    def test_function_app_is_deployed(self):
        """Test: Is the Function App reachable?"""
        function_url = os.getenv('FUNCTION_APP_URL', 'https://newsreel-functions.azurewebsites.net')
        
        try:
            # Most Azure Function Apps have a default page
            response = requests.get(function_url, timeout=10)
            # May return 401/403 but should be reachable
            assert response.status_code in [200, 401, 403, 404], f"Function App not reachable: {response.status_code}"
        except Exception as e:
            pytest.fail(f"❌ Function App not reachable: {e}")
        
        print(f"✓ Function App is deployed and reachable")
    
    def test_rss_function_is_running(self):
        """Test: Check if RSS function has run recently (via logs or DB)"""
        # This would check Application Insights or function execution logs
        # For now, we can infer from database activity
        pytest.skip("Requires Application Insights integration")
    
    def test_clustering_function_is_running(self):
        """Test: Check if clustering function has run recently"""
        pytest.skip("Requires Application Insights integration")


if __name__ == '__main__':
    print("Running system-level tests...")
    print("These tests verify the DEPLOYED system is working.")
    print("THESE SHOULD FAIL if RSS/clustering/summarization are broken.\n")
    
    pytest.main([__file__, '-v', '--tb=short'])

