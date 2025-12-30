"""
A/B Testing Framework for Clustering Systems - Phase 2

Enables comparison between old fingerprinting clustering and new embedding-based clustering.
Supports gradual rollout and performance validation.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import hashlib
import random

from .config import config

logger = logging.getLogger(__name__)


class ClusteringExperiment:
    """
    Represents an A/B test experiment for clustering algorithms

    Supports:
    - Traffic splitting by percentage or user segments
    - Performance metrics collection
    - Gradual rollout capabilities
    - Automated winner determination
    """

    def __init__(
        self,
        experiment_id: str,
        variants: Dict[str, Dict[str, Any]],
        traffic_split: Dict[str, float],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ):
        """
        Initialize an A/B test experiment

        Args:
            experiment_id: Unique experiment identifier
            variants: Dict of variant_name -> variant_config
            traffic_split: Dict of variant_name -> percentage (0.0-1.0)
            start_time: When experiment starts (default: now)
            end_time: When experiment ends (optional)
        """
        self.experiment_id = experiment_id
        self.variants = variants
        self.traffic_split = traffic_split
        self.start_time = start_time or datetime.now()
        self.end_time = end_time

        # Validate traffic split
        total_split = sum(traffic_split.values())
        if abs(total_split - 1.0) > 0.001:
            raise ValueError(f"Traffic split must sum to 1.0, got {total_split}")

        # Validate variants
        if not variants:
            raise ValueError("At least one variant required")

        for variant_name in traffic_split:
            if variant_name not in variants:
                raise ValueError(f"Variant '{variant_name}' in traffic_split but not in variants")

    def assign_variant(self, article_id: str) -> str:
        """
        Assign an article to a variant based on consistent hashing

        Args:
            article_id: Unique article identifier

        Returns:
            Variant name to use for this article
        """
        # Use consistent hashing for deterministic assignment
        hash_value = int(hashlib.md5(f"{self.experiment_id}:{article_id}".encode()).hexdigest(), 16)
        normalized_hash = (hash_value % 10000) / 10000.0  # 0.0 to 1.0

        cumulative = 0.0
        for variant_name, split in self.traffic_split.items():
            cumulative += split
            if normalized_hash <= cumulative:
                return variant_name

        # Fallback (should not happen with proper validation)
        return list(self.traffic_split.keys())[0]

    def is_active(self) -> bool:
        """
        Check if experiment is currently active

        Returns:
            True if experiment should be running
        """
        now = datetime.now()
        if now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False
        return True

    def get_variant_config(self, variant_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific variant

        Args:
            variant_name: Name of the variant

        Returns:
            Variant configuration dictionary
        """
        return self.variants.get(variant_name, {})


class ClusteringABTest:
    """
    A/B testing framework for clustering algorithms

    Manages multiple experiments and provides utilities for:
    - Variant assignment
    - Metrics collection
    - Results analysis
    - Gradual rollout
    """

    def __init__(self):
        """Initialize A/B testing framework"""
        self.experiments: Dict[str, ClusteringExperiment] = {}
        self.metrics: Dict[str, List[Dict[str, Any]]] = {}

        # Set up default Phase 2 experiment
        self._setup_default_experiment()

    def _setup_default_experiment(self):
        """Set up the default Phase 2 clustering experiment"""
        # Define variants
        variants = {
            'control': {
                'algorithm': 'fingerprinting',
                'description': 'Original MD5 fingerprinting with text similarity fallback',
                'use_embeddings': False,
                'use_simhash': config.CLUSTERING_USE_SIMHASH,
                'use_time_window': config.CLUSTERING_USE_TIME_WINDOW,
                'use_adaptive_threshold': config.CLUSTERING_USE_ADAPTIVE_THRESHOLD
            },
            'embedding_v1': {
                'algorithm': 'semantic_embeddings',
                'description': 'New SentenceTransformers + FAISS + BM25 hybrid search',
                'use_embeddings': True,
                'use_simhash': config.CLUSTERING_USE_SIMHASH,
                'use_time_window': config.CLUSTERING_USE_TIME_WINDOW,
                'use_adaptive_threshold': config.CLUSTERING_USE_ADAPTIVE_THRESHOLD,
                'embedding_model': config.EMBEDDINGS_MODEL,
                'similarity_threshold': 0.75  # Higher threshold for embeddings
            }
        }

        # Traffic split (gradual rollout)
        traffic_split = {
            'control': 0.7,      # 70% control (existing system)
            'embedding_v1': 0.3  # 30% new system
        }

        # Create experiment
        experiment = ClusteringExperiment(
            experiment_id='clustering_phase2_rollout',
            variants=variants,
            traffic_split=traffic_split
        )

        self.experiments[experiment.experiment_id] = experiment

    def get_experiment(self, experiment_id: str) -> Optional[ClusteringExperiment]:
        """
        Get an experiment by ID

        Args:
            experiment_id: Experiment identifier

        Returns:
            ClusteringExperiment instance or None
        """
        return self.experiments.get(experiment_id)

    def assign_variant(self, article_id: str, experiment_id: str = 'clustering_phase2_rollout') -> str:
        """
        Assign an article to a variant in the specified experiment

        Args:
            article_id: Unique article identifier
            experiment_id: Experiment to use (default: main rollout)

        Returns:
            Assigned variant name
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment or not experiment.is_active():
            # Default to control if experiment not found or inactive
            return 'control'

        return experiment.assign_variant(article_id)

    def get_clustering_config(self, article_id: str) -> Dict[str, Any]:
        """
        Get clustering configuration for an article based on A/B assignment

        Args:
            article_id: Unique article identifier

        Returns:
            Clustering configuration dictionary
        """
        variant = self.assign_variant(article_id)
        experiment = self.get_experiment('clustering_phase2_rollout')

        if experiment:
            config_dict = experiment.get_variant_config(variant).copy()
            config_dict['variant'] = variant
            config_dict['experiment_id'] = experiment.experiment_id
            return config_dict

        # Fallback to default config
        return {
            'variant': 'control',
            'algorithm': 'fingerprinting',
            'use_embeddings': False
        }

    def record_metric(
        self,
        article_id: str,
        metric_name: str,
        value: Any,
        experiment_id: str = 'clustering_phase2_rollout',
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record a metric for A/B testing analysis

        Args:
            article_id: Article that generated the metric
            metric_name: Name of the metric (e.g., 'clustering_time', 'stories_created')
            value: Metric value
            experiment_id: Experiment ID
            metadata: Additional metadata
        """
        variant = self.assign_variant(article_id, experiment_id)

        metric_record = {
            'timestamp': datetime.now().isoformat(),
            'experiment_id': experiment_id,
            'variant': variant,
            'article_id': article_id,
            'metric_name': metric_name,
            'value': value,
            'metadata': metadata or {}
        }

        if experiment_id not in self.metrics:
            self.metrics[experiment_id] = []

        self.metrics[experiment_id].append(metric_record)

        logger.debug(f"Recorded metric: {metric_name}={value} for variant {variant}")

    def get_experiment_results(self, experiment_id: str) -> Dict[str, Any]:
        """
        Get aggregated results for an experiment

        Args:
            experiment_id: Experiment identifier

        Returns:
            Dictionary with experiment results and metrics
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return {'error': f'Experiment {experiment_id} not found'}

        metrics = self.metrics.get(experiment_id, [])

        # Aggregate metrics by variant
        variant_metrics = {}
        for metric in metrics:
            variant = metric['variant']
            metric_name = metric['metric_name']

            if variant not in variant_metrics:
                variant_metrics[variant] = {}

            if metric_name not in variant_metrics[variant]:
                variant_metrics[variant][metric_name] = []

            variant_metrics[variant][metric_name].append(metric['value'])

        # Calculate statistics
        results = {
            'experiment_id': experiment_id,
            'is_active': experiment.is_active(),
            'traffic_split': experiment.traffic_split,
            'variants': experiment.variants,
            'total_metrics': len(metrics),
            'variant_stats': {}
        }

        for variant, metrics_dict in variant_metrics.items():
            results['variant_stats'][variant] = {}
            for metric_name, values in metrics_dict.items():
                if isinstance(values[0], (int, float)):
                    results['variant_stats'][variant][metric_name] = {
                        'count': len(values),
                        'mean': sum(values) / len(values),
                        'min': min(values),
                        'max': max(values)
                    }
                else:
                    # For non-numeric metrics, just count occurrences
                    results['variant_stats'][variant][metric_name] = {
                        'count': len(values),
                        'unique_values': len(set(values))
                    }

        return results

    def update_traffic_split(self, experiment_id: str, new_split: Dict[str, float]):
        """
        Update traffic split for gradual rollout

        Args:
            experiment_id: Experiment to update
            new_split: New traffic split dictionary
        """
        experiment = self.get_experiment(experiment_id)
        if experiment:
            # Validate new split
            total = sum(new_split.values())
            if abs(total - 1.0) > 0.001:
                raise ValueError(f"Traffic split must sum to 1.0, got {total}")

            experiment.traffic_split = new_split
            logger.info(f"Updated traffic split for {experiment_id}: {new_split}")

    def gradual_rollout(self, experiment_id: str, target_split: Dict[str, float], steps: int = 5):
        """
        Plan gradual rollout to target traffic split

        Args:
            experiment_id: Experiment to rollout
            target_split: Target traffic distribution
            steps: Number of rollout steps

        Returns:
            List of intermediate traffic splits for gradual rollout
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        current_split = experiment.traffic_split.copy()
        rollout_plan = []

        for step in range(1, steps + 1):
            # Linear interpolation between current and target
            factor = step / steps
            step_split = {}

            for variant in set(current_split.keys()) | set(target_split.keys()):
                current = current_split.get(variant, 0.0)
                target = target_split.get(variant, 0.0)
                step_split[variant] = current + (target - current) * factor

            rollout_plan.append(step_split.copy())

        return rollout_plan


# Global A/B testing instance
_ab_test_instance: Optional[ClusteringABTest] = None


def get_ab_tester() -> ClusteringABTest:
    """
    Get or create global A/B testing instance (singleton pattern)

    Returns:
        ClusteringABTest instance
    """
    global _ab_test_instance
    if _ab_test_instance is None:
        _ab_test_instance = ClusteringABTest()
    return _ab_test_instance


def get_clustering_config(article_id: str) -> Dict[str, Any]:
    """
    Get clustering configuration for an article (with A/B testing)

    Args:
        article_id: Unique article identifier

    Returns:
        Clustering configuration dictionary
    """
    tester = get_ab_tester()
    return tester.get_clustering_config(article_id)


def record_clustering_metric(article_id: str, metric_name: str, value: Any, metadata: Optional[Dict[str, Any]] = None):
    """
    Record a clustering metric for A/B testing

    Args:
        article_id: Article identifier
        metric_name: Metric name (e.g., 'stories_created', 'clustering_time_ms')
        value: Metric value
        metadata: Additional metadata
    """
    tester = get_ab_tester()
    tester.record_metric(article_id, metric_name, value, metadata=metadata)
