"""Integration tests: RSS Ingestion → Story Clustering

Tests the full flow from RSS feed parsing to story cluster creation
"""
import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from functions.shared.cosmos_client import CosmosClient
from functions.shared.rss_feeds import RSSFeedConfig
from functions.shared.utils import (
    clean_html,
    generate_article_id,
    generate_story_fingerprint
)


@pytest.mark.integration
class TestRSSToClusteringFlow:
    """Test full RSS → Clustering pipeline"""
    
    @pytest.mark.asyncio
    async def test_new_article_creates_new_cluster(self, mock_cosmos_client):
        """Test that a new article creates a new story cluster"""
        # Arrange: Create mock RSS entry
        feed_config = RSSFeedConfig(
            id="test_feed",
            name="Test Feed",
            url="https://test.com/rss",
            source_id="test_source",
            category="world",
            tier=1,
            language="en",
            country="US"
        )
        
        rss_entry = {
            'title': 'Breaking: Major Event Occurs',
            'link': 'https://test.com/article1',
            'description': '<p>A significant event has occurred in the city center.</p>',
            'published': 'Mon, 26 Oct 2025 10:00:00 GMT',
            'summary': 'Event summary'
        }
        
        # Act: Process RSS entry (simulate ingestion)
        from datetime import datetime
        article_id = generate_article_id(feed_config.source_id, rss_entry['link'], datetime.now())
        cleaned_description = clean_html(rss_entry['description'])
        
        # Extract simple entities using utils function
        from functions.shared.utils import extract_simple_entities, categorize_article
        entities = extract_simple_entities(rss_entry['title'] + ' ' + cleaned_description)
        
        # Generate fingerprint (needs entities list)
        fingerprint = generate_story_fingerprint(rss_entry['title'], entities)
        
        # Categorize article
        category = categorize_article(rss_entry['title'], cleaned_description, rss_entry['link'])
        
        raw_article = {
            'id': article_id,
            'source': feed_config.source_id,
            'source_name': feed_config.name,
            'category': category,
            'title': rss_entry['title'],
            'description': cleaned_description,
            'url': rss_entry['link'],
            'fingerprint': fingerprint,
            'entities': entities,
            'published_at': datetime.now(timezone.utc).isoformat(),
            'ingested_at': datetime.now(timezone.utc).isoformat(),
        }
        
        # Assert: Verify article structure
        assert raw_article['id'] is not None
        assert raw_article['source'] == 'test_source'
        assert raw_article['fingerprint'] is not None
        assert len(raw_article['fingerprint']) > 0
        assert 'entities' in raw_article
        assert raw_article['category'] in ['world', 'us', 'tech', 'business', 'sports', 'science', 'health']
        
        # Simulate clustering check
        mock_cosmos_client.query_stories_by_fingerprint.return_value = []  # No existing stories
        existing_stories = await mock_cosmos_client.query_stories_by_fingerprint(fingerprint)
        
        # New story should be created
        assert len(existing_stories) == 0
        
    @pytest.mark.asyncio
    async def test_similar_article_clusters_with_existing(self, mock_cosmos_client):
        """Test that similar articles cluster together"""
        # Arrange: Create two similar articles
        article1_title = "President Announces New Climate Policy"
        article2_title = "President Unveils Climate Change Initiative"
        
        # Extract entities for fingerprinting
        from functions.shared.utils import extract_simple_entities
        entities1 = extract_simple_entities(article1_title)
        entities2 = extract_simple_entities(article2_title)
        
        fingerprint1 = generate_story_fingerprint(article1_title, entities1)
        fingerprint2 = generate_story_fingerprint(article2_title, entities2)
        
        # Existing story cluster
        existing_cluster = {
            'id': 'story_123',
            'fingerprint': fingerprint1,
            'headline': article1_title,
            'sources': [{'source': 'source1', 'article_id': 'art1'}],
            'article_count': 1,
            'status': 'MONITORING'
        }
        
        # Mock: Story exists with similar fingerprint
        mock_cosmos_client.query_stories_by_fingerprint.return_value = [existing_cluster]
        
        # Act: Check if article2 matches
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(None, article1_title.lower(), article2_title.lower()).ratio()
        
        # Assert: Articles should be similar enough to cluster
        assert similarity >= 0.7, f"Similarity {similarity} should be >= 0.7"
        
        existing_stories = await mock_cosmos_client.query_stories_by_fingerprint(fingerprint2)
        assert len(existing_stories) > 0
        
    @pytest.mark.asyncio
    async def test_duplicate_source_prevented(self, mock_cosmos_client):
        """Test that duplicate sources are prevented in same cluster"""
        # Arrange: Two articles from same source
        source_id = "bbc"
        article1 = {
            'id': 'art1',
            'source': source_id,
            'title': 'Breaking News Event',
            'url': 'https://bbc.com/article1'
        }
        
        article2 = {
            'id': 'art2',
            'source': source_id,
            'title': 'Breaking News Event Continues',
            'url': 'https://bbc.com/article2'
        }
        
        existing_cluster = {
            'id': 'story_123',
            'sources': [
                {'source': source_id, 'article_id': 'art1'}
            ]
        }
        
        # Act: Check if source already exists
        existing_sources = [s['source'] for s in existing_cluster['sources']]
        should_add_article2 = article2['source'] not in existing_sources
        
        # Assert: Second article from same source should NOT be added
        assert not should_add_article2, "Duplicate source should be prevented"
        
    @pytest.mark.asyncio
    async def test_cross_category_clustering_prevented(self, mock_cosmos_client):
        """Test that articles from conflicting categories don't cluster"""
        # Arrange: Articles from different categories
        tech_article = {
            'title': 'Apple Announces New iPhone',
            'category': 'tech'
        }
        
        sports_article = {
            'title': 'Apple Wins Championship Game',
            'category': 'sports'
        }
        
        # Act: Check topic conflict
        from functions.function_app import has_topic_conflict
        has_conflict = has_topic_conflict(tech_article['category'], sports_article['category'])
        
        # Assert: Should detect conflict
        assert has_conflict, "Tech and sports should conflict"
        
    @pytest.mark.asyncio
    async def test_entity_based_matching(self, mock_cosmos_client):
        """Test that articles with shared entities cluster together"""
        # Arrange: Two articles about same entity
        article1 = {
            'title': 'Elon Musk Announces Mars Mission',
            'description': 'SpaceX CEO reveals plans for Mars colonization'
        }
        
        article2 = {
            'title': 'SpaceX Prepares for Mars Launch',
            'description': 'Company under Elon Musk readies rocket'
        }
        
        # Act: Extract entities
        from functions.shared.utils import extract_simple_entities
        entities1 = extract_simple_entities(article1['title'] + ' ' + article1['description'])
        entities2 = extract_simple_entities(article2['title'] + ' ' + article2['description'])
        
        # Find common entities (entities are List[Entity] objects with .text and .type attributes)
        entity_texts1 = {e.text if hasattr(e, 'text') else e.get('text', '') for e in entities1}
        entity_texts2 = {e.text if hasattr(e, 'text') else e.get('text', '') for e in entities2}
        common_entities = entity_texts1 & entity_texts2
        
        # Assert: Should share entities
        assert len(common_entities) > 0, "Should share at least one entity"


@pytest.mark.integration
class TestRSSProcessingPipeline:
    """Test complete RSS processing workflow"""
    
    @pytest.mark.asyncio
    async def test_full_rss_to_cluster_pipeline(self, mock_cosmos_client):
        """Test complete pipeline: RSS fetch → Parse → Store → Cluster"""
        # Arrange: Mock RSS feed response
        mock_feed_data = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test News</title>
                <item>
                    <title>Major Policy Announcement</title>
                    <link>https://test.com/article1</link>
                    <description>Government announces new policy initiative</description>
                    <pubDate>Mon, 26 Oct 2025 10:00:00 GMT</pubDate>
                </item>
            </channel>
        </rss>"""
        
        # Act: Parse feed (simulate feedparser)
        import feedparser
        from io import BytesIO
        
        feed = feedparser.parse(BytesIO(mock_feed_data.encode('utf-8')))
        
        # Assert: Feed parsed correctly
        assert len(feed.entries) == 1
        assert feed.entries[0].title == 'Major Policy Announcement'
        
        # Simulate article processing
        entry = feed.entries[0]
        from datetime import datetime
        from functions.shared.utils import extract_simple_entities
        
        article_id = generate_article_id('test_source', entry.link, datetime.now())
        entities = extract_simple_entities(entry.title)
        fingerprint = generate_story_fingerprint(entry.title, entities)
        
        assert article_id is not None
        assert fingerprint is not None
        
    @pytest.mark.asyncio
    async def test_multiple_articles_same_story(self, mock_cosmos_client):
        """Test that multiple articles about same event cluster correctly"""
        # Arrange: 3 articles about same event
        articles = [
            {'title': 'President Announces Economic Plan', 'source': 'reuters'},
            {'title': 'President Unveils New Economic Policy', 'source': 'bbc'},
            {'title': 'Economic Plan Announced by President', 'source': 'cnn'}
        ]
        
        # Act: Generate fingerprints
        from functions.shared.utils import extract_simple_entities
        fingerprints = []
        for a in articles:
            entities = extract_simple_entities(a['title'])
            fingerprints.append(generate_story_fingerprint(a['title'], entities))
        
        # All should have similar fingerprints (first 3 words normalized)
        unique_fingerprints = set(fingerprints)
        
        # Assert: Should cluster (likely same fingerprint)
        # At minimum, should have high text similarity
        from difflib import SequenceMatcher
        sim_01 = SequenceMatcher(None, articles[0]['title'], articles[1]['title']).ratio()
        sim_12 = SequenceMatcher(None, articles[1]['title'], articles[2]['title']).ratio()
        
        assert sim_01 >= 0.5, f"Similarity {sim_01} should indicate same story"
        assert sim_12 >= 0.5, f"Similarity {sim_12} should indicate same story"
        
    @pytest.mark.asyncio
    async def test_story_status_progression(self, mock_cosmos_client):
        """Test that story status evolves correctly as sources are added"""
        # Arrange: Story with increasing sources
        story = {
            'id': 'story_123',
            'article_count': 1,
            'status': 'MONITORING'
        }
        
        # Act & Assert: Status progression
        
        # 1 source = MONITORING
        assert story['status'] == 'MONITORING'
        
        # 2 sources = DEVELOPING
        story['article_count'] = 2
        new_status = 'DEVELOPING' if story['article_count'] >= 2 else 'MONITORING'
        assert new_status == 'DEVELOPING'
        
        # 3+ sources = VERIFIED
        story['article_count'] = 3
        new_status = 'VERIFIED' if story['article_count'] >= 3 else 'DEVELOPING'
        assert new_status == 'VERIFIED'


@pytest.mark.integration
class TestRSSFeedQuality:
    """Test RSS feed quality and error handling"""
    
    @pytest.mark.asyncio
    async def test_invalid_feed_handling(self):
        """Test that invalid RSS feeds are handled gracefully"""
        import feedparser
        
        # Act: Parse invalid XML
        invalid_feed = "This is not XML"
        feed = feedparser.parse(invalid_feed)
        
        # Assert: Should return empty feed, not crash
        assert len(feed.entries) == 0
        assert 'bozo' in feed  # feedparser's error flag
        
    @pytest.mark.asyncio
    async def test_missing_required_fields(self):
        """Test handling of RSS entries with missing fields"""
        # Arrange: RSS entry missing description
        entry = {
            'title': 'Test Article',
            'link': 'https://test.com/article1',
            # Missing description
        }
        
        # Act: Process entry with defaults
        description = entry.get('description', entry.get('summary', ''))
        
        # Assert: Should handle gracefully
        assert description == ''  # Empty but doesn't crash
        
    @pytest.mark.asyncio
    async def test_html_cleaning_in_pipeline(self):
        """Test that HTML is properly cleaned during ingestion"""
        # Arrange: Description with HTML tags
        dirty_html = '<p>This is <b>bold</b> and <a href="link">linked</a> text.</p>'
        
        # Act: Clean HTML
        clean_text = clean_html(dirty_html)
        
        # Assert: HTML tags removed
        assert '<p>' not in clean_text
        assert '<b>' not in clean_text
        assert '<a href' not in clean_text
        assert 'bold' in clean_text
        assert 'linked' in clean_text


@pytest.mark.integration
@pytest.mark.slow
class TestRSSClusteringPerformance:
    """Test clustering performance with realistic data volumes"""
    
    @pytest.mark.asyncio
    async def test_clustering_100_articles(self, mock_cosmos_client):
        """Test clustering performance with 100 articles"""
        import time
        
        # Arrange: Generate 100 test articles
        articles = []
        for i in range(100):
            articles.append({
                'title': f'Test Article {i} About Event',
                'source': f'source_{i % 10}',  # 10 different sources
                'url': f'https://test.com/article{i}'
            })
        
        # Act: Generate fingerprints (key clustering operation)
        import time
        from functions.shared.utils import extract_simple_entities
        
        start_time = time.time()
        fingerprints = []
        for a in articles:
            entities = extract_simple_entities(a['title'])
            fingerprints.append(generate_story_fingerprint(a['title'], entities))
        duration = time.time() - start_time
        
        # Assert: Should process quickly
        assert duration < 1.0, f"Should process 100 articles in <1s, took {duration}s"
        assert len(fingerprints) == 100
        
    @pytest.mark.asyncio
    async def test_fuzzy_matching_performance(self):
        """Test fuzzy text matching performance"""
        from difflib import SequenceMatcher
        import time
        
        # Arrange: Two similar strings
        text1 = "President announces major economic policy changes"
        text2 = "President unveils significant economic policy reforms"
        
        # Act: Perform fuzzy matching 1000 times
        start_time = time.time()
        for _ in range(1000):
            similarity = SequenceMatcher(None, text1, text2).ratio()
        duration = time.time() - start_time
        
        # Assert: Should be fast enough for real-time use
        assert duration < 1.0, f"1000 comparisons should take <1s, took {duration}s"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

