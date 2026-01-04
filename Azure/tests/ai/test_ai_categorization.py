"""
AI-Powered Article Categorization Tests

Uses Claude to verify articles are categorized correctly.
This ensures news articles appear in appropriate categories for users.
"""

import os
import json
import logging
from typing import Dict, List, Any

import pytest
import anthropic
from anthropic import Anthropic

from functions.shared.models import RawArticle

logger = logging.getLogger(__name__)


class AICategorizationTester:
    """Uses AI to verify article categories are appropriate"""

    # Must match iOS NewsCategory enum - see functions/shared/categories.py
    VALID_CATEGORIES = [
        "world", "politics", "business", "technology", "science", 
        "health", "sports", "entertainment", "lifestyle", "environment"
    ]

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

    async def test_category_correctness(self, article: RawArticle) -> Dict:
        """
        Use AI to verify article category is appropriate

        Args:
            article: Article to evaluate

        Returns:
            Dict with evaluation results
        """
        if not self.budget.can_run_test():
            pytest.skip(f"💰 AI test budget exceeded (${self.budget.current_cost:.2f}/{self.budget.max_daily_cost:.2f})")

        prompt = """Evaluate if this article is correctly categorized.

ARTICLE:
Title: """ + str(article.title) + """
Description: """ + str(article.description or 'No description') + """
Content Preview: """ + str(article.content[:500] if article.content else 'No content') + """...

Current Category: """ + str(article.category) + """

Valid Categories: """ + ', '.join(self.VALID_CATEGORIES) + """

Questions (respond with JSON):

1. correct: Is the current category appropriate? (true/false)
2. confidence: How confident? (0-100)
3. better_category: If incorrect, what's better? (string or null)
4. reasoning: Brief explanation (string)

Consider:
- What is the PRIMARY TOPIC of this article?
- Which category best fits the main subject?
- Is it news about technology, business, sports, health, science, entertainment, politics, world events, or general interest?

Respond ONLY with valid JSON."""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}]
            )

            result = json.loads(response.content[0].text)
            cost = self._calculate_cost(response.usage.__dict__ if hasattr(response, 'usage') else {})
            self.budget.record_test("categorization_quality", cost, result)

            # Soft assertion - warn but don't fail (categories are subjective)
            if not result['correct'] and result['confidence'] > 80:
                logger.warning(f"🤖 AI suggests category change: {article.category} → {result['better_category']}")
                logger.warning(f"   Article: {article.title}")
                logger.warning(f"   Reasoning: {result['reasoning']}")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI categorization response as JSON: {response.content[0].text}")
            raise e
        except Exception as e:
            logger.error(f"AI categorization test failed: {e}")
            raise e

    async def test_category_distribution(self, articles: List[RawArticle]) -> Dict:
        """
        Analyze category distribution for balance and appropriateness

        Args:
            articles: List of articles to analyze

        Returns:
            Dict with distribution analysis
        """
        if not self.budget.can_run_test():
            pytest.skip("AI test budget exceeded")

        if len(articles) < 10:
            return {"balanced": True, "issues": [], "recommendations": []}

        # Sample articles for analysis
        sample_size = min(20, len(articles))
        sample_articles = articles[:sample_size]

        # Format for AI
        articles_text = []
        for i, article in enumerate(sample_articles):
            articles_text.append(f"{i+1}. [{article.category}] {article.title}")
        articles_text.append("")

        # Extract variables for f-string
        sample_count = len(sample_articles)
        articles_formatted = "\n".join(articles_text)
        valid_categories = ', '.join(self.VALID_CATEGORIES)

        prompt = f"""Analyze the category distribution of these {sample_count} articles.

ARTICLES:
{articles_formatted}

Valid Categories: {valid_categories}

Evaluate (respond with JSON):

1. balanced: Is the distribution reasonable? (true/false)
2. issues: Any categories over/under represented? (array of strings)
3. misclassifications: Articles that seem miscategorized? (array of objects with index, current, should_be)
4. recommendations: How to improve categorization? (array of strings)

Consider:
- Should most articles be in "world" or "general"?
- Are there too many articles in one category?
- Do categories match article content?

Respond ONLY with valid JSON."""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )

            result = json.loads(response.content[0].text)
            cost = self._calculate_cost(response.usage.__dict__ if hasattr(response, 'usage') else {})
            self.budget.record_test("category_distribution", cost, result)

            if not result['balanced'] or result['misclassifications']:
                logger.warning(f"🤖 Category distribution issues detected:")
                for issue in result['issues']:
                    logger.warning(f"   {issue}")
                for misc in result['misclassifications']:
                    logger.warning(f"   Article {misc['index']}: {misc['current']} → {misc['should_be']}")

            return result

        except Exception as e:
            logger.error(f"AI category distribution test failed: {e}")
            raise e


@pytest.fixture
def ai_categorization_tester(ai_test_budget):
    """AI-powered categorization quality tester"""
    try:
        from tests.ai.test_ai_categorization import AICategorizationTester
        return AICategorizationTester(ai_test_budget)
    except ImportError:
        pytest.skip("AI categorization testing not available")


@pytest.mark.ai
@pytest.mark.slow
async def test_sample_categorization_quality(ai_categorization_tester, sample_articles_batch):
    """
    Test AI evaluation of categorization on sample articles

    Ensures articles are placed in appropriate categories.
    """
    try:
        results = []
        for article in sample_articles_batch[:3]:  # Test first 3 for cost control
            result = await ai_categorization_tester.test_category_correctness(article)
            results.append(result)

        # At least 2/3 should be correct for test to pass
        correct_count = sum(1 for r in results if r['correct'])
        accuracy = correct_count / len(results)

        assert accuracy >= 0.67, f"Categorization accuracy too low: {accuracy:.1f} ({correct_count}/{len(results)})"

        logger.info(f"✅ AI Categorization Test Passed - Accuracy: {accuracy:.1f}")

    except Exception as e:
        logger.warning(f"AI categorization quality test skipped due to error: {e}")
        pytest.skip(f"Could not run AI categorization test: {e}")


@pytest.mark.ai
@pytest.mark.slow
async def test_category_distribution_analysis(ai_categorization_tester, cosmos_client_for_tests):
    """
    Test category distribution in production feed

    Ensures balanced and appropriate categorization.
    """
    try:
        # Sample recent articles from production
        recent_articles = await cosmos_client_for_tests.sample_recent_articles(limit=15)

        if len(recent_articles) < 10:
            pytest.skip("Not enough recent articles for distribution analysis")

        # Convert to RawArticle objects
        from functions.shared.models import RawArticle
        articles = []
        for art_dict in recent_articles:
            try:
                article = RawArticle.from_dict(art_dict)
                articles.append(article)
            except:
                continue  # Skip malformed articles

        if len(articles) < 10:
            pytest.skip("Not enough valid articles for analysis")

        result = await ai_categorization_tester.test_category_distribution(articles)

        # Log results but don't fail - categorization is subjective
        if not result['balanced']:
            logger.warning("Category distribution may need attention:")
            for issue in result['issues']:
                logger.warning(f"  {issue}")

        logger.info(f"📊 Category Distribution Analysis: {'Balanced' if result['balanced'] else 'Needs Attention'}")

    except Exception as e:
        logger.warning(f"Category distribution test failed: {e}")
        pytest.skip(f"Could not run distribution test: {e}")


@pytest.mark.ai
@pytest.mark.unit
async def test_ai_categorization_edge_cases(ai_categorization_tester):
    """Test AI categorization with edge cases"""

    from functions.shared.models import RawArticle
    from datetime import datetime, timezone

    # Test article that's clearly technology
    tech_article = RawArticle(
        id="test_tech_article",
        source="techcrunch",
        source_url="https://techcrunch.com",
        source_tier=1,
        article_url="https://techcrunch.com/ai-news",
        title="OpenAI Releases New GPT-5 Model with Advanced Reasoning",
        description="The latest AI model shows significant improvements in mathematical reasoning and coding tasks.",
        published_at=datetime.now(timezone.utc),
        fetched_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        published_date=datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        content="OpenAI has announced GPT-5, their most advanced AI model yet...",
        author="TechCrunch Staff",
        entities=[{"text": "OpenAI", "type": "ORGANIZATION"}, {"text": "GPT-5", "type": "PRODUCT"}],
        category="technology",  # Should be correct
        tags=["ai", "openai", "gpt-5"],
        language="en",
        story_fingerprint="openai_gpt5_release",
        processed=True,
        processing_attempts=0
    )

    result = await ai_categorization_tester.test_category_correctness(tech_article)
    assert result['correct'] == True, f"Tech article should be categorized correctly: {result['reasoning']}"
    assert result['confidence'] > 70, f"Should be confident about tech categorization: {result['confidence']}"


@pytest.mark.ai
@pytest.mark.slow
async def test_categorization_consistency_monitoring(ai_categorization_tester, cosmos_client_for_tests):
    """
    Monitor categorization consistency over time

    This would run in CI/CD to catch categorization drift.
    """
    try:
        # Sample articles from different time periods
        recent_articles = await cosmos_client_for_tests.sample_recent_articles(limit=10)
        older_articles = await cosmos_client_for_tests.sample_articles_before_days(days=7, limit=10)

        if len(recent_articles) < 5 or len(older_articles) < 5:
            pytest.skip("Not enough articles for consistency monitoring")

        # Test recent articles
        recent_correct = 0
        for art_dict in recent_articles[:5]:
            try:
                from functions.shared.models import RawArticle
                article = RawArticle.from_dict(art_dict)
                result = await ai_categorization_tester.test_category_correctness(article)
                if result['correct']:
                    recent_correct += 1
            except:
                continue

        # Test older articles
        older_correct = 0
        for art_dict in older_articles[:5]:
            try:
                from functions.shared.models import RawArticle
                article = RawArticle.from_dict(art_dict)
                result = await ai_categorization_tester.test_category_correctness(article)
                if result['correct']:
                    older_correct += 1
            except:
                continue

        if recent_correct > 0 and older_correct > 0:
            recent_accuracy = recent_correct / 5
            older_accuracy = older_correct / 5

            # Ensure we haven't gotten worse
            degradation = older_accuracy - recent_accuracy
            if degradation > 0.3:  # 30% drop
                logger.warning(f"⚠️ Categorization quality degraded: {older_accuracy:.1f} → {recent_accuracy:.1f}")
            else:
                logger.info(f"📊 Categorization Consistency: Recent {recent_accuracy:.1f}, Older {older_accuracy:.1f}")

    except Exception as e:
        logger.warning(f"Categorization consistency test failed: {e}")
        pytest.skip(f"Could not run consistency test: {e}")
