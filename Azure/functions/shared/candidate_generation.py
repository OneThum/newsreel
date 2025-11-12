"""Hybrid candidate generation using FAISS + BM25 for news clustering"""
from rank_bm25 import BM25Okapi
from datetime import datetime, timedelta
from typing import List, Set, Tuple, Dict, Any, Optional
import logging
import numpy as np

from .vector_index import VectorIndex, search_similar_articles

logger = logging.getLogger(__name__)


class CandidateGenerator:
    """
    Generates candidate clusters using hybrid search:
    1. FAISS vector search (semantic similarity)
    2. BM25 keyword search (lexical precision)
    3. Time window filtering
    4. Result merging and deduplication
    """

    def __init__(self, vector_index: Optional[VectorIndex] = None):
        """
        Initialize candidate generator

        Args:
            vector_index: Optional VectorIndex instance (will create if None)
        """
        self.vector_index = vector_index
        self.bm25_index = None  # Built from recent articles
        self.bm25_corpus = []
        self.bm25_article_ids = []
        self.last_bm25_update = None

    def build_bm25_index(self, articles, max_age_hours: int = 168):
        """
        Build BM25 index from recent articles

        Args:
            articles: List of RawArticle objects
            max_age_hours: Maximum age of articles to include (default: 1 week)
        """
        if not articles:
            logger.warning("No articles provided for BM25 index")
            return

        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        recent_articles = []

        # Filter recent articles
        for article in articles:
            pub_time = getattr(article, 'published_at', datetime.now())
            if pub_time >= cutoff_time:
                recent_articles.append(article)

        if not recent_articles:
            logger.warning(f"No articles within {max_age_hours} hours for BM25 index")
            return

        # Build corpus
        self.bm25_corpus = []
        self.bm25_article_ids = []

        for article in recent_articles:
            # Tokenize title (BM25 works best on titles for news)
            title = getattr(article, 'title', '')
            if title:
                # Simple tokenization: lowercase, split, remove short words
                tokens = [w.lower() for w in title.split() if len(w) > 2]
                if tokens:  # Only add if we have tokens
                    self.bm25_corpus.append(tokens)
                    self.bm25_article_ids.append(getattr(article, 'id', 'unknown'))

        # Build BM25 index
        if self.bm25_corpus:
            self.bm25_index = BM25Okapi(self.bm25_corpus)
            self.last_bm25_update = datetime.now()
            logger.info(f"✅ Built BM25 index with {len(self.bm25_corpus)} documents")
        else:
            logger.warning("No valid documents for BM25 index")

    def find_candidates(
        self,
        article,
        embedding: np.ndarray,
        time_window_hours: int = 72,
        max_candidates: int = 150
    ) -> List[str]:
        """
        Find candidate clusters using hybrid search

        Strategy:
        1. Vector search (FAISS) for semantic similarity - 70% of candidates
        2. Keyword search (BM25) for lexical precision - 30% of candidates
        3. Time window filtering
        4. Merge and deduplicate

        Args:
            article: RawArticle object
            embedding: Article embedding vector
            time_window_hours: Hours back to search
            max_candidates: Maximum candidates to return

        Returns:
            List of candidate article IDs
        """
        # Time window: from article publish time back to cutoff
        article_time = getattr(article, 'published_at', datetime.now())
        time_min = article_time - timedelta(hours=time_window_hours)
        time_max = article_time + timedelta(hours=6)  # Small future window

        time_window = (time_min, time_max)
        category = getattr(article, 'category', None)

        # 1. Vector search (semantic similarity) - get more candidates
        vector_candidates = []
        try:
            vector_results = search_similar_articles(
                embedding,
                k=max_candidates * 2,  # Get more for diversity
                time_window_hours=time_window_hours,
                category=category
            )
            vector_candidates = [article_id for article_id, _ in vector_results]
        except Exception as e:
            logger.error(f"❌ Vector search failed: {e}")

        # 2. BM25 search (keyword precision)
        bm25_candidates = []
        try:
            if self.bm25_index and self.bm25_article_ids:
                # Query with article title
                title = getattr(article, 'title', '')
                if title:
                    query_tokens = [w.lower() for w in title.split() if len(w) > 2]
                    if query_tokens:
                        bm25_scores = self.bm25_index.get_scores(query_tokens)

                        # Get top candidates
                        top_indices = np.argsort(bm25_scores)[-max_candidates//2:][::-1]  # Top 50% from BM25
                        bm25_candidates = [self.bm25_article_ids[i] for i in top_indices if bm25_scores[i] > 0]
        except Exception as e:
            logger.error(f"❌ BM25 search failed: {e}")

        # 3. Merge candidates (union for diversity)
        all_candidates = set(vector_candidates + bm25_candidates)

        # Remove self if present
        article_id = getattr(article, 'id', None)
        if article_id in all_candidates:
            all_candidates.remove(article_id)

        # 4. Cap at maximum candidates
        candidate_list = list(all_candidates)[:max_candidates]

        logger.info(f"🔍 Hybrid search for article '{getattr(article, 'title', '')[:50]}...': "
                   f"vector={len(vector_candidates)}, bm25={len(bm25_candidates)}, "
                   f"merged={len(all_candidates)}, final={len(candidate_list)}")

        return candidate_list

    def find_candidates_by_text(
        self,
        title: str,
        embedding: Optional[np.ndarray] = None,
        category: Optional[str] = None,
        time_window_hours: int = 72,
        max_candidates: int = 150
    ) -> List[str]:
        """
        Find candidates using only text (for fallback or testing)

        Args:
            title: Article title
            embedding: Optional embedding vector
            category: Article category
            time_window_hours: Hours back to search
            max_candidates: Maximum candidates to return

        Returns:
            List of candidate article IDs
        """
        # This is a simplified version for when we don't have a full article object
        # Use BM25 only, or vector search if embedding provided

        candidates = set()

        # BM25 search
        try:
            if self.bm25_index and self.bm25_article_ids and title:
                query_tokens = [w.lower() for w in title.split() if len(w) > 2]
                if query_tokens:
                    bm25_scores = self.bm25_index.get_scores(query_tokens)
                    top_indices = np.argsort(bm25_scores)[-max_candidates//2:][::-1]
                    bm25_candidates = [self.bm25_article_ids[i] for i in top_indices if bm25_scores[i] > 0]
                    candidates.update(bm25_candidates)
        except Exception as e:
            logger.error(f"❌ BM25 text search failed: {e}")

        # Vector search if embedding provided
        try:
            if embedding is not None:
                vector_results = search_similar_articles(
                    embedding,
                    k=max_candidates//2,
                    time_window_hours=time_window_hours,
                    category=category
                )
                vector_candidates = [article_id for article_id, _ in vector_results]
                candidates.update(vector_candidates)
        except Exception as e:
            logger.error(f"❌ Vector text search failed: {e}")

        return list(candidates)[:max_candidates]

    def is_bm25_stale(self, max_age_minutes: int = 60) -> bool:
        """
        Check if BM25 index is stale and needs rebuild

        Args:
            max_age_minutes: Maximum age in minutes

        Returns:
            True if index needs rebuild
        """
        if not self.last_bm25_update:
            return True

        age = datetime.now() - self.last_bm25_update
        return age.total_seconds() > (max_age_minutes * 60)

    def get_stats(self) -> Dict[str, Any]:
        """Get candidate generator statistics"""
        return {
            'bm25_documents': len(self.bm25_corpus) if self.bm25_corpus else 0,
            'bm25_article_ids': len(self.bm25_article_ids) if self.bm25_article_ids else 0,
            'last_bm25_update': self.last_bm25_update.isoformat() if self.last_bm25_update else None,
            'vector_index_available': self.vector_index is not None
        }


# Global candidate generator instance
_candidate_generator: Optional[CandidateGenerator] = None


def get_candidate_generator() -> CandidateGenerator:
    """Get or create global candidate generator instance"""
    global _candidate_generator
    if _candidate_generator is None:
        _candidate_generator = CandidateGenerator()
    return _candidate_generator


def find_article_candidates(
    article,
    embedding: np.ndarray,
    time_window_hours: int = 72,
    max_candidates: int = 150
) -> List[str]:
    """
    Convenience function to find candidate articles for clustering

    Args:
        article: RawArticle object
        embedding: Article embedding vector
        time_window_hours: Hours back to search
        max_candidates: Maximum candidates to return

    Returns:
        List of candidate article IDs
    """
    try:
        generator = get_candidate_generator()
        return generator.find_candidates(
            article=article,
            embedding=embedding,
            time_window_hours=time_window_hours,
            max_candidates=max_candidates
        )
    except Exception as e:
        logger.error(f"❌ Failed to find article candidates: {e}")
        return []
