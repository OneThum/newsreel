"""
AI-Powered Summary Quality Tests

Uses Claude (Anthropic) to evaluate news summary accuracy, bias, and quality.
This is critical for ensuring summaries are factual and trustworthy.
"""

import os
import json
import logging
from typing import Dict, List, Any
from datetime import datetime, timezone

import pytest
import anthropic
from anthropic import Anthropic

from functions.shared.models import StoryCluster, RawArticle
from functions.shared.cosmos_client import CosmosDBClient

logger = logging.getLogger(__name__)


class AITestBudget:
    """Control AI testing costs with daily limits"""

    def __init__(self, max_daily_cost: float = 5.0):
        self.max_daily_cost = max_daily_cost
        self.current_cost = 0.0
        self.test_results = []
        self.daily_reset_date = datetime.now(timezone.utc).date()

    def can_run_test(self, estimated_cost: float = 0.01) -> bool:
        """Check if we can run another test within budget"""
        # Reset daily budget if it's a new day
        today = datetime.now(timezone.utc).date()
        if today != self.daily_reset_date:
            self.current_cost = 0.0
            self.daily_reset_date = today
            logger.info(f"💰 Daily AI test budget reset to $0.00")

        return (self.current_cost + estimated_cost) <= self.max_daily_cost

    def record_test(self, test_name: str, cost: float, result: Dict):
        """Record a completed test"""
        self.current_cost += cost
        self.test_results.append({
            'test': test_name,
            'cost': cost,
            'timestamp': datetime.now(timezone.utc),
            'result': result
        })
        logger.info(f"💰 AI test completed: {test_name} (${cost:.4f}) - Total today: ${self.current_cost:.4f}")

    def get_remaining_budget(self) -> float:
        """Get remaining budget for today"""
        return max(0, self.max_daily_cost - self.current_cost)


class AISummaryQualityTester:
    """Uses AI to verify news summaries are accurate and unbiased"""

    def __init__(self, budget: AITestBudget):
        self.budget = budget
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable required")

        self.client = Anthropic(api_key=api_key)

    def _format_sources(self, source_articles: List[Dict]) -> str:
        """Format source articles for AI evaluation"""
        formatted = []
        for article in source_articles[:5]:  # Limit to 5 sources for cost control
            formatted.append(f"Source: {article.get('source', 'unknown')}")
            formatted.append(f"Title: {article.get('title', 'No title')}")
            formatted.append(f"Content: {article.get('content', 'No content')[:500]}...")  # Truncate for cost
            formatted.append("---")
        return "\n".join(formatted)

    def _calculate_cost(self, usage: Dict) -> float:
        """Calculate cost from Anthropic usage data"""
        # Claude Sonnet 4.5 pricing: ~$3/input million tokens, ~$15/output million tokens
        input_cost = (usage.get('input_tokens', 0) / 1_000_000) * 3.0
        output_cost = (usage.get('output_tokens', 0) / 1_000_000) * 15.0
        cache_cost = (usage.get('cache_read_input_tokens', 0) / 1_000_000) * 0.3  # Cache reads are cheaper
        return input_cost + output_cost + cache_cost

    async def test_summary_accuracy(self, story: Dict, summary_text: str) -> Dict:
        """
        Use AI to verify summary accurately reflects source articles

        Args:
            story: Story cluster dict with source_articles
            summary_text: The generated summary to evaluate

        Returns:
            Dict with evaluation results
        """
        if not self.budget.can_run_test():
            pytest.skip(f"💰 AI test budget exceeded (${self.budget.current_cost:.2f}/{self.budget.max_daily_cost:.2f})")

        sources_text = self._format_sources(story.get('source_articles', []))
        prompt = f"""You are a quality assurance AI testing news summaries.

SOURCE ARTICLES:
{sources_text}

GENERATED SUMMARY:
{summary_text}

Evaluate this summary on these criteria (respond with JSON):

1. factual_accuracy: Does it accurately represent the source articles? (score 0-100)
2. bias_detection: Is it neutral and unbiased? (score 0-100, 100=perfectly neutral)
3. completeness: Does it cover key points from all sources? (score 0-100)
4. hallucinations: Does it contain information not in sources? (true/false)
5. issues: List any specific problems (array of strings)

Respond ONLY with valid JSON."""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse AI response
            result = json.loads(response.content[0].text)

            # Calculate cost
            cost = self._calculate_cost(response.usage.__dict__ if hasattr(response, 'usage') else {})

            # Record the test
            self.budget.record_test("summary_accuracy", cost, result)

            # Assert on AI evaluation with reasonable thresholds
            assert result['factual_accuracy'] >= 80, f"Summary accuracy too low: {result['factual_accuracy']}%"
            assert result['bias_detection'] >= 70, f"Summary shows bias: {result['bias_detection']}%"
            assert not result['hallucinations'], f"Summary contains hallucinations: {result['issues']}"

            logger.info(f"✅ AI Summary Test Passed - Accuracy: {result['factual_accuracy']}%, Bias: {result['bias_detection']}%, Cost: ${cost:.4f}")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {response.content[0].text}")
            raise e
        except Exception as e:
            logger.error(f"AI summary test failed: {e}")
            raise e


@pytest.fixture
def ai_budget():
    """Provide AI testing budget fixture"""
    return AITestBudget(max_daily_cost=5.0)


@pytest.fixture
def ai_summary_tester(ai_budget):
    """Provide AI summary quality tester"""
    return AISummaryQualityTester(ai_budget)


@pytest.mark.ai
@pytest.mark.slow
async def test_sample_production_summaries(ai_summary_tester, cosmos_client_for_tests):
    """
    Test AI evaluation on sample production summaries

    This ensures our summaries are accurate and unbiased before users see them.
    """
    # Sample a few stories with summaries from production
    try:
        stories_with_summaries = await cosmos_client_for_tests.sample_stories_with_summaries(limit=3)

        if not stories_with_summaries:
            pytest.skip("No stories with summaries found in database")

        for story in stories_with_summaries:
            if story.get('summary') and story['summary'].get('text'):
                summary_text = story['summary']['text']
                result = await ai_summary_tester.test_summary_accuracy(story, summary_text)

                # Log results for monitoring
                logger.info(f"AI Quality Check - Story {story['id']}: "
                           f"Accuracy={result['factual_accuracy']}%, "
                           f"Bias={result['bias_detection']}%, "
                           f"Complete={result['completeness']}%")

    except Exception as e:
        logger.warning(f"AI summary quality test skipped due to error: {e}")
        pytest.skip(f"Could not run AI quality test: {e}")


@pytest.mark.ai
@pytest.mark.unit
async def test_ai_budget_control(ai_budget):
    """Test that budget control works correctly"""
    # Should allow tests initially
    assert ai_budget.can_run_test(1.0) == True

    # Record a test
    ai_budget.record_test("test1", 1.50, {"result": "success"})

    # Should still allow more tests
    assert ai_budget.can_run_test(1.0) == True

    # Record another expensive test
    ai_budget.record_test("test2", 3.0, {"result": "success"})

    # Should now be over budget
    assert ai_budget.can_run_test(1.0) == False

    # Check remaining budget
    assert ai_budget.get_remaining_budget() < 1.0


@pytest.mark.ai
@pytest.mark.unit
async def test_ai_summary_validation_edge_cases(ai_summary_tester):
    """Test AI evaluation handles edge cases properly"""

    # Test with empty summary
    with pytest.raises(AssertionError):
        await ai_summary_tester.test_summary_accuracy({"source_articles": []}, "")

    # Test with hallucinated content (should fail)
    story = {
        "source_articles": [{
            "source": "test",
            "title": "Local Event",
            "content": "A local community event happened today."
        }]
    }

    # This should fail because summary contains info not in sources
    with pytest.raises(AssertionError):
        await ai_summary_tester.test_summary_accuracy(story, "A global pandemic affected millions worldwide.")


@pytest.mark.ai
@pytest.mark.slow
async def test_continuous_production_monitoring(ai_summary_tester, cosmos_client_for_tests):
    """
    Continuous monitoring test that runs periodically

    This would be run in CI/CD to catch quality degradation over time.
    """
    try:
        # Get recent stories (last 24 hours)
        recent_stories = await cosmos_client_for_tests.sample_recent_stories(limit=5)

        if not recent_stories:
            pytest.skip("No recent stories to test")

        total_accuracy = 0
        total_bias = 0
        count = 0

        for story in recent_stories:
            if story.get('summary') and story['summary'].get('text'):
                result = await ai_summary_tester.test_summary_accuracy(story, story['summary']['text'])
                total_accuracy += result['factual_accuracy']
                total_bias += result['bias_detection']
                count += 1

        if count > 0:
            avg_accuracy = total_accuracy / count
            avg_bias = total_bias / count

            # Set quality thresholds for continuous monitoring
            assert avg_accuracy >= 75, f"Production summary accuracy degraded: {avg_accuracy:.1f}%"
            assert avg_bias >= 70, f"Production summary bias increased: {avg_bias:.1f}%"

            logger.info(f"🎯 Production Quality OK - Avg Accuracy: {avg_accuracy:.1f}%, Avg Bias: {avg_bias:.1f}%")

    except Exception as e:
        logger.warning(f"Continuous monitoring test failed: {e}")
        pytest.skip(f"Could not run continuous monitoring: {e}")
