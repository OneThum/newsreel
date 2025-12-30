"""
Cluster Maintenance - Phase 3 Clustering Overhaul

Automatically maintains cluster quality over time by:
- Merging similar clusters
- Splitting divergent clusters
- Decaying/archiving old clusters

Ensures ongoing clustering accuracy without manual intervention.
"""
import logging
from typing import List, Dict, Any, Tuple, Optional, Set
from datetime import datetime, timedelta
import numpy as np
try:
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from .config import config

logger = logging.getLogger(__name__)


class ClusterMaintenance:
    """
    Automated cluster quality maintenance system.

    Performs periodic maintenance jobs to ensure clustering accuracy:
    - Merge: Combine clusters that represent the same story
    - Split: Divide clusters that have become too diverse
    - Decay: Archive clusters that are no longer relevant
    """

    def __init__(self):
        """Initialize cluster maintenance system."""
        self.maintenance_stats = {
            'last_run': None,
            'clusters_processed': 0,
            'merges_performed': 0,
            'splits_performed': 0,
            'clusters_decayed': 0,
            'errors': 0
        }

    def perform_maintenance(
        self,
        clusters: List[Dict[str, Any]],
        max_clusters_to_process: int = 1000
    ) -> Dict[str, Any]:
        """
        Perform comprehensive cluster maintenance.

        Args:
            clusters: List of story clusters to maintain
            max_clusters_to_process: Maximum clusters to process in one run

        Returns:
            Maintenance results and statistics
        """
        logger.info(f"Starting cluster maintenance on {len(clusters)} clusters")

        start_time = datetime.now()
        results = {
            'merges': [],
            'splits': [],
            'decayed': [],
            'processed': 0,
            'errors': 0,
            'duration_seconds': 0
        }

        try:
            # Limit processing for performance
            clusters_to_process = clusters[:max_clusters_to_process]

            # 1. Merge similar clusters
            merge_results = self._merge_similar_clusters(clusters_to_process)
            results['merges'] = merge_results

            # 2. Split divergent clusters
            split_results = self._split_divergent_clusters(clusters_to_process)
            results['splits'] = split_results

            # 3. Decay old clusters
            decay_results = self._decay_old_clusters(clusters_to_process)
            results['decayed'] = decay_results

            results['processed'] = len(clusters_to_process)

        except Exception as e:
            logger.error(f"Cluster maintenance failed: {e}")
            results['errors'] = 1

        results['duration_seconds'] = (datetime.now() - start_time).total_seconds()

        # Update maintenance stats
        self._update_maintenance_stats(results)

        logger.info(f"Cluster maintenance completed: {len(results['merges'])} merges, "
                   f"{len(results['splits'])} splits, {len(results['decayed'])} decayed")

        return results

    def _merge_similar_clusters(self, clusters: List[Dict[str, Any]]) -> List[Tuple[str, str, str]]:
        """
        Identify and merge clusters that are too similar.

        Args:
            clusters: List of clusters to check for merging

        Returns:
            List of (cluster1_id, cluster2_id, merged_id) tuples
        """
        merges = []

        # Only process clusters with minimum size
        viable_clusters = [c for c in clusters if len(c.get('source_articles', [])) >= 2]

        if len(viable_clusters) < 2:
            return merges

        # Compare each pair of clusters
        for i, cluster1 in enumerate(viable_clusters):
            for cluster2 in viable_clusters[i+1:]:
                if self._should_merge_clusters(cluster1, cluster2):
                    merged_cluster = self._merge_clusters(cluster1, cluster2)
                    if merged_cluster:
                        merges.append((cluster1['id'], cluster2['id'], merged_cluster['id']))
                        # Remove cluster2 from consideration (it's been merged)
                        viable_clusters.remove(cluster2)
                        break

        return merges

    def _should_merge_clusters(self, cluster1: Dict[str, Any], cluster2: Dict[str, Any]) -> bool:
        """
        Determine if two clusters should be merged.

        Criteria:
        - Same category
        - High temporal overlap
        - High semantic similarity (would need embeddings)
        - Shared significant entities
        - Similar event signatures (Phase 3.1)
        """
        # Same category required
        if cluster1.get('category') != cluster2.get('category'):
            return False

        # Both clusters must be recent (not decayed)
        now = datetime.now()
        for cluster in [cluster1, cluster2]:
            last_updated = cluster.get('last_updated')
            if isinstance(last_updated, str):
                last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))

            # Don't merge clusters older than 7 days
            if (now - last_updated).days > 7:
                return False

        # Check temporal overlap (stories from similar time periods)
        time_overlap = self._calculate_temporal_overlap(cluster1, cluster2)
        if time_overlap < 0.5:  # Less than 50% temporal overlap
            return False

        # Check entity overlap (shared named entities)
        entity_overlap = self._calculate_entity_overlap(cluster1, cluster2)
        if entity_overlap < 0.6:  # Less than 60% entity overlap
            return False

        # Check geographic proximity (Phase 3.2)
        geo_similarity = self._calculate_geographic_similarity(cluster1, cluster2)
        if geo_similarity < 0.7:  # Geographic locations too different
            return False

        # Check event signature similarity (Phase 3.1)
        signature_similarity = self._calculate_signature_similarity(cluster1, cluster2)
        if signature_similarity < 0.8:  # Event signatures too different
            return False

        return True

    def _merge_clusters(self, cluster1: Dict[str, Any], cluster2: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Merge two clusters into one.

        Args:
            cluster1: First cluster
            cluster2: Second cluster

        Returns:
            Merged cluster dictionary
        """
        try:
            # Determine which cluster to keep as base (prefer larger/more recent)
            size1 = len(cluster1.get('source_articles', []))
            size2 = len(cluster2.get('source_articles', []))

            if size1 >= size2:
                base_cluster = cluster1.copy()
                merge_cluster = cluster2
            else:
                base_cluster = cluster2.copy()
                merge_cluster = cluster1

            # Generate new cluster ID
            base_cluster['id'] = f"merged_{base_cluster['id']}_{merge_cluster['id'][:8]}"

            # Merge source articles (avoid duplicates)
            base_articles = base_cluster.get('source_articles', [])
            merge_articles = merge_cluster.get('source_articles', [])

            # Create set of existing article IDs
            existing_ids = {art.get('id') for art in base_articles}

            # Add non-duplicate articles
            for article in merge_articles:
                if article.get('id') not in existing_ids:
                    base_articles.append(article)

            base_cluster['source_articles'] = base_articles

            # Update metadata
            base_cluster['last_updated'] = datetime.now().isoformat()

            # Update verification level
            base_cluster['verification_level'] = len(base_articles)

            # Merge entity histograms if present
            if 'entity_histogram' in base_cluster and 'entity_histogram' in merge_cluster:
                for entity, count in merge_cluster['entity_histogram'].items():
                    base_cluster['entity_histogram'][entity] = \
                        base_cluster['entity_histogram'].get(entity, 0) + count

            # Update geographic features if present
            if 'geographic_features' in base_cluster and 'geographic_features' in merge_cluster:
                # Combine location hierarchies
                geo1 = base_cluster['geographic_features']
                geo2 = merge_cluster['geographic_features']

                # Merge location lists
                combined_locations = geo1.get('locations', []) + geo2.get('locations', [])
                base_cluster['geographic_features']['locations'] = self._deduplicate_locations(combined_locations)

                # Recalculate primary location and hierarchy
                from .geographic_features import get_geographic_extractor
                extractor = get_geographic_extractor()
                # This would need the actual article content to recalculate properly
                # For now, keep the base cluster's geographic features

            return base_cluster

        except Exception as e:
            logger.error(f"Failed to merge clusters {cluster1.get('id')} and {cluster2.get('id')}: {e}")
            return None

    def _split_divergent_clusters(self, clusters: List[Dict[str, Any]]) -> List[Tuple[str, List[str]]]:
        """
        Identify and split clusters that have become too divergent.

        Args:
            clusters: List of clusters to check for splitting

        Returns:
            List of (original_cluster_id, [new_cluster_ids]) tuples
        """
        splits = []

        for cluster in clusters:
            if self._should_split_cluster(cluster):
                subclusters = self._split_cluster(cluster)
                if subclusters and len(subclusters) > 1:
                    new_ids = [sc['id'] for sc in subclusters]
                    splits.append((cluster['id'], new_ids))

        return splits

    def _should_split_cluster(self, cluster: Dict[str, Any]) -> bool:
        """
        Determine if a cluster should be split due to divergence.

        Criteria:
        - Minimum size (too small clusters shouldn't split)
        - Temporal span (stories spread over too long a period)
        - Semantic diversity (embeddings too spread out)
        - Geographic diversity (locations too spread out)
        """
        articles = cluster.get('source_articles', [])
        if len(articles) < 10:  # Minimum size for splitting
            return False

        # Check temporal span
        timestamps = []
        for article in articles:
            published_at = article.get('published_at')
            if isinstance(published_at, str):
                try:
                    published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    timestamps.append(published_at)
                except:
                    continue

        if len(timestamps) < 2:
            return False

        time_span = max(timestamps) - min(timestamps)
        if time_span < timedelta(days=3):  # Not spread out enough temporally
            return False

        # Check semantic diversity using embeddings (if available)
        if cluster.get('embeddings_available'):
            embedding_diversity = self._calculate_embedding_diversity(cluster)
            if embedding_diversity < 0.7:  # Not diverse enough
                return False

        # Check geographic diversity
        if cluster.get('geographic_features'):
            geo_diversity = self._calculate_geographic_diversity(cluster)
            if geo_diversity < 0.6:  # Not geographically diverse
                return False

        return True

    def _split_cluster(self, cluster: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split a divergent cluster into subclusters.

        Uses K-means clustering on embeddings to determine natural groupings.

        Args:
            cluster: Cluster to split

        Returns:
            List of subcluster dictionaries
        """
        try:
            articles = cluster.get('source_articles', [])
            if len(articles) < 10:
                return [cluster]

            # Try to get embeddings for clustering
            embeddings = []
            article_indices = []

            for i, article in enumerate(articles):
                # This would need to be implemented to retrieve embeddings
                # For now, fall back to temporal clustering
                embedding = None  # TODO: Retrieve from storage or recompute
                if embedding is not None:
                    embeddings.append(embedding)
                    article_indices.append(i)

            if len(embeddings) >= 10 and SKLEARN_AVAILABLE:
                # Use K-means on embeddings
                embeddings_array = np.array(embeddings)
                n_clusters = min(3, len(embeddings) // 4)  # Up to 3 subclusters

                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                labels = kmeans.fit_predict(embeddings_array)

                # Create subclusters
                subclusters = []
                for k in range(n_clusters):
                    cluster_indices = [i for i, label in enumerate(labels) if label == k]
                    cluster_articles = [articles[article_indices[i]] for i in cluster_indices]

                    if len(cluster_articles) >= 2:  # Minimum size
                        subcluster = cluster.copy()
                        subcluster['id'] = f"{cluster['id']}_split_{k}"
                        subcluster['source_articles'] = cluster_articles
                        subcluster['verification_level'] = len(cluster_articles)
                        subclusters.append(subcluster)

                if subclusters:
                    return subclusters

            # Fallback: temporal splitting
            return self._split_temporally(cluster)

        except Exception as e:
            logger.error(f"Failed to split cluster {cluster.get('id')}: {e}")
            return [cluster]

    def _split_temporally(self, cluster: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split cluster temporally when embedding-based splitting isn't available.

        Args:
            cluster: Cluster to split

        Returns:
            List of temporal subclusters
        """
        articles = cluster.get('source_articles', [])

        # Sort by publication time
        sorted_articles = []
        for article in articles:
            published_at = article.get('published_at')
            if isinstance(published_at, str):
                try:
                    published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    sorted_articles.append((published_at, article))
                except:
                    continue

        sorted_articles.sort(key=lambda x: x[0])

        # Split into roughly equal temporal groups
        if len(sorted_articles) < 10:
            return [cluster]

        mid_point = len(sorted_articles) // 2

        sub1_articles = [art for _, art in sorted_articles[:mid_point]]
        sub2_articles = [art for _, art in sorted_articles[mid_point:]]

        if len(sub1_articles) >= 2 and len(sub2_articles) >= 2:
            sub1 = cluster.copy()
            sub1['id'] = f"{cluster['id']}_early"
            sub1['source_articles'] = sub1_articles
            sub1['verification_level'] = len(sub1_articles)

            sub2 = cluster.copy()
            sub2['id'] = f"{cluster['id']}_late"
            sub2['source_articles'] = sub2_articles
            sub2['verification_level'] = len(sub2_articles)

            return [sub1, sub2]

        return [cluster]

    def _decay_old_clusters(self, clusters: List[Dict[str, Any]]) -> List[str]:
        """
        Identify clusters that should be decayed/archived.

        Args:
            clusters: List of clusters to check

        Returns:
            List of cluster IDs to decay
        """
        to_decay = []
        now = datetime.now()

        for cluster in clusters:
            should_decay, reason = self._should_decay_cluster(cluster, now)
            if should_decay:
                to_decay.append(cluster['id'])
                logger.info(f"Marking cluster {cluster['id']} for decay: {reason}")

        return to_decay

    def _should_decay_cluster(self, cluster: Dict[str, Any], now: datetime) -> Tuple[bool, str]:
        """
        Determine if a cluster should be decayed.

        Criteria:
        - Single article clusters older than 14 days
        - Any clusters with no updates in 30+ days
        - Clusters with very low engagement/activity
        """
        articles = cluster.get('source_articles', [])
        last_updated = cluster.get('last_updated')

        if isinstance(last_updated, str):
            try:
                last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            except:
                last_updated = cluster.get('first_seen')
                if isinstance(last_updated, str):
                    try:
                        last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    except:
                        return False, "unable to parse dates"

        if not last_updated:
            return False, "no update timestamp"

        days_since_update = (now - last_updated).days

        # Single article clusters decay faster
        if len(articles) == 1 and days_since_update > 14:
            return True, f"single article, {days_since_update} days old"

        # Any cluster with no updates in 30+ days
        if days_since_update > 30:
            return True, f"no updates for {days_since_update} days"

        # Small clusters with very low activity
        if len(articles) <= 2 and days_since_update > 21:
            return True, f"small cluster, {days_since_update} days inactive"

        return False, ""

    def _calculate_temporal_overlap(self, cluster1: Dict[str, Any], cluster2: Dict[str, Any]) -> float:
        """Calculate temporal overlap between two clusters."""
        # Extract time ranges
        range1 = self._get_cluster_time_range(cluster1)
        range2 = self._get_cluster_time_range(cluster2)

        if not range1 or not range2:
            return 0.0

        # Calculate overlap
        overlap_start = max(range1[0], range2[0])
        overlap_end = min(range1[1], range2[1])

        if overlap_start >= overlap_end:
            return 0.0

        overlap_duration = (overlap_end - overlap_start).total_seconds()
        total_duration = max((range1[1] - range1[0]).total_seconds(),
                           (range2[1] - range2[0]).total_seconds())

        return overlap_duration / total_duration if total_duration > 0 else 0.0

    def _get_cluster_time_range(self, cluster: Dict[str, Any]) -> Optional[Tuple[datetime, datetime]]:
        """Get the time range covered by a cluster."""
        articles = cluster.get('source_articles', [])
        timestamps = []

        for article in articles:
            published_at = article.get('published_at')
            if isinstance(published_at, str):
                try:
                    published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    timestamps.append(published_at)
                except:
                    continue

        if len(timestamps) < 2:
            return None

        return (min(timestamps), max(timestamps))

    def _calculate_entity_overlap(self, cluster1: Dict[str, Any], cluster2: Dict[str, Any]) -> float:
        """Calculate entity overlap between two clusters."""
        entities1 = set(cluster1.get('entity_histogram', {}).keys())
        entities2 = set(cluster2.get('entity_histogram', {}).keys())

        if not entities1 or not entities2:
            return 0.0

        intersection = len(entities1.intersection(entities2))
        union = len(entities1.union(entities2))

        return intersection / union if union > 0 else 0.0

    def _calculate_geographic_similarity(self, cluster1: Dict[str, Any], cluster2: Dict[str, Any]) -> float:
        """Calculate geographic similarity between clusters."""
        from .geographic_features import calculate_geographic_similarity

        geo1 = cluster1.get('geographic_features', {})
        geo2 = cluster2.get('geographic_features', {})

        if not geo1 or not geo2:
            return 0.5  # Neutral similarity if no geo data

        return calculate_geographic_similarity(geo1, geo2)

    def _calculate_signature_similarity(self, cluster1: Dict[str, Any], cluster2: Dict[str, Any]) -> float:
        """Calculate event signature similarity between clusters."""
        from .event_signatures import compare_event_signatures

        sig1 = cluster1.get('event_signature')
        sig2 = cluster2.get('event_signature')

        if not sig1 or not sig2:
            return 0.5  # Neutral similarity if no signature data

        return compare_event_signatures(sig1, sig2)

    def _calculate_embedding_diversity(self, cluster: Dict[str, Any]) -> float:
        """Calculate embedding diversity within a cluster."""
        # Placeholder - would need actual embeddings
        return 0.5

    def _calculate_geographic_diversity(self, cluster: Dict[str, Any]) -> float:
        """Calculate geographic diversity within a cluster."""
        geo_features = cluster.get('geographic_features', {})
        locations = geo_features.get('locations', [])

        if len(locations) <= 1:
            return 0.0

        # Calculate pairwise distances and average diversity
        total_distance = 0
        count = 0

        for i, loc1 in enumerate(locations):
            for loc2 in enumerate(locations[i+1:], i+1):
                # This would need proper location objects with distance calculation
                total_distance += 100  # Placeholder
                count += 1

        return min(total_distance / count / 1000, 1.0) if count > 0 else 0.0

    def _deduplicate_locations(self, locations: List[Any]) -> List[Any]:
        """Remove duplicate locations."""
        # Placeholder - would need proper location deduplication logic
        return locations

    def _update_maintenance_stats(self, results: Dict[str, Any]):
        """Update maintenance statistics."""
        self.maintenance_stats['last_run'] = datetime.now()
        self.maintenance_stats['clusters_processed'] = results.get('processed', 0)
        self.maintenance_stats['merges_performed'] += len(results.get('merges', []))
        self.maintenance_stats['splits_performed'] += len(results.get('splits', []))
        self.maintenance_stats['clusters_decayed'] += len(results.get('decayed', []))
        self.maintenance_stats['errors'] += results.get('errors', 0)

    def get_maintenance_stats(self) -> Dict[str, Any]:
        """Get maintenance statistics."""
        return self.maintenance_stats.copy()


# Global instance
_cluster_maintenance = None


def get_cluster_maintenance() -> ClusterMaintenance:
    """Get global cluster maintenance instance."""
    global _cluster_maintenance
    if _cluster_maintenance is None:
        _cluster_maintenance = ClusterMaintenance()
    return _cluster_maintenance


def perform_cluster_maintenance(clusters: List[Dict[str, Any]], max_clusters: int = 1000) -> Dict[str, Any]:
    """
    Convenience function to perform cluster maintenance.

    Args:
        clusters: List of clusters to maintain
        max_clusters: Maximum clusters to process

    Returns:
        Maintenance results
    """
    maintenance = get_cluster_maintenance()
    return maintenance.perform_maintenance(clusters, max_clusters)
