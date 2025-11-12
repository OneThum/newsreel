"""
API Integration Tests for Newsreel
Tests source diversity, clustering quality, and API response validation
"""
import pytest
import requests
from collections import Counter
from datetime import datetime, timedelta

# API Configuration
API_BASE_URL = "https://newsreel-func-51689.azurewebsites.net/api"
# For local testing: API_BASE_URL = "http://localhost:7071/api"


class TestSourceDiversity:
    """Test that stories come from diverse sources, not dominated by one outlet"""

    def test_source_diversity_in_feed(self):
        """Verify feed has diverse sources (no single source >30%)"""
        response = requests.get(f"{API_BASE_URL}/stories")
        assert response.status_code == 200

        stories = response.json()
        assert len(stories) > 0, "Should have stories in feed"

        # Extract all sources from all stories
        all_sources = []
        for story in stories:
            source_articles = story.get('source_articles', [])
            for source_article in source_articles:
                if isinstance(source_article, dict):
                    all_sources.append(source_article.get('source', 'unknown'))
                elif isinstance(source_article, str):
                    # Handle old format (just IDs)
                    source_id = source_article.split('_')[0]
                    all_sources.append(source_id)

        # Count source distribution
        source_counts = Counter(all_sources)
        total_articles = len(all_sources)

        print(f"\n📊 Source Distribution Analysis:")
        print(f"   Total articles across all stories: {total_articles}")
        print(f"   Unique sources: {len(source_counts)}")
        print(f"\n   Top 10 sources:")
        for source, count in source_counts.most_common(10):
            percentage = (count / total_articles * 100)
            print(f"   {source:30} {count:5} articles ({percentage:5.1f}%)")

        # Assertions
        assert len(source_counts) >= 10, f"Should have at least 10 unique sources, got {len(source_counts)}"

        # Check that no single source dominates (>30%)
        top_source, top_count = source_counts.most_common(1)[0]
        top_percentage = (top_count / total_articles * 100)
        assert top_percentage < 30, f"Top source '{top_source}' accounts for {top_percentage:.1f}%, should be <30%"

        print(f"\n✅ Source diversity test passed!")
        print(f"   {len(source_counts)} unique sources, no source >30%")

    def test_clustering_quality(self):
        """Verify stories are properly clustered (multiple sources per story)"""
        response = requests.get(f"{API_BASE_URL}/stories")
        assert response.status_code == 200

        stories = response.json()

        # Count stories by source count
        single_source_count = 0
        multi_source_count = 0
        source_count_distribution = Counter()

        for story in stories:
            source_articles = story.get('source_articles', [])
            source_count = len(source_articles)
            source_count_distribution[source_count] += 1

            if source_count == 1:
                single_source_count += 1
            else:
                multi_source_count += 1

        total_stories = len(stories)
        multi_source_percentage = (multi_source_count / total_stories * 100) if total_stories > 0 else 0

        print(f"\n📈 Clustering Quality Analysis:")
        print(f"   Total stories: {total_stories}")
        print(f"   Single-source stories: {single_source_count} ({100 - multi_source_percentage:.1f}%)")
        print(f"   Multi-source stories: {multi_source_count} ({multi_source_percentage:.1f}%)")
        print(f"\n   Source count distribution:")
        for count in sorted(source_count_distribution.keys()):
            story_count = source_count_distribution[count]
            percentage = (story_count / total_stories * 100)
            print(f"   {count} source{'s' if count > 1 else ' '}: {story_count:3} stories ({percentage:5.1f}%)")

        # Assertions
        # At least 50% of stories should have multiple sources (after clustering is working)
        assert multi_source_percentage >= 50, f"Only {multi_source_percentage:.1f}% of stories have multiple sources, should be >=50%"

        print(f"\n✅ Clustering quality test passed!")
        print(f"   {multi_source_percentage:.1f}% of stories have multiple sources")

    def test_status_distribution(self):
        """Verify stories have appropriate status distribution"""
        response = requests.get(f"{API_BASE_URL}/stories")
        assert response.status_code == 200

        stories = response.json()

        status_counts = Counter()
        for story in stories:
            status = story.get('status', 'UNKNOWN')
            status_counts[status] += 1

        total = len(stories)

        print(f"\n📊 Status Distribution:")
        for status in ['BREAKING', 'VERIFIED', 'DEVELOPING', 'MONITORING']:
            count = status_counts.get(status, 0)
            percentage = (count / total * 100) if total > 0 else 0
            print(f"   {status:12} {count:5} stories ({percentage:5.1f}%)")

        # Assertions
        # Should NOT have all stories in MONITORING status (sign of broken clustering)
        monitoring_percentage = (status_counts.get('MONITORING', 0) / total * 100) if total > 0 else 0
        assert monitoring_percentage < 80, f"{monitoring_percentage:.1f}% stories in MONITORING, clustering may be broken"

        # Should have some DEVELOPING or VERIFIED stories
        developed_count = status_counts.get('DEVELOPING', 0) + status_counts.get('VERIFIED', 0)
        assert developed_count > 0, "Should have some DEVELOPING or VERIFIED stories"

        print(f"\n✅ Status distribution test passed!")


class TestAPIEndpoints:
    """Test API endpoint responses and data quality"""

    def test_stories_endpoint(self):
        """Test GET /stories returns valid data"""
        response = requests.get(f"{API_BASE_URL}/stories")
        assert response.status_code == 200

        stories = response.json()
        assert isinstance(stories, list)
        assert len(stories) > 0

        # Validate first story structure
        story = stories[0]
        assert 'id' in story
        assert 'title' in story
        assert 'category' in story
        assert 'status' in story
        assert 'source_articles' in story
        assert isinstance(story['source_articles'], list)

        print(f"✅ Stories endpoint test passed! ({len(stories)} stories)")

    def test_story_sources_endpoint(self):
        """Test GET /stories/{story_id}/sources returns source articles"""
        # First get a story ID
        response = requests.get(f"{API_BASE_URL}/stories")
        assert response.status_code == 200
        stories = response.json()

        if not stories:
            pytest.skip("No stories available for testing")

        story = stories[0]
        story_id = story['id']

        # Get sources for this story
        response = requests.get(f"{API_BASE_URL}/stories/{story_id}/sources")
        assert response.status_code == 200

        sources = response.json()
        assert isinstance(sources, list)

        if len(sources) > 0:
            # Validate source structure
            source = sources[0]
            assert 'id' in source
            assert 'source' in source
            assert 'title' in source

            print(f"✅ Story sources endpoint test passed! ({len(sources)} sources for story {story_id})")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
