#!/usr/bin/env python3
"""
Train Similarity Model for Clustering Overhaul

This script trains the ML-based similarity scoring model using the ground truth dataset.
It loads the labeled training pairs and trains a model to predict article similarity.
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add functions directory to path
functions_path = Path(__file__).parent / "functions"
sys.path.insert(0, str(functions_path))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_ground_truth_data():
    """Load ground truth dataset for training"""
    dataset_path = Path(__file__).parent / "tests" / "ground_truth_dataset.json"

    if not dataset_path.exists():
        raise FileNotFoundError(f"Ground truth dataset not found at {dataset_path}")

    logger.info(f"Loading ground truth data from {dataset_path}")

    with open(dataset_path, 'r') as f:
        data = json.load(f)

    dataset = data["dataset"]
    metadata = data["metadata"]

    logger.info(f"Loaded {len(dataset)} training pairs")
    logger.info(f"Positive pairs: {metadata['positive_pairs']}")
    logger.info(f"Negative pairs: {metadata['negative_pairs']}")

    # Convert to training format
    training_pairs = []
    for pair_data in dataset:
        article1 = pair_data["article1"]
        article2 = pair_data["article2"]
        label = pair_data["label"]
        training_pairs.append((article1, article2, label))

    return training_pairs

def check_ml_dependencies():
    """Check if ML dependencies are available"""
    try:
        import sklearn
        logger.info("✅ scikit-learn is available")
        return True
    except ImportError:
        logger.warning("⚠️ scikit-learn not available - ML training will be skipped")
        logger.info("To enable ML training, install: pip install scikit-learn pandas")
        return False

def train_similarity_model():
    """Train the similarity scoring model"""
    logger.info("🚀 Starting similarity model training")

    # Check dependencies
    if not check_ml_dependencies():
        logger.info("Skipping ML training due to missing dependencies")
        return False

    try:
        # Load training data
        training_pairs = load_ground_truth_data()

        if len(training_pairs) < 10:
            logger.warning(f"Insufficient training data: {len(training_pairs)} pairs")
            return False

        # Import ML components
        from shared.scoring_optimization import get_similarity_scorer

        # Get scorer instance
        scorer = get_similarity_scorer()

        # Check if model is already trained
        if scorer.is_trained:
            logger.info("Model is already trained. Use force_retrain=True to retrain.")
            return True

        # Train the model
        logger.info(f"Training model on {len(training_pairs)} pairs...")
        scorer.train(training_pairs)

        # Evaluate performance
        performance = scorer.evaluate_on_data(training_pairs)

        logger.info("🎯 Training completed!")
        logger.info(".3f")
        logger.info(".3f")
        logger.info(".3f")

        # Save training report
        report = {
            "training_timestamp": "2025-11-12T22:00:00Z",
            "training_pairs": len(training_pairs),
            "performance": performance,
            "model_path": scorer.model_path,
            "is_trained": scorer.is_trained
        }

        report_path = Path(__file__).parent / "models" / "training_report.json"
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"✅ Training report saved to {report_path}")
        return True

    except Exception as e:
        logger.error(f"❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_trained_model():
    """Validate the trained model with sample predictions"""
    logger.info("🔍 Validating trained model...")

    try:
        from shared.scoring_optimization import predict_article_similarity

        # Sample articles for testing
        article1 = {
            "title": "Apple announces new iPhone",
            "description": "Apple unveiled the latest iPhone model",
            "entities": [{"text": "Apple", "type": "ORGANIZATION"}]
        }

        article2_similar = {
            "title": "Apple launches iPhone 15",
            "description": "Apple released the new iPhone 15 smartphone",
            "entities": [{"text": "Apple", "type": "ORGANIZATION"}]
        }

        article2_different = {
            "title": "Tesla reports earnings",
            "description": "Electric car maker Tesla posted quarterly results",
            "entities": [{"text": "Tesla", "type": "ORGANIZATION"}]
        }

        # Test predictions
        score_similar = predict_article_similarity(article1, article2_similar)
        score_different = predict_article_similarity(article1, article2_different)

        logger.info(".3f")
        logger.info(".3f")

        if score_similar > score_different:
            logger.info("✅ Model validation passed - similar articles score higher")
            return True
        else:
            logger.warning("⚠️ Model validation inconclusive - similar articles don't score higher")
            return False

    except Exception as e:
        logger.error(f"❌ Model validation failed: {e}")
        return False

def main():
    """Main training function"""
    print("🚀 Newsreel Clustering Overhaul - Similarity Model Training")
    print("=" * 60)

    # Train the model
    success = train_similarity_model()

    if success:
        # Validate the trained model
        validation_success = validate_trained_model()

        if validation_success:
            print("\n🎉 SUCCESS: Similarity model trained and validated!")
            print("\nNext steps:")
            print("1. Deploy embedding service to ACI")
            print("2. Enable A/B testing in production")
            print("3. Monitor clustering metrics")
            print("4. Retrain model periodically with new data")
            return 0
        else:
            print("\n⚠️ WARNING: Model trained but validation inconclusive")
            return 1
    else:
        print("\n❌ FAILURE: Model training failed")
        print("\nTroubleshooting:")
        print("1. Ensure scikit-learn is installed: pip install scikit-learn pandas")
        print("2. Check ground truth dataset exists: Azure/tests/ground_truth_dataset.json")
        print("3. Verify all dependencies are available")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
