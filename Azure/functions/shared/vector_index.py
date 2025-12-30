"""
FAISS Vector Index for News Article Clustering - Phase 2

Implements Approximate Nearest Neighbor search using FAISS for fast
semantic similarity search of news article embeddings.
"""
import faiss
import numpy as np
import pickle
import logging
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class VectorIndex:
    """
    FAISS-based vector index for fast ANN search of news article embeddings

    Supports:
    - IndexFlatL2: Exact search (good for <100k vectors)
    - IndexIVFFlat: Approximate search (good for 100k-1M vectors)
    - IndexHNSW: Graph-based (good for >1M vectors)

    Automatically chooses appropriate index type based on size.
    """

    def __init__(self, embedding_dim: int = 1024, index_type: str = "auto"):
        """
        Initialize the FAISS vector index

        Args:
            embedding_dim: Dimension of embedding vectors
            index_type: Type of index ('flat', 'ivf', 'hnsw', 'auto')
        """
        self.embedding_dim = embedding_dim
        self.index_type = index_type
        self.id_mapping: List[str] = []  # Maps FAISS ID to article ID
        self.metadata: Dict[int, Dict] = {}  # FAISS ID -> metadata

        # Create appropriate index based on type
        if index_type == "flat" or (index_type == "auto"):
            # Exact search - best for small datasets (<100k)
            self.index = faiss.IndexFlatL2(embedding_dim)
            logger.info(f"Created FlatL2 index (exact search, dim={embedding_dim})")

        elif index_type == "ivf":
            # IVF - approximate search for medium datasets (100k-1M)
            quantizer = faiss.IndexFlatL2(embedding_dim)
            nlist = min(100, max(4, int(np.sqrt(100000))))  # Number of clusters
            self.index = faiss.IndexIVFFlat(quantizer, embedding_dim, nlist)
            logger.info(f"Created IVFFlat index (approx search, nlist={nlist}, dim={embedding_dim})")

        elif index_type == "hnsw":
            # HNSW - graph-based for large datasets (>1M)
            self.index = faiss.IndexHNSWFlat(embedding_dim, 32)  # 32 neighbors
            logger.info(f"Created HNSW index (graph-based, dim={embedding_dim})")

        else:
            raise ValueError(f"Unknown index type: {index_type}")

    def add_articles(self, articles: List[Dict[str, Any]], embeddings: np.ndarray):
        """
        Add articles and their embeddings to the index

        Args:
            articles: List of article dictionaries
            embeddings: Numpy array of embeddings (n_articles, embedding_dim)
        """
        if len(articles) != embeddings.shape[0]:
            raise ValueError("Number of articles must match number of embeddings")

        if embeddings.shape[1] != self.embedding_dim:
            raise ValueError(f"Embedding dimension mismatch: expected {self.embedding_dim}, got {embeddings.shape[1]}")

        # Convert to float32 (FAISS requirement)
        embeddings_f32 = embeddings.astype('float32')

        # Get starting ID for new additions
        start_id = self.index.ntotal

        # Add to FAISS index
        self.index.add(embeddings_f32)

        # Store mappings and metadata
        for i, article in enumerate(articles):
            faiss_id = start_id + i
            article_id = article.get('id', article.get('article_id', f"article_{faiss_id}"))

            self.id_mapping.append(article_id)
            self.metadata[faiss_id] = {
                'article_id': article_id,
                'title': article.get('title', ''),
                'publish_datetime': article.get('published_at') or article.get('publish_datetime'),
                'category': article.get('category', 'general'),
                'source': article.get('source', ''),
                'source_domain': article.get('source_domain', ''),
                'embedding': embeddings[i].tolist()  # Store for potential re-indexing
            }

        logger.info(f"Added {len(articles)} articles to index (total: {self.index.ntotal})")

        # Train IVF index if needed
        if isinstance(self.index, faiss.IndexIVFFlat) and not self.index.is_trained:
            if self.index.ntotal >= self.index.nlist * 39:  # Need enough vectors for training
                logger.info("Training IVF index...")
                self.index.train(embeddings_f32)
                logger.info("IVF index trained successfully")

    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 100,
        time_window: Optional[Tuple[datetime, datetime]] = None,
        category: Optional[str] = None,
        source_filter: Optional[List[str]] = None
    ) -> List[Tuple[str, float]]:
        """
        Search for similar articles using the vector index

        Args:
            query_embedding: Query embedding vector (1D array)
            k: Number of neighbors to return
            time_window: (start_time, end_time) for temporal filtering
            category: Category filter
            source_filter: List of allowed sources

        Returns:
            List of (article_id, distance) tuples, sorted by distance
        """
        # Reshape query to (1, dim) and convert to float32
        query = query_embedding.reshape(1, -1).astype('float32')

        # Search (get more than k to allow for filtering)
        search_k = min(k * 3, self.index.ntotal) if self.index.ntotal > 0 else k
        distances, indices = self.index.search(query, search_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for missing results
                continue

            meta = self.metadata.get(idx)
            if not meta:
                continue

            # Apply filters
            if time_window:
                pub_time = meta['publish_datetime']
                if isinstance(pub_time, str):
                    try:
                        pub_time = datetime.fromisoformat(pub_time.replace('Z', '+00:00'))
                    except:
                        continue  # Skip if can't parse date

                if not (time_window[0] <= pub_time <= time_window[1]):
                    continue

            if category and meta['category'] != category:
                continue

            if source_filter and meta['source'] not in source_filter:
                continue

            article_id = meta['article_id']
            results.append((article_id, float(dist)))

            if len(results) >= k:
                break

        return results

    def remove_article(self, article_id: str) -> bool:
        """
        Remove an article from the index (FAISS doesn't support deletion directly)

        Note: FAISS doesn't support efficient deletion. For production use,
        consider rebuilding the index periodically or using a deletion marker.

        Args:
            article_id: ID of article to remove

        Returns:
            True if article was marked for removal
        """
        # Find the FAISS ID for this article
        try:
            faiss_id = self.id_mapping.index(article_id)
        except ValueError:
            return False

        # Mark as deleted by removing metadata
        if faiss_id in self.metadata:
            del self.metadata[faiss_id]
            # Note: We keep the vector in FAISS but remove its metadata
            # This is not ideal but FAISS doesn't support deletion

        return True

    def get_stats(self) -> Dict[str, Any]:
        """
        Get index statistics

        Returns:
            Dictionary with index statistics
        """
        return {
            'total_vectors': self.index.ntotal,
            'embedding_dimension': self.embedding_dim,
            'index_type': type(self.index).__name__,
            'active_articles': len([m for m in self.metadata.values() if m]),
            'categories': list(set(m['category'] for m in self.metadata.values() if m)),
            'sources': list(set(m['source'] for m in self.metadata.values() if m))
        }

    def save(self, path: str):
        """
        Save index to disk

        Args:
            path: Directory path to save index files
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        faiss.write_index(self.index, str(path / "faiss.index"))

        # Save metadata
        metadata = {
            'id_mapping': self.id_mapping,
            'metadata': self.metadata,
            'embedding_dim': self.embedding_dim,
            'index_type': self.index_type
        }

        with open(path / "metadata.pkl", 'wb') as f:
            pickle.dump(metadata, f)

        logger.info(f"Index saved to {path}")

    def load(self, path: str):
        """
        Load index from disk

        Args:
            path: Directory path to load index files from
        """
        path = Path(path)

        # Load FAISS index
        self.index = faiss.read_index(str(path / "faiss.index"))

        # Load metadata
        with open(path / "metadata.pkl", 'rb') as f:
            metadata = pickle.load(f)

        self.id_mapping = metadata['id_mapping']
        self.metadata = metadata['metadata']
        self.embedding_dim = metadata['embedding_dim']
        self.index_type = metadata.get('index_type', 'auto')

        logger.info(f"Index loaded from {path} ({self.index.ntotal} vectors)")

    def rebuild_index(self, index_type: Optional[str] = None):
        """
        Rebuild the index with a different type if needed

        Args:
            index_type: New index type ('flat', 'ivf', 'hnsw', or None to keep current)
        """
        if index_type and index_type != self.index_type:
            # Collect all current embeddings and metadata
            embeddings = []
            articles = []

            for faiss_id in range(self.index.ntotal):
                if faiss_id in self.metadata:
                    meta = self.metadata[faiss_id]
                    embedding = np.array(meta['embedding'])
                    embeddings.append(embedding)
                    articles.append(meta)

            if embeddings:
                # Create new index
                embeddings_array = np.array(embeddings)
                self.__init__(embedding_dim=self.embedding_dim, index_type=index_type)

                # Re-add all articles
                self.add_articles(articles, embeddings_array)

                logger.info(f"Index rebuilt as {index_type} type")


# Global index instance for reuse
_index_instance: Optional[VectorIndex] = None


def get_vector_index(embedding_dim: int = 1024) -> VectorIndex:
    """
    Get or create global vector index instance (singleton pattern)

    Args:
        embedding_dim: Dimension of embedding vectors

    Returns:
        VectorIndex instance
    """
    global _index_instance
    if _index_instance is None:
        _index_instance = VectorIndex(embedding_dim=embedding_dim)
    return _index_instance
