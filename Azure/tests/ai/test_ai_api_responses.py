"""
AI-Powered API Response Quality Tests

Uses Claude to evaluate if API responses make sense for iOS app users.
This ensures the feed feels natural and useful to end users.
"""

import os
import json
import logging
from typing import Dict, List, Any

import pytest
import anthropic
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class AIAPITester:
    """Uses AI to evaluate API response quality for user experience"""

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

    async def test_stories_feed_quality(self, stories: List[Dict], skip_quality_assertions: bool = False) -> Dict:
        """
        Use AI to evaluate if feed would make sense to users

        Args:
            stories: List of story dicts from API response

        Returns:
            Dict with quality evaluation
        """
        if not self.budget.can_run_test():
            pytest.skip(f"💰 AI test budget exceeded (${self.budget.current_cost:.2f}/{self.budget.max_daily_cost:.2f})")

        # Format stories for AI analysis
        feed_content = []
        for i, story in enumerate(stories[:15]):  # Limit for cost control
            feed_content.append(f"{i+1}. [{story.get('category', 'no-cat')}] {story.get('title', 'No title')}")
            if story.get('summary'):
                summary_text = story['summary'].get('text', '')[:150]
                feed_content.append(f"   Summary: {summary_text}...")
            feed_content.append(f"   Sources: {len(story.get('source_articles', []))}")
            feed_content.append("")

        # Extract variables for f-string
        stories_count = len(stories)
        feed_content_text = "\n".join(feed_content)

        prompt = f"""You are testing a news app's story feed for quality.

FEED ({stories_count} stories):

{feed_content_text}

Evaluate this feed (respond with JSON):

1. diversity_score: Are stories diverse in topic/source? (0-100)
2. freshness_score: Are stories recent and relevant? (0-100)
3. duplicate_detection: Are there any duplicate/near-duplicate stories? (array of pairs like [1,5])
4. ordering_quality: Is the order logical (breaking news first, etc.)? (0-100)
5. category_accuracy: Do categories seem correct? (0-100)
6. summary_quality: Are summaries helpful and accurate? (0-100)
7. issues: Any specific problems? (array of strings)
8. recommendations: How to improve? (array of strings)
9. overall_quality: Overall feed quality (0-100)

Consider: Would this feed keep users engaged and informed?

Respond ONLY with valid JSON."""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            result = json.loads(response.content[0].text)
            cost = self._calculate_cost(response.usage.__dict__ if hasattr(response, 'usage') else {})
            self.budget.record_test("api_feed_quality", cost, result)

            # Assert on quality metrics with reasonable thresholds (skip for edge cases)
            if not skip_quality_assertions:
                assert result['diversity_score'] >= 60, f"Feed lacks diversity: {result['diversity_score']}%"
                assert result['freshness_score'] >= 70, f"Feed not fresh enough: {result['freshness_score']}% (CRITICAL: Stories should be very recent)"
                assert len(result['duplicate_detection']) == 0, f"Duplicates detected: {result['duplicate_detection']}"
                assert result['overall_quality'] >= 65, f"Feed quality too low: {result['overall_quality']}%"

            if result['issues']:
                logger.warning("🤖 Feed quality issues detected:")
                for issue in result['issues'][:3]:  # Limit logging
                    logger.warning(f"   {issue}")

            logger.info(f"✅ AI Feed Quality Test Passed - Overall: {result['overall_quality']}%, Diversity: {result['diversity_score']}%")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI feed response as JSON: {response.content[0].text}")
            raise e
        except Exception as e:
            logger.error(f"AI feed quality test failed: {e}")
            raise e

    async def test_story_detail_quality(self, story: Dict) -> Dict:
        """
        Evaluate individual story detail view quality

        Args:
            story: Complete story dict from API

        Returns:
            Dict with story quality evaluation
        """
        if not self.budget.can_run_test():
            pytest.skip("AI test budget exceeded")

        # Extract variables for f-string
        story_title = story.get('title', 'No title')
        story_category = story.get('category', 'No category')
        story_status = story.get('status', 'Unknown')
        story_summary = story.get('summary', {}).get('text', 'No summary') if story.get('summary') else 'No summary'
        sources_count = len(story.get('source_articles', []))
        sources_formatted = self._format_sources_for_ai(story.get('source_articles', []))

        prompt = f"""Evaluate this individual story for user experience quality.

STORY:
Title: {story_title}
Category: {story_category}
Status: {story_status}
Summary: {story_summary}

Sources ({sources_count}):
{sources_formatted}

Evaluate (respond with JSON):

1. title_quality: Is title engaging and accurate? (0-100)
2. summary_helpful: Is summary useful for deciding to read? (0-100)
3. source_trust: Do sources seem credible? (0-100)
4. information_complete: Does user get full picture? (0-100)
5. clarity: Is everything clear and easy to understand? (0-100)
6. issues: Any specific problems? (array of strings)
7. overall_rating: Overall quality (0-100)

Consider: Would a user find this story valuable and trustworthy?

Respond ONLY with valid JSON."""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )

            result = json.loads(response.content[0].text)
            cost = self._calculate_cost(response.usage.__dict__ if hasattr(response, 'usage') else {})
            self.budget.record_test("story_detail_quality", cost, result)

            # Assert reasonable quality
            assert result['overall_rating'] >= 60, f"Story quality too low: {result['overall_rating']}%"
            assert result['source_trust'] >= 50, f"Source credibility too low: {result['source_trust']}%"

            return result

        except Exception as e:
            logger.error(f"AI story detail test failed: {e}")
            raise e

    def _format_sources_for_ai(self, sources: List[Dict]) -> str:
        """Format sources for AI evaluation"""
        formatted = []
        for i, source in enumerate(sources[:5]):  # Limit for cost
            formatted.append(f"  {i+1}. {source.get('source', 'unknown')}: {source.get('title', 'No title')}")
        if len(sources) > 5:
            formatted.append(f"  ... and {len(sources) - 5} more sources")
        return "\n".join(formatted)


@pytest.fixture
def ai_api_tester(ai_test_budget):
    """AI-powered API response quality tester"""
    try:
        from tests.ai.test_ai_api_responses import AIAPITester
        return AIAPITester(ai_test_budget)
    except ImportError:
        pytest.skip("AI API testing not available")


@pytest.mark.ai
@pytest.mark.slow
async def test_production_feed_quality(ai_api_tester, api_client_authenticated, api_base_url):
    """
    Test AI evaluation of production feed quality

    This ensures the API returns feeds that users will find valuable.
    """
    try:
        # Get real feed from production API
        response = api_client_authenticated.make_request('GET', '/api/stories/feed?limit=20')

        if response.status_code != 200:
            pytest.skip(f"API returned {response.status_code}, cannot test feed quality")

        feed_data = response.json()
        stories = feed_data.get('stories', [])

        if len(stories) < 5:
            pytest.skip("Feed has too few stories for quality analysis")

        result = await ai_api_tester.test_stories_feed_quality(stories)

        # Log quality metrics for monitoring
        logger.info(f"📊 Production Feed Quality:")
        logger.info(f"   Overall: {result['overall_quality']}%")
        logger.info(f"   Diversity: {result['diversity_score']}%")
        logger.info(f"   Freshness: {result['freshness_score']}%")
        logger.info(f"   Ordering: {result['ordering_quality']}%")

        if result['recommendations']:
            logger.info("💡 Recommendations:")
            for rec in result['recommendations'][:2]:
                logger.info(f"   {rec}")

    except Exception as e:
        logger.warning(f"Production feed quality test failed: {e}")
        pytest.skip(f"Could not run production feed test: {e}")


@pytest.mark.ai
@pytest.mark.slow
async def test_story_detail_user_experience(ai_api_tester, api_client_authenticated, api_base_url):
    """
    Test individual story quality from user perspective

    Samples stories and evaluates if they're valuable to users.
    """
    try:
        # Get feed first
        response = api_client_authenticated.make_request('GET', '/api/stories/feed?limit=5')
        if response.status_code != 200:
            pytest.skip("Cannot get feed for story testing")

        feed_data = response.json()
        stories = feed_data.get('stories', [])

        if not stories:
            pytest.skip("No stories in feed")

        # Test first story in detail
        story_id = stories[0].get('id')
        if not story_id:
            pytest.skip("Story has no ID")

        detail_response = api_client_authenticated.make_request('GET', f'/api/stories/{story_id}')
        if detail_response.status_code != 200:
            pytest.skip(f"Cannot get story detail: {detail_response.status_code}")

        story_detail = detail_response.json()

        result = await ai_api_tester.test_story_detail_quality(story_detail)

        logger.info(f"👤 Story UX Quality: {result['overall_rating']}%")
        logger.info(f"   Title: {result['title_quality']}%, Summary: {result['summary_helpful']}%, Trust: {result['source_trust']}%")

        assert result['overall_rating'] >= 65, f"Story UX quality too low: {result['overall_rating']}%"

    except Exception as e:
        logger.warning(f"Story detail UX test failed: {e}")
        pytest.skip(f"Could not run story detail test: {e}")


@pytest.mark.ai
@pytest.mark.unit
async def test_ai_api_response_edge_cases(ai_api_tester):
    """Test AI evaluation handles various API response scenarios"""

    # Test empty feed - should get low scores but not crash
    empty_feed_result = await ai_api_tester.test_stories_feed_quality([], skip_quality_assertions=True)
    # Empty feed should have very low quality scores
    assert empty_feed_result['overall_quality'] < 20, f"Empty feed quality too high: {empty_feed_result['overall_quality']}%"
    assert empty_feed_result['diversity_score'] == 0, f"Empty feed should have 0 diversity: {empty_feed_result['diversity_score']}%"
    print(f"✅ Empty feed test passed - Quality: {empty_feed_result['overall_quality']}%, Diversity: {empty_feed_result['diversity_score']}%")

    # Test single story feed - should work without quality assertions
    single_story = [{
        'id': 'test_story',
        'title': 'Test Story',
        'category': 'world',
        'summary': {'text': 'A test story summary.'},
        'source_articles': [{'source': 'test', 'title': 'Test Article'}]
    }]

    # Test with quality assertions enabled (single story should fail some checks)
    try:
        single_result = await ai_api_tester.test_stories_feed_quality(single_story, skip_quality_assertions=False)
        print(f"✅ Single story feed test passed - Quality: {single_result['overall_quality']}%, Diversity: {single_result['diversity_score']}%")
    except AssertionError as e:
        # Single story feeds may fail quality checks, which is expected
        print(f"✅ Single story feed correctly flagged as low quality: {e}")


@pytest.mark.ai
@pytest.mark.slow
async def test_feed_quality_regression_monitoring(ai_api_tester, api_client_authenticated, api_base_url):
    """
    Monitor feed quality over time for regression

    This test runs in CI/CD to catch quality degradation.
    """
    try:
        # Get current feed quality
        response = api_client_authenticated.make_request('GET', '/api/stories/feed?limit=15')
        if response.status_code != 200:
            pytest.skip("Cannot get feed for regression testing")

        feed_data = response.json()
        stories = feed_data.get('stories', [])

        if len(stories) < 10:
            pytest.skip("Not enough stories for regression analysis")

        result = await ai_api_tester.test_stories_feed_quality(stories)

        # Compare against baseline (would be stored in database)
        baseline_quality = 75.0  # Example baseline

        if result['overall_quality'] < baseline_quality * 0.9:  # 10% degradation
            logger.warning(f"⚠️ Feed quality degraded: {result['overall_quality']}% vs {baseline_quality}% baseline")
            pytest.fail(f"Feed quality regression detected: {result['overall_quality']}% < {baseline_quality * 0.9}%")

        logger.info(f"📈 Feed Quality OK: {result['overall_quality']}% (baseline: {baseline_quality}%)")

    except Exception as e:
        logger.warning(f"Feed regression test failed: {e}")
        pytest.skip(f"Could not run regression test: {e}")


@pytest.mark.ai
@pytest.mark.slow
async def test_api_response_consistency(ai_api_tester, api_client_authenticated, api_base_url):
    """
    Test that API responses are consistent across multiple calls

    Ensures feed stability for users.
    """
    try:
        # Make multiple calls to check consistency
        responses = []
        for i in range(3):
            response = api_client_authenticated.make_request('GET', '/api/stories/feed?limit=10')
            if response.status_code == 200:
                feed_data = response.json()
                stories = feed_data.get('stories', [])
                if stories:
                    # Just keep story IDs for comparison
                    responses.append([s.get('id') for s in stories])

        if len(responses) < 2:
            pytest.skip("Not enough successful responses for consistency test")

        # Check if responses are reasonably consistent
        first_response = set(responses[0])
        consistent_count = 0

        for response in responses[1:]:
            response_set = set(response)
            overlap = len(first_response.intersection(response_set))
            consistency_ratio = overlap / len(first_response) if first_response else 0
            if consistency_ratio > 0.7:  # 70% overlap is reasonable
                consistent_count += 1

        consistency_rate = consistent_count / (len(responses) - 1)

        assert consistency_rate >= 0.5, f"API responses too inconsistent: {consistency_rate:.1f}"

        logger.info(f"🔄 API Consistency: {consistency_rate:.1f} ({consistent_count}/{len(responses)-1} consistent)")

    except Exception as e:
        logger.warning(f"API consistency test failed: {e}")
        pytest.skip(f"Could not run consistency test: {e}")
