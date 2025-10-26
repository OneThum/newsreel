"""Shared fixtures for integration tests"""
import pytest
from datetime import datetime, timezone
from typing import Dict, List


@pytest.fixture
def sample_rss_feed():
    """Sample RSS feed XML for testing"""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Test News Feed</title>
            <link>https://test.com</link>
            <description>Test news feed</description>
            <item>
                <title>Breaking: Major Political Event</title>
                <link>https://test.com/article1</link>
                <description><![CDATA[<p>A significant political event has occurred in the capital city.</p>]]></description>
                <pubDate>Mon, 26 Oct 2025 10:00:00 GMT</pubDate>
                <category>Politics</category>
            </item>
            <item>
                <title>Tech Company Announces Innovation</title>
                <link>https://test.com/article2</link>
                <description><![CDATA[<p>Major tech company reveals groundbreaking technology.</p>]]></description>
                <pubDate>Mon, 26 Oct 2025 09:30:00 GMT</pubDate>
                <category>Technology</category>
            </item>
            <item>
                <title>Sports Team Wins Championship</title>
                <link>https://test.com/article3</link>
                <description><![CDATA[<p>Local team celebrates victory in final game.</p>]]></description>
                <pubDate>Mon, 26 Oct 2025 09:00:00 GMT</pubDate>
                <category>Sports</category>
            </item>
        </channel>
    </rss>"""


@pytest.fixture
def sample_articles() -> List[Dict]:
    """Sample article data for testing"""
    return [
        {
            'id': 'reuters_article1',
            'source': 'reuters',
            'source_name': 'Reuters',
            'category': 'world',
            'title': 'President Announces Climate Initiative',
            'description': 'New climate policy aims to reduce emissions',
            'url': 'https://reuters.com/article1',
            'fingerprint': 'president announces climate',
            'entities': {
                'people': ['President'],
                'organizations': [],
                'locations': []
            },
            'published_at': '2025-10-26T10:00:00Z',
            'ingested_at': '2025-10-26T10:05:00Z'
        },
        {
            'id': 'bbc_article1',
            'source': 'bbc',
            'source_name': 'BBC News',
            'category': 'world',
            'title': 'President Unveils Climate Plan',
            'description': 'Climate change policy announced today',
            'url': 'https://bbc.com/article1',
            'fingerprint': 'president unveils climate',
            'entities': {
                'people': ['President'],
                'organizations': [],
                'locations': []
            },
            'published_at': '2025-10-26T10:15:00Z',
            'ingested_at': '2025-10-26T10:20:00Z'
        },
        {
            'id': 'cnn_article1',
            'source': 'cnn',
            'source_name': 'CNN',
            'category': 'world',
            'title': 'New Climate Policy Revealed',
            'description': 'Government reveals environmental strategy',
            'url': 'https://cnn.com/article1',
            'fingerprint': 'new climate policy',
            'entities': {
                'people': [],
                'organizations': ['Government'],
                'locations': []
            },
            'published_at': '2025-10-26T10:30:00Z',
            'ingested_at': '2025-10-26T10:35:00Z'
        }
    ]


@pytest.fixture
def sample_story_cluster() -> Dict:
    """Sample story cluster for testing"""
    return {
        'id': 'story_12345',
        'fingerprint': 'president announces climate',
        'headline': 'President Announces Major Climate Initiative',
        'summary': None,
        'status': 'DEVELOPING',
        'category': 'world',
        'sources': [
            {
                'source': 'reuters',
                'source_name': 'Reuters',
                'article_id': 'reuters_article1',
                'title': 'President Announces Climate Initiative',
                'url': 'https://reuters.com/article1',
                'published_at': '2025-10-26T10:00:00Z',
                'added_at': '2025-10-26T10:05:00Z'
            },
            {
                'source': 'bbc',
                'source_name': 'BBC News',
                'article_id': 'bbc_article1',
                'title': 'President Unveils Climate Plan',
                'url': 'https://bbc.com/article1',
                'published_at': '2025-10-26T10:15:00Z',
                'added_at': '2025-10-26T10:20:00Z'
            }
        ],
        'article_count': 2,
        'entities': {
            'people': ['President'],
            'organizations': [],
            'locations': []
        },
        'first_seen': '2025-10-26T10:00:00Z',
        'last_updated': '2025-10-26T10:20:00Z',
        'created_at': '2025-10-26T10:05:00Z',
        'updated_at': '2025-10-26T10:20:00Z'
    }


@pytest.fixture
def sample_verified_story() -> Dict:
    """Sample verified story (3+ sources) for testing"""
    # Build story directly to avoid fixture dependency loop
    story = {
        'id': 'story_12345',
        'fingerprint': 'president announces climate',
        'headline': 'President Announces Major Climate Initiative',
        'summary': None,
        'status': 'VERIFIED',
        'category': 'world',
        'sources': [
            {
                'source': 'reuters',
                'source_name': 'Reuters',
                'article_id': 'reuters_article1',
                'title': 'President Announces Climate Initiative',
                'url': 'https://reuters.com/article1',
                'published_at': '2025-10-26T10:00:00Z',
                'added_at': '2025-10-26T10:05:00Z'
            },
            {
                'source': 'bbc',
                'source_name': 'BBC News',
                'article_id': 'bbc_article1',
                'title': 'President Unveils Climate Plan',
                'url': 'https://bbc.com/article1',
                'published_at': '2025-10-26T10:15:00Z',
                'added_at': '2025-10-26T10:20:00Z'
            },
            {
                'source': 'cnn',
                'source_name': 'CNN',
                'article_id': 'cnn_article1',
                'title': 'New Climate Policy Revealed',
                'url': 'https://cnn.com/article1',
                'published_at': '2025-10-26T10:30:00Z',
                'added_at': '2025-10-26T10:35:00Z'
            }
        ],
        'article_count': 3,
        'entities': {
            'people': ['President'],
            'organizations': [],
            'locations': []
        },
        'first_seen': '2025-10-26T10:00:00Z',
        'last_updated': '2025-10-26T10:35:00Z',
        'created_at': '2025-10-26T10:05:00Z',
        'updated_at': '2025-10-26T10:35:00Z'
    }
    return story


@pytest.fixture
def sample_breaking_story() -> Dict:
    """Sample breaking news story for testing"""
    return {
        'id': 'story_breaking_1',
        'fingerprint': 'earthquake strikes major',
        'headline': 'Earthquake Strikes Major City',
        'summary': 'A powerful earthquake has struck a major metropolitan area, causing significant damage.',
        'status': 'BREAKING',
        'category': 'world',
        'sources': [
            {'source': 'reuters', 'source_name': 'Reuters', 'article_id': 'reuters_eq1'},
            {'source': 'bbc', 'source_name': 'BBC News', 'article_id': 'bbc_eq1'},
            {'source': 'cnn', 'source_name': 'CNN', 'article_id': 'cnn_eq1'},
            {'source': 'ap', 'source_name': 'Associated Press', 'article_id': 'ap_eq1'}
        ],
        'article_count': 4,
        'first_seen': '2025-10-26T09:00:00Z',
        'last_updated': '2025-10-26T09:15:00Z',
        'breaking_triggered_at': '2025-10-26T09:15:00Z',
        'notification_sent': True
    }


@pytest.fixture
def sample_batch_request() -> Dict:
    """Sample batch summarization request for testing"""
    return {
        'id': 'batch_req_123',
        'batch_id': 'batch_ant_20251026_001',
        'story_ids': ['story_1', 'story_2', 'story_3', 'story_4', 'story_5'],
        'status': 'submitted',
        'submitted_at': '2025-10-26T08:00:00Z',
        'anthropic_batch_id': 'msgbatch_123abc',
        'request_count': 5,
        'cost_estimate': 0.025
    }


@pytest.fixture
def sample_completed_batch() -> Dict:
    """Sample completed batch with results for testing"""
    return {
        'id': 'batch_req_123',
        'batch_id': 'batch_ant_20251026_001',
        'story_ids': ['story_1', 'story_2', 'story_3'],
        'status': 'completed',
        'submitted_at': '2025-10-26T08:00:00Z',
        'completed_at': '2025-10-26T08:30:00Z',
        'anthropic_batch_id': 'msgbatch_123abc',
        'request_count': 3,
        'succeeded_count': 3,
        'failed_count': 0,
        'results': [
            {
                'custom_id': 'story_1',
                'result': {
                    'type': 'succeeded',
                    'message': {
                        'content': [{
                            'type': 'text',
                            'text': 'Three-sentence summary of story 1.'
                        }]
                    }
                }
            },
            {
                'custom_id': 'story_2',
                'result': {
                    'type': 'succeeded',
                    'message': {
                        'content': [{
                            'type': 'text',
                            'text': 'Three-sentence summary of story 2.'
                        }]
                    }
                }
            },
            {
                'custom_id': 'story_3',
                'result': {
                    'type': 'succeeded',
                    'message': {
                        'content': [{
                            'type': 'text',
                            'text': 'Three-sentence summary of story 3.'
                        }]
                    }
                }
            }
        ],
        'total_cost': 0.015
    }


@pytest.fixture
def mock_anthropic_response() -> Dict:
    """Mock Anthropic API response for testing"""
    return {
        'id': 'msg_123abc',
        'type': 'message',
        'role': 'assistant',
        'content': [{
            'type': 'text',
            'text': 'This is a concise three-sentence summary of the news story. It captures the main points. It provides context.'
        }],
        'model': 'claude-3-5-haiku-20241022',
        'usage': {
            'input_tokens': 500,
            'output_tokens': 50
        }
    }

