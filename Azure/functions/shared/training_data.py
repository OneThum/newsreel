"""
Training Data Generation for Scoring Optimization (Phase 3.5)

Generates labeled training pairs for the similarity scoring model.
Uses various strategies to create positive and negative examples.
"""
import logging
import json
import random
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta, timezone
import asyncio
from pathlib import Path

from .config import config
from .cosmos_client import cosmos_client

logger = logging.getLogger(__name__)


class TrainingDataGenerator:
    """
    Generates labeled training data for similarity scoring.

    Strategies:
    - Positive pairs: Articles in same story cluster
    - Negative pairs: Articles from different categories/time periods
    - Hard negatives: Similar but different articles
    """

    def __init__(self):
        self.cosmos_client = cosmos_client

    async def generate_training_data(
        self,
        num_pairs: int = 1000,
        positive_ratio: float = 0.4,
        hard_negative_ratio: float = 0.3,
        time_window_days: int = 7
    ) -> List[Tuple[Dict[str, Any], Dict[str, Any], int]]:
        """
        Generate balanced training data.

        Args:
            num_pairs: Total number of training pairs to generate
            positive_ratio: Fraction of positive pairs (similar articles)
            hard_negative_ratio: Fraction of hard negative pairs (tricky dissimilar)
            time_window_days: How far back to look for articles

        Returns:
            List of (article1, article2, label) tuples where label is 1 for similar, 0 for dissimilar
        """
        logger.info(f"Generating {num_pairs} training pairs (positive: {positive_ratio:.1%}, hard_neg: {hard_negative_ratio:.1%})")

        # Calculate pair counts
        num_positive = int(num_pairs * positive_ratio)
        num_hard_negative = int(num_pairs * hard_negative_ratio)
        num_easy_negative = num_pairs - num_positive - num_hard_negative

        training_pairs = []

        # Generate positive pairs (articles in same cluster)
        positive_pairs = await self._generate_positive_pairs(num_positive, time_window_days)
        training_pairs.extend(positive_pairs)
        logger.info(f"Generated {len(positive_pairs)} positive pairs")

        # Generate hard negative pairs (similar but different)
        hard_negative_pairs = await self._generate_hard_negative_pairs(num_hard_negative, time_window_days)
        training_pairs.extend(hard_negative_pairs)
        logger.info(f"Generated {len(hard_negative_pairs)} hard negative pairs")

        # Generate easy negative pairs (obviously different)
        easy_negative_pairs = await self._generate_easy_negative_pairs(num_easy_negative, time_window_days)
        training_pairs.extend(easy_negative_pairs)
        logger.info(f"Generated {len(easy_negative_pairs)} easy negative pairs")

        # Shuffle to avoid ordering bias
        random.shuffle(training_pairs)

        logger.info(f"Total training pairs generated: {len(training_pairs)}")
        return training_pairs

    async def _generate_positive_pairs(self, num_pairs: int, time_window_days: int) -> List[Tuple[Dict[str, Any], Dict[str, Any], int]]:
        """Generate positive pairs from articles in the same story cluster."""
        pairs = []

        # Get recent story clusters
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=time_window_days)
        clusters = await self.cosmos_client.query_recent_story_clusters(cutoff_date.isoformat())

        # Filter clusters with multiple articles
        multi_article_clusters = [c for c in clusters if len(c.get('source_articles', [])) >= 2]

        if not multi_article_clusters:
            logger.warning("No clusters with multiple articles found")
            return pairs

        logger.info(f"Found {len(multi_article_clusters)} clusters with multiple articles")

        pairs_generated = 0
        attempts = 0
        max_attempts = num_pairs * 10  # Avoid infinite loops

        while pairs_generated < num_pairs and attempts < max_attempts:
            attempts += 1

            # Pick random cluster
            cluster = random.choice(multi_article_clusters)
            articles = cluster.get('source_articles', [])

            if len(articles) < 2:
                continue

            # Pick two different articles from same cluster
            article1_meta, article2_meta = random.sample(articles, 2)

            # Fetch full article data
            article1 = await self.cosmos_client.get_raw_article(article1_meta['id'])
            article2 = await self.cosmos_client.get_raw_article(article2_meta['id'])

            if article1 and article2 and self._articles_are_valid(article1, article2):
                pairs.append((article1, article2, 1))  # Label 1 = similar
                pairs_generated += 1

        logger.info(f"Generated {pairs_generated} positive pairs from {len(multi_article_clusters)} clusters")
        return pairs

    async def _generate_hard_negative_pairs(self, num_pairs: int, time_window_days: int) -> List[Tuple[Dict[str, Any], Dict[str, Any], int]]:
        """Generate hard negative pairs - articles that are similar but from different clusters."""
        pairs = []

        # Get recent articles
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=time_window_days)
        articles = await self.cosmos_client.query_recent_raw_articles(cutoff_date.isoformat(), limit=5000)

        if len(articles) < 2:
            logger.warning("Not enough articles for hard negative pairs")
            return pairs

        # Group articles by cluster
        cluster_groups = {}
        for article in articles:
            # Find which cluster this article belongs to
            cluster_id = await self._find_article_cluster(article['id'])
            if cluster_id:
                if cluster_id not in cluster_groups:
                    cluster_groups[cluster_id] = []
                cluster_groups[cluster_id].append(article)

        # Generate pairs from different clusters but similar characteristics
        pairs_generated = 0
        attempts = 0
        max_attempts = num_pairs * 20

        while pairs_generated < num_pairs and attempts < max_attempts:
            attempts += 1

            # Pick two different clusters
            if len(cluster_groups) < 2:
                break

            cluster_ids = list(cluster_groups.keys())
            cluster1_id, cluster2_id = random.sample(cluster_ids, 2)

            cluster1_articles = cluster_groups[cluster1_id]
            cluster2_articles = cluster_groups[cluster2_id]

            # Pick one article from each cluster
            article1 = random.choice(cluster1_articles)
            article2 = random.choice(cluster2_articles)

            # Check if they're "hard negatives" (some similarity but not too obvious)
            if self._are_hard_negatives(article1, article2):
                pairs.append((article1, article2, 0))  # Label 0 = dissimilar
                pairs_generated += 1

        logger.info(f"Generated {pairs_generated} hard negative pairs")
        return pairs

    async def _generate_easy_negative_pairs(self, num_pairs: int, time_window_days: int) -> List[Tuple[Dict[str, Any], Dict[str, Any], int]]:
        """Generate easy negative pairs - obviously different articles."""
        pairs = []

        # Get recent articles
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=time_window_days)
        articles = await self.cosmos_client.query_recent_raw_articles(cutoff_date.isoformat(), limit=2000)

        if len(articles) < 2:
            return pairs

        # Group by category for easy negatives
        category_groups = {}
        for article in articles:
            category = article.get('category', 'unknown')
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(article)

        pairs_generated = 0
        attempts = 0
        max_attempts = num_pairs * 5

        while pairs_generated < num_pairs and attempts < max_attempts:
            attempts += 1

            # Pick articles from different categories
            if len(category_groups) < 2:
                # Fallback: pick random different articles
                if len(articles) >= 2:
                    article1, article2 = random.sample(articles, 2)
                    if self._articles_are_valid(article1, article2):
                        pairs.append((article1, article2, 0))
                        pairs_generated += 1
                continue

            # Pick different categories
            categories = list(category_groups.keys())
            cat1, cat2 = random.sample(categories, 2)

            cat1_articles = category_groups[cat1]
            cat2_articles = category_groups[cat2]

            if cat1_articles and cat2_articles:
                article1 = random.choice(cat1_articles)
                article2 = random.choice(cat2_articles)

                if self._articles_are_valid(article1, article2):
                    pairs.append((article1, article2, 0))
                    pairs_generated += 1

        logger.info(f"Generated {pairs_generated} easy negative pairs")
        return pairs

    def _articles_are_valid(self, article1: Dict[str, Any], article2: Dict[str, Any]) -> bool:
        """Check if two articles are valid for training (have required fields)."""
        required_fields = ['id', 'title', 'description', 'published_at']

        for article in [article1, article2]:
            if not all(field in article and article[field] for field in required_fields):
                return False

        # Must be different articles
        if article1['id'] == article2['id']:
            return False

        return True

    def _are_hard_negatives(self, article1: Dict[str, Any], article2: Dict[str, Any]) -> bool:
        """Check if two articles make a good hard negative pair."""
        # Similar titles but different content (high title overlap, low description overlap)
        title1_words = set(article1.get('title', '').lower().split())
        title2_words = set(article2.get('title', '').lower().split())

        if not title1_words or not title2_words:
            return False

        title_overlap = len(title1_words.intersection(title2_words)) / len(title1_words.union(title2_words))

        # Hard negative: some title similarity but not too much
        if 0.1 < title_overlap < 0.6:
            return True

        # Similar entities but different context
        entities1 = {e.get('text', '').lower() for e in article1.get('entities', [])}
        entities2 = {e.get('text', '').lower() for e in article2.get('entities', [])}

        if entities1 and entities2:
            entity_overlap = len(entities1.intersection(entities2)) / len(entities1.union(entities2))
            if 0.2 < entity_overlap < 0.8:
                return True

        return False

    async def _find_article_cluster(self, article_id: str) -> Optional[str]:
        """Find which cluster an article belongs to."""
        try:
            # Query story clusters to find which one contains this article
            clusters = await self.cosmos_client.query_recent_story_clusters(
                (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
                limit=1000
            )

            for cluster in clusters:
                article_ids = {art['id'] for art in cluster.get('source_articles', [])}
                if article_id in article_ids:
                    return cluster['id']

        except Exception as e:
            logger.warning(f"Error finding cluster for article {article_id}: {e}")

        return None

    async def save_training_data(self, pairs: List[Tuple[Dict[str, Any], Dict[str, Any], int]], filepath: str):
        """Save training data to JSON file."""
        # Convert to serializable format
        serializable_pairs = []
        for article1, article2, label in pairs:
            pair_data = {
                'article1': {
                    'id': article1['id'],
                    'title': article1.get('title', ''),
                    'description': article1.get('description', ''),
                    'published_at': article1.get('published_at'),
                    'source': article1.get('source'),
                    'category': article1.get('category'),
                    'entities': article1.get('entities', []),
                    'embedding': article1.get('embedding')
                },
                'article2': {
                    'id': article2['id'],
                    'title': article2.get('title', ''),
                    'description': article2.get('description', ''),
                    'published_at': article2.get('published_at'),
                    'source': article2.get('source'),
                    'category': article2.get('category'),
                    'entities': article2.get('entities', []),
                    'embedding': article2.get('embedding')
                },
                'label': label
            }
            serializable_pairs.append(pair_data)

        # Save to file
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'pairs': serializable_pairs,
                'metadata': {
                    'generated_at': datetime.now(timezone.utc).isoformat(),
                    'num_pairs': len(serializable_pairs),
                    'positive_pairs': sum(1 for p in serializable_pairs if p['label'] == 1),
                    'negative_pairs': sum(1 for p in serializable_pairs if p['label'] == 0)
                }
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(serializable_pairs)} training pairs to {filepath}")

    async def load_training_data(self, filepath: str) -> List[Tuple[Dict[str, Any], Dict[str, Any], int]]:
        """Load training data from JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            pairs = []
            for pair_data in data.get('pairs', []):
                article1 = pair_data['article1']
                article2 = pair_data['article2']
                label = pair_data['label']
                pairs.append((article1, article2, label))

            logger.info(f"Loaded {len(pairs)} training pairs from {filepath}")
            return pairs

        except Exception as e:
            logger.error(f"Failed to load training data from {filepath}: {e}")
            return []


async def generate_training_data(num_pairs: int = 1000) -> List[Tuple[Dict[str, Any], Dict[str, Any], int]]:
    """Convenience function to generate training data."""
    generator = TrainingDataGenerator()
    return await generator.generate_training_data(num_pairs)


async def save_training_data(pairs: List[Tuple[Dict[str, Any], Dict[str, Any], int]], filepath: str = None):
    """Convenience function to save training data."""
    if filepath is None:
        filepath = config.SCORING_TRAINING_DATA_PATH

    generator = TrainingDataGenerator()
    await generator.save_training_data(pairs, filepath)


async def load_training_data(filepath: str = None) -> List[Tuple[Dict[str, Any], Dict[str, Any], int]]:
    """Convenience function to load training data."""
    if filepath is None:
        filepath = config.SCORING_TRAINING_DATA_PATH

    generator = TrainingDataGenerator()
    return await generator.load_training_data(filepath)
