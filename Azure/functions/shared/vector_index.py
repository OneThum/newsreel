"""FAISS vector index for fast semantic similarity search"""
import faiss
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import pickle
import os

logger = logging.getLogger(__name__)


class VectorIndex:
    """
    FAISS-based vector index for fast approximate nearest neighbor search

    Supports:
    - IndexFlatL2: Exact search (good for <100k vectors)
    - IndexIVFFlat: Approximate search (good for 100k-1M vectors)
    - IndexHNSW: Graph-based (good for >1M vectors)
    """

    def __init__(self, embedding_dim: int = 384, index_type: str = "flat"):
        """
        Initialize FAISS index

        Args:
            embedding_dim: Dimension of embedding vectors
            index_type: 'flat' (exact), 'ivf' (approximate), 'hnsw' (graph)
        """
        self.embedding_dim = embedding_dim
        self.index_type = index_type

        # Create appropriate FAISS index
        if index_type == "flat":
            # Exact search - best quality, slower for large datasets
            self.index = faiss.IndexFlatL2(embedding_dim)
        elif index_type == "ivf":
            # Approximate search - good balance of speed/quality
            quantizer = faiss.IndexFlatL2(embedding_dim)
            self.index = faiss.IndexIVFFlat(quantizer, embedding_dim, 100)  # 100 clusters
            # IVF needs training, but we'll handle this in add_articles
        elif index_type == "hnsw":
            # Graph-based - best for very large datasets
            self.index = faiss.IndexHNSWFlat(embedding_dim, 32)  # 32 neighbors
        else:
            raise ValueError(f"Unknown index type: {index_type}")

        # Map FAISS ID -> Article ID
        self.id_mapping: List[str] = []

        # Metadata for filtering (article_id -> metadata)
        self.metadata: Dict[str, Dict] = {}

        logger.info(f"✅ Initialized FAISS {index_type} index for {embedding_dim}D vectors")

    def add_articles(self, articles, embeddings: np.ndarray, train_if_needed: bool = True):
        """
        Add articles to the vector index

        Args:
            articles: List of RawArticle objects
            embeddings: numpy array of shape (len(articles), embedding_dim)
            train_if_needed: Whether to train IVF index if required
        """
        if len(articles) == 0:
            return

        if embeddings.shape[0] != len(articles):
            raise ValueError(f"Embeddings shape {embeddings.shape} doesn't match articles count {len(articles)}")

        # Convert to float32 (FAISS requirement)
        embeddings = embeddings.astype('float32')

        # Train IVF index if needed
        if self.index_type == "ivf" and not self.index.is_trained and train_if_needed:
            logger.info("Training IVF index...")
            self.index.train(embeddings)
            logger.info("✅ IVF index trained")

        # Add to index
        start_id = self.index.ntotal
        self.index.add(embeddings)

        # Store mappings and metadata
        for i, article in enumerate(articles):
            faiss_id = start_id + i
            article_id = getattr(article, 'id', f"unknown_{faiss_id}")

            self.id_mapping.append(article_id)
            self.metadata[article_id] = {
                'faiss_id': faiss_id,
                'article_id': article_id,
                'publish_datetime': getattr(article, 'published_at', datetime.now()),
                'category': getattr(article, 'category', 'general'),
                'source': getattr(article, 'source', 'unknown'),
                'title': getattr(article, 'title', '')[:100]  # Truncate for storage
            }

        logger.info(f"✅ Added {len(articles)} articles to index (total: {self.index.ntotal})")

    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 100,
        time_window: Optional[Tuple[datetime, datetime]] = None,
        category: Optional[str] = None,
        max_results: int = 1000
    ) -> List[Tuple[str, float]]:
        """
        Search for similar articles

        Args:
            query_embedding: Query vector (1D array)
            k: Number of neighbors to return
            time_window: (start_time, end_time) for temporal filtering
            category: Category filter (optional)
            max_results: Maximum results to consider for filtering

        Returns:
            List of (article_id, distance) tuples, sorted by distance
        """
        # Reshape query to (1, dim)
        query = query_embedding.reshape(1, -1).astype('float32')

        # Search (get more than k to allow for filtering)
        search_k = min(max_results, max(k * 3, 1000))  # Get more candidates for filtering
        distances, indices = self.index.search(query, search_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for missing results
                continue

            # Get article ID from mapping
            if idx >= len(self.id_mapping):
                continue

            article_id = self.id_mapping[idx]
            meta = self.metadata.get(article_id)

            if not meta:
                continue

            # Apply filters
            if time_window:
                pub_time = meta['publish_datetime']
                if not (time_window[0] <= pub_time <= time_window[1]):
                    continue

            if category and meta['category'] != category:
                continue

            results.append((article_id, float(dist)))

            if len(results) >= k:
                break

        # Sort by distance (ascending - lower is better)
        results.sort(key=lambda x: x[1])

        return results

    def save(self, path: str):
        """
        Save index to disk

        Args:
            path: Directory path to save index files
        """
        os.makedirs(path, exist_ok=True)

        # Save FAISS index
        index_path = os.path.join(path, "faiss.index")
        faiss.write_index(self.index, index_path)

        # Save metadata
        metadata_path = os.path.join(path, "metadata.pkl")
        with open(metadata_path, 'wb') as f:
            pickle.dump({
                'id_mapping': self.id_mapping,
                'metadata': self.metadata,
                'embedding_dim': self.embedding_dim,
                'index_type': self.index_type
            }, f)

        logger.info(f"✅ Saved index to {path}")

    def load(self, path: str):
        """
        Load index from disk

        Args:
            path: Directory path containing index files
        """
        # Load FAISS index
        index_path = os.path.join(path, "faiss.index")
        self.index = faiss.read_index(index_path)

        # Load metadata
        metadata_path = os.path.join(path, "metadata.pkl")
        with open(metadata_path, 'rb') as f:
            data = pickle.load(f)
            self.id_mapping = data['id_mapping']
            self.metadata = data['metadata']
            self.embedding_dim = data['embedding_dim']
            self.index_type = data['index_type']

        logger.info(f"✅ Loaded index from {path} ({self.index.ntotal} vectors)")

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        return {
            'total_vectors': self.index.ntotal,
            'embedding_dim': self.embedding_dim,
            'index_type': self.index_type,
            'is_trained': getattr(self.index, 'is_trained', True),
            'metadata_count': len(self.metadata)
        }

    def clear(self):
        """Clear all data from index"""
        # Recreate index
        if self.index_type == "flat":
            self.index = faiss.IndexFlatL2(self.embedding_dim)
        elif self.index_type == "ivf":
            quantizer = faiss.IndexFlatL2(self.embedding_dim)
            self.index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, 100)
        elif self.index_type == "hnsw":
            self.index = faiss.IndexHNSWFlat(self.embedding_dim, 32)

        self.id_mapping = []
        self.metadata = {}
        logger.info("✅ Cleared index")


# Global index instance (lazy-loaded)
_vector_index: Optional[VectorIndex] = None


def get_vector_index(embedding_dim: int = 384) -> VectorIndex:
    """Get or create global vector index instance"""
    global _vector_index
    if _vector_index is None:
        _vector_index = VectorIndex(embedding_dim=embedding_dim, index_type="flat")
    return _vector_index


def search_similar_articles(
    query_embedding: np.ndarray,
    k: int = 100,
    time_window_hours: Optional[int] = 72,
    category: Optional[str] = None
) -> List[Tuple[str, float]]:
    """
    Convenience function to search for similar articles

    Args:
        query_embedding: Query embedding vector
        k: Number of results to return
        time_window_hours: Hours back to search (None for no limit)
        category: Category filter

    Returns:
        List of (article_id, distance) tuples
    """
    try:
        index = get_vector_index()

        time_window = None
        if time_window_hours:
            now = datetime.now()
            time_window = (now - timedelta(hours=time_window_hours), now)

        return index.search(query_embedding, k=k, time_window=time_window, category=category)

    except Exception as e:
        logger.error(f"❌ Failed to search vector index: {e}")
        return []
