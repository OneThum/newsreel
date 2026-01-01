"""
Semantic Clustering for News Articles - 2025 Best Practices

Uses OpenAI's text-embedding-3-small for high-quality semantic embeddings.
Replaces old keyword-based fingerprinting with true semantic understanding.

Cost: ~$0.02 per 1M tokens (~$0.00002 per article)
Quality: State-of-the-art semantic similarity
"""
import os
import logging
import numpy as np
from typing import List, Optional, Tuple, Dict, Any
from openai import OpenAI
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# OpenAI client - initialized lazily
_openai_client: Optional[OpenAI] = None

# Embedding model configuration
EMBEDDING_MODEL = "text-embedding-3-small"  # 1536 dimensions, best price/performance
EMBEDDING_DIMENSIONS = 1536

# Clustering thresholds (cosine similarity)
# Lowered from 0.82 to 0.75 to improve story matching
# This allows related stories from different sources to be grouped together
CLUSTER_MATCH_THRESHOLD = 0.75  # Stories above this are same event
CLUSTER_MAYBE_THRESHOLD = 0.68  # Stories between maybe and match need entity validation


def get_openai_client() -> Optional[OpenAI]:
    """Get or create OpenAI client. Returns None if API key not configured."""
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("⚠️ OPENAI_API_KEY not configured - semantic clustering disabled")
            return None
        _openai_client = OpenAI(api_key=api_key)
        logger.info("✅ OpenAI client initialized for semantic clustering")
    return _openai_client


def is_semantic_clustering_enabled() -> bool:
    """Check if semantic clustering is available (OpenAI API key configured)"""
    return bool(os.getenv("OPENAI_API_KEY"))


def generate_embedding(text: str, max_tokens: int = 8000) -> Optional[List[float]]:
    """
    Generate semantic embedding for text using OpenAI's embedding API.
    
    Args:
        text: Text to embed (title + description)
        max_tokens: Maximum tokens to process (truncates if longer)
    
    Returns:
        List of floats (1536 dimensions) or None if failed or API not configured
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for embedding")
        return None
    
    try:
        client = get_openai_client()
        if client is None:
            # OpenAI not configured - return None (clustering will create new stories)
            return None
        
        # Truncate if too long (rough estimate: 4 chars per token)
        if len(text) > max_tokens * 4:
            text = text[:max_tokens * 4]
            logger.debug(f"Truncated text to ~{max_tokens} tokens")
        
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
            dimensions=EMBEDDING_DIMENSIONS
        )
        
        embedding = response.data[0].embedding
        logger.debug(f"Generated embedding: {len(embedding)} dimensions")
        return embedding
        
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return None


def generate_article_embedding(title: str, description: str = "") -> Optional[List[float]]:
    """
    Generate embedding for a news article.
    
    Combines title and description for richer semantic representation.
    Title is weighted more heavily by appearing first.
    
    Args:
        title: Article title (required)
        description: Article description/summary (optional)
    
    Returns:
        Embedding vector or None if failed
    """
    # Combine title and description (title first for emphasis)
    if description:
        # Limit description to first 500 chars to focus on key content
        desc_truncated = description[:500] if len(description) > 500 else description
        text = f"{title}. {desc_truncated}"
    else:
        text = title
    
    return generate_embedding(text)


def cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Calculate cosine similarity between two embeddings.
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
    
    Returns:
        Similarity score between 0 and 1
    """
    if not embedding1 or not embedding2:
        return 0.0
    
    # Convert to numpy for efficient computation
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)
    
    # Cosine similarity
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(dot_product / (norm1 * norm2))


def find_matching_story(
    article_embedding: List[float],
    article_title: str,
    candidate_stories: List[Dict[str, Any]],
    threshold: float = CLUSTER_MATCH_THRESHOLD
) -> Tuple[Optional[Dict[str, Any]], float]:
    """
    Find the best matching story for an article using semantic similarity.
    
    Args:
        article_embedding: Embedding of the new article
        article_title: Title of the new article (for logging)
        candidate_stories: List of story dicts with 'embedding' field
        threshold: Minimum similarity to consider a match
    
    Returns:
        Tuple of (best_matching_story, similarity_score) or (None, 0.0)
    """
    if not article_embedding:
        logger.warning("No embedding provided for matching")
        return None, 0.0
    
    best_match = None
    best_similarity = 0.0
    similarities = []
    
    for story in candidate_stories:
        story_embedding = story.get('embedding')
        if not story_embedding:
            continue
        
        similarity = cosine_similarity(article_embedding, story_embedding)
        similarities.append({
            'story_id': story.get('id', 'unknown'),
            'story_title': story.get('title', '')[:60],
            'similarity': similarity
        })
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = story
    
    # Log similarity analysis
    if similarities:
        above_threshold = [s for s in similarities if s['similarity'] >= threshold]
        above_maybe = [s for s in similarities if s['similarity'] >= CLUSTER_MAYBE_THRESHOLD]
        
        logger.info(f"🧠 SEMANTIC CLUSTERING: '{article_title[:60]}...'")
        logger.info(f"   Compared against {len(similarities)} stories")
        logger.info(f"   Best match: {best_similarity:.3f} - '{best_match.get('title', '')[:50]}...' " if best_match else "   No matches found")
        logger.info(f"   Above threshold ({threshold}): {len(above_threshold)}")
        logger.info(f"   Above maybe ({CLUSTER_MAYBE_THRESHOLD}): {len(above_maybe)}")
    
    if best_similarity >= threshold:
        logger.info(f"✅ SEMANTIC MATCH: {best_similarity:.3f} >= {threshold}")
        return best_match, best_similarity
    elif best_similarity >= CLUSTER_MAYBE_THRESHOLD:
        # For "maybe" matches, do additional entity validation
        logger.info(f"🤔 MAYBE MATCH: {best_similarity:.3f} - checking entities...")
        if _validate_entity_overlap(article_title, best_match.get('title', '')):
            logger.info(f"✅ ENTITY VALIDATION PASSED - accepting match")
            return best_match, best_similarity
        else:
            logger.info(f"❌ ENTITY VALIDATION FAILED - rejecting match")
            return None, best_similarity
    else:
        logger.info(f"❌ NO MATCH: best similarity {best_similarity:.3f} < {CLUSTER_MAYBE_THRESHOLD}")
        return None, best_similarity


def _validate_entity_overlap(title1: str, title2: str) -> bool:
    """
    Validate that two titles share significant named entities.
    Used as secondary validation for borderline matches.
    
    Args:
        title1: First title
        title2: Second title
    
    Returns:
        True if titles share at least 2 significant entities
    """
    # Extract likely entities (capitalized words > 3 chars)
    entities1 = set(
        word.lower() for word in title1.split() 
        if len(word) > 3 and word[0].isupper()
    )
    entities2 = set(
        word.lower() for word in title2.split() 
        if len(word) > 3 and word[0].isupper()
    )
    
    overlap = entities1.intersection(entities2)
    return len(overlap) >= 2


def compute_story_embedding(source_articles: List[Dict[str, Any]]) -> Optional[List[float]]:
    """
    Compute a representative embedding for a story cluster.
    
    Uses the average of all article embeddings in the cluster.
    This centroid represents the "semantic center" of the story.
    
    Args:
        source_articles: List of article dicts with embeddings
    
    Returns:
        Averaged embedding vector or None if no embeddings available
    """
    embeddings = []
    
    for article in source_articles:
        embedding = article.get('embedding')
        if embedding:
            embeddings.append(np.array(embedding))
    
    if not embeddings:
        return None
    
    # Compute centroid (average of all embeddings)
    centroid = np.mean(embeddings, axis=0)
    
    # Normalize to unit length for consistent cosine similarity
    norm = np.linalg.norm(centroid)
    if norm > 0:
        centroid = centroid / norm
    
    return centroid.tolist()


def batch_generate_embeddings(texts: List[str]) -> List[Optional[List[float]]]:
    """
    Generate embeddings for multiple texts in a single API call.
    More efficient than individual calls for batch processing.
    
    Args:
        texts: List of texts to embed
    
    Returns:
        List of embeddings (None for failed items)
    """
    if not texts:
        return []
    
    try:
        client = get_openai_client()
        
        # Filter and truncate texts
        processed_texts = []
        for text in texts:
            if text and text.strip():
                # Truncate if too long
                if len(text) > 32000:  # ~8000 tokens
                    text = text[:32000]
                processed_texts.append(text)
            else:
                processed_texts.append("empty")  # Placeholder for empty texts
        
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=processed_texts,
            dimensions=EMBEDDING_DIMENSIONS
        )
        
        # Extract embeddings in order
        embeddings = [None] * len(texts)
        for item in response.data:
            embeddings[item.index] = item.embedding
        
        logger.info(f"Batch generated {len([e for e in embeddings if e])} embeddings")
        return embeddings
        
    except Exception as e:
        logger.error(f"Batch embedding failed: {e}")
        return [None] * len(texts)


# Legacy compatibility - generate a simple fingerprint for stories without embeddings
def generate_legacy_fingerprint(title: str) -> str:
    """
    Generate a simple hash fingerprint for backward compatibility.
    Only used for stories created before semantic clustering was enabled.
    """
    import hashlib
    import re
    
    # Normalize
    normalized = title.lower().strip()
    normalized = re.sub(r'[^\w\s]', '', normalized)
    
    # Hash
    return hashlib.md5(normalized.encode()).hexdigest()[:12]

