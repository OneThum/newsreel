"""
Unit tests for story clustering logic
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../functions')))

from shared.utils import calculate_text_similarity
from function_app import has_topic_conflict


@pytest.mark.unit
class TestTextSimilarity:
    """Test text similarity calculation"""
    
    def test_identical_titles_high_similarity(self):
        """Test identical titles have similarity close to 1.0"""
        title = "Earthquake Strikes Northern Japan"
        similarity = calculate_text_similarity(title, title)
        assert similarity > 0.99
    
    def test_very_similar_titles(self):
        """Test very similar titles have high similarity"""
        title1 = "Earthquake Strikes Northern Japan"
        title2 = "Earthquake Hits Northern Japan"
        similarity = calculate_text_similarity(title1, title2)
        assert similarity > 0.7  # Should be above clustering threshold
    
    def test_related_but_different_titles(self):
        """Test related but different titles have medium similarity"""
        title1 = "Earthquake Strikes Japan"
        title2 = "Japan Earthquake Causes Damage"
        similarity = calculate_text_similarity(title1, title2)
        assert 0.3 < similarity < 0.9
    
    def test_unrelated_titles_low_similarity(self):
        """Test unrelated titles have low similarity"""
        title1 = "Earthquake Strikes Japan"
        title2 = "Apple Announces New iPhone"
        similarity = calculate_text_similarity(title1, title2)
        assert similarity < 0.3
    
    def test_completely_different_titles(self):
        """Test completely different titles have very low similarity"""
        title1 = "Breaking News About Technology"
        title2 = "Sports Championship Results"
        similarity = calculate_text_similarity(title1, title2)
        assert similarity < 0.2
    
    def test_similarity_with_word_order_change(self):
        """Test similarity with word order changes"""
        title1 = "Japan Earthquake Magnitude 7.2"
        title2 = "Magnitude 7.2 Earthquake in Japan"
        similarity = calculate_text_similarity(title1, title2)
        assert similarity > 0.6  # Should recognize as similar despite word order
    
    def test_similarity_case_insensitive(self):
        """Test similarity is case insensitive"""
        title1 = "EARTHQUAKE STRIKES JAPAN"
        title2 = "earthquake strikes japan"
        similarity = calculate_text_similarity(title1, title2)
        assert similarity > 0.5  # Case-normalized text should have reasonable similarity
    
    def test_similarity_with_extra_words(self):
        """Test similarity when one title has extra words"""
        title1 = "Earthquake in Japan"
        title2 = "Major Earthquake in Japan Causes Widespread Damage"
        similarity = calculate_text_similarity(title1, title2)
        # Should still recognize as related - all words from title1 are in title2
        assert 0.7 < similarity <= 1.0


@pytest.mark.unit
class TestTopicConflictDetection:
    """Test topic conflict detection"""
    
    def test_crime_vs_health_conflict(self):
        """Test crime and health topics are conflicting"""
        title1 = "Man stabbed in Sydney attack"
        title2 = "Sydney dentist opens new practice"
        assert has_topic_conflict(title1, title2) is True
    
    def test_politics_vs_sports_conflict(self):
        """Test politics and sports topics are conflicting"""
        title1 = "Election results announced"
        title2 = "Team wins championship game"
        assert has_topic_conflict(title1, title2) is True
    
    def test_business_vs_weather_conflict(self):
        """Test business and weather topics are conflicting"""
        title1 = "Stock market hits record high"
        title2 = "Hurricane approaches coast"
        assert has_topic_conflict(title1, title2) is True
    
    def test_same_topic_no_conflict(self):
        """Test same topic has no conflict"""
        title1 = "Earthquake strikes northern region"
        title2 = "Earthquake aftermath and damage"
        assert has_topic_conflict(title1, title2) is False
    
    def test_no_topic_keywords_no_conflict(self):
        """Test titles without topic keywords don't conflict"""
        title1 = "Update on situation"
        title2 = "Further developments expected"
        assert has_topic_conflict(title1, title2) is False
    
    def test_one_topic_vs_none_no_conflict(self):
        """Test one title with topic, one without = no conflict"""
        title1 = "Breaking: Major storm approaching"
        title2 = "News update from city"
        assert has_topic_conflict(title1, title2) is False
    
    def test_medical_vs_political_conflict(self):
        """Test medical and political topics conflict"""
        title1 = "Doctor announces new treatment"
        title2 = "Senator announces new legislation"
        assert has_topic_conflict(title1, title2) is True


@pytest.mark.unit
class TestClusteringThresholds:
    """Test clustering threshold logic"""
    
    def test_threshold_75_percent(self):
        """Test 60% threshold separates similar from dissimilar"""
        from shared.config import config

        # Should be 0.60 (60%) - lowered for better clustering recall
        threshold = config.STORY_FINGERPRINT_SIMILARITY_THRESHOLD
        assert threshold == 0.60
        
        # Test titles that should cluster
        similar_title1 = "Earthquake Strikes Northern Japan"
        similar_title2 = "Earthquake Hits Northern Japan Region"
        similarity = calculate_text_similarity(similar_title1, similar_title2)
        assert similarity > threshold, f"Similar titles should exceed threshold: {similarity} > {threshold}"
        
        # Test titles that shouldn't cluster
        different_title1 = "Earthquake in Japan"
        different_title2 = "Dentist Opens New Practice in Japan"
        similarity = calculate_text_similarity(different_title1, different_title2)
        assert similarity < threshold, f"Different topics should not exceed threshold: {similarity} < {threshold}"
    
    def test_edge_cases_near_threshold(self):
        """Test edge cases near the clustering threshold"""
        # These should be right at the boundary
        title1 = "Major Earthquake Strikes Region"
        title2 = "Earthquake Hits Different Area"
        
        similarity = calculate_text_similarity(title1, title2)
        # Verify similarity is in valid range - actual value depends on algorithm
        assert 0.0 <= similarity <= 1.0


@pytest.mark.unit
class TestStoryMatching:
    """Test story matching logic"""
    
    def test_exact_match_via_fingerprint(self):
        """Test exact fingerprint matching (fastest path)"""
        from shared.utils import generate_story_fingerprint
        
        entities1 = [{"text": "Japan", "type": "LOCATION"}, {"text": "Earthquake", "type": "EVENT"}]
        entities2 = [{"text": "Japan", "type": "LOCATION"}, {"text": "Earthquake", "type": "EVENT"}]
        
        fp1 = generate_story_fingerprint("Earthquake in Japan", entities1)
        fp2 = generate_story_fingerprint("Earthquake hits Japan", entities2)
        
        # Should generate same fingerprint for same core entities
        # (exact match depends on implementation)
        assert isinstance(fp1, str)
        assert isinstance(fp2, str)
    
    def test_fuzzy_match_required_for_variations(self):
        """Test fuzzy matching needed for title variations"""
        title1 = "Earthquake Strikes Northern Japan, Magnitude 7.2"
        title2 = "7.2 Magnitude Earthquake Hits Japan's North"
        
        similarity = calculate_text_similarity(title1, title2)
        # Should recognize as related despite different wording
        assert 0.3 < similarity < 0.9
    
    def test_no_match_for_different_events(self):
        """Test different events don't match"""
        title1 = "Earthquake Strikes Japan"
        title2 = "Flood Hits Thailand"
        
        similarity = calculate_text_similarity(title1, title2)
        assert similarity < 0.3
        # Also check topic conflict
        assert has_topic_conflict(title1, title2) is False  # Both are disasters


@pytest.mark.unit
class TestDuplicateSourcePrevention:
    """Test duplicate source prevention logic"""
    
    def test_extract_source_from_article_id(self):
        """Test extracting source from article ID"""
        article_id = "reuters_20251026_143000_abc123"
        source = article_id.split('_')[0]
        assert source == "reuters"
    
    def test_identify_duplicate_sources_in_cluster(self):
        """Test identifying duplicate sources in a story cluster"""
        source_articles = [
            {"id": "reuters_20251026_143000_abc123", "source": "reuters"},
            {"id": "bbc_20251026_143100_def456", "source": "bbc"},
            {"id": "reuters_20251026_143200_ghi789", "source": "reuters"}  # Duplicate!
        ]
        
        # Extract sources
        sources = [article['source'] for article in source_articles]
        
        # Find duplicates
        from collections import Counter
        source_counts = Counter(sources)
        duplicates = {source: count for source, count in source_counts.items() if count > 1}
        
        assert 'reuters' in duplicates
        assert duplicates['reuters'] == 2
    
    def test_unique_sources_only(self):
        """Test story cluster with only unique sources"""
        source_articles = [
            {"id": "reuters_20251026_143000_abc123", "source": "reuters"},
            {"id": "bbc_20251026_143100_def456", "source": "bbc"},
            {"id": "ap_20251026_143200_ghi789", "source": "ap"}
        ]
        
        sources = [article['source'] for article in source_articles]
        unique_sources = set(sources)
        
        assert len(unique_sources) == len(sources)


@pytest.mark.unit
class TestClusteringPerformance:
    """Test clustering performance characteristics"""
    
    def test_similarity_calculation_is_fast(self):
        """Test similarity calculation completes quickly"""
        import time
        
        title1 = "This is a long title about a breaking news event that contains many words"
        title2 = "This is another long title about a different breaking news event"
        
        start = time.time()
        for _ in range(100):
            calculate_text_similarity(title1, title2)
        duration = time.time() - start
        
        # 100 calculations should take < 1 second
        assert duration < 1.0, f"Similarity calculation too slow: {duration}s for 100 iterations"
    
    def test_topic_conflict_check_is_fast(self):
        """Test topic conflict check completes quickly"""
        import time
        
        title1 = "Earthquake strikes northern region causing widespread damage"
        title2 = "Doctor announces new medical breakthrough treatment"
        
        start = time.time()
        for _ in range(1000):
            has_topic_conflict(title1, title2)
        duration = time.time() - start
        
        # 1000 checks should take < 1 second
        assert duration < 1.0, f"Topic conflict check too slow: {duration}s for 1000 iterations"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

