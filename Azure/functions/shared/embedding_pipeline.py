"""
Embedding Generation Pipeline - Phase 2

Integrates semantic embeddings into the news article processing workflow.
Generates embeddings for new articles and maintains the FAISS vector index.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

from .embeddings_client import EmbeddingsClient, get_embeddings_client
from .vector_index import VectorIndex, get_vector_index
from .candidate_generation import CandidateGenerator, get_candidate_generator
from .config import config
from .cosmos_client import CosmosClient

logger = logging.getLogger(__name__)


class EmbeddingPipeline:
    """
    Pipeline for generating and managing semantic embeddings

    Workflow:
    1. Process new articles from change feed
    2. Generate embeddings via ACI service
    3. Add to FAISS vector index
    4. Store embedding metadata in Cosmos DB
    5. Maintain BM25 index for hybrid search
    """

    def __init__(
        self,
        embeddings_client: Optional[EmbeddingsClient] = None,
        vector_index: Optional[VectorIndex] = None,
        cosmos_client: Optional[CosmosClient] = None
    ):
        """
        Initialize the embedding pipeline

        Args:
            embeddings_client: Client for embedding service
            vector_index: FAISS vector index
            cosmos_client: Cosmos DB client
        """
        self.embeddings_client = embeddings_client
        self.vector_index = vector_index or get_vector_index(embedding_dim=config.EMBEDDINGS_DIMENSION)
        self.cosmos_client = cosmos_client
        self.candidate_generator: Optional[CandidateGenerator] = None

    async def initialize(self):
        """Initialize async components"""
        if not self.embeddings_client:
            self.embeddings_client = await get_embeddings_client()

        if not self.candidate_generator:
            self.candidate_generator = await get_candidate_generator()

    async def process_articles(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a batch of articles through the embedding pipeline.

        Args:
            articles: List of article dictionaries from Cosmos DB

        Returns:
            Processing statistics
        """
        await self.initialize()

        if not articles:
            return {"processed": 0, "errors": 0, "stats": {}}

        logger.info(f"Processing {len(articles)} articles through embedding pipeline")

        # Filter articles that need processing
        articles_to_process = []
        for article in articles:
            if self._needs_processing(article):
                articles_to_process.append(article)

        if not articles_to_process:
            logger.info("No articles need processing")
            return {"processed": 0, "errors": 0, "stats": {"skipped": len(articles)}}

        # Phase 3: Extract enhanced entities with Wikidata linking if enabled
        if config.WIKIDATA_LINKING_ENABLED:
            await self._extract_enhanced_entities(articles_to_process)

        # Phase 3: Extract event signatures if enabled
        if config.EVENT_SIGNATURES_ENABLED:
            await self._extract_event_signatures(articles_to_process)

        # Phase 3: Extract geographic features if enabled
        if config.GEOGRAPHIC_FEATURES_ENABLED:
            await self._extract_geographic_features(articles_to_process)

        # Generate embeddings
        embeddings = await self._generate_embeddings_batch(articles_to_process)

        if embeddings is None or len(embeddings) == 0:
            logger.error("Failed to generate embeddings for batch")
            return {"processed": 0, "errors": len(articles_to_process), "stats": {}}

        # Add to vector index
        await self._add_to_vector_index(articles_to_process, embeddings)

        # Update BM25 index
        await self._update_bm25_index(articles_to_process)

        # Store embedding metadata in Cosmos DB
        await self._store_embedding_metadata(articles_to_process, embeddings)

        logger.info(f"Successfully processed {len(articles_to_process)} articles")

        return {
            "processed": len(articles_to_process),
            "errors": 0,
            "stats": {
                "embeddings_generated": len(embeddings),
                "vector_index_size": self.vector_index.index.ntotal,
                "bm25_index_size": len(self.candidate_generator.bm25_corpus) if self.candidate_generator.bm25_corpus else 0
            }
        }

    def _needs_processing(self, article: Dict[str, Any]) -> bool:
        """
        Check if article needs processing (embedding + event signatures)

        Args:
            article: Article dictionary

        Returns:
            True if processing is needed
        """
        # Check if article is processed
        if not article.get('processed', False):
            return False

        # Check if embedding is needed
        needs_embedding = not (article.get('embedding') or article.get('embedding_generated'))

        # Phase 3: Check if enhanced entities with Wikidata linking are needed
        needs_entities = (config.WIKIDATA_LINKING_ENABLED and
                          not article.get('wikidata_linked', False))

        # Phase 3: Check if event signature is needed
        needs_signature = (config.EVENT_SIGNATURES_ENABLED and
                          not article.get('event_signature') and
                          article.get('confidence', 0) >= config.EVENT_SIGNATURE_CONFIDENCE_THRESHOLD)

        # Phase 3: Check if geographic features are needed
        needs_geographic = (config.GEOGRAPHIC_FEATURES_ENABLED and
                           not article.get('geographic_features'))

        # Only process articles from recent time (avoid backfill for now)
        published_at = article.get('published_at')
        if published_at:
            try:
                if isinstance(published_at, str):
                    published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))

                # Only process articles from last 7 days
                age_days = (datetime.now() - published_at).days
                if age_days > 7:
                    return False
            except:
                # If we can't parse date, assume it needs processing
                pass

        return needs_embedding or needs_entities or needs_signature or needs_geographic

    async def _extract_enhanced_entities(self, articles: List[Dict[str, Any]]):
        """
        Extract and enhance entities with Wikidata linking (Phase 3).
        """
        from .utils import extract_simple_entities_with_wikidata

        for article in articles:
            if not article.get('entities') or not article.get('wikidata_linked', False):
                try:
                    # Phase 3: Extract entities with Wikidata linking
                    text = f"{article.get('title', '')}. {article.get('description', '')}"
                    entities = await extract_simple_entities_with_wikidata(text)

                    # Convert Entity objects to dictionaries for storage
                    entity_dicts = []
                    for entity in entities:
                        entity_dict = {
                            'text': entity.text,
                            'type': entity.type,
                            'linked_name': entity.linked_name
                        }
                        if entity.wikidata:
                            entity_dict['wikidata'] = entity.wikidata
                        entity_dicts.append(entity_dict)

                    article['entities'] = entity_dicts
                    article['wikidata_linked'] = True

                    logger.debug(f"Enhanced entities for article {article.get('id')}: {len(entity_dicts)} entities")

                except Exception as e:
                    logger.warning(f"Failed to extract enhanced entities for article {article.get('id')}: {e}")

    async def _extract_event_signatures(self, articles: List[Dict[str, Any]]):
        """
        Extract event signatures for articles that need them

        Args:
            articles: List of article dictionaries
        """
        from .event_signatures import extract_event_signature

        for article in articles:
            if not article.get('event_signature'):
                try:
                    signature = extract_event_signature(
                        title=article.get('title', ''),
                        description=article.get('description', ''),
                        entities=article.get('entities', [])
                    )

                    if signature.get('confidence', 0) >= config.EVENT_SIGNATURE_CONFIDENCE_THRESHOLD:
                        article['event_signature'] = signature
                        logger.debug(f"Extracted event signature for article {article.get('id')}: {signature.get('signature_hash', 'unknown')}")
                    else:
                        logger.debug(f"Event signature confidence too low for article {article.get('id')}: {signature.get('confidence', 0)}")

                except Exception as e:
                    logger.warning(f"Failed to extract event signature for article {article.get('id')}: {e}")

    async def _extract_geographic_features(self, articles: List[Dict[str, Any]]):
        """
        Extract geographic features for articles that need them

        Args:
            articles: List of article dictionaries
        """
        from .geographic_features import extract_geographic_features

        for article in articles:
            if not article.get('geographic_features'):
                try:
                    geo_features = extract_geographic_features(
                        title=article.get('title', ''),
                        description=article.get('description', ''),
                        entities=article.get('entities', [])
                    )

                    if geo_features.get('locations'):
                        article['geographic_features'] = geo_features
                        logger.debug(f"Extracted geographic features for article {article.get('id')}: {len(geo_features.get('locations', []))} locations")
                    else:
                        logger.debug(f"No geographic features found for article {article.get('id')}")

                except Exception as e:
                    logger.warning(f"Failed to extract geographic features for article {article.get('id')}: {e}")

    async def _generate_embeddings_batch(self, articles: List[Dict[str, Any]]) -> Optional[np.ndarray]:
        """
        Generate embeddings for a batch of articles

        Args:
            articles: List of article dictionaries

        Returns:
            Numpy array of embeddings or None if failed
        """
        try:
            # Prepare articles for embedding API
            embedding_requests = []
            for article in articles:
                request = {
                    "title": article.get('title', ''),
                    "description": article.get('description', ''),
                    "entities": article.get('entities', [])
                }
                embedding_requests.append(request)

            # Batch embed
            embeddings = await self.embeddings_client.embed_articles_batch(
                articles=embedding_requests,
                batch_size=config.EMBEDDINGS_BATCH_SIZE
            )

            logger.info(f"Generated embeddings for {len(articles)} articles")
            return embeddings

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return None

    async def _add_to_vector_index(self, articles: List[Dict[str, Any]], embeddings: np.ndarray):
        """
        Add articles and embeddings to FAISS vector index

        Args:
            articles: List of article dictionaries
            embeddings: Corresponding embeddings
        """
        try:
            self.vector_index.add_articles(articles, embeddings)
            logger.info(f"Added {len(articles)} articles to vector index")

            # Check if index needs rebuilding (scale up from IVF to HNSW)
            if (config.VECTOR_INDEX_TYPE == "auto" and
                self.vector_index.index.ntotal > config.VECTOR_INDEX_REBUILD_THRESHOLD):

                logger.info("Index size threshold reached, considering rebuild...")
                # For now, just log - in production you'd rebuild with HNSW

        except Exception as e:
            logger.error(f"Failed to add to vector index: {e}")

    async def _update_bm25_index(self, articles: List[Dict[str, Any]]):
        """
        Update BM25 index with new articles

        Args:
            articles: List of article dictionaries
        """
        try:
            await self.candidate_generator.build_bm25_index(articles, force_rebuild=False)
            logger.debug(f"Updated BM25 index with {len(articles)} articles")

        except Exception as e:
            logger.error(f"Failed to update BM25 index: {e}")

    async def _store_embedding_metadata(self, articles: List[Dict[str, Any]], embeddings: np.ndarray):
        """
        Store embedding and event signature metadata in Cosmos DB

        Args:
            articles: List of article dictionaries
            embeddings: Corresponding embeddings
        """
        try:
            for i, article in enumerate(articles):
                article_id = article.get('id')

                # Prepare update data
                update_data = {
                    'embedding_generated': True,
                    'embedding_timestamp': datetime.now().isoformat(),
                    'embedding_model': config.EMBEDDINGS_MODEL,
                    'embedding_dimension': config.EMBEDDINGS_DIMENSION
                }

                # Store embedding vector (optional - can be large)
                if config.get('STORE_EMBEDDINGS_IN_DB', False):
                    update_data['embedding'] = embeddings[i].tolist()

                # Phase 3: Store enhanced entities with Wikidata linking if available
                if article.get('entities'):
                    update_data['entities'] = article['entities']
                    update_data['wikidata_linked'] = article.get('wikidata_linked', False)

                # Phase 3: Store event signature if available
                if article.get('event_signature'):
                    update_data['event_signature'] = article['event_signature']
                    update_data['event_signature_extracted'] = True

                # Phase 3: Store geographic features if available
                if article.get('geographic_features'):
                    update_data['geographic_features'] = article['geographic_features']
                    update_data['geographic_features_extracted'] = True

                # Update article in Cosmos DB
                await self.cosmos_client.update_raw_article_embedding(article_id, update_data)

            logger.debug(f"Stored metadata for {len(articles)} articles")

        except Exception as e:
            logger.error(f"Failed to store metadata: {e}")

    async def search_similar(self, query_article: Dict[str, Any], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Find similar articles using the embedding pipeline

        Args:
            query_article: Article to find similar articles for
            top_k: Number of similar articles to return

        Returns:
            List of similar articles with similarity scores
        """
        await self.initialize()

        try:
            # Generate embedding for query article
            embedding = await self.embeddings_client.embed_article(
                title=query_article.get('title', ''),
                description=query_article.get('description', ''),
                entities=query_article.get('entities', [])
            )

            # Find similar articles
            similar_results = await self.candidate_generator.find_similar_stories(
                article=query_article,
                article_embedding=embedding,
                max_results=top_k
            )

            # Enrich results with article data
            enriched_results = []
            for article_id, similarity, match_type in similar_results:
                try:
                    # Get article data from Cosmos DB
                    article_data = await self.cosmos_client.get_raw_article(article_id)
                    if article_data:
                        result = {
                            'article_id': article_id,
                            'similarity': similarity,
                            'match_type': match_type,
                            'article': article_data
                        }
                        enriched_results.append(result)
                except Exception as e:
                    logger.warning(f"Failed to get article {article_id}: {e}")

            return enriched_results

        except Exception as e:
            logger.error(f"Failed to search similar articles: {e}")
            return []

    async def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive pipeline statistics

        Returns:
            Dictionary with pipeline statistics
        """
        await self.initialize()

        stats = {
            'embeddings_service': {
                'configured': bool(config.EMBEDDINGS_SERVICE_URL),
                'healthy': False
            },
            'vector_index': self.vector_index.get_stats() if self.vector_index else {},
            'candidate_generator': self.candidate_generator.get_stats() if self.candidate_generator else {}
        }

        # Check embeddings service health
        try:
            health = await self.embeddings_client.health_check()
            stats['embeddings_service']['healthy'] = health.get('status') == 'healthy'
            stats['embeddings_service']['model_loaded'] = health.get('model_loaded', False)
        except:
            stats['embeddings_service']['healthy'] = False

        return stats


# Global pipeline instance
_pipeline_instance: Optional[EmbeddingPipeline] = None


async def get_embedding_pipeline() -> EmbeddingPipeline:
    """
    Get or create global embedding pipeline instance (singleton pattern)

    Returns:
        EmbeddingPipeline instance
    """
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = EmbeddingPipeline()
        await _pipeline_instance.initialize()
    return _pipeline_instance


async def process_articles_for_embedding(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convenience function to process articles through embedding pipeline

    Args:
        articles: List of article dictionaries

    Returns:
        Processing results
    """
    pipeline = await get_embedding_pipeline()
    return await pipeline.process_articles(articles)
