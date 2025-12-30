"""
Client for communicating with the Embedding Service (Azure Container Instance)

Phase 2: Semantic embeddings for improved clustering accuracy.
"""
import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
import numpy as np
from .config import config

logger = logging.getLogger(__name__)


class EmbeddingsClient:
    """
    HTTP client for the Newsreel Embedding Service

    Handles communication with the ACI-hosted SentenceTransformers service.
    Provides both single and batch embedding capabilities.
    """

    def __init__(self, service_url: Optional[str] = None, timeout_seconds: Optional[int] = None):
        """
        Initialize the embeddings client

        Args:
            service_url: URL of the embeddings service (default: from config)
            timeout_seconds: Request timeout (default: from config)
        """
        self.service_url = service_url or config.EMBEDDINGS_SERVICE_URL
        self.timeout_seconds = timeout_seconds or config.EMBEDDINGS_TIMEOUT_SECONDS

        if not self.service_url:
            raise ValueError("Embeddings service URL not configured. Set EMBEDDINGS_SERVICE_URL.")

        # Remove trailing slash
        self.service_url = self.service_url.rstrip('/')

        # Create aiohttp session
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def start(self):
        """Initialize the HTTP session"""
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
            self._session = aiohttp.ClientSession(timeout=timeout)

    async def close(self):
        """Close the HTTP session"""
        if self._session:
            await self._session.close()
            self._session = None

    async def health_check(self) -> Dict[str, Any]:
        """
        Check if the embeddings service is healthy

        Returns:
            Health status dictionary
        """
        await self.start()
        url = f"{self.service_url}/health"

        try:
            async with self._session.get(url) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def embed_article(
        self,
        title: str,
        description: str = "",
        entities: Optional[List[Dict[str, Any]]] = None
    ) -> np.ndarray:
        """
        Generate embedding for a single article

        Args:
            title: Article title
            description: Article description/content
            entities: Extracted named entities

        Returns:
            Embedding vector as numpy array
        """
        await self.start()
        url = f"{self.service_url}/embed"

        payload = {
            "title": title,
            "description": description,
            "entities": entities or []
        }

        try:
            async with self._session.post(url, json=payload) as response:
                response.raise_for_status()
                result = await response.json()

                # Convert to numpy array
                embedding = np.array(result["embedding"])
                processing_time = result.get("processing_time_ms", 0)

                logger.debug(f"Single embedding generated in {processing_time:.1f}ms")

                return embedding

        except Exception as e:
            logger.error(f"Single embedding failed: {e}")
            raise

    async def embed_articles_batch(
        self,
        articles: List[Dict[str, Any]],
        batch_size: Optional[int] = None
    ) -> np.ndarray:
        """
        Generate embeddings for multiple articles in batch

        Args:
            articles: List of article dictionaries with 'title', 'description', 'entities'
            batch_size: Processing batch size (default: from config)

        Returns:
            Array of embeddings as numpy array
        """
        await self.start()
        url = f"{self.service_url}/embed/batch"

        batch_size = batch_size or config.EMBEDDINGS_BATCH_SIZE

        # Prepare payload
        payload = {
            "articles": articles,
            "batch_size": batch_size
        }

        try:
            async with self._session.post(url, json=payload) as response:
                response.raise_for_status()
                result = await response.json()

                # Convert to numpy array
                embeddings = np.array(result["embeddings"])
                processing_time = result.get("processing_time_ms", 0)
                count = result.get("count", 0)

                logger.info(f"Batch embedding completed: {count} articles in {processing_time:.1f}ms")

                return embeddings

        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            raise

    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model

        Returns:
            Model information dictionary
        """
        await self.start()
        url = f"{self.service_url}/model-info"

        try:
            async with self._session.get(url) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Model info request failed: {e}")
            raise


# Global client instance for reuse
_client_instance: Optional[EmbeddingsClient] = None


async def get_embeddings_client() -> EmbeddingsClient:
    """
    Get or create global embeddings client instance (singleton pattern)

    Returns:
        EmbeddingsClient instance
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = EmbeddingsClient()
        await _client_instance.start()
    return _client_instance


async def embed_article_async(
    title: str,
    description: str = "",
    entities: Optional[List[Dict[str, Any]]] = None
) -> np.ndarray:
    """
    Convenience function to embed a single article asynchronously

    Args:
        title: Article title
        description: Article description
        entities: Extracted entities

    Returns:
        Embedding vector
    """
    client = await get_embeddings_client()
    return await client.embed_article(title, description, entities)


async def embed_articles_batch_async(
    articles: List[Dict[str, Any]],
    batch_size: Optional[int] = None
) -> np.ndarray:
    """
    Convenience function to batch embed articles asynchronously

    Args:
        articles: List of article dictionaries
        batch_size: Processing batch size

    Returns:
        Array of embeddings
    """
    client = await get_embeddings_client()
    return await client.embed_articles_batch(articles, batch_size)
