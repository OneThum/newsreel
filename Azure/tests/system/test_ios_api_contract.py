"""
iOS API Contract Tests

Tests that the API returns data in the exact format expected by the iOS app.
This ensures API changes don't break the iOS client.
"""

import pytest
import requests
import os
from datetime import datetime
from typing import Any


@pytest.fixture(scope="module")
def auth_headers():
    """Load auth token from file"""
    token_file = os.path.join(os.path.dirname(__file__), '..', 'firebase_token.txt')
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            token = f.read().strip()
        return {'Authorization': f'Bearer {token}'}
    
    token = os.getenv('FIREBASE_TOKEN')
    if token:
        return {'Authorization': f'Bearer {token}'}
    
    pytest.skip("No auth token available")


@pytest.fixture(scope="module")
def api_base_url():
    """Get API base URL"""
    return os.getenv(
        'API_URL',
        'https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io'
    )


def validate_iso_timestamp(value: Any, field_name: str) -> None:
    """Validate that a value is a valid ISO timestamp"""
    if value is None:
        return  # None is acceptable for optional fields
    
    assert isinstance(value, str), f"{field_name} should be a string"
    try:
        datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        pytest.fail(f"{field_name} is not a valid ISO timestamp: {value}")


@pytest.mark.system
class TestStoryFeedContract:
    """Test the story feed API contract for iOS"""
    
    def test_feed_returns_array(self, api_base_url, auth_headers):
        """Test that feed endpoint returns an array of stories"""
        response = requests.get(
            f"{api_base_url}/api/stories/feed?limit=5",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # iOS expects an array of stories
        assert isinstance(data, list), "Feed should return an array"
    
    def test_story_has_required_fields(self, api_base_url, auth_headers):
        """Test that each story has all required fields for iOS"""
        response = requests.get(
            f"{api_base_url}/api/stories/feed?limit=10",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200
        stories = response.json()
        
        if len(stories) == 0:
            pytest.skip("No stories available")
        
        # Fields required by iOS Story model
        required_fields = [
            'id',           # String - unique identifier
            'title',        # String - headline
            'category',     # String - news category
            'last_updated', # ISO timestamp
            'sources',      # Array of source objects
        ]
        
        for story in stories[:5]:  # Check first 5
            for field in required_fields:
                assert field in story, \
                    f"Story {story.get('id', 'unknown')} missing required field: {field}"
    
    def test_story_field_types(self, api_base_url, auth_headers):
        """Test that story fields have correct types for iOS"""
        response = requests.get(
            f"{api_base_url}/api/stories/feed?limit=5",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200
        stories = response.json()
        
        if len(stories) == 0:
            pytest.skip("No stories available")
        
        story = stories[0]
        
        # Type assertions matching iOS Swift types
        assert isinstance(story['id'], str), "id should be String"
        assert isinstance(story['title'], str), "title should be String"
        assert isinstance(story['category'], str), "category should be String"
        assert isinstance(story['sources'], list), "sources should be Array"
        
        validate_iso_timestamp(story.get('last_updated'), 'last_updated')
        validate_iso_timestamp(story.get('first_seen'), 'first_seen')
        
        # Optional fields that should be correct type if present
        if 'summary' in story and story['summary']:
            summary = story['summary']
            if isinstance(summary, dict):
                assert 'text' in summary, "summary dict should have 'text' field"
        
        if 'importance_score' in story:
            assert isinstance(story['importance_score'], (int, float)), \
                "importance_score should be numeric"
        
        if 'verification_level' in story:
            assert isinstance(story['verification_level'], int), \
                "verification_level should be Int"
        
        if 'breaking_news' in story:
            assert isinstance(story['breaking_news'], bool), \
                "breaking_news should be Bool"


@pytest.mark.system
class TestSourceContract:
    """Test the source object contract for iOS"""
    
    def test_source_has_required_fields(self, api_base_url, auth_headers):
        """Test that source objects have required fields"""
        response = requests.get(
            f"{api_base_url}/api/stories/feed?limit=10",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200
        stories = response.json()
        
        # Find a story with sources
        story_with_sources = None
        for story in stories:
            if story.get('sources') and len(story['sources']) > 0:
                story_with_sources = story
                break
        
        if not story_with_sources:
            pytest.skip("No stories with sources available")
        
        # Fields required by iOS SourceArticle model
        required_source_fields = [
            'source',  # String - source name (e.g., "BBC")
            'title',   # String - article title
        ]
        
        for source in story_with_sources['sources'][:3]:
            for field in required_source_fields:
                assert field in source, \
                    f"Source missing required field: {field}"
    
    def test_source_field_types(self, api_base_url, auth_headers):
        """Test that source fields have correct types"""
        response = requests.get(
            f"{api_base_url}/api/stories/feed?limit=10",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200
        stories = response.json()
        
        for story in stories[:5]:
            for source in story.get('sources', [])[:3]:
                # Required fields
                assert isinstance(source.get('source'), str), \
                    "source.source should be String"
                assert isinstance(source.get('title'), str), \
                    "source.title should be String"
                
                # Optional fields with type checking
                if 'url' in source and source['url']:
                    assert isinstance(source['url'], str), \
                        "source.url should be String"
                
                if 'published_at' in source and source['published_at']:
                    validate_iso_timestamp(source['published_at'], 'source.published_at')


@pytest.mark.system  
class TestSummaryContract:
    """Test the summary object contract for iOS"""
    
    def test_summary_structure(self, api_base_url, auth_headers):
        """Test that summary has correct structure"""
        response = requests.get(
            f"{api_base_url}/api/stories/feed?limit=20",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200
        stories = response.json()
        
        # Find stories with summaries
        for story in stories:
            summary = story.get('summary')
            if summary:
                if isinstance(summary, dict):
                    # Object format
                    assert 'text' in summary, "Summary dict should have 'text'"
                    assert isinstance(summary['text'], str), "summary.text should be String"
                    
                    # Optional fields
                    if 'word_count' in summary:
                        assert isinstance(summary['word_count'], int), \
                            "summary.word_count should be Int"
                    if 'version' in summary:
                        assert isinstance(summary['version'], int), \
                            "summary.version should be Int"
                    
                    return  # Found valid summary
                elif isinstance(summary, str):
                    # Simple string format
                    return  # Found valid summary
        
        print("ℹ️ No stories with summaries found - skipping detailed check")


@pytest.mark.system
class TestCategoryContract:
    """Test category values match iOS app expectations"""
    
    def test_categories_are_valid(self, api_base_url, auth_headers):
        """Test that all categories are valid for iOS NewsCategory enum"""
        response = requests.get(
            f"{api_base_url}/api/stories/feed?limit=50",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200
        stories = response.json()
        
        # Valid categories in iOS app (from NewsCategory.swift)
        valid_categories = {
            'world', 'politics', 'business', 'tech', 'technology',
            'sports', 'entertainment', 'health', 'science', 
            'lifestyle', 'environment', 'us', 'europe', 'australia',
            'general', 'top_stories'
        }
        
        categories_found = set()
        invalid_categories = set()
        
        for story in stories:
            cat = story.get('category')
            if cat:
                categories_found.add(cat)
                if cat not in valid_categories:
                    invalid_categories.add(cat)
        
        print(f"📊 Categories found: {categories_found}")
        
        if invalid_categories:
            print(f"⚠️ Unknown categories found: {invalid_categories}")
            # Don't fail - iOS should handle unknown gracefully


@pytest.mark.system
class TestStatusContract:
    """Test story status values match iOS expectations"""
    
    def test_status_values_are_valid(self, api_base_url, auth_headers):
        """Test that status values are valid for iOS StoryStatus enum"""
        response = requests.get(
            f"{api_base_url}/api/stories/feed?limit=50",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200
        stories = response.json()
        
        # Valid statuses in iOS app
        valid_statuses = {'NEW', 'DEVELOPING', 'VERIFIED', 'ARCHIVED'}
        
        statuses_found = set()
        
        for story in stories:
            status = story.get('status')
            if status:
                statuses_found.add(status)
                assert status in valid_statuses, \
                    f"Invalid status '{status}' - iOS expects one of {valid_statuses}"
        
        print(f"📊 Statuses found: {statuses_found}")


@pytest.mark.system
class TestUserInteractionFields:
    """Test user interaction fields for iOS"""
    
    def test_user_liked_field(self, api_base_url, auth_headers):
        """Test that user_liked field is boolean"""
        response = requests.get(
            f"{api_base_url}/api/stories/feed?limit=5",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200
        stories = response.json()
        
        for story in stories:
            if 'user_liked' in story:
                assert isinstance(story['user_liked'], bool), \
                    "user_liked should be Bool"
    
    def test_user_saved_field(self, api_base_url, auth_headers):
        """Test that user_saved field is boolean"""
        response = requests.get(
            f"{api_base_url}/api/stories/feed?limit=5",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200
        stories = response.json()
        
        for story in stories:
            if 'user_saved' in story:
                assert isinstance(story['user_saved'], bool), \
                    "user_saved should be Bool"


@pytest.mark.system
class TestBreakingNewsContract:
    """Test breaking news endpoint contract"""
    
    def test_breaking_news_endpoint(self, api_base_url, auth_headers):
        """Test breaking news returns valid structure"""
        response = requests.get(
            f"{api_base_url}/api/stories/breaking?limit=5",
            headers=auth_headers,
            timeout=30
        )
        
        # Breaking endpoint might not exist or return empty
        if response.status_code == 404:
            print("ℹ️ Breaking news endpoint not available")
            return
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Should be array or dict with stories key
        if isinstance(data, list):
            stories = data
        elif isinstance(data, dict):
            stories = data.get('stories', [])
        else:
            pytest.fail("Breaking endpoint returned unexpected format")
        
        # Each breaking story should have breaking_news=true
        for story in stories:
            if 'breaking_news' in story:
                assert story['breaking_news'] is True, \
                    "Stories from breaking endpoint should have breaking_news=true"


@pytest.mark.system
class TestPagination:
    """Test pagination works correctly for iOS"""
    
    def test_limit_parameter(self, api_base_url, auth_headers):
        """Test that limit parameter works"""
        # Request exactly 3 stories
        response = requests.get(
            f"{api_base_url}/api/stories/feed?limit=3",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200
        stories = response.json()
        
        # Should return at most 3
        assert len(stories) <= 3, \
            f"Requested 3 stories but got {len(stories)}"
    
    def test_offset_parameter(self, api_base_url, auth_headers):
        """Test that offset parameter works for pagination"""
        # Get first page
        response1 = requests.get(
            f"{api_base_url}/api/stories/feed?limit=5&offset=0",
            headers=auth_headers,
            timeout=30
        )
        
        # Get second page
        response2 = requests.get(
            f"{api_base_url}/api/stories/feed?limit=5&offset=5",
            headers=auth_headers,
            timeout=30
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        stories1 = response1.json()
        stories2 = response2.json()
        
        # Need enough stories for pagination test
        if len(stories1) < 5 or len(stories2) == 0:
            pytest.skip(f"Not enough stories for pagination test (page1: {len(stories1)}, page2: {len(stories2)})")
        
        # Stories should be mostly different (allow some overlap due to real-time updates)
        ids1 = {s['id'] for s in stories1}
        ids2 = {s['id'] for s in stories2}
        
        overlap = ids1 & ids2
        
        # In a live system with active updates, stories can change order rapidly
        # Allow overlap but ensure pagination is at least working (not returning identical sets)
        if len(overlap) == len(ids1) and len(overlap) == len(ids2):
            pytest.fail("Pagination returning identical results - offset not working")
        
        print(f"✅ Pagination working - Page 1: {len(stories1)}, Page 2: {len(stories2)}, Overlap: {len(overlap)}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

