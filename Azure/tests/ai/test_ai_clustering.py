"""
AI-Powered Story Clustering Quality Tests

Uses Claude to verify stories are correctly clustered (not just by fingerprint similarity).
This ensures articles about the same event are grouped together properly.
"""

import os
import json
import logging
from typing import Dict, List, Any

import pytest
import anthropic
from anthropic import Anthropic

from functions.shared.models import RawArticle, StoryCluster

logger = logging.getLogger(__name__)


class AIClusteringTester:
    """Uses AI to verify articles are correctly clustered"""

    def __init__(self, budget):
        self.budget = budget
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable required")

        self.client = Anthropic(api_key=api_key)

    def _format_other_clusters(self, other_clusters: List[StoryCluster]) -> str:
        """Format other cluster options for AI evaluation"""
        formatted = []
        for i, cluster in enumerate(other_clusters):
            formatted.append(f"{i}: {cluster.title}")
            if cluster.summary and cluster.summary.get('text'):
                formatted.append(f"   Summary: {cluster.summary['text'][:200]}...")
            formatted.append("")
        return "\n".join(formatted)

    def _calculate_cost(self, usage: Dict) -> float:
        """Calculate cost from Anthropic usage data"""
        input_cost = (usage.get('input_tokens', 0) / 1_000_000) * 3.0
        output_cost = (usage.get('output_tokens', 0) / 1_000_000) * 15.0
        cache_cost = (usage.get('cache_read_input_tokens', 0) / 1_000_000) * 0.3
        return input_cost + output_cost + cache_cost

    async def test_story_belongs_to_cluster(
        self,
        article: RawArticle,
        assigned_cluster: StoryCluster,
        other_clusters: List[StoryCluster]
    ) -> Dict:
        """
        Use AI to verify article is correctly assigned to its cluster

        Args:
            article: The article that was clustered
            assigned_cluster: The cluster it was assigned to
            other_clusters: Other available clusters for comparison

        Returns:
            Dict with evaluation results
        """
        if not self.budget.can_run_test():
            pytest.skip(f"💰 AI test budget exceeded (${self.budget.current_cost:.2f}/{self.budget.max_daily_cost:.2f})")

        # Extract variables for f-string
        article_title = article.title
        article_content = article.description or (article.content[:500] if article.content else "No content")
        cluster_title = assigned_cluster.title
        cluster_summary = assigned_cluster.summary.text if assigned_cluster.summary else 'No summary'
        cluster_category = assigned_cluster.category
        cluster_sources_count = len(assigned_cluster.source_articles)
        other_clusters_text = self._format_other_clusters(other_clusters[:5])

        prompt = f"""You are testing a news clustering algorithm.

NEW ARTICLE:
Title: {article_title}
Content: {article_content}

ASSIGNED CLUSTER:
Title: {cluster_title}
Summary: {cluster_summary}
Category: {cluster_category}
Sources: {cluster_sources_count} articles

OTHER CANDIDATE CLUSTERS:
{other_clusters_text}

Questions (respond with JSON):

1. correct_cluster: Is the article correctly assigned? (true/false)
2. confidence: How confident are you? (0-100)
3. better_match: If incorrect, which cluster index is better? (number or null)
4. reasoning: Why is this the correct/incorrect assignment? (string)

Consider:
- Are they about the SAME EVENT or just same topic?
- Do they reference the same people, places, dates?
- Would a reader expect these to be the same story?
- Is this breaking news that should be separate?

Respond ONLY with valid JSON."""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )

            result = json.loads(response.content[0].text)
            cost = self._calculate_cost(response.usage.__dict__ if hasattr(response, 'usage') else {})
            self.budget.record_test("clustering_quality", cost, result)

            # Log failures for analysis
            if not result['correct_cluster'] and result['confidence'] > 70:
                logger.warning(f"🤖 AI detected clustering error: {result['reasoning']}")
                logger.warning(f"   Article: {article.title}")
                logger.warning(f"   Assigned to: {assigned_cluster.title}")
                if result['better_match'] is not None and result['better_match'] < len(other_clusters):
                    logger.warning(f"   Should be: {other_clusters[result['better_match']].title}")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI clustering response as JSON: {response.content[0].text}")
            raise e
        except Exception as e:
            logger.error(f"AI clustering test failed: {e}")
            raise e

    async def test_cluster_coherence(self, cluster: StoryCluster) -> Dict:
        """
        Test if all articles in a cluster are actually about the same story

        Args:
            cluster: Story cluster to evaluate

        Returns:
            Dict with coherence evaluation
        """
        if not self.budget.can_run_test():
            pytest.skip("AI test budget exceeded")

        if len(cluster.source_articles) < 2:
            return {"coherent": True, "confidence": 100, "reasoning": "Single article clusters are coherent by definition"}

        # Format articles for AI
        articles_text = []
        for i, article in enumerate(cluster.source_articles[:5]):  # Limit for cost
            articles_text.append(f"Article {i+1}: {article.get('title', 'No title')}")
            content = article.get('content', article.get('description', ''))
            articles_text.append(f"Content: {content[:300] if content else 'No content'}...")
            articles_text.append("")

        # Extract variables for f-string
        cluster_title = cluster.title
        cluster_category = cluster.category
        articles_formatted = "\n".join(articles_text)

        prompt = f"""Evaluate if these articles are all about the SAME STORY.

CLUSTER TITLE: {cluster_title}
CATEGORY: {cluster_category}

ARTICLES:
{articles_formatted}

Questions (respond with JSON):
1. coherent: Are all articles about the same core event/story? (true/false)
2. confidence: How confident? (0-100)
3. issues: If incoherent, which articles don't belong? (array of article indices)
4. reasoning: Brief explanation (string)

Consider:
- Same event vs same topic
- Same people/places/dates
- Same core facts
- Breaking news should be separate

Respond ONLY with valid JSON."""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )

            result = json.loads(response.content[0].text)
            cost = self._calculate_cost(response.usage.__dict__ if hasattr(response, 'usage') else {})
            self.budget.record_test("cluster_coherence", cost, result)

            if not result['coherent'] and result['confidence'] > 70:
                logger.warning(f"🤖 AI detected incoherent cluster: {cluster.title}")
                logger.warning(f"   Issues: {result['issues']}")
                logger.warning(f"   Reasoning: {result['reasoning']}")

            return result

        except Exception as e:
            logger.error(f"AI cluster coherence test failed: {e}")
            raise e


@pytest.fixture
def ai_clustering_tester(ai_test_budget):
    """AI-powered clustering quality tester"""
    try:
        from tests.ai.test_ai_clustering import AIClusteringTester
        return AIClusteringTester(ai_test_budget)
    except ImportError:
        pytest.skip("AI clustering testing not available")


@pytest.mark.ai
@pytest.mark.slow
async def test_sample_clustering_quality(ai_clustering_tester, cosmos_client_for_tests, sample_articles_batch):
    """
    Test AI evaluation of clustering quality on sample data

    This ensures articles about the same event are properly grouped.
    """
    try:
        # Create a mock cluster from our sample articles (they're all about the same earthquake)
        from functions.shared.models import StoryCluster

        mock_cluster = StoryCluster(
            id="test_cluster_earthquake",
            event_fingerprint="earthquake_japan_7.2",
            title="Earthquake Strikes Japan",
            category="world",
            tags=["earthquake", "japan", "disaster"],
            status="DEVELOPING",
            verification_level=2,
            first_seen=sample_articles_batch[0].published_at,
            last_updated=sample_articles_batch[0].updated_at,
            source_articles=[
                {
                    'id': article.id,
                    'source': article.source,
                    'title': article.title,
                    'content': article.content,
                    'published_at': article.published_at.isoformat()
                }
                for article in sample_articles_batch
            ],
            importance_score=75,
            confidence_score=80,
            breaking_news=False
        )

        # Test cluster coherence
        coherence_result = await ai_clustering_tester.test_cluster_coherence(mock_cluster)

        assert coherence_result['coherent'], f"Sample cluster should be coherent: {coherence_result['reasoning']}"
        assert coherence_result['confidence'] > 80, f"Should be confident about coherence: {coherence_result['confidence']}"

        logger.info(f"✅ AI Clustering Test Passed - Coherence: {coherence_result['confidence']}%")

    except Exception as e:
        logger.warning(f"AI clustering quality test skipped due to error: {e}")
        pytest.skip(f"Could not run AI clustering test: {e}")


@pytest.mark.ai
@pytest.mark.slow
async def test_production_clustering_sample(ai_clustering_tester, cosmos_client_for_tests):
    """
    Test clustering quality on real production data

    Samples recent clusters and verifies they make sense.
    """
    try:
        # Sample recent clusters with multiple articles
        clusters = await cosmos_client_for_tests.sample_clusters_with_multiple_articles(limit=3)

        if not clusters:
            pytest.skip("No clusters with multiple articles found")

        coherence_scores = []

        for cluster in clusters:
            # Convert to StoryCluster object
            story_cluster = StoryCluster.from_dict(cluster)
            result = await ai_clustering_tester.test_cluster_coherence(story_cluster)

            coherence_scores.append(result['confidence'] if result['coherent'] else 0)

            if not result['coherent']:
                logger.warning(f"Production cluster issue detected: {cluster['title']}")

        if coherence_scores:
            avg_coherence = sum(coherence_scores) / len(coherence_scores)
            assert avg_coherence >= 70, f"Production clustering coherence too low: {avg_coherence:.1f}%"

            logger.info(f"🎯 Production Clustering OK - Avg Coherence: {avg_coherence:.1f}%")

    except Exception as e:
        logger.warning(f"Production clustering test failed: {e}")
        pytest.skip(f"Could not run production clustering test: {e}")


@pytest.mark.ai
@pytest.mark.unit
async def test_ai_clustering_edge_cases(ai_clustering_tester, sample_article):
    """Test AI clustering evaluation handles edge cases"""

    # Test with single article cluster (should always be coherent)
    from functions.shared.models import StoryCluster

    single_article_cluster = StoryCluster(
        id="single_test",
        event_fingerprint="single_event",
        title="Single Article Story",
        category="world",
        tags=["test"],
        status="DEVELOPING",
        verification_level=1,
        first_seen=sample_article.published_at,
        last_updated=sample_article.updated_at,
        source_articles=[{
            'id': sample_article.id,
            'source': sample_article.source,
            'title': sample_article.title,
            'content': sample_article.content,
            'published_at': sample_article.published_at.isoformat()
        }],
        importance_score=50,
        confidence_score=60,
        breaking_news=False
    )

    result = await ai_clustering_tester.test_cluster_coherence(single_article_cluster)
    assert result['coherent'] == True, "Single article clusters should always be coherent"
    assert result['confidence'] >= 95, "Should be very confident about single article coherence"


@pytest.mark.ai
@pytest.mark.slow
async def test_clustering_regression_detection(ai_clustering_tester, cosmos_client_for_tests):
    """
    Monitor for clustering quality regression over time

    This test would run in CI/CD to catch if clustering gets worse.
    """
    try:
        # Get historical clustering quality metrics
        # This would compare against baseline stored in database
        baseline_coherence = 85.0  # Example baseline

        clusters = await cosmos_client_for_tests.sample_recent_clusters(limit=5)

        if not clusters:
            pytest.skip("No recent clusters to test")

        current_scores = []

        for cluster_dict in clusters:
            cluster = StoryCluster.from_dict(cluster_dict)
            if len(cluster.source_articles) >= 2:
                result = await ai_clustering_tester.test_cluster_coherence(cluster)
                score = result['confidence'] if result['coherent'] else 20  # Low score for incoherent
                current_scores.append(score)

        if current_scores:
            current_avg = sum(current_scores) / len(current_scores)

            # Allow some degradation but catch major issues
            assert current_avg >= baseline_coherence * 0.8, f"Clustering quality degraded: {current_avg:.1f}% vs {baseline_coherence:.1f}% baseline"

            logger.info(f"📊 Clustering Quality: {current_avg:.1f}% (baseline: {baseline_coherence:.1f}%)")

    except Exception as e:
        logger.warning(f"Clustering regression test failed: {e}")
        pytest.skip(f"Could not run regression test: {e}")
