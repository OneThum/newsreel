#!/usr/bin/env python3
"""
Simple validation script for clustering overhaul components.

This script validates that all clustering components can be imported and
perform basic functionality without complex test framework dependencies.
"""

import sys
import os
import json
from pathlib import Path

# Add the functions directory to path
functions_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, functions_path)
print(f"Added to path: {functions_path}")
print(f"Current path: {sys.path[:3]}")

def validate_imports():
    """Validate that all components can be imported"""
    print("🔍 Validating component imports...")

    components = []
    errors = []

    try:
        from functions.shared.config import config
        print("✅ Config imported successfully")
        components.append("config")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        errors.append(f"config: {e}")

    try:
        from functions.shared.utils import extract_simple_entities, extract_simple_entities_with_wikidata
        print("✅ Utils imported successfully")
        components.append("utils")
    except Exception as e:
        print(f"❌ Utils import failed: {e}")
        errors.append(f"utils: {e}")

    try:
        from functions.shared.wikidata_linking import WikidataLinker
        print("✅ Wikidata linking imported successfully")
        components.append("wikidata_linking")
    except Exception as e:
        print(f"❌ Wikidata linking import failed: {e}")
        errors.append(f"wikidata_linking: {e}")

    try:
        from functions.shared.event_signatures import extract_event_signature
        print("✅ Event signatures imported successfully")
        components.append("event_signatures")
    except Exception as e:
        print(f"❌ Event signatures import failed: {e}")
        errors.append(f"event_signatures: {e}")

    try:
        from functions.shared.geographic_features import extract_geographic_features
        print("✅ Geographic features imported successfully")
        components.append("geographic_features")
    except Exception as e:
        print(f"❌ Geographic features import failed: {e}")
        errors.append(f"geographic_features: {e}")

    try:
        from functions.shared.vector_index import VectorIndex
        print("✅ Vector index imported successfully")
        components.append("vector_index")
    except Exception as e:
        print(f"❌ Vector index import failed: {e}")
        errors.append(f"vector_index: {e}")

    try:
        from functions.shared.cluster_maintenance import ClusterMaintenance
        print("✅ Cluster maintenance imported successfully")
        components.append("cluster_maintenance")
    except Exception as e:
        print(f"❌ Cluster maintenance import failed: {e}")
        errors.append(f"cluster_maintenance: {e}")

    # ML components (optional)
    try:
        from functions.shared.scoring_optimization import OptimizedSimilarityScorer
        print("✅ ML scoring imported successfully (optional)")
        components.append("scoring_optimization")
    except Exception as e:
        print(f"⚠️ ML scoring not available (optional): {e}")

    try:
        from functions.shared.training_data import TrainingDataGenerator
        print("✅ Training data imported successfully (optional)")
        components.append("training_data")
    except Exception as e:
        print(f"⚠️ Training data not available (optional): {e}")

    return components, errors

def validate_basic_functionality():
    """Validate basic functionality of imported components"""
    print("\n🔧 Validating basic functionality...")

    results = []
    errors = []

    # Test entity extraction
    try:
        from functions.shared.utils import extract_simple_entities
        entities = extract_simple_entities("Apple announces new iPhone in California")
        assert len(entities) > 0, "Entity extraction returned no entities"
        print("✅ Entity extraction works")
        results.append("entity_extraction")
    except Exception as e:
        print(f"❌ Entity extraction failed: {e}")
        errors.append(f"entity_extraction: {e}")

    # Test event signature extraction
    try:
        from functions.shared.event_signatures import extract_event_signature
        signature = extract_event_signature(
            "Apple launches iPhone",
            "Apple released the new iPhone model",
            [{"text": "Apple", "type": "ORGANIZATION"}]
        )
        assert "event_types" in signature, "Event signature missing event_types"
        assert len(signature["event_types"]) > 0, "No event types extracted"
        print("✅ Event signature extraction works")
        results.append("event_signatures")
    except Exception as e:
        print(f"❌ Event signature extraction failed: {e}")
        errors.append(f"event_signatures: {e}")

    # Test geographic features
    try:
        from functions.shared.geographic_features import extract_geographic_features
        geo = extract_geographic_features(
            "Earthquake in California",
            "A quake struck Northern California",
            [{"text": "California", "type": "LOCATION"}]
        )
        assert "locations" in geo, "Geographic extraction missing locations"
        print("✅ Geographic feature extraction works")
        results.append("geographic_features")
    except Exception as e:
        print(f"❌ Geographic feature extraction failed: {e}")
        errors.append(f"geographic_features: {e}")

    # Test vector index
    try:
        from functions.shared.vector_index import VectorIndex
        index = VectorIndex(embedding_dim=64)  # Small dimension for testing
        assert index.index is not None, "Vector index not initialized"
        print("✅ Vector index initialization works")
        results.append("vector_index")
    except Exception as e:
        print(f"❌ Vector index initialization failed: {e}")
        errors.append(f"vector_index: {e}")

    return results, errors

def validate_ground_truth_dataset():
    """Validate the ground truth dataset"""
    print("\n📊 Validating ground truth dataset...")

    dataset_path = Path(__file__).parent / "ground_truth_dataset.json"

    if not dataset_path.exists():
        print("❌ Ground truth dataset not found")
        return False, ["Ground truth dataset file missing"]

    try:
        with open(dataset_path, 'r') as f:
            data = json.load(f)

        dataset = data["dataset"]
        metadata = data["metadata"]

        # Basic validation
        assert len(dataset) > 0, "Dataset is empty"
        assert "positive_pairs" in metadata, "Missing positive pairs count"
        assert "negative_pairs" in metadata, "Missing negative pairs count"

        positive_count = metadata["positive_pairs"]
        negative_count = metadata["negative_pairs"]

        assert positive_count > 0, "No positive pairs in dataset"
        assert negative_count > 0, "No negative pairs in dataset"

        print(f"✅ Ground truth dataset valid: {len(dataset)} pairs")
        print(f"   Positive pairs: {positive_count}")
        print(f"   Negative pairs: {negative_count}")

        return True, []

    except Exception as e:
        print(f"❌ Ground truth dataset validation failed: {e}")
        return False, [str(e)]

def generate_validation_report():
    """Generate a comprehensive validation report"""
    print("\n📋 Generating validation report...")

    # Run all validations
    imported_components, import_errors = validate_imports()
    functional_components, functional_errors = validate_basic_functionality()
    dataset_valid, dataset_errors = validate_ground_truth_dataset()

    # Create report
    report = {
        "timestamp": "2025-11-12T22:00:00Z",
        "validation_results": {
            "imports": {
                "successful": imported_components,
                "errors": import_errors
            },
            "functionality": {
                "successful": functional_components,
                "errors": functional_errors
            },
            "dataset": {
                "valid": dataset_valid,
                "errors": dataset_errors
            }
        },
        "overall_status": "PASS" if not (import_errors or functional_errors or dataset_errors) else "FAIL",
        "recommendations": []
    }

    # Add recommendations based on results
    if import_errors:
        report["recommendations"].append("Fix import errors for failed components")

    if functional_errors:
        report["recommendations"].append("Debug functionality issues in failed components")

    if dataset_errors:
        report["recommendations"].append("Regenerate or fix ground truth dataset")

    if not any(comp in imported_components for comp in ["scoring_optimization", "training_data"]):
        report["recommendations"].append("Install scikit-learn for ML components: pip install scikit-learn pandas")

    # Save report
    report_path = Path(__file__).parent / "validation_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"✅ Validation report saved to {report_path}")

    # Print summary
    print("\n🎯 VALIDATION SUMMARY:")
    print(f"   Overall Status: {report['overall_status']}")
    print(f"   Components Imported: {len(imported_components)}")
    print(f"   Functional Tests Passed: {len(functional_components)}")
    print(f"   Dataset Valid: {dataset_valid}")

    if report["recommendations"]:
        print("\n💡 RECOMMENDATIONS:")
        for rec in report["recommendations"]:
            print(f"   • {rec}")

    return report

if __name__ == "__main__":
    print("🚀 Starting Clustering Overhaul Validation")
    print("=" * 50)

    report = generate_validation_report()

    print("\n" + "=" * 50)
    if report["overall_status"] == "PASS":
        print("🎉 VALIDATION PASSED! Ready for deployment.")
        sys.exit(0)
    else:
        print("❌ VALIDATION FAILED! Check errors above.")
        sys.exit(1)
