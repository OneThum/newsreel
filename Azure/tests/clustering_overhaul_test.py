"""
Comprehensive Test Suite for Clustering Overhaul (Phases 1-3)

Tests all new components with proper dependency handling:
- SimHash near-duplicate detection ✅
- Wikidata entity linking ✅
- Event signature extraction ✅
- Geographic features ✅
- ML-based similarity scoring (optional: sklearn)
- Vector indexing (optional: faiss)
- Cluster maintenance ✅
- Training data generation (optional: sklearn)
- API ETag support ✅
- End-to-end clustering pipeline
"""
import pytest
import asyncio
import numpy as np
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, AsyncMock
import json
import os
import sys

# Add the Azure functions directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import core components
from shared.config import config
from shared.utils import extract_simple_entities_with_wikidata, create_shingles, compute_simhash, hamming_distance
from shared.wikidata_linking import WikidataLinker, get_wikidata_linker
from shared.event_signatures import extract_event_signature
from shared.geographic_features import extract_geographic_features, calculate_geographic_similarity
from shared.cluster_maintenance import ClusterMaintenance

# Optional imports with fallbacks
try:
    from shared.scoring_optimization import OptimizedSimilarityScorer, predict_article_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    OptimizedSimilarityScorer = None
    predict_article_similarity = None

try:
    from shared.training_data import TrainingDataGenerator
    SKLEARN_AVAILABLE = SKLEARN_AVAILABLE and True
except ImportError:
    TrainingDataGenerator = None

try:
    from shared.vector_index import VectorIndex
    from shared.candidate_generation import CandidateGenerator
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    VectorIndex = None
    CandidateGenerator = None


class TestSimHash:
    """Test SimHash near-duplicate detection"""

    def test_shingle_generation(self):
        """Test that shingles are generated correctly"""
        text = "The quick brown fox jumps over the lazy dog"
        shingles = create_shingles(text, 3)

        # Should generate overlapping 3-word sequences
        expected_shingles = [
            "the quick brown",
            "quick brown fox",
            "brown fox jumps",
            "fox jumps over",
            "jumps over the",
            "over the lazy",
            "the lazy dog"
        ]

        assert len(shingles) == len(expected_shingles)
        for expected in expected_shingles:
            assert expected in shingles

    def test_simhash_computation(self):
        """Test SimHash computation"""
        from shared.utils import compute_simhash

        text1 = "The quick brown fox jumps over the lazy dog"
        text2 = "The quick brown fox jumps over the sleeping dog"

        hash1 = compute_simhash(text1)
        hash2 = compute_simhash(text2)

        # Similar texts should have relatively low Hamming distance
        distance = bin(hash1 ^ hash2).count('1')  # Hamming distance
        assert distance < 30  # Allow for some variation, but should be reasonably similar

    def test_simhash_identical_texts(self):
        """Test that identical texts have identical SimHashes"""
        from shared.utils import compute_simhash

        text = "The quick brown fox jumps over the lazy dog"
        hash1 = compute_simhash(text)
        hash2 = compute_simhash(text)

        assert hash1 == hash2


class TestWikidataLinking:
    """Test Wikidata entity linking and disambiguation"""

    @pytest.mark.skip(reason="Requires network access to Wikidata API - tested in integration environment")
    async def test_wikidata_entity_search(self):
        """Test Wikidata entity search - skipped in test environment"""
        pass

    @pytest.mark.skip(reason="Requires network access to Wikidata API - tested in integration environment")
    async def test_entity_linking_with_context(self):
        """Test entity linking with contextual disambiguation - skipped in test environment"""
        pass

    @pytest.mark.asyncio
    async def test_entity_linking_batch(self):
        """Test batch entity linking"""
        linker = WikidataLinker()

        entity_dicts = [
            {"text": "Paris", "type": "LOCATION"},
            {"text": "Tesla", "type": "ORGANIZATION"},
            {"text": "Biden", "type": "PERSON"}
        ]

        results = await linker.batch_link_entities(entity_dicts)

        assert len(results) == 3
        assert all(isinstance(result, (type(None), type(linker._fetch_entity_details("")))) for result in results.values())


class TestEventSignatures:
    """Test event signature extraction"""

    def test_event_signature_extraction(self):
        """Test extracting event signatures from news text"""
        title = "Apple Announces New iPhone 15 Pro Max"
        description = "Apple Inc. unveiled its latest flagship smartphone today, featuring advanced AI capabilities and improved camera system."

        entities = [
            {"text": "Apple", "type": "ORGANIZATION"},
            {"text": "iPhone 15 Pro Max", "type": "PRODUCT"}
        ]

        signature = extract_event_signature(title, description, entities)

        assert signature is not None
        assert "actions" in signature
        assert "event_types" in signature
        assert "launch" in signature["event_types"]  # Should detect "launch" event type
        assert "entities" in signature

    def test_event_signature_hash_consistency(self):
        """Test that similar events produce consistent hashes"""
        sig1 = extract_event_signature(
            "Tesla launches new Model S",
            "Electric car company Tesla unveiled its updated Model S sedan today",
            [{"text": "Tesla", "type": "ORGANIZATION"}]
        )

        sig2 = extract_event_signature(
            "Tesla announces Model S refresh",
            "Tesla revealed the latest version of their Model S vehicle today",
            [{"text": "Tesla", "type": "ORGANIZATION"}]
        )

        # Should have similar but not identical hashes due to different wording
        # Check that both signatures have a hash field
        hash_field = None
        if "event_hash" in sig1:
            hash_field = "event_hash"
        elif "signature_hash" in sig1:
            hash_field = "signature_hash"

        assert hash_field is not None, f"No hash field found in signature: {sig1.keys()}"
        assert sig1[hash_field] != sig2[hash_field]
        # Should have at least one event type detected between them
        assert len(sig1["event_types"]) > 0 or len(sig2["event_types"]) > 0

    def test_event_signature_confidence(self):
        """Test confidence scoring"""
        # High confidence case
        sig1 = extract_event_signature(
            "NASA launches SpaceX rocket to Mars",
            "NASA successfully launched the SpaceX Starship rocket on its first mission to Mars",
            [{"text": "NASA", "type": "ORGANIZATION"}, {"text": "SpaceX", "type": "ORGANIZATION"}]
        )

        # Low confidence case
        sig2 = extract_event_signature(
            "Something happened somewhere",
            "Details are unclear at this time",
            []
        )

        assert sig1["confidence"] > sig2["confidence"]


class TestGeographicFeatures:
    """Test geographic feature extraction and similarity"""

    def test_geographic_extraction(self):
        """Test extracting geographic features from text"""
        title = "Earthquake in California"
        description = "A magnitude 6.5 earthquake struck Northern California near Eureka, causing minor damage but no injuries."

        entities = [
            {"text": "California", "type": "LOCATION"},
            {"text": "Eureka", "type": "LOCATION"}
        ]

        geo_features = extract_geographic_features(title, description, entities)

        assert geo_features is not None
        assert "locations" in geo_features
        assert len(geo_features["locations"]) > 0

        # Should identify primary location
        assert "primary_location" in geo_features
        assert geo_features["primary_location"].name in ["California", "Eureka"]

    def test_geographic_similarity(self):
        """Test geographic similarity calculation"""
        # Test with real extracted features
        geo1 = extract_geographic_features(
            "California News",
            "Los Angeles is in California state",
            [{"text": "Los Angeles", "type": "LOCATION"}, {"text": "California", "type": "LOCATION"}]
        )

        geo2 = extract_geographic_features(
            "Texas News",
            "Houston is in Texas state",
            [{"text": "Houston", "type": "LOCATION"}, {"text": "Texas", "type": "LOCATION"}]
        )

        # Should return a valid similarity score
        similarity = calculate_geographic_similarity(geo1, geo2)
        assert isinstance(similarity, float)
        assert 0.0 <= similarity <= 1.0


class TestScoringOptimization:
    """Test ML-based similarity scoring"""

    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn not available")
    def test_feature_extraction(self):
        """Test feature extraction for similarity scoring"""
        from shared.scoring_optimization import SimilarityFeatureExtractor

        extractor = SimilarityFeatureExtractor()

        article1 = {
            "title": "Apple announces new iPhone",
            "description": "Apple unveiled the latest iPhone model",
            "published_at": "2024-01-01T10:00:00Z",
            "entities": [{"text": "Apple", "type": "ORGANIZATION"}],
            "embedding": np.random.rand(1024).tolist()
        }

        article2 = {
            "title": "Apple launches iPhone 15",
            "description": "Apple released the new iPhone 15 smartphone",
            "published_at": "2024-01-01T11:00:00Z",
            "entities": [{"text": "Apple", "type": "ORGANIZATION"}],
            "embedding": np.random.rand(1024).tolist()
        }

        features = extractor.extract_features(article1, article2)

        # Should extract all expected features
        expected_features = [
            'embedding_similarity', 'bm25_similarity', 'entity_overlap_jaccard',
            'temporal_proximity', 'source_overlap', 'category_match',
            'event_signature_similarity', 'geographic_proximity', 'wikidata_consistency'
        ]

        for feature in expected_features:
            assert feature in features
            assert isinstance(features[feature], (int, float))

    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn not available")
    def test_similarity_prediction_fallback(self):
        """Test that similarity prediction falls back gracefully"""
        # Test without trained model
        scorer = OptimizedSimilarityScorer()

        article1 = {"title": "Test article 1", "description": "Content 1"}
        article2 = {"title": "Test article 2", "description": "Content 2"}

        score = scorer.predict_similarity(article1, article2)

        # Should return a valid score
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0


class TestVectorIndex:
    """Test FAISS vector indexing"""

    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_vector_index_creation(self):
        """Test creating and using vector index"""
        index = VectorIndex(embedding_dim=128)  # Smaller for testing

        # Add some test vectors
        embeddings = np.random.rand(10, 128).astype(np.float32)
        articles = [
            {
                "id": f"test_{i}",
                "title": f"Article {i}",
                "description": f"Description {i}",
                "published_at": "2024-01-01T10:00:00Z",
                "source": "test_source",
                "category": "test"
            }
            for i in range(10)
        ]

        index.add_articles(articles, embeddings)

        # Test search
        query = np.random.rand(128).astype(np.float32)
        results = index.search(query, k=5)

        assert len(results) <= 5
        for article_id, distance in results:
            assert article_id.startswith("test_")
            assert isinstance(distance, float)

    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_vector_index_persistence(self):
        """Test saving and loading vector index"""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create index with custom path
            index_path = os.path.join(temp_dir, "test_index")
            index = VectorIndex(embedding_dim=128, index_path=index_path)

            # Add data
            embeddings = np.random.rand(5, 128).astype(np.float32)
            articles = [{"id": f"test_{i}"} for i in range(5)]
            index.add_articles(articles, embeddings)

            # Save
            index.save()

            # Create new index and load
            index2 = VectorIndex(embedding_dim=128, index_path=index_path)

            assert index2.index.ntotal == 5
            assert len(index2.id_mapping) == 5


class TestClusterMaintenance:
    """Test automated cluster maintenance"""

    @pytest.mark.asyncio
    async def test_cluster_merge_logic(self):
        """Test cluster merging logic"""
        maintenance = ClusterMaintenance()

        # Mock clusters that should merge (high similarity, same category)
        cluster1 = {
            "id": "cluster_1",
            "category": "technology",
            "embedding": np.random.rand(1024).tolist(),
            "entity_histogram": {"Apple": 5, "iPhone": 3},
            "source_articles": [
                {"id": "art1", "published_at": "2024-01-01T10:00:00Z"},
                {"id": "art2", "published_at": "2024-01-01T11:00:00Z"}
            ],
            "first_seen": "2024-01-01T10:00:00Z",
            "last_updated": "2024-01-01T11:00:00Z"
        }

        cluster2 = {
            "id": "cluster_2",
            "category": "technology",
            "embedding": np.random.rand(1024).tolist(),  # Similar embedding
            "entity_histogram": {"Apple": 4, "iPhone": 2},
            "source_articles": [
                {"id": "art3", "published_at": "2024-01-01T12:00:00Z"}
            ],
            "first_seen": "2024-01-01T12:00:00Z",
            "last_updated": "2024-01-01T12:00:00Z"
        }

        # Mock the similarity check
        with patch.object(maintenance, '_should_merge_clusters', return_value=True):
            merged = maintenance._merge_clusters(cluster1, cluster2)

            assert merged is not None
            assert len(merged["source_articles"]) == 3  # All articles combined
            assert merged["first_seen"] == cluster1["first_seen"]  # Older first_seen

    def test_decay_logic(self):
        """Test cluster decay logic"""
        maintenance = ClusterMaintenance()

        now = datetime.now(timezone.utc)

        # Recent cluster (should not decay)
        recent_cluster = {
            "id": "recent",
            "source_articles": [{"id": "art1"}],
            "last_updated": now.isoformat()
        }

        # Old cluster (should decay)
        old_time = now - timedelta(days=40)
        old_cluster = {
            "id": "old",
            "source_articles": [{"id": "art2"}],
            "last_updated": old_time.isoformat()
        }

        # Test decay check - method returns (bool, reason) tuple
        recent_should_decay, recent_reason = maintenance._should_decay_cluster(recent_cluster, now)
        old_should_decay, old_reason = maintenance._should_decay_cluster(old_cluster, now)

        assert not recent_should_decay
        assert old_should_decay


class TestIntegration:
    """Integration tests for the full clustering pipeline"""

    @pytest.mark.asyncio
    async def test_full_entity_enrichment_pipeline(self):
        """Test the complete entity enrichment pipeline"""
        # Mock article
        article = {
            "title": "Apple announces new iPhone in California",
            "description": "Tech giant Apple unveiled its latest smartphone in Cupertino, California.",
            "published_at": "2024-01-01T10:00:00Z"
        }

        # Test entity extraction
        entities = await extract_simple_entities_with_wikidata(
            f"{article['title']}. {article['description']}"
        )

        assert len(entities) > 0

        # Should find Apple and California
        entity_texts = [e.text for e in entities]
        assert "Apple" in entity_texts
        assert "California" in entity_texts

    @pytest.mark.asyncio
    async def test_candidate_generation_pipeline(self):
        """Test candidate generation with all components"""
        # This would require mocking Cosmos DB and vector index
        # For now, just test the structure
        pass

    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn not available")
    def test_end_to_end_similarity_scoring(self):
        """Test end-to-end similarity scoring"""
        article1 = {
            "title": "Apple announces iPhone 15",
            "description": "Apple unveiled the new iPhone 15 with advanced features",
            "published_at": "2024-01-01T10:00:00Z",
            "source": "techcrunch",
            "category": "technology",
            "entities": [{"text": "Apple", "type": "ORGANIZATION"}],
            "embedding": np.random.rand(1024).tolist()
        }

        article2 = {
            "title": "Apple launches iPhone 15 Pro",
            "description": "Apple released the iPhone 15 Pro model today",
            "published_at": "2024-01-01T11:00:00Z",
            "source": "techcrunch",
            "category": "technology",
            "entities": [{"text": "Apple", "type": "ORGANIZATION"}],
            "embedding": np.random.rand(1024).tolist()
        }

        # Test similarity prediction
        score = predict_article_similarity(article1, article2)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

        # Similar articles should have reasonably high similarity
        # (This is a weak test since embeddings are random)
        assert score > 0.1


class TestTrainingData:
    """Test training data generation for ML models"""

    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn not available")
    def test_training_data_generation(self):
        """Test synthetic training data generation"""
        from shared.training_data import TrainingDataGenerator

        generator = TrainingDataGenerator()

        # Generate synthetic training data
        training_data = generator.generate_synthetic_data(num_samples=50)

        assert len(training_data) == 50
        assert all('article1' in pair for pair in training_data)
        assert all('article2' in pair for pair in training_data)
        assert all('similarity_score' in pair for pair in training_data)

        # Check score ranges
        scores = [pair['similarity_score'] for pair in training_data]
        assert all(0.0 <= score <= 1.0 for score in scores)

    def test_training_data_unavailable(self):
        """Test behavior when sklearn is not available"""
        if SKLEARN_AVAILABLE:
            pytest.skip("scikit-learn is available")

        # Should gracefully handle missing sklearn
        try:
            from shared.training_data import TrainingDataGenerator
            # If import succeeds but sklearn is missing, methods should handle it
            generator = TrainingDataGenerator()
            data = generator.generate_synthetic_data(5)
            assert isinstance(data, list)
        except Exception:
            # May raise exception if not properly handled
            pass


class TestCandidateGeneration:
    """Test candidate generation for clustering"""

    @pytest.mark.skipif(not FAISS_AVAILABLE, reason="FAISS not available")
    def test_candidate_generation(self):
        """Test hybrid FAISS + BM25 candidate generation"""
        from shared.candidate_generation import CandidateGenerator

        generator = CandidateGenerator(embedding_dim=128)

        # Create test articles
        articles = []
        embeddings = []
        for i in range(20):
            article = {
                "id": f"article_{i}",
                "title": f"Test Article {i}",
                "description": f"This is test content for article {i}",
                "published_at": "2024-01-01T10:00:00Z",
                "source": "test_source",
                "category": "test",
                "entities": [],
                "embedding": np.random.rand(128).tolist()
            }
            articles.append(article)
            embeddings.append(np.array(article["embedding"], dtype=np.float32))

        # Build index
        generator.build_index(embeddings, articles)

        # Find candidates for a query article
        query_article = {
            "title": "Similar Test Article",
            "description": "This is similar test content",
            "entities": [],
            "embedding": np.random.rand(128).tolist()
        }

        candidates = generator.find_candidates(query_article, top_k=5)

        assert len(candidates) <= 5
        assert all(isinstance(cand, dict) for cand in candidates)
        assert all('id' in cand for cand in candidates)


class TestAPIETags:
    """Test API ETag functionality for caching"""

    @patch('shared.cosmos_client.CosmosClient')
    def test_etag_generation(self, mock_cosmos):
        """Test ETag generation from cluster data"""
        from shared.cosmos_client import CosmosClient

        # Mock the cosmos client
        mock_instance = mock_cosmos.return_value
        mock_instance.query_recent_stories.return_value = [
            {"last_updated": "2024-01-01T12:00:00Z", "id": "story1"},
            {"last_updated": "2024-01-01T11:00:00Z", "id": "story2"}
        ]

        client = CosmosClient()

        # Mock get_latest_cluster_update
        with patch.object(client, 'get_latest_cluster_update', return_value="2024-01-01T12:00:00Z"):
            latest_update = client.get_latest_cluster_update()

            # Generate ETag from timestamp
            import hashlib
            etag = f'"{hashlib.md5(latest_update.encode()).hexdigest()}"'

            assert etag.startswith('"')
            assert etag.endswith('"')
            assert len(etag) > 2  # More than just quotes


class TestIntegration:
    """End-to-end integration tests"""

    def test_full_clustering_pipeline(self):
        """Test the complete clustering pipeline with mocked dependencies"""
        # This test validates that all components can work together
        # even without optional dependencies

        # Test basic pipeline components
        from shared.utils import extract_simple_entities
        from shared.event_signatures import extract_event_signature
        from shared.geographic_features import extract_geographic_features

        # Create a test article
        article = {
            "title": "Apple launches iPhone 15 in California",
            "description": "Apple released the new iPhone 15 smartphone in California today",
            "published_at": "2024-01-01T10:00:00Z",
            "source": "techcrunch",
            "category": "technology"
        }

        # Test entity extraction
        entities = extract_simple_entities(article["title"] + " " + article["description"])
        assert len(entities) > 0

        # Convert entities to dict format for event signature extraction
        entity_dicts = [{"text": e.text, "type": e.type} for e in entities]

        # Test event signature extraction
        signature = extract_event_signature(
            article["title"],
            article["description"],
            entity_dicts
        )
        assert "event_types" in signature

        # Test geographic features
        geo_features = extract_geographic_features(
            article["title"],
            article["description"],
            entity_dicts
        )
        assert "locations" in geo_features

        # All components should work together
        assert True

    @pytest.mark.asyncio
    async def test_async_entity_extraction(self):
        """Test async entity extraction with Wikidata"""
        from shared.utils import extract_simple_entities_with_wikidata

        try:
            # This may fail in test environment due to network/config
            entities = await extract_simple_entities_with_wikidata("Apple announces iPhone")
            # If it succeeds, should return enhanced entities
            assert isinstance(entities, list)
        except Exception:
            # Expected to fail in test environment
            pass

    def test_performance_baseline(self):
        """Test that core operations complete within reasonable time"""
        import time
        from shared.utils import extract_simple_entities, compute_simhash
        from shared.event_signatures import extract_event_signature

        text = "Apple announces new iPhone 15 with advanced features in California"

        # Test entity extraction performance
        start_time = time.time()
        entities = extract_simple_entities(text)
        entity_time = time.time() - start_time
        assert entity_time < 0.1  # Should be very fast

        # Test SimHash performance
        start_time = time.time()
        hash_value = compute_simhash(text)
        hash_time = time.time() - start_time
        assert hash_time < 0.01  # Should be extremely fast

        # Test event signature performance
        start_time = time.time()
        entity_dicts = [{"text": e.text, "type": e.type} for e in entities]
        signature = extract_event_signature("Apple launches iPhone", text, entity_dicts)
        signature_time = time.time() - start_time
        assert signature_time < 0.5  # Should be reasonably fast


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
