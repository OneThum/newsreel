#!/usr/bin/env python3
"""
Core Functionality Test for Newsreel

Tests the core components that exist in the current codebase.
"""

import sys
import os
from pathlib import Path
import pytest

# Add the Azure directory to path
azure_path = Path(__file__).parent.parent
sys.path.insert(0, str(azure_path))


@pytest.mark.unit
def test_entity_extraction():
    """Test entity extraction functionality"""
    print("🧪 Testing entity extraction...")

    from functions.shared.utils import extract_simple_entities

    # Test basic entity extraction
    text = "Apple announces new iPhone in California"
    entities = extract_simple_entities(text)

    assert len(entities) > 0, "No entities extracted"
    entity_texts = [e.text.lower() for e in entities]
    
    # Check that we found some relevant entities
    assert len(entity_texts) > 0, "Should extract some entities"
    print(f"✅ Basic entity extraction works - found {len(entities)} entities")


@pytest.mark.unit
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


@pytest.mark.unit
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


@pytest.mark.unit
def test_config():
    """Test configuration loading"""
    print("🧪 Testing configuration...")

    from functions.shared.config import config

    # Test basic config attributes that actually exist
    assert hasattr(config, 'COSMOS_CONNECTION_STRING') or hasattr(config, 'RSS_TIMEOUT_SECONDS'), \
        "Missing basic config attributes"
    assert hasattr(config, 'STORY_FINGERPRINT_SIMILARITY_THRESHOLD'), \
        "Missing similarity threshold config"

    print("✅ Configuration loading works")


@pytest.mark.unit
def test_utils_functions():
    """Test utility functions"""
    print("🧪 Testing utility functions...")

    from functions.shared.utils import (
        clean_html,
        generate_article_id,
        generate_story_fingerprint,
        calculate_text_similarity
    )
    from datetime import datetime

    # Test clean_html
    html = "<p>Hello <b>World</b></p>"
    cleaned = clean_html(html)
    assert "Hello" in cleaned
    assert "World" in cleaned
    assert "<p>" not in cleaned
    print("✅ clean_html works")

    # Test generate_article_id
    article_id = generate_article_id("source", "https://example.com/article", datetime.now())
    assert isinstance(article_id, str)
    assert len(article_id) > 0
    print("✅ generate_article_id works")

    # Test generate_story_fingerprint
    fingerprint = generate_story_fingerprint("Test title", [{"text": "Test", "type": "ENTITY"}])
    assert isinstance(fingerprint, str)
    assert len(fingerprint) > 0
    print("✅ generate_story_fingerprint works")

    # Test calculate_text_similarity
    similarity = calculate_text_similarity("Hello World", "Hello World")
    assert similarity > 0.9
    similarity2 = calculate_text_similarity("Hello World", "Goodbye Moon")
    assert similarity2 < similarity
    print("✅ calculate_text_similarity works")


@pytest.mark.unit
def test_semantic_clustering():
    """Test semantic clustering functions"""
    print("🧪 Testing semantic clustering...")

    from functions.shared.semantic_clustering import (
        cosine_similarity,
        generate_legacy_fingerprint,
        compute_story_embedding
    )

    # Test cosine_similarity
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    vec3 = [0.0, 1.0, 0.0]
    
    sim_same = cosine_similarity(vec1, vec2)
    sim_diff = cosine_similarity(vec1, vec3)
    
    assert abs(sim_same - 1.0) < 0.001, "Same vectors should have similarity 1.0"
    assert abs(sim_diff) < 0.001, "Orthogonal vectors should have similarity 0.0"
    print("✅ cosine_similarity works")

    # Test generate_legacy_fingerprint
    fp1 = generate_legacy_fingerprint("Test Title")
    fp2 = generate_legacy_fingerprint("Test Title")
    fp3 = generate_legacy_fingerprint("Different Title")
    
    assert fp1 == fp2, "Same input should produce same fingerprint"
    assert fp1 != fp3, "Different input should produce different fingerprint"
    print("✅ generate_legacy_fingerprint works")

    # Test compute_story_embedding with no embeddings
    result = compute_story_embedding([])
    assert result is None, "Empty list should return None"
    print("✅ compute_story_embedding handles empty input")


@pytest.mark.unit
def test_models():
    """Test Pydantic models"""
    print("🧪 Testing models...")

    from functions.shared.models import RawArticle, StoryCluster, StoryStatus
    from datetime import datetime

    # Test StoryStatus enum
    assert StoryStatus.NEW == "NEW"
    assert StoryStatus.DEVELOPING == "DEVELOPING"
    assert StoryStatus.VERIFIED == "VERIFIED"
    print("✅ StoryStatus enum works")

    # Test RawArticle model
    article = RawArticle(
        id="test_article_123",
        source="test_source",
        source_url="https://example.com/rss",
        source_tier=1,
        article_url="https://example.com/article",
        title="Test Article",
        description="Test description",
        published_at=datetime.now(),
        fetched_at=datetime.now(),
        updated_at=datetime.now(),
        published_date="2025-01-01",
        content="Test content",
        author="Test Author",
        entities=[],
        category="test",
        tags=[],
        language="en",
        story_fingerprint="test_fp"
    )
    assert article.id == "test_article_123"
    print("✅ RawArticle model works")


def run_all_tests():
    """Run all core functionality tests"""
    print("🚀 Running Core Functionality Tests")
    print("=" * 50)

    tests = [
        ("Configuration", test_config),
        ("Entity Extraction", test_entity_extraction),
        ("Event Signatures", test_event_signatures),
        ("Cluster Maintenance", test_cluster_maintenance),
        ("Utility Functions", test_utils_functions),
        ("Semantic Clustering", test_semantic_clustering),
        ("Models", test_models),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running {test_name}...")
            test_func()
            results.append((test_name, "PASS"))
            print(f"✅ {test_name} PASSED")
        except Exception as e:
            results.append((test_name, "FAIL"))
            print(f"❌ {test_name} FAILED: {e}")

    # Summary
    print("\n" + "=" * 50)
    print("🎯 TEST RESULTS SUMMARY")

    passed = sum(1 for _, status in results if status == "PASS")
    failed = sum(1 for _, status in results if status == "FAIL")

    for test_name, status in results:
        status_icon = "✅" if status == "PASS" else "❌"
        print(f"   {status_icon} {test_name}: {status}")

    print(f"\n📊 SUMMARY: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 CORE FUNCTIONALITY TESTS PASSED!")
        return 0
    else:
        print("❌ Some tests failed. Check output above.")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
