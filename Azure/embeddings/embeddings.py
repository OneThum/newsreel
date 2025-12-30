"""
Semantic embeddings for news article clustering (Phase 2)

Uses SentenceTransformers multilingual-e5-large model for generating
semantic embeddings of news articles for improved clustering accuracy.
"""
import numpy as np
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)


class ArticleEmbedder:
    """
    Generates semantic embeddings for news articles using SentenceTransformers

    Model: intfloat/multilingual-e5-large (2GB, 1024D embeddings)
    Supports multiple languages and provides high-quality semantic similarity.
    """

    def __init__(self, model_name: str = "intfloat/multilingual-e5-large"):
        """
        Initialize the embedding model

        Args:
            model_name: HuggingFace model name (default: multilingual-e5-large)
        """
        logger.info(f"Loading SentenceTransformers model: {model_name}")
        try:
            self.model = SentenceTransformer(model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            self.model_name = model_name
            logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise

    def embed_article(self, title: str, description: str = "", entities: Optional[List[dict]] = None) -> np.ndarray:
        """
        Generate semantic embedding for a single article

        Args:
            title: Article title
            description: Article description/content (optional)
            entities: List of extracted entities (optional)

        Returns:
            numpy array of shape (embedding_dim,) - L2 normalized
        """
        # Combine title + description for context (title weighted higher)
        if description:
            # Limit description to avoid overly long inputs
            description_truncated = description[:300] if len(description) > 300 else description
            text = f"{title}. {description_truncated}"
        else:
            text = title

        # Generate base embedding
        base_embedding = self.model.encode(
            text,
            normalize_embeddings=True  # L2 normalization for cosine similarity
        )

        # Optional: Entity-aware enhancement (Phase 3 feature)
        if entities:
            entity_text = ' '.join([e.get('text', '') for e in entities[:5] if e.get('text')])
            if entity_text.strip():
                try:
                    entity_embedding = self.model.encode(
                        entity_text,
                        normalize_embeddings=True
                    )

                    # Weighted combination (70% content, 30% entities)
                    final_embedding = 0.7 * base_embedding + 0.3 * entity_embedding

                    # Re-normalize after combination
                    final_embedding = final_embedding / np.linalg.norm(final_embedding)

                    return final_embedding
                except Exception as e:
                    logger.warning(f"Entity embedding failed: {e}")
                    # Fall back to base embedding

        return base_embedding

    def batch_embed(self, articles: List[dict], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for multiple articles efficiently

        Args:
            articles: List of article dicts with 'title' and optional 'description'
            batch_size: Batch size for processing

        Returns:
            numpy array of shape (n_articles, embedding_dim)
        """
        if not articles:
            return np.array([])

        # Prepare texts for batch processing
        texts = []
        for article in articles:
            title = article.get('title', '')
            description = article.get('description', '')[:300] if article.get('description') else ''

            if description:
                text = f"{title}. {description}"
            else:
                text = title

            texts.append(text)

        logger.info(f"Batch embedding {len(texts)} articles with batch_size={batch_size}")

        # Generate embeddings in batches
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False
        )

        logger.info(f"Batch embedding completed. Shape: {embeddings.shape}")
        return embeddings
