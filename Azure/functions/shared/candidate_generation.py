"""
Hybrid Candidate Generation for News Clustering - Phase 2

Combines semantic vector search (FAISS) with keyword-based search (BM25)
for finding candidate stories to compare against new articles.
"""
from rank_bm25 import BM25Okapi
from datetime import datetime, timedelta
from typing import List, Set, Tuple, Dict, Any, Optional
import numpy as np
import logging

from .vector_index import VectorIndex
from .embeddings_client import EmbeddingsClient

logger = logging.getLogger(__name__)


class CandidateGenerator:
    """
    Hybrid candidate generation using FAISS + BM25

    Strategy:
    1. Vector search (FAISS) for semantic similarity - O(log n) fast
    2. Keyword search (BM25) for lexical precision
    3. Time window filtering
    4. Merge and deduplicate results
    """

    def __init__(self, vector_index: VectorIndex, embeddings_client: Optional[EmbeddingsClient] = None):
        """
        Initialize the candidate generator

        Args:
            vector_index: FAISS vector index instance
            embeddings_client: Client for embedding service (optional)
        """
        self.vector_index = vector_index
        self.embeddings_client = embeddings_client

        # BM25 index components
        self.bm25_index: Optional[BM25Okapi] = None
        self.bm25_corpus: List[List[str]] = []  # Tokenized documents
        self.bm25_article_ids: List[str] = []  # Corresponding article IDs
        self.bm25_last_updated: Optional[datetime] = None

    async def build_bm25_index(self, articles: List[Dict[str, Any]], force_rebuild: bool = False):
        """
        Build or update BM25 index from recent articles

        Args:
            articles: List of article dictionaries
            force_rebuild: Force rebuild even if recent
        """
        if not articles:
            return

        # Check if rebuild is needed
        now = datetime.now()
        if (self.bm25_index and not force_rebuild and
            self.bm25_last_updated and (now - self.bm25_last_updated).seconds < 3600):  # 1 hour
            return

        logger.info(f"Building BM25 index from {len(articles)} articles...")

        # Prepare corpus
        self.bm25_corpus = []
        self.bm25_article_ids = []

        for article in articles:
            # Combine title and description for BM25
            title = article.get('title', '')
            description = article.get('description', '')[:200]  # Limit description length

            # Tokenize: simple whitespace split + lowercase
            text = f"{title} {description}".lower()
            tokens = text.split()

            # Filter out very short tokens and common stopwords
            stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would'}

            tokens = [token for token in tokens if len(token) > 2 and token not in stopwords]

            if tokens:  # Only add if we have meaningful tokens
                self.bm25_corpus.append(tokens)
                self.bm25_article_ids.append(article.get('id', article.get('article_id', '')))

        # Build BM25 index
        if self.bm25_corpus:
            self.bm25_index = BM25Okapi(self.bm25_corpus)
            self.bm25_last_updated = now
            logger.info(f"BM25 index built with {len(self.bm25_corpus)} documents")
        else:
            logger.warning("No valid documents for BM25 index")

    async def find_candidates(
        self,
        article: Dict[str, Any],
        article_embedding: np.ndarray,
        max_candidates: int = 150
    ) -> List[str]:
        """
        Find candidate stories for clustering comparison

        Strategy:
        1. Vector search (FAISS ANN) for semantic similarity
        2. Keyword search (BM25) for lexical precision
        3. Time window filtering (72 hours)
        4. Category filtering
        5. Merge and deduplicate

        Args:
            article: Article dictionary
            article_embedding: Pre-computed embedding vector
            max_candidates: Maximum candidates to return

        Returns:
            List of candidate article IDs
        """
        # Time window: -7 days to +6 hours from article publish time
        published_at = article.get('published_at') or article.get('publish_datetime')
        if isinstance(published_at, str):
            try:
                published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            except:
                published_at = datetime.now()  # Fallback

        time_min = published_at - timedelta(days=7)
        time_max = published_at + timedelta(hours=6)

        category = article.get('category', '')

        # 1. Vector search (semantic similarity)
        logger.debug("Performing vector search...")
        vector_candidates = self.vector_index.search(
            query_embedding=article_embedding,
            k=min(100, max_candidates // 2),  # Get half from vector search
            time_window=(time_min, time_max),
            category=category if category else None
        )
        vector_ids = set(cid for cid, _ in vector_candidates)

        # 2. BM25 search (keyword precision)
        logger.debug("Performing BM25 search...")
        keyword_ids = set()
        if self.bm25_index and self.bm25_article_ids:
            query_tokens = article.get('title', '').lower().split()
            # Filter query tokens same as corpus
            stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be'}
            query_tokens = [token for token in query_tokens if len(token) > 2 and token not in stopwords]

            if query_tokens:
                bm25_scores = self.bm25_index.get_scores(query_tokens)

                # Get top N by BM25 score
                top_n = min(50, max_candidates // 2)
                top_indices = np.argsort(bm25_scores)[::-1][:top_n]

                for idx in top_indices:
                    if idx < len(self.bm25_article_ids):
                        article_id = self.bm25_article_ids[idx]
                        # Additional time filtering for BM25 results
                        # (In production, you'd want to store timestamps with BM25)
                        keyword_ids.add(article_id)

        # 3. Merge candidates (union of vector and keyword results)
        all_candidates = vector_ids.union(keyword_ids)

        # 4. Cap at max_candidates
        candidate_list = list(all_candidates)[:max_candidates]

        logger.info(f"Found {len(candidate_list)} candidates "
                   f"({len(vector_ids)} vector, {len(keyword_ids)} keyword)")

        return candidate_list

    async def find_similar_stories(
        self,
        article: Dict[str, Any],
        article_embedding: np.ndarray,
        similarity_threshold: float = 0.7,
        max_results: int = 10
    ) -> List[Tuple[str, float, str]]:
        """
        Find most similar stories using hybrid search

        Args:
            article: Article dictionary
            article_embedding: Pre-computed embedding vector
            similarity_threshold: Minimum similarity score
            max_results: Maximum results to return

        Returns:
            List of (article_id, similarity_score, match_type) tuples
        """
        candidates = await self.find_candidates(article, article_embedding, max_candidates=100)

        if not candidates:
            return []

        # For each candidate, compute detailed similarity
        # In production, you'd want to pre-compute and cache embeddings
        results = []

        for candidate_id in candidates[:50]:  # Limit to avoid too many API calls
            try:
                # Get candidate embedding (in production, this would be cached)
                candidate_meta = None
                for fid, meta in self.vector_index.metadata.items():
                    if meta.get('article_id') == candidate_id:
                        candidate_meta = meta
                        break

                if candidate_meta and 'embedding' in candidate_meta:
                    candidate_embedding = np.array(candidate_meta['embedding'])

                    # Compute cosine similarity
                    similarity = np.dot(article_embedding, candidate_embedding) / (
                        np.linalg.norm(article_embedding) * np.linalg.norm(candidate_embedding)
                    )

                    if similarity >= similarity_threshold:
                        match_type = "semantic"  # Could be enhanced to detect keyword vs semantic
                        results.append((candidate_id, float(similarity), match_type))

            except Exception as e:
                logger.warning(f"Error computing similarity for {candidate_id}: {e}")
                continue

        # Sort by similarity (highest first) and limit results
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:max_results]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get candidate generator statistics

        Returns:
            Dictionary with statistics
        """
        return {
            'vector_index_size': self.vector_index.index.ntotal if self.vector_index else 0,
            'bm25_index_size': len(self.bm25_corpus) if self.bm25_corpus else 0,
            'bm25_last_updated': self.bm25_last_updated.isoformat() if self.bm25_last_updated else None,
            'has_embeddings_client': self.embeddings_client is not None
        }


# Global candidate generator instance
_candidate_generator_instance: Optional[CandidateGenerator] = None


async def get_candidate_generator() -> CandidateGenerator:
    """
    Get or create global candidate generator instance (singleton pattern)

    Returns:
        CandidateGenerator instance
    """
    global _candidate_generator_instance
    if _candidate_generator_instance is None:
        from .vector_index import get_vector_index
        from .embeddings_client import get_embeddings_client

        vector_index = get_vector_index()
        embeddings_client = await get_embeddings_client()

        _candidate_generator_instance = CandidateGenerator(
            vector_index=vector_index,
            embeddings_client=embeddings_client
        )

    return _candidate_generator_instance
