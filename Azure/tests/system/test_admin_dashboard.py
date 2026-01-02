"""
Admin Dashboard API Tests

Tests the /api/admin/metrics endpoint with comprehensive coverage
for system health, clustering pipeline, and monitoring data.
"""

import pytest
import requests
import os
from datetime import datetime, timezone


@pytest.fixture(scope="module")
def admin_auth_headers():
    """Load admin auth token from file"""
    token_file = os.path.join(os.path.dirname(__file__), '..', 'firebase_token.txt')
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            token = f.read().strip()
        return {'Authorization': f'Bearer {token}'}
    
    # Fallback to environment
    token = os.getenv('FIREBASE_TOKEN')
    if token:
        return {'Authorization': f'Bearer {token}'}
    
    pytest.skip("No admin auth token available")


@pytest.fixture(scope="module")
def api_base_url():
    """Get API base URL"""
    return os.getenv(
        'API_URL',
        'https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io'
    )


def get_admin_metrics(api_base_url, headers):
    """Helper to get admin metrics, skipping if not admin"""
    response = requests.get(
        f"{api_base_url}/api/admin/metrics",
        headers=headers,
        timeout=30
    )
    
    if response.status_code == 403:
        pytest.skip("Test user is not an admin - skipping admin metrics test")
    
    return response


@pytest.mark.system
class TestAdminMetricsEndpoint:
    """Test the admin metrics endpoint"""
    
    def test_admin_metrics_requires_auth(self, api_base_url):
        """Test that admin metrics requires authentication"""
        response = requests.get(f"{api_base_url}/api/admin/metrics", timeout=30)
        assert response.status_code in [401, 403], \
            f"Admin endpoint should require auth, got {response.status_code}"
    
    def test_admin_metrics_returns_data(self, api_base_url, admin_auth_headers):
        """Test that admin metrics returns valid data"""
        response = get_admin_metrics(api_base_url, admin_auth_headers)
        
        assert response.status_code == 200, \
            f"Admin metrics failed: {response.status_code} - {response.text[:200]}"
        
        data = response.json()
        assert 'timestamp' in data, "Missing timestamp"
        assert 'system_health' in data, "Missing system_health"
        assert 'database' in data, "Missing database stats"
        assert 'rss_ingestion' in data, "Missing RSS ingestion stats"
        assert 'clustering' in data, "Missing clustering stats"
        assert 'summarization' in data, "Missing summarization stats"


@pytest.mark.system
class TestAdminSystemHealth:
    """Test system health metrics"""
    
    def test_system_health_structure(self, api_base_url, admin_auth_headers):
        """Test system health has correct structure"""
        response = get_admin_metrics(api_base_url, admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        health = data['system_health']
        
        assert 'overall_status' in health
        assert 'api_health' in health
        assert 'functions_health' in health
        assert 'database_health' in health
        
        # Validate status values
        valid_statuses = ['healthy', 'degraded', 'down', 'unknown', 'error']
        assert health['overall_status'] in valid_statuses
        assert health['api_health'] in valid_statuses
        assert health['database_health'] in valid_statuses
    
    def test_api_is_healthy(self, api_base_url, admin_auth_headers):
        """Test that API reports itself as healthy"""
        response = get_admin_metrics(api_base_url, admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # API should always be healthy if we can reach it
        assert data['system_health']['api_health'] == 'healthy', \
            "API should report itself as healthy"


@pytest.mark.system
class TestAdminClusteringStats:
    """Test clustering statistics in admin metrics"""
    
    def test_clustering_stats_structure(self, api_base_url, admin_auth_headers):
        """Test clustering stats has all required fields"""
        response = get_admin_metrics(api_base_url, admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        clustering = data['clustering']
        
        # Core clustering metrics
        assert 'match_rate' in clustering, "Missing match_rate"
        assert 'avg_sources_per_story' in clustering, "Missing avg_sources_per_story"
        assert 'stories_created_24h' in clustering, "Missing stories_created_24h"
        assert 'stories_updated_24h' in clustering, "Missing stories_updated_24h"
        
        # Pipeline monitoring metrics
        assert 'unprocessed_articles' in clustering, "Missing unprocessed_articles"
        assert 'processed_articles' in clustering, "Missing processed_articles"
        assert 'processing_rate_per_hour' in clustering, "Missing processing_rate_per_hour"
        assert 'oldest_unprocessed_age_minutes' in clustering, "Missing oldest_unprocessed_age_minutes"
        assert 'clustering_health' in clustering, "Missing clustering_health"
    
    def test_clustering_health_valid_values(self, api_base_url, admin_auth_headers):
        """Test clustering health has valid status value"""
        response = get_admin_metrics(api_base_url, admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        valid_health_statuses = ['healthy', 'degraded', 'stalled', 'error', 'unknown']
        assert data['clustering']['clustering_health'] in valid_health_statuses
    
    def test_clustering_metrics_reasonable_values(self, api_base_url, admin_auth_headers):
        """Test clustering metrics have reasonable values"""
        response = get_admin_metrics(api_base_url, admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        clustering = data['clustering']
        
        # Match rate should be between 0 and 1
        assert 0 <= clustering['match_rate'] <= 1, \
            f"Match rate out of range: {clustering['match_rate']}"
        
        # Avg sources should be >= 1
        assert clustering['avg_sources_per_story'] >= 1, \
            "Average sources per story should be at least 1"
        
        # Counts should be non-negative
        assert clustering['unprocessed_articles'] >= 0
        assert clustering['processed_articles'] >= 0
        assert clustering['processing_rate_per_hour'] >= 0


@pytest.mark.system
class TestAdminDatabaseStats:
    """Test database statistics in admin metrics"""
    
    def test_database_stats_structure(self, api_base_url, admin_auth_headers):
        """Test database stats has correct structure"""
        response = get_admin_metrics(api_base_url, admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        db = data['database']
        
        assert 'total_articles' in db
        assert 'total_stories' in db
        assert 'stories_with_summaries' in db
        assert 'unique_sources' in db
        assert 'stories_by_status' in db
    
    def test_database_has_data(self, api_base_url, admin_auth_headers):
        """Test that database contains actual data"""
        response = get_admin_metrics(api_base_url, admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        db = data['database']
        
        # Should have some articles and stories
        assert db['total_articles'] > 0, "No articles in database"
        assert db['total_stories'] > 0, "No stories in database"
        assert db['unique_sources'] > 0, "No unique sources"


@pytest.mark.system
class TestAdminRSSIngestionStats:
    """Test RSS ingestion statistics"""
    
    def test_rss_stats_structure(self, api_base_url, admin_auth_headers):
        """Test RSS ingestion stats has correct structure"""
        response = get_admin_metrics(api_base_url, admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        rss = data['rss_ingestion']
        
        assert 'total_feeds' in rss
        assert 'last_run' in rss
        assert 'articles_per_hour' in rss
        assert 'success_rate' in rss
        assert 'top_sources' in rss
    
    def test_rss_success_rate_valid(self, api_base_url, admin_auth_headers):
        """Test RSS success rate is within valid range"""
        response = get_admin_metrics(api_base_url, admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Success rate should be between 0 and 1
        success_rate = data['rss_ingestion']['success_rate']
        assert 0 <= success_rate <= 1, \
            f"RSS success rate out of range: {success_rate}"


@pytest.mark.system
class TestAdminSummarizationStats:
    """Test summarization statistics"""
    
    def test_summarization_stats_structure(self, api_base_url, admin_auth_headers):
        """Test summarization stats has correct structure"""
        response = get_admin_metrics(api_base_url, admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        summary = data['summarization']
        
        assert 'coverage' in summary
        assert 'avg_generation_time' in summary
        assert 'summaries_generated_24h' in summary
        assert 'avg_word_count' in summary
        assert 'cost_24h' in summary
    
    def test_summarization_coverage_valid(self, api_base_url, admin_auth_headers):
        """Test summarization coverage is within valid range"""
        response = get_admin_metrics(api_base_url, admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Coverage should be between 0 and 1
        coverage = data['summarization']['coverage']
        assert 0 <= coverage <= 1, \
            f"Summarization coverage out of range: {coverage}"
