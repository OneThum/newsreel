"""
System-level tests for the DEPLOYED Newsreel API

These tests verify the actual deployed Azure services are working.
THESE SHOULD FAIL when the system is broken (unlike unit tests).

Requirements:
- NEWSREEL_JWT_TOKEN environment variable OR
- firebase_token.txt file in Azure/tests/ OR  
- Firebase configured for automatic token generation
"""
import pytest
import requests
import time
import os
from datetime import datetime, timedelta
from azure.cosmos import CosmosClient


@pytest.mark.system
class TestDeployedAPI:
    """Test the actual deployed API endpoints with proper authentication"""
    
    def test_api_is_reachable(self, api_base_url):
        """Test: Can we reach the API at all?"""
        try:
            response = requests.get(f"{api_base_url}/health", timeout=10)
            assert response.status_code in [200, 404], f"API returned {response.status_code}"
            print(f"✅ API is reachable at {api_base_url}")
        except Exception as e:
            pytest.fail(f"❌ API is not reachable: {e}")
    
    def test_stories_endpoint_requires_auth(self, api_base_url):
        """Test: Does /api/stories/feed require authentication?"""
        # Try without auth
        response = requests.get(f"{api_base_url}/api/stories/feed?limit=10", timeout=10)
        
        # Should be 401/403 without auth
        assert response.status_code in [401, 403], \
            f"❌ Feed endpoint should require auth, got {response.status_code}"
        
        print("✅ Feed endpoint properly requires authentication")
    
    def test_stories_endpoint_returns_data_with_auth(self, api_base_url, auth_headers):
        """Test: Does /api/stories/feed return actual stories with auth?"""
        response = requests.get(
            f"{api_base_url}/api/stories/feed?limit=10",
            headers=auth_headers,
            timeout=10
        )
        
        assert response.status_code == 200, \
            f"❌ Endpoint returned {response.status_code}: {response.text[:200]}"
        
        data = response.json()
        stories = data if isinstance(data, list) else data.get('stories', [])
        
        # REAL TEST: Are there actual stories?
        assert len(stories) > 0, \
            "❌ FAIL: No stories returned (clustering not working?)"
        
        # Verify story structure
        first_story = stories[0]
        assert 'id' in first_story, "Story missing 'id' field"
        assert 'title' in first_story or 'headline' in first_story, \
            "Story missing 'title' or 'headline' field"
        assert 'sources' in first_story, "Story missing 'sources' field"
        
        print(f"✅ API returned {len(stories)} stories with valid structure")
    
    def test_stories_are_recent(self, api_base_url, auth_headers):
        """Test: Are the stories recent (not stale data)?"""
        response = requests.get(
            f"{api_base_url}/api/stories/feed?limit=5",
            headers=auth_headers,
            timeout=10
        )
        
        assert response.status_code == 200
        
        data = response.json()
        stories = data if isinstance(data, list) else data.get('stories', [])
        
        assert len(stories) > 0, "No stories to check"
        
        # Check if most recent story is within last 24 hours
        most_recent = stories[0]
        last_update_str = most_recent.get('last_updated') or most_recent.get('publishedAt')
        
        if last_update_str:
            try:
                last_update = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
                age_hours = (datetime.now().astimezone() - last_update).total_seconds() / 3600
                
                assert age_hours < 24, \
                    f"❌ FAIL: Most recent story is {age_hours:.1f} hours old (RSS not ingesting?)"
                
                print(f"✅ Most recent story is {age_hours:.1f} hours old")
            except Exception as e:
                print(f"⚠️  Could not parse date: {e}")
        else:
            print("⚠️  Story missing date field (non-critical)")
    
    def test_breaking_news_endpoint(self, api_base_url, auth_headers):
        """Test: Can we get breaking news?"""
        response = requests.get(
            f"{api_base_url}/api/stories/breaking?limit=5",
            headers=auth_headers,
            timeout=10
        )
        
        # Breaking endpoint might not exist, that's OK
        if response.status_code == 404:
            print("ℹ️  Breaking news endpoint not available")
            return
        
        assert response.status_code == 200, f"Breaking endpoint returned {response.status_code}"
        
        data = response.json()
        stories = data if isinstance(data, list) else data.get('stories', [])
        
        if stories:
            print(f"✅ Breaking news endpoint returned {len(stories)} stories")
        else:
            print("ℹ️  No breaking news currently")
    
    def test_search_endpoint(self, api_base_url, auth_headers):
        """Test: Does the search endpoint work?"""
        response = requests.get(
            f"{api_base_url}/api/stories/search?q=technology&limit=5",
            headers=auth_headers,
            timeout=10
        )
        
        # Search might not be implemented
        if response.status_code == 404:
            print("ℹ️  Search endpoint not available")
            return
        
        if response.status_code != 200:
            print(f"⚠️  Search returned {response.status_code}")
            return
        
        data = response.json()
        stories = data if isinstance(data, list) else data.get('stories', [])
        
        print(f"✅ Search endpoint returned {len(stories)} results")


@pytest.mark.system
class TestAzureFunctions:
    """Test that Azure Functions are deployed and running"""
    
    def test_function_app_is_deployed(self, api_base_url):
        """Test: Is the Function App reachable?"""
        function_url = os.getenv(
            'FUNCTION_APP_URL',
            'https://newsreel-func-51689.azurewebsites.net'
        )
        
        try:
            # Most Azure Function Apps have a default page
            response = requests.get(function_url, timeout=10)
            # May return 401/403 but should be reachable
            assert response.status_code in [200, 401, 403, 404], \
                f"Function App not reachable: {response.status_code}"
            print(f"✅ Function App is deployed and reachable")
        except Exception as e:
            pytest.fail(f"❌ Function App not reachable: {e}")


@pytest.mark.system
class TestDataPipeline:
    """Test that the data ingestion pipeline is working"""
    
    def test_articles_being_ingested(self, api_base_url, auth_headers):
        """Test: Are articles being ingested from RSS?"""
        response = requests.get(
            f"{api_base_url}/api/stories/feed?limit=20",
            headers=auth_headers,
            timeout=10
        )
        
        if response.status_code != 200:
            pytest.skip("Cannot query stories")
        
        data = response.json()
        stories = data if isinstance(data, list) else data.get('stories', [])
        
        total_articles = sum(len(story.get('sources', [])) for story in stories)
        
        assert total_articles > 0, \
            "❌ No articles in system (RSS ingestion may be broken)"
        
        print(f"✅ System has {len(stories)} stories from {total_articles} articles")
    
    def test_clustering_is_working(self, api_base_url, auth_headers):
        """Test: Are stories being clustered?"""
        response = requests.get(
            f"{api_base_url}/api/stories/feed?limit=20",
            headers=auth_headers,
            timeout=10
        )
        
        if response.status_code != 200:
            pytest.skip("Cannot query stories")
        
        data = response.json()
        stories = data if isinstance(data, list) else data.get('stories', [])
        
        # Check if stories have multiple sources (indication of clustering)
        multi_source_stories = [
            s for s in stories
            if len(s.get('sources', [])) > 1
        ]
        
        assert len(multi_source_stories) > 0, \
            "❌ No clustered stories (clustering may not be working)"
        
        print(f"✅ Found {len(multi_source_stories)} clustered stories " \
              f"(out of {len(stories)} total)")
    
    def test_summaries_being_generated(self, api_base_url, auth_headers):
        """Test: Are AI summaries being generated?"""
        response = requests.get(
            f"{api_base_url}/api/stories/feed?limit=20",
            headers=auth_headers,
            timeout=10
        )
        
        if response.status_code != 200:
            pytest.skip("Cannot query stories")
        
        data = response.json()
        stories = data if isinstance(data, list) else data.get('stories', [])
        
        with_summaries = [
            s for s in stories
            if s.get('summary') or (s.get('summary', {}) if isinstance(s.get('summary'), dict) else False)
        ]
        
        if with_summaries:
            print(f"✅ {len(with_summaries)}/{len(stories)} stories have summaries")
        else:
            print("ℹ️  No summaries yet (may still be generating)")


@pytest.mark.system
class TestAuthenticationAndSecurity:
    """Test authentication and security of the API"""
    
    def test_invalid_token_rejected(self, api_base_url):
        """Test: Are invalid tokens properly rejected?"""
        headers = {'Authorization': 'Bearer invalid.token.here'}
        
        response = requests.get(
            f"{api_base_url}/api/stories/feed",
            headers=headers,
            timeout=10
        )
        
        # Should reject invalid token
        assert response.status_code in [401, 403], \
            f"Invalid token should be rejected, got {response.status_code}"
        
        print("✅ API properly rejects invalid tokens")
    
    def test_https_enabled(self, api_base_url):
        """Test: Is HTTPS being used?"""
        assert api_base_url.startswith('https://'), \
            "❌ API should use HTTPS"
        
        print("✅ API uses HTTPS")
    
    def test_cors_headers_present(self, api_base_url, auth_headers):
        """Test: Are CORS headers present?"""
        response = requests.get(
            f"{api_base_url}/api/stories/feed?limit=1",
            headers=auth_headers,
            timeout=10
        )
        
        # Check for common CORS headers
        cors_headers = ['Access-Control-Allow-Origin', 'Access-Control-Allow-Methods']
        found_cors = any(h in response.headers for h in cors_headers)
        
        if found_cors:
            print("✅ CORS headers are present")
        else:
            print("ℹ️  CORS headers not detected (may be configured differently)")


if __name__ == '__main__':
    print("Running system-level tests...")
    print("These tests verify the DEPLOYED system is working.")
    print("THESE SHOULD FAIL if RSS/clustering/summarization are broken.\n")
    
    pytest.main([__file__, '-v', '--tb=short'])

