"""Semantic embeddings for news clustering using SentenceTransformers"""
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class ArticleEmbedder:
    """Generates semantic embeddings for news articles"""

    def __init__(self, model_name: str = "intfloat/multilingual-e5-large"):
        """
        Initialize the embedder with a SentenceTransformers model

        Args:
            model_name: HuggingFace model identifier
        """
        logger.info(f"Loading SentenceTransformers model: {model_name}")
        try:
            self.model = SentenceTransformer(model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            self.model_name = model_name
            logger.info(f"✅ Model loaded successfully. Embedding dimension: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"❌ Failed to load model {model_name}: {e}")
            raise

    def embed_article(self, article) -> np.ndarray:
        """
        Generate semantic embedding for a single article

        Args:
            article: RawArticle object with title, description, entities

        Returns:
            numpy array of shape (embedding_dim,)
        """
        # Combine title + lead for context (title weighted higher)
        text_parts = []

        # Title (most important)
        if hasattr(article, 'title') and article.title:
            text_parts.append(article.title)

        # Description/summary (secondary)
        if hasattr(article, 'description') and article.description:
            # Take first 300 chars to avoid overly long descriptions
            desc = article.description[:300].strip()
            if desc:
                text_parts.append(desc)

        # If no content, use title only
        if not text_parts:
            text_parts = ["No content available"]

        # Combine with separator
        text = ". ".join(text_parts)

        # Generate base embedding
        try:
            base_embedding = self.model.encode(
                text,
                normalize_embeddings=True  # L2 normalization for cosine similarity
            )

            # Optional: Entity-aware enhancement (Phase 3 feature)
            enhanced_embedding = self._enhance_with_entities(base_embedding, article)

            return enhanced_embedding

        except Exception as e:
            logger.error(f"❌ Failed to embed article {getattr(article, 'id', 'unknown')}: {e}")
            # Return zero vector as fallback
            return np.zeros(self.embedding_dim)

    def _enhance_with_entities(self, base_embedding: np.ndarray, article) -> np.ndarray:
        """
        Enhance embedding with entity information (Phase 3 feature)

        For now, just return the base embedding.
        Future: Weight by entity salience and type.
        """
        return base_embedding

    def batch_embed(self, articles: List, batch_size: int = 32) -> np.ndarray:
        """
        Batch embedding for efficiency

        Args:
            articles: List of RawArticle objects
            batch_size: Batch size for processing

        Returns:
            numpy array of shape (len(articles), embedding_dim)
        """
        if not articles:
            return np.array([])

        # Prepare texts
        texts = []
        for article in articles:
            text_parts = []

            if hasattr(article, 'title') and article.title:
                text_parts.append(article.title)

            if hasattr(article, 'description') and article.description:
                desc = article.description[:300].strip()
                if desc:
                    text_parts.append(desc)

            if not text_parts:
                text_parts = ["No content available"]

            text = ". ".join(text_parts)
            texts.append(text)

        try:
            logger.info(f"Generating embeddings for {len(texts)} articles in batches of {batch_size}")

            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=True,
                show_progress_bar=False
            )

            logger.info(f"✅ Generated {len(embeddings)} embeddings successfully")
            return embeddings

        except Exception as e:
            logger.error(f"❌ Failed batch embedding: {e}")
            # Return zero vectors as fallback
            return np.zeros((len(articles), self.embedding_dim))

    def get_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (-1 to 1, but normalized to 0-1)
        """
        try:
            similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            )
            # Normalize to 0-1 range (cosine similarity is -1 to 1)
            return (similarity + 1) / 2
        except Exception as e:
            logger.error(f"❌ Failed to calculate similarity: {e}")
            return 0.0


# Global embedder instance (lazy-loaded)
_embedder: Optional[ArticleEmbedder] = None


def get_embedder() -> ArticleEmbedder:
    """Get or create global embedder instance"""
    global _embedder
    if _embedder is None:
        # Use smaller model for Phase 2, upgrade to multilingual in Phase 3
        _embedder = ArticleEmbedder(model_name="all-MiniLM-L6-v2")  # 80MB, fast, English-only
    return _embedder


def embed_article(article) -> Optional[np.ndarray]:
    """
    Convenience function to embed a single article

    Args:
        article: RawArticle object

    Returns:
        Embedding vector or None if failed
    """
    try:
        embedder = get_embedder()
        return embedder.embed_article(article)
    except Exception as e:
        logger.error(f"❌ Failed to embed article: {e}")
        return None


def batch_embed_articles(articles: List) -> Optional[np.ndarray]:
    """
    Convenience function to batch embed articles

    Args:
        articles: List of RawArticle objects

    Returns:
        Embedding matrix or None if failed
    """
    try:
        embedder = get_embedder()
        return embedder.batch_embed(articles)
    except Exception as e:
        logger.error(f"❌ Failed to batch embed articles: {e}")
        return None
