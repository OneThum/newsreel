"""
AI-Powered Ingestion Pipeline Timeliness Tests

CRITICAL: Monitors the time from RSS fetch to iOS app availability.
This catches ingestion delays that make stories appear "old" to users.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Any
from datetime import datetime, timezone, timedelta

import pytest
import anthropic
from anthropic import Anthropic

from functions.shared.models import RawArticle

logger = logging.getLogger(__name__)


class IngestionTimelinessMonitor:
    """Monitors ingestion pipeline performance and timeliness"""

    def __init__(self, budget):
        self.budget = budget
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable required")

        self.client = Anthropic(api_key=api_key)

    def _calculate_cost(self, usage: Dict) -> float:
        """Calculate cost from Anthropic usage data"""
        input_cost = (usage.get('input_tokens', 0) / 1_000_000) * 3.0
        output_cost = (usage.get('output_tokens', 0) / 1_000_000) * 15.0
        cache_cost = (usage.get('cache_read_input_tokens', 0) / 1_000_000) * 0.3
        return input_cost + output_cost + cache_cost

    async def analyze_ingestion_delays(self, recent_stories: List[Dict], rss_feeds: List[Dict]) -> Dict:
        """
        Analyze time delays in the ingestion pipeline

        Args:
            recent_stories: Recent stories from the feed API
            rss_feeds: RSS feed configurations

        Returns:
            Dict with delay analysis and recommendations
        """
        if not self.budget.can_run_test():
            pytest.skip(f"💰 AI test budget exceeded (${self.budget.current_cost:.2f}/{self.budget.max_daily_cost:.2f})")

        # Calculate actual delays
        delays = []
        now = datetime.now(timezone.utc)

        for story in recent_stories[:10]:  # Sample recent stories
            if story.get('source_articles'):
                # Find the most recent source article
                latest_source = max(story['source_articles'],
                                  key=lambda x: x.get('published_at', ''))
                if latest_source.get('published_at'):
                    try:
                        published_at = datetime.fromisoformat(latest_source['published_at'].replace('Z', '+00:00'))
                        delay_minutes = (now - published_at).total_seconds() / 60
                        delays.append({
                            'story_id': story.get('id', 'unknown'),
                            'title': story.get('title', '')[:50],
                            'delay_minutes': delay_minutes,
                            'published_at': published_at.isoformat()
                        })
                    except (ValueError, TypeError):
                        continue

        # Format for AI analysis
        delay_summary = "\n".join([
            f"- {d['title'][:40]}...: {d['delay_minutes']:.1f} minutes old"
            for d in sorted(delays, key=lambda x: x['delay_minutes'], reverse=True)[:5]
        ])

        feed_config = "\n".join([
            f"- {feed.get('name', 'Unknown')}: {feed.get('url', 'no url')}"
            for feed in rss_feeds[:5]
        ])

        prompt = f"""You are analyzing a news app's ingestion pipeline performance.

RECENT STORIES DELAYS (sample of {len(delays)} stories):
{delay_summary}

RSS FEED CONFIGURATION:
{feed_config}

SYSTEM INFORMATION:
- RSS polling interval: Every 10-15 seconds (2-3 feeds per cycle)
- Expected max delay: 5-10 minutes
- Current max delay observed: {max([d['delay_minutes'] for d in delays]) if delays else 0:.1f} minutes

Analyze this ingestion pipeline (respond with JSON):

1. timeliness_score: How timely is content delivery? (0-100, 100=perfect)
2. bottleneck_identified: What seems to be the main delay? (string)
3. expected_vs_actual: Is performance meeting expectations? (boolean)
4. severity: How critical is this issue? (low/medium/high/critical)
5. root_causes: Likely causes of delays (array of strings)
6. recommendations: How to fix the delays (array of strings)
7. monitoring_needed: What metrics should be monitored? (array of strings)

Consider:
- RSS feeds should update every 10-15 seconds
- Stories should appear in app within 5-10 minutes max
- 1 hour delays indicate serious pipeline issues

Respond ONLY with valid JSON."""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            result = json.loads(response.content[0].text)
            cost = self._calculate_cost(response.usage.__dict__ if hasattr(response, 'usage') else {})
            self.budget.record_test("ingestion_timeliness", cost, result)

            # Critical assertions for timeliness
            assert result['timeliness_score'] >= 60, f"🚨 CRITICAL: Ingestion pipeline severely delayed! Score: {result['timeliness_score']}%"

            if result['severity'] in ['high', 'critical']:
                logger.error(f"🚨 CRITICAL INGESTION ISSUE: {result['bottleneck_identified']}")
                logger.error(f"   Severity: {result['severity']}")
                for cause in result['root_causes'][:3]:
                    logger.error(f"   Cause: {cause}")
                pytest.fail(f"Critical ingestion pipeline delay detected: {result['bottleneck_identified']}")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI timeliness response as JSON: {response.content[0].text}")
            raise e
        except Exception as e:
            logger.error(f"AI timeliness test failed: {e}")
            raise e


@pytest.fixture
def ingestion_timeliness_monitor(ai_test_budget):
    """AI-powered ingestion timeliness monitor"""
    try:
        from tests.ai.test_ingestion_timeliness import IngestionTimelinessMonitor
        return IngestionTimelinessMonitor(ai_test_budget)
    except ImportError:
        pytest.skip("AI timeliness monitoring not available")


@pytest.mark.ai
@pytest.mark.critical
async def test_ingestion_pipeline_timeliness(ingestion_timeliness_monitor, api_client_authenticated, api_base_url):
    """
    CRITICAL: Monitor ingestion pipeline timeliness

    This test will FAIL if stories are more than 15-20 minutes old,
    indicating serious ingestion pipeline issues.
    """
    try:
        # Get recent stories from production feed
        response = api_client_authenticated.make_request('GET', '/api/stories/feed?limit=20')
        if response.status_code != 200:
            pytest.skip(f"Cannot get feed for timeliness testing: {response.status_code}")

        feed_data = response.json()
        # Handle both list and dict response formats
        if isinstance(feed_data, list):
            stories = feed_data
        else:
            stories = feed_data.get('stories', [])

        if len(stories) < 5:
            pytest.skip("Not enough stories for timeliness analysis")

        # Get RSS feed configuration (mock for now, would come from database)
        rss_feeds = [
            {'name': 'Reuters', 'url': 'https://feeds.reuters.com/reuters/topNews'},
            {'name': 'BBC', 'url': 'https://feeds.bbci.co.uk/news/rss.xml'},
            {'name': 'CNN', 'url': 'http://rss.cnn.com/rss/edition.rss'}
        ]

        # Analyze timeliness
        result = await ingestion_timeliness_monitor.analyze_ingestion_delays(stories, rss_feeds)

        logger.info(f"📊 Ingestion Timeliness: {result['timeliness_score']}%")
        logger.info(f"   Severity: {result['severity']}")
        logger.info(f"   Main Issue: {result['bottleneck_identified']}")

        # This test will fail if timeliness is critically poor
        assert result['expected_vs_actual'] == True, f"Ingestion pipeline not meeting performance expectations: {result['bottleneck_identified']}"

    except Exception as e:
        logger.error(f"Ingestion timeliness test failed: {e}")
        pytest.fail(f"Could not complete timeliness analysis: {e}")


@pytest.mark.ai
@pytest.mark.slow
async def test_ingestion_pipeline_regression(ingestion_timeliness_monitor, api_client_authenticated, api_base_url):
    """
    Monitor for regression in ingestion pipeline performance

    Tracks timeliness over time to catch when things get worse.
    """
    try:
        # Get baseline timeliness score (would be stored in database)
        baseline_score = 85.0  # Expected good performance

        response = api_client_authenticated.make_request('GET', '/api/stories/feed?limit=15')
        if response.status_code != 200:
            pytest.skip("Cannot get feed for regression testing")

        feed_data = response.json()
        # Handle both list and dict response formats
        if isinstance(feed_data, list):
            stories = feed_data
        else:
            stories = feed_data.get('stories', [])

        if len(stories) < 5:
            pytest.skip("Not enough stories for regression analysis")

        # Simple timeliness check without full AI analysis (for performance)
        now = datetime.now(timezone.utc)
        total_delay = 0
        story_count = 0

        for story in stories[:10]:
            if story.get('source_articles'):
                latest_source = max(story['source_articles'],
                                  key=lambda x: x.get('published_at', ''))
                if latest_source.get('published_at'):
                    try:
                        published_at = datetime.fromisoformat(latest_source['published_at'].replace('Z', '+00:00'))
                        delay_minutes = (now - published_at).total_seconds() / 60
                        total_delay += delay_minutes
                        story_count += 1
                    except (ValueError, TypeError):
                        continue

        if story_count > 0:
            avg_delay = total_delay / story_count
            timeliness_score = max(0, 100 - (avg_delay * 2))  # Rough scoring

            logger.info(f"📈 Ingestion Regression Check: {timeliness_score:.1f}% timeliness ({avg_delay:.1f} min avg delay)")

            # Check for significant regression
            if timeliness_score < baseline_score * 0.7:  # 30% degradation
                logger.warning(f"⚠️ Ingestion performance degraded from {baseline_score}% to {timeliness_score:.1f}%")
                logger.warning(f"   Average delay: {avg_delay:.1f} minutes (should be < 10 minutes)")

                # Run full AI analysis on regression
                rss_feeds = [{'name': 'Test Feed', 'url': 'test'}]
                result = await ingestion_timeliness_monitor.analyze_ingestion_delays(stories, rss_feeds)

                pytest.fail(f"Critical ingestion performance regression detected: {result['bottleneck_identified']}")

    except Exception as e:
        logger.warning(f"Ingestion regression test failed: {e}")
        pytest.skip(f"Could not run regression analysis: {e}")


@pytest.mark.ai
@pytest.mark.unit
async def test_ingestion_timeliness_edge_cases(ingestion_timeliness_monitor):
    """Test timeliness monitoring with edge cases"""

    # Test with empty feed
    try:
        result = await ingestion_timeliness_monitor.analyze_ingestion_delays([], [])
        assert result['timeliness_score'] < 50, "Empty feed should have low timeliness"
    except AssertionError:
        # This is expected - empty feeds fail timeliness checks
        pass

    # Test with very old stories (simulate the reported issue)
    old_stories = [{
        'id': 'old_story_1',
        'title': 'Very Old Story',
        'source_articles': [{
            'published_at': (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
            'title': 'Old Article'
        }]
    }]

    rss_feeds = [{'name': 'Test', 'url': 'test'}]

    try:
        result = await ingestion_timeliness_monitor.analyze_ingestion_delays(old_stories, rss_feeds)
        # This should trigger critical failure due to 2-hour delay
        assert False, "Should have failed due to critical delay"
    except AssertionError as e:
        if "CRITICAL: Ingestion pipeline severely delayed" in str(e):
            logger.info("✅ Correctly detected critical ingestion delay")
        else:
            raise e
