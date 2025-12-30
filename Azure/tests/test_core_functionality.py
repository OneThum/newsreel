#!/usr/bin/env python3
"""
Core Functionality Test for Clustering Overhaul

Tests the core components that don't require optional dependencies like faiss/sklearn.
"""

import sys
import os
from pathlib import Path

# Add the Azure directory to path
azure_path = Path(__file__).parent.parent
sys.path.insert(0, str(azure_path))

async def test_entity_extraction():
    """Test entity extraction functionality"""
    print("🧪 Testing entity extraction...")

    from functions.shared.utils import extract_simple_entities, extract_simple_entities_with_wikidata

    # Test basic entity extraction
    text = "Apple announces new iPhone in California"
    entities = extract_simple_entities(text)

    assert len(entities) > 0, "No entities extracted"
    assert any(e.text.lower() == "apple" for e in entities), "Apple not found in entities"
    assert any(e.text.lower() == "california" for e in entities), "California not found in entities"

    print("✅ Basic entity extraction works")

    # Test enhanced entity extraction (may fail without Wikidata)
    try:
        entities_enhanced = await extract_simple_entities_with_wikidata(text)
        print("✅ Enhanced entity extraction works")
        return True
    except Exception as e:
        print(f"⚠️ Enhanced entity extraction failed (expected): {e}")
        return False

def test_event_signatures():
    """Test event signature extraction"""
    print("🧪 Testing event signatures...")

    from functions.shared.event_signatures import extract_event_signature

    signature = extract_event_signature(
        "Apple launches iPhone",
        "Apple released the new iPhone model with advanced features",
        [{"text": "Apple", "type": "ORGANIZATION"}]
    )

    assert "event_types" in signature, "Missing event_types in signature"
    assert len(signature["event_types"]) > 0, "No event types extracted"
    assert "confidence" in signature, "Missing confidence score"
    assert signature["confidence"] > 0, "Confidence should be positive"

    print("✅ Event signature extraction works")
    return True

def test_geographic_features():
    """Test geographic feature extraction"""
    print("🧪 Testing geographic features...")

    from functions.shared.geographic_features import extract_geographic_features, calculate_geographic_similarity

    geo_features = extract_geographic_features(
        "Earthquake in California",
        "A magnitude 6.5 earthquake struck Northern California",
        [{"text": "California", "type": "LOCATION"}]
    )

    assert "locations" in geo_features, "Missing locations in geo features"
    assert len(geo_features["locations"]) > 0, "No locations extracted"

    # Test similarity calculation with proper structure
    # Create a simple geo2 structure that matches geo1's format
    from functions.shared.geographic_features import GeographicLocation

    geo2 = {
        "locations": [GeographicLocation("Texas", 31.9686, -99.9018, "state")],
        "primary_location": GeographicLocation("Texas", 31.9686, -99.9018, "state"),
        "location_hierarchy": {},
        "regional_context": "North America",
        "geographic_scope": "regional"
    }

    similarity = calculate_geographic_similarity(geo_features, geo2)
    assert isinstance(similarity, float), "Similarity should be a float"
    assert 0 <= similarity <= 1, "Similarity should be between 0 and 1"

    print("✅ Geographic feature extraction works")
    return True

def test_cluster_maintenance():
    """Test cluster maintenance logic"""
    print("🧪 Testing cluster maintenance...")

    from functions.shared.cluster_maintenance import ClusterMaintenance

    maintenance = ClusterMaintenance()

    # Test basic initialization
    assert hasattr(maintenance, '_merge_clusters'), "Missing merge method"
    assert hasattr(maintenance, '_split_cluster'), "Missing split method"
    assert hasattr(maintenance, 'perform_maintenance'), "Missing maintenance method"

    print("✅ Cluster maintenance initialization works")
    return True

def test_config():
    """Test configuration loading"""
    print("🧪 Testing configuration...")

    from functions.shared.config import config

    # Test basic config attributes
    assert hasattr(config, 'EMBEDDINGS_MODEL'), "Missing embeddings model config"
    assert hasattr(config, 'WIKIDATA_LINKING_ENABLED'), "Missing Wikidata config"
    assert hasattr(config, 'SCORING_OPTIMIZATION_ENABLED'), "Missing scoring config"

    print("✅ Configuration loading works")
    return True

def test_simhash():
    """Test SimHash functionality"""
    print("🧪 Testing SimHash...")

    from functions.shared.utils import create_shingles, compute_simhash, hamming_distance

    # Test shingle creation
    text = "The quick brown fox jumps over the lazy dog"
    shingles = create_shingles(text, 3)  # Use positional argument
    assert len(shingles) > 0, "No shingles created"
    assert all(len(s.split()) == 3 for s in shingles), "Incorrect shingle size"

    # Test SimHash computation
    hash1 = compute_simhash(text)
    hash2 = compute_simhash(text)  # Same text
    hash3 = compute_simhash("The fast brown fox leaps over the lazy dog")  # Similar text

    assert hash1 == hash2, "Identical texts should have identical hashes"
    assert isinstance(hash1, int), "Hash should be an integer"

    # Test Hamming distance
    distance_identical = hamming_distance(hash1, hash2)
    distance_similar = hamming_distance(hash1, hash3)

    assert distance_identical == 0, "Identical hashes should have distance 0"
    assert distance_similar > 0, "Similar texts should have some distance difference"

    print("✅ SimHash functionality works")
    return True

def run_all_tests():
    """Run all core functionality tests"""
    print("🚀 Running Core Functionality Tests")
    print("=" * 50)

    tests = [
        ("Configuration", test_config),
        ("Entity Extraction", test_entity_extraction),
        ("Event Signatures", test_event_signatures),
        ("Geographic Features", test_geographic_features),
        ("SimHash", test_simhash),
        ("Cluster Maintenance", test_cluster_maintenance),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running {test_name}...")
            if test_name == "Entity Extraction":
                # Handle async test
                import asyncio
                success = asyncio.run(test_func())
            else:
                success = test_func()
            if success:
                results.append((test_name, "PASS"))
                print(f"✅ {test_name} PASSED")
            else:
                results.append((test_name, "PARTIAL"))
                print(f"⚠️ {test_name} PARTIAL")
        except Exception as e:
            results.append((test_name, "FAIL"))
            print(f"❌ {test_name} FAILED: {e}")

    # Summary
    print("\n" + "=" * 50)
    print("🎯 TEST RESULTS SUMMARY")

    passed = sum(1 for _, status in results if status == "PASS")
    partial = sum(1 for _, status in results if status == "PARTIAL")
    failed = sum(1 for _, status in results if status == "FAIL")

    for test_name, status in results:
        status_icon = "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
        print(f"   {status_icon} {test_name}: {status}")

    print(f"\n📊 SUMMARY: {passed} passed, {partial} partial, {failed} failed")

    if failed == 0 and partial <= 1:  # Allow 1 partial for enhanced entity extraction
        print("🎉 CORE FUNCTIONALITY TESTS PASSED!")
        return 0
    else:
        print("❌ Some tests failed. Check output above.")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
