"""
Advanced Clustering Algorithms - Phase 3

Multi-factor scoring system for semantic clustering with geographic and event features.
"""
import logging
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import numpy as np

from .config import config
from .geographic_features import calculate_geographic_similarity
from .event_signatures import compare_event_signatures

logger = logging.getLogger(__name__)


def score_candidate(
    article: Dict[str, Any],
    cluster: Dict[str, Any],
    article_embedding: np.ndarray
) -> Tuple[float, Dict[str, float]]:
    """
    Compute multi-factor similarity score for clustering decision

    Factors (Phase 3 enhanced):
    1. Semantic similarity (cosine of embeddings) - 45%
    2. Entity overlap (Jaccard) - 15%
    3. Title similarity (BM25/fuzzy) - 10%
    4. Time decay (Gaussian) - 10%
    5. Geographic proximity - 10%
    6. Event signature similarity - 10%

    Args:
        article: Article dictionary
        cluster: Cluster dictionary
        article_embedding: Article embedding vector

    Returns:
        (final_score, component_scores)
    """
    components = {}

    # 1. Semantic similarity (45%) - reduced from 55% to make room for new factors
    cluster_centroid = np.array(cluster.get('embedding', [0] * config.EMBEDDINGS_DIMENSION))
    if len(cluster_centroid) == len(article_embedding):
        cosine_sim = cosine_similarity(article_embedding, cluster_centroid)
    else:
        cosine_sim = 0.0
    components['cosine'] = cosine_sim

    # 2. Entity overlap (15%) - reduced from 20%
    article_entities = set(e.get('text', '').lower() for e in article.get('entities', []))
    cluster_entities = set(cluster.get('entity_histogram', {}).keys())

    if article_entities and cluster_entities:
        intersection = article_entities.intersection(cluster_entities)
        union = article_entities.union(cluster_entities)
        entity_jaccard = len(intersection) / len(union)
    else:
        entity_jaccard = 0.0

    components['entities'] = entity_jaccard

    # 3. Title similarity (10%) - kept same
    article_words = set(article.get('title', '').lower().split())
    cluster_words = set(cluster.get('title', '').lower().split())

    if article_words and cluster_words:
        word_overlap = len(article_words.intersection(cluster_words))
        title_sim = word_overlap / len(article_words.union(cluster_words))
    else:
        title_sim = 0.0

    components['title'] = title_sim

    # 4. Time decay (10%) - kept same
    time_decay = calculate_time_decay(article, cluster)
    components['time'] = time_decay

    # 5. Geographic proximity (10%) - NEW Phase 3 feature
    geo_similarity = calculate_geographic_similarity_score(article, cluster)
    components['geographic'] = geo_similarity

    # 6. Event signature similarity (10%) - NEW Phase 3 feature
    event_similarity = calculate_event_signature_similarity(article, cluster)
    components['event_signature'] = event_similarity

    # Weighted combination
    final_score = (
        0.45 * cosine_sim +
        0.15 * entity_jaccard +
        0.10 * title_sim +
        0.10 * time_decay +
        0.10 * geo_similarity +
        0.10 * event_similarity
    )

    return final_score, components


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors"""
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return np.dot(v1, v2) / (norm1 * norm2)


def calculate_time_decay(article: Dict[str, Any], cluster: Dict[str, Any]) -> float:
    """
    Calculate time decay factor using Gaussian decay

    Closer in time = higher similarity
    """
    # Get timestamps
    article_time = article.get('published_at')
    cluster_time = cluster.get('last_updated', cluster.get('first_seen'))

    if not article_time or not cluster_time:
        return 0.5  # Neutral score if timestamps missing

    # Parse timestamps
    try:
        if isinstance(article_time, str):
            article_time = datetime.fromisoformat(article_time.replace('Z', '+00:00'))
        if isinstance(cluster_time, str):
            cluster_time = datetime.fromisoformat(cluster_time.replace('Z', '+00:00'))
    except:
        return 0.5

    # Calculate time difference in hours
    time_diff_hours = abs((article_time - cluster_time).total_seconds()) / 3600

    # Gaussian decay with adaptive sigma
    if cluster.get('breaking_news', False):
        sigma = 24  # 24-hour window for breaking news
    else:
        sigma = 72  # 72-hour window for regular news

    time_decay = np.exp(-(time_diff_hours / sigma) ** 2)
    return time_decay


def calculate_geographic_similarity_score(article: Dict[str, Any], cluster: Dict[str, Any]) -> float:
    """
    Calculate geographic similarity between article and cluster

    Uses geographic features if available, otherwise defaults to moderate similarity
    """
    if not config.GEOGRAPHIC_FEATURES_ENABLED:
        return 0.5  # Neutral score if feature disabled

    article_geo = article.get('geographic_features')
    cluster_geo = cluster.get('geographic_features')

    if not article_geo or not cluster_geo:
        return 0.5  # Neutral score if features missing

    # Use the geographic similarity calculator
    similarity = calculate_geographic_similarity(
        article_geo,
        cluster_geo,
        max_distance_km=config.GEOGRAPHIC_MAX_DISTANCE_KM
    )

    return similarity


def calculate_event_signature_similarity(article: Dict[str, Any], cluster: Dict[str, Any]) -> float:
    """
    Calculate event signature similarity between article and cluster

    Uses event signatures if available, otherwise defaults to moderate similarity
    """
    if not config.EVENT_SIGNATURES_ENABLED:
        return 0.5  # Neutral score if feature disabled

    article_sig = article.get('event_signature')
    cluster_sig = cluster.get('event_signature')

    if not article_sig or not cluster_sig:
        return 0.5  # Neutral score if signatures missing

    # Use the event signature similarity calculator
    similarity = compare_event_signatures(article_sig, cluster_sig)

    return similarity


def assign_article_to_cluster(
    article: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    article_embedding: np.ndarray
) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Assign article to best matching cluster or create new cluster

    Enhanced with Phase 3 geographic and event signature features

    Args:
        article: Article dictionary
        candidates: List of candidate cluster dictionaries
        article_embedding: Article embedding vector

    Returns:
        (cluster_id, assignment_metadata)
    """
    if not candidates:
        return None, {'decision': 'new_cluster', 'reason': 'no_candidates'}

    # Score all candidates
    scored_candidates = []
    for cluster in candidates:
        score, components = score_candidate(article, cluster, article_embedding)
        scored_candidates.append({
            'cluster': cluster,
            'score': score,
            'components': components
        })

    # Sort by score
    scored_candidates.sort(key=lambda x: x['score'], reverse=True)
    best_match = scored_candidates[0]

    # Adaptive threshold based on article age
    article_age_hours = 0
    published_at = article.get('published_at')
    if published_at:
        try:
            if isinstance(published_at, str):
                published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            article_age_hours = (datetime.now() - published_at).total_seconds() / 3600
        except:
            article_age_hours = 24  # Default to 1 day

    if article_age_hours < 12:
        threshold = 0.65  # Breaking news - higher threshold (stricter)
    elif article_age_hours < 72:
        threshold = 0.60  # Recent news
    else:
        threshold = 0.55  # Older stories - lower threshold (more lenient)

    # Statistical guardrail: Require best match to be significantly better than mean
    if len(scored_candidates) > 1:
        scores = [c['score'] for c in scored_candidates]
        mean_score = np.mean(scores)
        std_score = np.std(scores)

        # Require best match to be at least 1.5 std devs above mean (less strict than 2.0)
        statistical_threshold = mean_score + 1.5 * std_score

        if best_match['score'] >= statistical_threshold:
            # Best match is statistically significant
            threshold = min(threshold, best_match['score'] - 0.01)

    # Make assignment decision
    if best_match['score'] >= threshold:
        return best_match['cluster']['id'], {
            'decision': 'assigned',
            'score': best_match['score'],
            'threshold': threshold,
            'components': best_match['components'],
            'cluster_title': best_match['cluster'].get('title', ''),
            'reason': 'score_above_threshold'
        }
    else:
        return None, {
            'decision': 'new_cluster',
            'reason': 'below_threshold',
            'best_score': best_match['score'],
            'threshold': threshold,
            'components': best_match['components'],
            'best_cluster_title': best_match['cluster'].get('title', ''),
            'gap_to_threshold': threshold - best_match['score']
        }


def should_merge_clusters(cluster1: Dict[str, Any], cluster2: Dict[str, Any]) -> bool:
    """
    Determine if two clusters should be merged

    Phase 3: Enhanced with geographic and event signature similarity
    """
    # Basic checks
    if cluster1.get('category') != cluster2.get('category'):
        return False

    # Time overlap check
    time_overlap = calculate_time_overlap(cluster1, cluster2)
    if time_overlap < 0.3:  # Require 30% time overlap
        return False

    # Embedding similarity check
    emb1 = np.array(cluster1.get('embedding', []))
    emb2 = np.array(cluster2.get('embedding', []))
    if len(emb1) == len(emb2) and len(emb1) > 0:
        emb_similarity = cosine_similarity(emb1, emb2)
        if emb_similarity < 0.7:  # Require 70% embedding similarity
            return False
    else:
        return False

    # Geographic similarity check (Phase 3)
    if config.GEOGRAPHIC_FEATURES_ENABLED:
        geo_sim = calculate_geographic_similarity_score(cluster1, cluster2)
        if geo_sim < 0.6:  # Require 60% geographic similarity
            return False

    # Event signature similarity check (Phase 3)
    if config.EVENT_SIGNATURES_ENABLED:
        event_sim = calculate_event_signature_similarity(cluster1, cluster2)
        if event_sim < 0.6:  # Require 60% event signature similarity
            return False

    return True


def calculate_time_overlap(cluster1: Dict[str, Any], cluster2: Dict[str, Any]) -> float:
    """
    Calculate temporal overlap between two clusters

    Returns:
        Overlap ratio (0-1)
    """
    try:
        start1 = datetime.fromisoformat(cluster1['first_seen'].replace('Z', '+00:00'))
        end1 = datetime.fromisoformat(cluster1['last_updated'].replace('Z', '+00:00'))
        start2 = datetime.fromisoformat(cluster2['first_seen'].replace('Z', '+00:00'))
        end2 = datetime.fromisoformat(cluster2['last_updated'].replace('Z', '+00:00'))

        # Find overlap period
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)

        if overlap_end <= overlap_start:
            return 0.0

        overlap_duration = (overlap_end - overlap_start).total_seconds()

        # Total span of both clusters
        total_start = min(start1, start2)
        total_end = max(end1, end2)
        total_duration = (total_end - total_start).total_seconds()

        return overlap_duration / total_duration if total_duration > 0 else 0.0

    except:
        return 0.0  # Return no overlap if parsing fails


def should_split_cluster(cluster: Dict[str, Any], articles: List[Dict[str, Any]]) -> bool:
    """
    Determine if a cluster should be split due to becoming too diverse

    Phase 3: Enhanced with geographic and temporal analysis
    """
    if len(articles) < 10:  # Need minimum size to consider splitting
        return False

    # Check temporal span
    try:
        timestamps = []
        for article in articles:
            pub_time = article.get('published_at')
            if pub_time:
                if isinstance(pub_time, str):
                    pub_time = datetime.fromisoformat(pub_time.replace('Z', '+00:00'))
                timestamps.append(pub_time)

        if timestamps:
            time_span = max(timestamps) - min(timestamps)
            if time_span.days > 7:  # Spans more than a week
                # Check if articles are geographically diverse
                if config.GEOGRAPHIC_FEATURES_ENABLED:
                    locations = []
                    for article in articles:
                        geo = article.get('geographic_features', {})
                        if geo.get('primary_location'):
                            locations.append(geo['primary_location'])

                    # If we have locations from different countries, might need splitting
                    countries = set(loc.country_code for loc in locations if loc.country_code)
                    if len(countries) > 1:
                        return True

    except Exception as e:
        logger.warning(f"Error checking cluster split conditions: {e}")

    return False
