"""
Scoring Model Optimization - Phase 3 Clustering Overhaul

Implements a learned scoring model for article similarity using labeled training data.
Combines multiple similarity signals with machine learning for improved clustering accuracy.
"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, timedelta, timezone
import pickle
import os
import hashlib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import StandardScaler
import pandas as pd

from .config import config

logger = logging.getLogger(__name__)


class SimilarityFeatureExtractor:
    """
    Extracts features for similarity scoring between article pairs.

    Features include:
    - Semantic embedding similarity (cosine)
    - BM25 keyword similarity
    - Entity overlap metrics
    - Temporal proximity
    - Source credibility overlap
    - Event signature similarity
    - Geographic proximity
    - Wikidata entity consistency
    """

    def __init__(self):
        self.scaler = StandardScaler()

    def extract_features(self, article1: Dict[str, Any], article2: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract similarity features between two articles.

        Args:
            article1: First article dictionary
            article2: Second article dictionary

        Returns:
            Dictionary of feature values
        """
        features = {}

        # Semantic similarity (cosine similarity of embeddings)
        features['embedding_similarity'] = self._cosine_similarity(
            article1.get('embedding', []),
            article2.get('embedding', [])
        )

        # BM25 keyword similarity (if available)
        features['bm25_similarity'] = self._calculate_bm25_similarity(article1, article2)

        # Entity overlap features
        entity_features = self._extract_entity_features(article1, article2)
        features.update(entity_features)

        # Temporal proximity
        features['temporal_proximity'] = self._calculate_temporal_proximity(article1, article2)

        # Source overlap
        features['source_overlap'] = self._calculate_source_overlap(article1, article2)

        # Category consistency
        features['category_match'] = 1.0 if article1.get('category') == article2.get('category') else 0.0

        # Event signature similarity (Phase 3.1)
        features['event_signature_similarity'] = self._calculate_event_signature_similarity(article1, article2)

        # Geographic proximity (Phase 3.2)
        features['geographic_proximity'] = self._calculate_geographic_proximity(article1, article2)

        # Wikidata entity consistency (Phase 3.4)
        features['wikidata_consistency'] = self._calculate_wikidata_consistency(article1, article2)

        # Text length ratio (avoid clustering very different sized articles)
        len1 = len(f"{article1.get('title', '')} {article1.get('description', '')}")
        len2 = len(f"{article2.get('title', '')} {article2.get('description', '')}")
        features['text_length_ratio'] = min(len1, len2) / max(len1, len2) if max(len1, len2) > 0 else 0.0

        # Title overlap (Jaccard similarity)
        features['title_overlap'] = self._calculate_text_overlap(
            article1.get('title', ''),
            article2.get('title', '')
        )

        return features

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)

        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return np.dot(vec1_np, vec2_np) / (norm1 * norm2)

    def _calculate_bm25_similarity(self, article1: Dict[str, Any], article2: Dict[str, Any]) -> float:
        """Calculate BM25-based text similarity."""
        # This would use the BM25 index from candidate generation
        # For now, return a placeholder based on text overlap
        text1 = f"{article1.get('title', '')} {article1.get('description', '')}".lower()
        text2 = f"{article2.get('title', '')} {article2.get('description', '')}".lower()

        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _extract_entity_features(self, article1: Dict[str, Any], article2: Dict[str, Any]) -> Dict[str, float]:
        """Extract entity-based similarity features."""
        entities1 = article1.get('entities', [])
        entities2 = article2.get('entities', [])

        if not entities1 or not entities2:
            return {
                'entity_overlap_jaccard': 0.0,
                'person_entity_overlap': 0.0,
                'org_entity_overlap': 0.0,
                'location_entity_overlap': 0.0,
                'wikidata_entity_match': 0.0
            }

        # Convert to sets for comparison
        texts1 = {e.get('text', '').lower() for e in entities1}
        texts2 = {e.get('text', '').lower() for e in entities2}

        # Jaccard similarity
        intersection = texts1.intersection(texts2)
        union = texts1.union(texts2)
        jaccard = len(intersection) / len(union) if union else 0.0

        # Type-specific overlaps
        person_overlap = self._entity_type_overlap(entities1, entities2, 'PERSON')
        org_overlap = self._entity_type_overlap(entities1, entities2, 'ORGANIZATION')
        location_overlap = self._entity_type_overlap(entities1, entities2, 'LOCATION')

        # Wikidata QID matches (Phase 3.4)
        wikidata_matches = 0
        qids1 = {e.get('wikidata', {}).get('qid') for e in entities1 if e.get('wikidata')}
        qids2 = {e.get('wikidata', {}).get('qid') for e in entities2 if e.get('wikidata')}
        if qids1 and qids2:
            wikidata_matches = len(qids1.intersection(qids2)) / len(qids1.union(qids2))

        return {
            'entity_overlap_jaccard': jaccard,
            'person_entity_overlap': person_overlap,
            'org_entity_overlap': org_overlap,
            'location_entity_overlap': location_overlap,
            'wikidata_entity_match': wikidata_matches
        }

    def _entity_type_overlap(self, entities1: List[Dict], entities2: List[Dict], entity_type: str) -> float:
        """Calculate overlap for specific entity type."""
        type1 = {e.get('text', '').lower() for e in entities1 if e.get('type') == entity_type}
        type2 = {e.get('text', '').lower() for e in entities2 if e.get('type') == entity_type}

        if not type1 or not type2:
            return 0.0

        intersection = type1.intersection(type2)
        union = type1.union(type2)

        return len(intersection) / len(union)

    def _calculate_temporal_proximity(self, article1: Dict[str, Any], article2: Dict[str, Any]) -> float:
        """Calculate temporal proximity between articles."""
        try:
            time1 = datetime.fromisoformat(article1.get('published_at', '').replace('Z', '+00:00'))
            time2 = datetime.fromisoformat(article2.get('published_at', '').replace('Z', '+00:00'))

            # Convert to hours difference
            time_diff_hours = abs((time1 - time2).total_seconds()) / 3600

            # Exponential decay: closer in time = higher similarity
            # Max similarity at 0 hours, decays to 0.1 at 168 hours (1 week)
            decay_rate = 0.01  # Adjust for desired decay
            return max(0.1, np.exp(-decay_rate * time_diff_hours))

        except (ValueError, TypeError):
            return 0.5  # Neutral score if dates are invalid

    def _calculate_source_overlap(self, article1: Dict[str, Any], article2: Dict[str, Any]) -> float:
        """Calculate source credibility overlap."""
        source1 = article1.get('source', '').lower()
        source2 = article2.get('source', '').lower()

        if not source1 or not source2:
            return 0.0

        # Exact match
        if source1 == source2:
            return 1.0

        # Partial match (e.g., "bbc.com" and "bbc.co.uk")
        source1_parts = set(source1.split('.'))
        source2_parts = set(source2.split('.'))

        overlap = len(source1_parts.intersection(source2_parts))
        total = len(source1_parts.union(source2_parts))

        return overlap / total if total > 0 else 0.0

    def _calculate_event_signature_similarity(self, article1: Dict[str, Any], article2: Dict[str, Any]) -> float:
        """Calculate event signature similarity (Phase 3.1)."""
        sig1 = article1.get('event_signature', {})
        sig2 = article2.get('event_signature', {})

        if not sig1 or not sig2:
            return 0.0

        # Hash-based similarity (exact match of signature)
        hash1 = sig1.get('signature_hash')
        hash2 = sig2.get('signature_hash')

        if hash1 and hash2 and hash1 == hash2:
            return 1.0

        # Component-wise similarity
        action_sim = 1.0 if sig1.get('action') == sig2.get('action') else 0.0
        event_sim = 1.0 if sig1.get('event_type') == sig2.get('event_type') else 0.0

        # Entity overlap
        entities1 = set(sig1.get('main_entities', []))
        entities2 = set(sig2.get('main_entities', []))
        entity_overlap = len(entities1.intersection(entities2)) / len(entities1.union(entities2)) if entities1 or entities2 else 0.0

        return (action_sim + event_sim + entity_overlap) / 3.0

    def _calculate_geographic_proximity(self, article1: Dict[str, Any], article2: Dict[str, Any]) -> float:
        """Calculate geographic proximity (Phase 3.2)."""
        geo1 = article1.get('geographic_features', {})
        geo2 = article2.get('geographic_features', {})

        if not geo1 or not geo2:
            return 0.0

        # Use the geographic_features module for calculation
        try:
            from .geographic_features import calculate_geographic_similarity
            return calculate_geographic_similarity(geo1, geo2)
        except ImportError:
            # Fallback: simple location name overlap
            locs1 = {loc.get('name', '').lower() for loc in geo1.get('locations', [])}
            locs2 = {loc.get('name', '').lower() for loc in geo2.get('locations', [])}

            if not locs1 or not locs2:
                return 0.0

            intersection = locs1.intersection(locs2)
            union = locs1.union(locs2)

            return len(intersection) / len(union)

    def _calculate_wikidata_consistency(self, article1: Dict[str, Any], article2: Dict[str, Any]) -> float:
        """Calculate Wikidata entity consistency (Phase 3.4)."""
        entities1 = article1.get('entities', [])
        entities2 = article2.get('entities', [])

        if not entities1 or not entities2:
            return 0.0

        # Count Wikidata QID matches
        qids1 = {e.get('wikidata', {}).get('qid') for e in entities1 if e.get('wikidata')}
        qids2 = {e.get('wikidata', {}).get('qid') for e in entities2 if e.get('wikidata')}

        if not qids1 or not qids2:
            return 0.0

        intersection = qids1.intersection(qids2)
        union = qids1.union(qids2)

        return len(intersection) / len(union)

    def _calculate_text_overlap(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity of word sets."""
        if not text1 or not text2:
            return 0.0

        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0


class OptimizedSimilarityScorer:
    """
    Machine learning-based similarity scorer using labeled training data.

    Trains a model to predict article similarity based on multiple features.
    Combines with rule-based scoring for robustness.
    """

    def __init__(self, model_path: str = None):
        self.feature_extractor = SimilarityFeatureExtractor()
        self.model: Optional[Union[RandomForestClassifier, GradientBoostingClassifier]] = None
        self.feature_names: List[str] = []
        self.model_path = model_path or os.path.join(os.getcwd(), 'similarity_model.pkl')
        self.is_trained = False

        # Load existing model if available
        self._load_model()

    def _load_model(self):
        """Load trained model from disk."""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data['model']
                    self.feature_names = data['feature_names']
                    self.is_trained = data.get('is_trained', True)
                logger.info(f"Loaded similarity model from {self.model_path}")
        except Exception as e:
            logger.warning(f"Failed to load similarity model: {e}")

    def _save_model(self):
        """Save trained model to disk."""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'feature_names': self.feature_names,
                    'is_trained': self.is_trained,
                    'timestamp': datetime.now().isoformat()
                }, f)
            logger.info(f"Saved similarity model to {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to save similarity model: {e}")

    def train(self, labeled_pairs: List[Tuple[Dict[str, Any], Dict[str, Any], int]],
              test_size: float = 0.2, random_state: int = 42):
        """
        Train the similarity model on labeled data.

        Args:
            labeled_pairs: List of (article1, article2, similarity_label) tuples
            test_size: Fraction of data to use for testing
            random_state: Random state for reproducibility
        """
        if len(labeled_pairs) < 10:
            logger.warning("Not enough labeled data for training")
            return

        logger.info(f"Training similarity model on {len(labeled_pairs)} labeled pairs")

        # Extract features
        X = []
        y = []

        for article1, article2, label in labeled_pairs:
            features = self.feature_extractor.extract_features(article1, article2)
            X.append(list(features.values()))
            y.append(label)

        X = np.array(X)
        y = np.array(y)

        # Store feature names
        if not self.feature_names:
            self.feature_names = list(features.keys())

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        # Train model (try GradientBoosting first, fallback to RandomForest)
        try:
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=6,
                random_state=random_state
            )
            self.model.fit(X_train, y_train)
            logger.info("Trained GradientBoostingClassifier")
        except Exception as e:
            logger.warning(f"GradientBoosting failed, trying RandomForest: {e}")
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=6,
                random_state=random_state
            )
            self.model.fit(X_train, y_train)
            logger.info("Trained RandomForestClassifier")

        # Evaluate
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)

        y_pred = self.model.predict(X_test)
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')

        logger.info(".3f")
        logger.info(".3f")
        logger.info(".3f")
        logger.info(".3f")
        logger.info(".3f")

        self.is_trained = True
        self._save_model()

    def predict_similarity(self, article1: Dict[str, Any], article2: Dict[str, Any]) -> float:
        """
        Predict similarity score between two articles.

        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not self.is_trained or not self.model:
            # Fallback to rule-based scoring
            return self._rule_based_similarity(article1, article2)

        try:
            features = self.feature_extractor.extract_features(article1, article2)
            feature_values = np.array([list(features.values())])

            # Ensure feature order matches training
            if len(feature_values[0]) != len(self.feature_names):
                logger.warning("Feature mismatch, using rule-based fallback")
                return self._rule_based_similarity(article1, article2)

            prediction_proba = self.model.predict_proba(feature_values)[0]

            # Return probability of positive class (similar)
            if len(prediction_proba) > 1:
                return float(prediction_proba[1])
            else:
                return float(prediction_proba[0])

        except Exception as e:
            logger.warning(f"ML prediction failed, using rule-based: {e}")
            return self._rule_based_similarity(article1, article2)

    def _rule_based_similarity(self, article1: Dict[str, Any], article2: Dict[str, Any]) -> float:
        """Rule-based similarity scoring as fallback."""
        features = self.feature_extractor.extract_features(article1, article2)

        # Weighted combination of features
        weights = {
            'embedding_similarity': 0.4,
            'entity_overlap_jaccard': 0.2,
            'temporal_proximity': 0.15,
            'event_signature_similarity': 0.1,
            'geographic_proximity': 0.1,
            'wikidata_consistency': 0.05
        }

        score = 0.0
        total_weight = 0.0

        for feature, weight in weights.items():
            if feature in features:
                score += features[feature] * weight
                total_weight += weight

        return score / total_weight if total_weight > 0 else 0.0

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores from the trained model."""
        if not self.is_trained or not hasattr(self.model, 'feature_importances_'):
            return {}

        importance_dict = {}
        for name, importance in zip(self.feature_names, self.model.feature_importances_):
            importance_dict[name] = float(importance)

        return importance_dict

    def evaluate_on_data(self, test_pairs: List[Tuple[Dict[str, Any], Dict[str, Any], int]]) -> Dict[str, float]:
        """Evaluate model performance on test data."""
        if not test_pairs:
            return {}

        predictions = []
        actuals = []

        for article1, article2, actual in test_pairs:
            pred = self.predict_similarity(article1, article2)
            # Convert to binary prediction (threshold 0.5)
            pred_binary = 1 if pred >= 0.5 else 0
            predictions.append(pred_binary)
            actuals.append(actual)

        return {
            'accuracy': accuracy_score(actuals, predictions),
            'precision': precision_score(actuals, predictions, average='weighted'),
            'recall': recall_score(actuals, predictions, average='weighted'),
            'f1': f1_score(actuals, predictions, average='weighted')
        }


# Global instance
_similarity_scorer = None


def get_similarity_scorer() -> OptimizedSimilarityScorer:
    """Get global similarity scorer instance."""
    global _similarity_scorer
    if _similarity_scorer is None:
        _similarity_scorer = OptimizedSimilarityScorer()
    return _similarity_scorer


def predict_article_similarity(article1: Dict[str, Any], article2: Dict[str, Any]) -> float:
    """
    Convenience function to predict similarity between two articles.

    Args:
        article1: First article
        article2: Second article

    Returns:
        Similarity score (0.0 to 1.0)
    """
    scorer = get_similarity_scorer()
    return scorer.predict_similarity(article1, article2)
