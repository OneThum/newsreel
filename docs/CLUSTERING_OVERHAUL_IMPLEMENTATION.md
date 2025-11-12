# Newsreel Story Clustering System Overhaul
## Time-Aware, Hybrid Embedding Pipeline - Implementation & Progress Tracker

**Status:** 🟡 PHASE 1 IN PROGRESS
**Last Updated:** 2025-11-12
**Implementation Phase:** Phase 1: Foundation & Quick Wins

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Current System Analysis](#current-system-analysis)
3. [Architecture Overview](#architecture-overview)
4. [Implementation Phases](#implementation-phases)
5. [Component Specifications](#component-specifications)
6. [Progress Tracking](#progress-tracking)
7. [Testing & Validation](#testing--validation)
8. [Rollback Strategy](#rollback-strategy)
9. [Success Metrics](#success-metrics)

---

## Executive Summary

### The Problem
The current MD5 fingerprinting clustering system is fundamentally brittle and failing to meet production needs:

**Current Metrics (Unacceptable):**
- ❌ **New stories/day**: ~1-5 (should be 50-100)
- ❌ **Duplicate rate**: 15-20% (should be <5%)
- ❌ **False positives**: Stories like "Sydney dentist" clustering with "Sydney stabbing"
- ❌ **Scalability**: O(n) performance, struggles with 100+ feeds
- ❌ **Brittleness**: MD5 fingerprinting misses semantic matches

**Current Implementation ([function_app.py](../Azure/functions/function_app.py), [utils.py](../Azure/functions/shared/utils.py)):**
```python
def generate_story_fingerprint(title: str, entities: List[Entity]) -> str:
    # Takes 6 words + 3 entities, creates MD5 hash
    # Problem: Semantic variations produce different hashes
    return hashlib.md5(combined.encode()).hexdigest()[:8]
```

### The Solution
Semantic embedding-based clustering with hybrid retrieval, time-awareness, and adaptive thresholds.

**Target Metrics (Achievable):**
- ✅ **New stories/day**: 50-100
- ✅ **Duplicate rate**: <5%
- ✅ **Accuracy**: 90%+ clustering precision
- ✅ **Latency**: <200ms P95
- ✅ **Scale**: Handle 100+ feeds without degradation

**Technology Stack:**
- **Embeddings**: SentenceTransformers (`multilingual-e5-large`)
- **Vector Search**: FAISS (Approximate Nearest Neighbor)
- **Deduplication**: SimHash for near-duplicate detection
- **Entity Recognition**: spaCy with Wikidata linking
- **Infrastructure**: Azure Functions + Container Instances + Cosmos DB

---

## Current System Analysis

### Architecture Diagram (Current)
```
┌─────────────┐
│  RSS Feeds  │ (100+ feeds, 5min polling)
└──────┬──────┘
       │
       v
┌─────────────────────┐
│ Ingestion Function  │ (Azure Function, HTTP Timer)
│ - Parse RSS         │
│ - Extract entities  │
│ - MD5 fingerprint   │
└──────┬──────────────┘
       │
       v
┌───────────────────────┐
│  Cosmos DB            │
│  - raw_articles       │ (partition by date)
│  - story_clusters     │ (partition by category)
└──────┬────────────────┘
       │
       v
┌─────────────────────────┐
│ Clustering Function     │ (Cosmos Change Feed)
│ - Compare fingerprints  │ O(n) - SLOW!
│ - calculate_text_sim()  │ BRITTLE!
└──────┬──────────────────┘
       │
       v
┌──────────────┐
│  API/iOS     │
└──────────────┘
```

### Current Clustering Logic
**File:** [Azure/functions/function_app.py](../Azure/functions/function_app.py)

**Problem Areas:**
1. **Fingerprint matching only** (lines 501, 163-241 in utils.py):
   - Uses MD5 hash of 6 words + 3 entities
   - Semantic variations = different fingerprints = separate stories
   - Example: "President announces aid" vs "President unveils aid package" = DIFFERENT hashes

2. **Text similarity fallback** (lines 283-350 in utils.py):
   - `calculate_text_similarity()` uses Jaccard + keyword matching
   - Threshold: 50% (config line 48)
   - Still string-based, misses semantic similarity

3. **No time awareness**:
   - All articles in category compared equally
   - No time-based windowing or decay

4. **No deduplication**:
   - Syndicated articles (AP, Reuters wire) create duplicates
   - Same story from different outlets = separate clusters

5. **Entity extraction is primitive** (lines 250-280 in utils.py):
   - Capitalized words only
   - No entity linking or disambiguation
   - Can't distinguish "Paris, France" from "Paris Hilton"

### Files to Modify/Replace
| File | Current Size | Status | Action |
|------|-------------|--------|--------|
| `Azure/functions/function_app.py` | ~25K tokens | ⚠️ Core clustering logic | Refactor clustering section |
| `Azure/functions/shared/utils.py` | 608 lines | ❌ Replace fingerprinting | Complete overhaul |
| `Azure/functions/shared/models.py` | 294 lines | ⚠️ Add embedding fields | Extend models |
| `Azure/functions/shared/config.py` | 85 lines | ⚠️ Add new config | Add embedding settings |
| `Azure/api/app/routers/stories.py` | 567 lines | ✅ Minimal changes | Add ETag support |

---

## Architecture Overview

### New Architecture Diagram
```
┌─────────────┐
│  RSS Feeds  │ (100+ feeds, ETag-aware polling)
└──────┬──────┘
       │
       v
┌──────────────────────────┐
│ Ingestion Function       │
│ 1. Parse RSS             │
│ 2. Normalize             │
│ 3. Language detection    │
│ 4. Spam filter (SimHash) │
└──────┬───────────────────┘
       │
       v
┌────────────────────────────┐
│ Enrichment Function        │
│ 1. NER (spaCy)             │
│ 2. Entity linking (Wikidata)│
│ 3. Event signature         │
│ 4. Generate embedding      │
└──────┬─────────────────────┘
       │
       v
┌──────────────────────────────┐
│  Cosmos DB                   │
│  - raw_articles (+ embedding)│
│  - story_clusters (enhanced) │
│  - entity_index              │
└──────┬───────────────────────┘
       │
       v
┌────────────────────────────────────┐
│ Hybrid Clustering Function         │
│ 1. Candidate generation            │
│    a. FAISS ANN search (semantic)  │ O(log n) - FAST!
│    b. BM25 search (lexical)        │
│    c. Time window filter           │
│ 2. Multi-factor scoring            │
│    - Cosine similarity (55%)       │
│    - Entity overlap (20%)          │
│    - Title BM25 (10%)              │
│    - Time decay (10%)              │
│    - Geographic (5%)               │
│ 3. Adaptive threshold              │
│ 4. Cluster assignment/creation     │
└──────┬─────────────────────────────┘
       │
       v
┌────────────────────────┐
│ Cluster Maintenance    │ (Hourly job)
│ - Merge similar        │
│ - Split divergent      │
│ - Decay old            │
└──────┬─────────────────┘
       │
       v
┌──────────────────┐
│  API (+ ETags)   │
└──────┬───────────┘
       │
       v
┌──────────────┐
│  iOS App     │
└──────────────┘
```

### Data Flow

**Article Lifecycle:**
```
RSS Entry → Normalization → Deduplication → Enrichment → Embedding →
Candidate Generation → Scoring → Assignment → Summary → API
```

**Timing:**
- Ingestion: Every 5 minutes
- Enrichment: Triggered by change feed (< 5s latency)
- Clustering: Triggered by enrichment completion (< 1s latency)
- Maintenance: Hourly

---

## Implementation Phases

### Phase 1: Foundation & Quick Wins (Week 1)
**Status:** ✅ COMPLETED
**Duration:** 3-5 days
**Goal:** Immediate improvements without architectural changes

#### Components
- [x] **1.1** SimHash near-duplicate detection ✅ 2025-11-12
- [x] **1.2** Time-window filtering (72-hour windows) ✅ 2025-11-12
- [x] **1.3** Adaptive thresholds based on article age ✅ 2025-11-12
- [x] **1.4** Enable all RSS feeds (`RSS_USE_ALL_FEEDS=true`) ✅ 2025-11-12
- [ ] **1.5** iOS ETag caching support
- [ ] **1.6** Basic entity linking (string matching)

**Expected Impact:** 50% reduction in duplicates, 2x more unique stories

---

### Phase 2: Semantic Embeddings (Week 2)
**Status:** 🟡 IN PROGRESS
**Duration:** 5-7 days
**Goal:** Replace fingerprinting with semantic embeddings

#### Components
- [x] **2.1** Deploy SentenceTransformers model ✅ 2025-11-12
- [x] **2.2** Build FAISS vector index ✅ 2025-11-12
- [x] **2.3** Implement hybrid search (FAISS + BM25) ✅ 2025-11-12
- [ ] **2.4** Create embedding pipeline
- [ ] **2.5** A/B test vs. old system
- [ ] **2.6** Cutover to new system

**Expected Impact:** 80% better clustering accuracy

---

### Phase 3: Advanced Features (Week 3-4)
**Status:** ⬜ NOT STARTED
**Duration:** 10-14 days
**Goal:** Production-ready with full feature set

#### Components
- [ ] **3.1** Event signature extraction
- [ ] **3.2** Geographic features
- [ ] **3.3** Cluster maintenance (merge/split/decay)
- [ ] **3.4** Wikidata entity linking
- [ ] **3.5** Scoring model optimization
- [ ] **3.6** Upgrade to multilingual model

**Expected Impact:** 95% accuracy, <5% duplicates, 100+ feeds

---

## Component Specifications

### Component 1: Normalization Pipeline
**Status:** ⬜ NOT STARTED
**Files:** `Azure/functions/function_app.py` (RSS ingestion section)
**Dependencies:** None
**Priority:** P0 (Critical)

#### Specification
```python
def normalize_article(article: Dict[str, Any]) -> RawArticle:
    """
    Normalize article for clustering

    Steps:
    1. Language detection (langdetect)
    2. Translation if needed (optional - can use multilingual embeddings)
    3. Clean and standardize text
    4. Extract core fields
    5. Store in Cosmos DB
    """
    # Language detection
    language = langdetect.detect(article['title'] + article.get('description', ''))

    # For Phase 2+: Translation for non-English
    if language != 'en':
        # Option A: Translate to English for English-only model
        # article['text_en'] = translate_to_english(article['title'], article['description'])

        # Option B (RECOMMENDED): Use multilingual embedding model
        # No translation needed - model handles multiple languages
        pass

    # Extract core fields
    normalized = {
        'publish_datetime': parse_datetime(article['pub_date']),
        'source_domain': extract_domain(article['url']),
        'clean_text': strip_boilerplate(article['content']),
        'language': language,
    }

    return normalized
```

#### Implementation Checklist
- [ ] Add language detection library (`pip install langdetect`)
- [ ] Implement `parse_datetime()` with timezone awareness
- [ ] Implement `strip_boilerplate()` for content cleaning
- [ ] Update `process_feed_entry()` in function_app.py
- [ ] Add language field to RawArticle model
- [ ] Test with multilingual RSS feeds
- [ ] Validate datetime parsing across timezones

#### Testing
- [ ] Unit test: Language detection accuracy (>95% on test set)
- [ ] Unit test: Datetime parsing for various RSS date formats
- [ ] Integration test: End-to-end normalization pipeline
- [ ] Edge case: Articles without publish dates
- [ ] Edge case: Non-UTF8 encodings

---

### Component 2: Near-Duplicate Filtering (SimHash)
**Status:** ✅ COMPLETED
**Files:** `Azure/functions/shared/utils.py` (new functions)
**Dependencies:** Component 1
**Priority:** P0 (Critical - Phase 1)

#### Specification
```python
def detect_duplicates(article: RawArticle) -> Tuple[bool, Optional[str]]:
    """
    Two-stage deduplication:
    1. Exact match via SHA1 hash
    2. Near-duplicate via SimHash

    Returns:
        (is_duplicate, duplicate_type)
        duplicate_type: 'exact_duplicate' | 'syndication_duplicate' | None
    """
    # Stage 1: Exact match
    exact_hash = hashlib.sha1(
        normalize_text(article.title).encode() +
        article.source_domain.encode()
    ).hexdigest()

    if exact_hash in recent_hashes:  # recent_hashes = Redis or Cosmos cache
        return True, 'exact_duplicate'

    # Stage 2: SimHash for near-duplicates
    shingles = create_shingles(article.title + article.description, n=3)
    simhash = compute_simhash(shingles)

    # Check against recent simhashes (last 7 days)
    for existing_hash, article_id in recent_simhashes:
        hamming_dist = hamming_distance(simhash, existing_hash)
        if hamming_dist <= 3:  # Threshold: 3 bits difference
            return True, 'syndication_duplicate'

    # Store hashes for future comparisons
    store_hashes(exact_hash, simhash, article.id)

    return False, None

def create_shingles(text: str, n: int = 3) -> List[str]:
    """Create n-grams (shingles) from text"""
    words = text.lower().split()
    return [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]

def compute_simhash(shingles: List[str], bits: int = 64) -> int:
    """Compute SimHash fingerprint"""
    v = [0] * bits

    for shingle in shingles:
        h = int(hashlib.md5(shingle.encode()).hexdigest(), 16)
        for i in range(bits):
            if h & (1 << i):
                v[i] += 1
            else:
                v[i] -= 1

    fingerprint = 0
    for i in range(bits):
        if v[i] > 0:
            fingerprint |= (1 << i)

    return fingerprint

def hamming_distance(hash1: int, hash2: int) -> int:
    """Calculate Hamming distance between two hashes"""
    x = hash1 ^ hash2
    return bin(x).count('1')
```

#### Implementation Checklist
- [x] Implement `create_shingles()` function ✅ 2025-11-12
- [x] Implement `compute_simhash()` function ✅ 2025-11-12
- [x] Implement `hamming_distance()` function ✅ 2025-11-12
- [x] Implement `detect_duplicates()` function (placeholder) ✅ 2025-11-12
- [ ] Add hash storage to Cosmos DB (or Redis cache)
- [ ] Add 7-day TTL for hash records
- [ ] Integrate into ingestion pipeline (function_app.py)
- [ ] Add duplicate_of field to RawArticle model
- [ ] Add logging for duplicate detection

#### Testing
- [ ] Unit test: SimHash computation correctness
- [ ] Unit test: Hamming distance calculation
- [ ] Integration test: Detect exact duplicates
- [ ] Integration test: Detect syndicated articles (AP, Reuters wire)
- [ ] Performance test: Hash lookup latency (<10ms)
- [ ] Edge case: Empty or very short titles

#### Success Criteria
- ✅ Detects >95% of exact duplicates
- ✅ Detects >90% of syndicated content
- ✅ False positive rate <1%
- ✅ Latency <10ms per article

---

### Component 3: Named Entity Recognition & Linking
**Status:** ⬜ NOT STARTED
**Files:** `Azure/functions/shared/entity_extraction.py` (new file)
**Dependencies:** Component 1
**Priority:** P1 (High - Phase 2)

#### Specification
```python
# Using spaCy for NER
import spacy
from typing import List, Dict, Any

class EntityExtractor:
    def __init__(self):
        # Load spaCy model (en_core_web_lg or multilingual)
        self.nlp = spacy.load("en_core_web_lg")

        # Optional: Entity linker for Wikidata
        self.entity_linker = WikidataLinker()  # Phase 3

    def enrich_article(self, article: RawArticle) -> RawArticle:
        """
        Extract and link named entities

        Entities extracted:
        - PERSON (people)
        - ORG (organizations, companies)
        - LOC (locations, countries, cities)
        - GPE (geopolitical entities)
        - EVENT (optional - Phase 3)
        """
        # Process text with spaCy
        doc = self.nlp(article.clean_text[:5000])  # Limit to 5000 chars

        entities = []
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG', 'LOC', 'GPE']:
                entity_data = {
                    'text': ent.text,
                    'type': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'confidence': self._calculate_confidence(ent)
                }

                # Phase 3: Link to Wikidata
                # qid = self.entity_linker.link(ent.text, ent.label_)
                # if qid:
                #     entity_data['qid'] = qid

                entities.append(entity_data)

        # Sort by salience (position in text + frequency)
        entities = self._rank_entities(entities, article.title)

        # Take top 10
        article.entities = entities[:10]

        return article

    def _calculate_confidence(self, entity) -> float:
        """Calculate entity extraction confidence"""
        # Simple confidence based on entity length and capitalization
        score = 0.5

        # Longer entities are more reliable
        if len(entity.text.split()) > 1:
            score += 0.2

        # All capitalized = higher confidence
        if entity.text.isupper():
            score += 0.1

        # In title = higher confidence
        # (checked in _rank_entities)

        return min(score, 1.0)

    def _rank_entities(self, entities: List[Dict], title: str) -> List[Dict]:
        """Rank entities by salience"""
        for ent in entities:
            salience = 0.0

            # In title = very important
            if ent['text'].lower() in title.lower():
                salience += 1.0

            # Early in text = more important
            position_score = 1.0 - (ent['start'] / 5000)
            salience += position_score * 0.5

            # Confidence
            salience += ent.get('confidence', 0.5) * 0.3

            ent['salience'] = salience

        return sorted(entities, key=lambda e: e['salience'], reverse=True)
```

#### Implementation Checklist
- [ ] Install spaCy: `pip install spacy`
- [ ] Download model: `python -m spacy download en_core_web_lg`
- [ ] Create `entity_extraction.py` file
- [ ] Implement `EntityExtractor` class
- [ ] Integrate into enrichment function
- [ ] Add entities field to RawArticle model (already exists)
- [ ] Test entity extraction accuracy
- [ ] Optimize for Azure Functions cold start

#### Testing
- [ ] Unit test: Entity extraction on known articles
- [ ] Accuracy test: >85% precision/recall on test set
- [ ] Performance test: <500ms per article
- [ ] Edge case: Non-English text
- [ ] Edge case: Very short articles

---

### Component 4: Embedding Generation
**Status:** ⬜ NOT STARTED
**Files:** `Azure/functions/shared/embeddings.py` (new file)
**Dependencies:** Component 3
**Priority:** P0 (Critical - Phase 2)

#### Specification
```python
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List

class ArticleEmbedder:
    def __init__(self):
        # Phase 2: Start with English-only model (small, fast)
        # self.model = SentenceTransformer('all-MiniLM-L6-v2')  # 80MB, 384D

        # Phase 3: Upgrade to multilingual (larger, better)
        self.model = SentenceTransformer('intfloat/multilingual-e5-large')  # 2GB, 1024D

        self.embedding_dim = self.model.get_sentence_embedding_dimension()

    def embed_article(self, article: RawArticle) -> np.ndarray:
        """
        Generate semantic embedding for article

        Returns:
            numpy array of shape (embedding_dim,)
        """
        # Combine title + lead for context (title weighted higher)
        text = f"{article.title}. {article.description[:300]}"

        # Generate base embedding
        base_embedding = self.model.encode(
            text,
            normalize_embeddings=True  # L2 normalization for cosine similarity
        )

        # Optional: Entity-aware enhancement
        if article.entities:
            entity_text = ' '.join([e['text'] for e in article.entities[:5]])
            entity_embedding = self.model.encode(
                entity_text,
                normalize_embeddings=True
            )

            # Weighted combination (70% content, 30% entities)
            final_embedding = 0.7 * base_embedding + 0.3 * entity_embedding

            # Re-normalize
            final_embedding = final_embedding / np.linalg.norm(final_embedding)
        else:
            final_embedding = base_embedding

        return final_embedding

    def batch_embed(self, articles: List[RawArticle], batch_size: int = 32) -> np.ndarray:
        """Batch embedding for efficiency"""
        texts = [f"{a.title}. {a.description[:300]}" for a in articles]

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False
        )

        return embeddings
```

#### Deployment Strategy

**Option A: Azure Container Instance (Recommended)**
```dockerfile
# Dockerfile
FROM python:3.11-slim

RUN pip install sentence-transformers torch

# Download model at build time (not runtime)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/multilingual-e5-large')"

COPY embeddings_service.py /app/
WORKDIR /app

EXPOSE 8080
CMD ["python", "embeddings_service.py"]
```

**Option B: Azure Functions with Custom Container**
- Package model in container image
- Use Premium plan for larger memory

**Option C: Azure ML Managed Endpoint**
- Deploy as managed inference endpoint
- Auto-scaling

#### Implementation Checklist
- [ ] Create `embeddings.py` file
- [ ] Implement `ArticleEmbedder` class
- [ ] Test locally with sample articles
- [ ] Create Dockerfile for model service
- [ ] Deploy to Azure Container Instance
- [ ] Add API endpoint for embedding generation
- [ ] Integrate with enrichment pipeline
- [ ] Add embedding field to RawArticle model
- [ ] Monitor memory usage and cold start times

#### Testing
- [ ] Unit test: Embedding generation correctness
- [ ] Performance test: Latency per article (<200ms)
- [ ] Performance test: Batch throughput (>100 articles/sec)
- [ ] Memory test: Container memory usage (<4GB)
- [ ] Integration test: End-to-end embedding pipeline

#### Success Criteria
- ✅ Embedding generation <200ms per article
- ✅ Batch processing >100 articles/sec
- ✅ Memory usage <4GB
- ✅ 99.9% uptime

---

### Component 5: FAISS Vector Index
**Status:** ⬜ NOT STARTED
**Files:** `Azure/functions/shared/vector_index.py` (new file)
**Dependencies:** Component 4
**Priority:** P0 (Critical - Phase 2)

#### Specification
```python
import faiss
import numpy as np
from typing import List, Tuple
from datetime import datetime, timedelta

class VectorIndex:
    def __init__(self, embedding_dim: int = 1024):
        """
        FAISS index for fast ANN search

        Index types:
        - IndexFlatL2: Exact search, good for <100k vectors
        - IndexIVFFlat: Approximate search, good for 100k-1M vectors
        - IndexHNSW: Graph-based, good for >1M vectors
        """
        self.embedding_dim = embedding_dim

        # Start with exact search (Phase 2)
        self.index = faiss.IndexFlatL2(embedding_dim)

        # Phase 3: Upgrade to approximate search
        # quantizer = faiss.IndexFlatL2(embedding_dim)
        # self.index = faiss.IndexIVFFlat(quantizer, embedding_dim, 100)  # 100 clusters

        # Map FAISS ID -> Article ID
        self.id_mapping: List[str] = []

        # Metadata for filtering
        self.metadata: Dict[int, Dict] = {}  # faiss_id -> {publish_datetime, category}

    def add_articles(self, articles: List[RawArticle], embeddings: np.ndarray):
        """Add articles to index"""
        # Convert to float32 (FAISS requirement)
        embeddings = embeddings.astype('float32')

        # Add to index
        start_id = self.index.ntotal
        self.index.add(embeddings)

        # Store mappings
        for i, article in enumerate(articles):
            faiss_id = start_id + i
            self.id_mapping.append(article.id)
            self.metadata[faiss_id] = {
                'article_id': article.id,
                'publish_datetime': article.published_at,
                'category': article.category,
                'source': article.source
            }

    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 100,
        time_window: Optional[Tuple[datetime, datetime]] = None,
        category: Optional[str] = None
    ) -> List[Tuple[str, float]]:
        """
        Search for similar articles

        Args:
            query_embedding: Query vector (1D array)
            k: Number of neighbors to return
            time_window: (start_time, end_time) for temporal filtering
            category: Category filter (optional)

        Returns:
            List of (article_id, distance) tuples
        """
        # Reshape query to (1, dim)
        query = query_embedding.reshape(1, -1).astype('float32')

        # Search (get more than k to allow for filtering)
        distances, indices = self.index.search(query, k * 3)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for missing results
                continue

            meta = self.metadata.get(idx)
            if not meta:
                continue

            # Apply filters
            if time_window:
                pub_time = meta['publish_datetime']
                if not (time_window[0] <= pub_time <= time_window[1]):
                    continue

            if category and meta['category'] != category:
                continue

            article_id = meta['article_id']
            results.append((article_id, float(dist)))

            if len(results) >= k:
                break

        return results

    def save(self, path: str):
        """Save index to disk"""
        faiss.write_index(self.index, f"{path}/faiss.index")

        # Save metadata
        import pickle
        with open(f"{path}/metadata.pkl", 'wb') as f:
            pickle.dump({
                'id_mapping': self.id_mapping,
                'metadata': self.metadata
            }, f)

    def load(self, path: str):
        """Load index from disk"""
        self.index = faiss.read_index(f"{path}/faiss.index")

        import pickle
        with open(f"{path}/metadata.pkl", 'rb') as f:
            data = pickle.load(f)
            self.id_mapping = data['id_mapping']
            self.metadata = data['metadata']
```

#### Implementation Checklist
- [ ] Install FAISS: `pip install faiss-cpu` (or faiss-gpu)
- [ ] Create `vector_index.py` file
- [ ] Implement `VectorIndex` class
- [ ] Test index creation and search locally
- [ ] Set up Azure Blob Storage for index persistence
- [ ] Implement index rebuild job (daily)
- [ ] Implement incremental updates
- [ ] Add monitoring for index size and query latency

#### Testing
- [ ] Unit test: Index add/search correctness
- [ ] Performance test: Search latency (<10ms for 100k vectors)
- [ ] Performance test: Index rebuild time
- [ ] Load test: Concurrent search requests
- [ ] Integration test: Time window filtering

#### Success Criteria
- ✅ Search latency <10ms P95
- ✅ Index rebuild <5 minutes for 100k articles
- ✅ Handles 100+ QPS

---

### Component 6: Hybrid Candidate Generation
**Status:** ⬜ NOT STARTED
**Files:** `Azure/functions/shared/candidate_generation.py` (new file)
**Dependencies:** Component 5
**Priority:** P0 (Critical - Phase 2)

#### Specification
```python
from rank_bm25 import BM25Okapi
from datetime import datetime, timedelta
from typing import List, Set, Tuple

class CandidateGenerator:
    def __init__(self, vector_index: VectorIndex):
        self.vector_index = vector_index
        self.bm25_index = None  # Built from recent articles
        self.bm25_corpus = []
        self.bm25_article_ids = []

    def build_bm25_index(self, articles: List[RawArticle]):
        """Build BM25 index from recent articles"""
        self.bm25_corpus = []
        self.bm25_article_ids = []

        for article in articles:
            # Tokenize
            tokens = article.title.lower().split()
            self.bm25_corpus.append(tokens)
            self.bm25_article_ids.append(article.id)

        self.bm25_index = BM25Okapi(self.bm25_corpus)

    def find_candidates(
        self,
        article: RawArticle,
        embedding: np.ndarray
    ) -> List[str]:
        """
        Find candidate clusters using hybrid search

        Strategy:
        1. Vector search (FAISS) for semantic similarity
        2. Keyword search (BM25) for lexical precision
        3. Time window filtering
        4. Merge and deduplicate

        Returns:
            List of candidate cluster IDs
        """
        # Time window: -7 days to +6 hours from article publish time
        time_min = article.published_at - timedelta(days=7)
        time_max = article.published_at + timedelta(hours=6)

        # 1. Vector search (semantic similarity)
        vector_candidates = self.vector_index.search(
            embedding,
            k=100,
            time_window=(time_min, time_max),
            category=article.category
        )
        vector_ids = set(cid for cid, _ in vector_candidates)

        # 2. BM25 search (keyword precision)
        query_tokens = article.title.lower().split()
        bm25_scores = self.bm25_index.get_scores(query_tokens)

        # Get top 50 by BM25 score
        top_indices = np.argsort(bm25_scores)[-50:][::-1]
        keyword_ids = set(self.bm25_article_ids[i] for i in top_indices)

        # 3. Filter keyword candidates by time
        keyword_ids_filtered = set()
        for article_id in keyword_ids:
            # TODO: Look up article metadata to check time window
            # For now, assume all BM25 results are recent
            keyword_ids_filtered.add(article_id)

        # 4. Merge candidates (union)
        all_candidates = vector_ids.union(keyword_ids_filtered)

        # 5. Cap at 150 total candidates
        candidate_list = list(all_candidates)[:150]

        return candidate_list
```

#### Implementation Checklist
- [ ] Install rank-bm25: `pip install rank-bm25`
- [ ] Create `candidate_generation.py` file
- [ ] Implement `CandidateGenerator` class
- [ ] Implement BM25 index building
- [ ] Test hybrid search locally
- [ ] Optimize BM25 index rebuild frequency
- [ ] Add candidate generation metrics

#### Testing
- [ ] Unit test: FAISS search returns expected candidates
- [ ] Unit test: BM25 search returns expected candidates
- [ ] Integration test: Hybrid search merges correctly
- [ ] Performance test: Candidate generation <50ms
- [ ] Accuracy test: Top candidates include ground truth

---

### Component 7: Multi-Factor Scoring
**Status:** ⬜ NOT STARTED
**Files:** `Azure/functions/shared/clustering.py` (new file)
**Dependencies:** Component 6
**Priority:** P0 (Critical - Phase 2)

#### Specification
```python
from typing import Dict, Any, Tuple
import numpy as np
from datetime import datetime

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Cosine similarity between two vectors"""
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def score_candidate(
    article: RawArticle,
    cluster: StoryCluster,
    article_embedding: np.ndarray
) -> Tuple[float, Dict[str, float]]:
    """
    Compute multi-factor similarity score

    Factors:
    1. Semantic similarity (cosine of embeddings) - 55%
    2. Entity overlap (Jaccard) - 20%
    3. Title similarity (BM25) - 10%
    4. Time decay (Gaussian) - 10%
    5. Geographic proximity - 5%

    Returns:
        (final_score, component_scores)
    """
    components = {}

    # 1. Semantic similarity (55%)
    cluster_centroid = np.array(cluster.embedding)  # Cluster centroid embedding
    cosine_sim = cosine_similarity(article_embedding, cluster_centroid)
    components['cosine'] = cosine_sim

    # 2. Entity overlap (20%)
    article_entities = set(e['text'].lower() for e in article.entities)
    cluster_entities = set(cluster.entity_histogram.keys())  # Top entities in cluster

    if article_entities and cluster_entities:
        intersection = article_entities.intersection(cluster_entities)
        union = article_entities.union(cluster_entities)
        entity_jaccard = len(intersection) / len(union)
    else:
        entity_jaccard = 0.0

    components['entities'] = entity_jaccard

    # 3. Title similarity (BM25) (10%)
    # Simplified: Use word overlap
    article_words = set(article.title.lower().split())
    cluster_words = set(cluster.title.lower().split())

    if article_words and cluster_words:
        word_overlap = len(article_words.intersection(cluster_words))
        title_sim = word_overlap / len(article_words.union(cluster_words))
    else:
        title_sim = 0.0

    components['title'] = title_sim

    # 4. Time decay (10%)
    time_diff_hours = abs(
        (article.published_at - cluster.last_updated).total_seconds() / 3600
    )

    # Gaussian decay with adaptive sigma
    if cluster.breaking_news:
        sigma = 24  # 24-hour window for breaking news
    else:
        sigma = 72  # 72-hour window for regular news

    time_decay = np.exp(-(time_diff_hours / sigma) ** 2)
    components['time'] = time_decay

    # 5. Geographic proximity (5%)
    geo_proximity = 0.0
    if article.location and cluster.location:
        # Simplified: Check if same country/region
        if article.location.get('country') == cluster.location.get('country'):
            geo_proximity = 1.0
        # TODO: Implement proper haversine distance

    components['geo'] = geo_proximity

    # 6. Event signature bonus (optional - Phase 3)
    event_bonus = 0.0
    # if article.event_signature and cluster.event_signatures:
    #     if article.event_signature['action'] in cluster.event_signatures:
    #         event_bonus = 0.1

    # Weighted combination
    final_score = (
        0.55 * cosine_sim +
        0.20 * entity_jaccard +
        0.10 * title_sim +
        0.10 * time_decay +
        0.05 * geo_proximity +
        event_bonus
    )

    return final_score, components


def assign_article_to_cluster(
    article: RawArticle,
    candidates: List[StoryCluster],
    article_embedding: np.ndarray
) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Assign article to best matching cluster or create new cluster

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
    hours_old = (datetime.now() - article.published_at).total_seconds() / 3600

    if hours_old < 12:
        threshold = 0.62  # Breaking news - higher threshold (stricter)
    elif hours_old < 72:
        threshold = 0.58  # Recent news
    else:
        threshold = 0.52  # Older stories - lower threshold (more lenient)

    # Statistical guardrail: Require best match to be significantly better than mean
    if len(scored_candidates) > 1:
        scores = [c['score'] for c in scored_candidates]
        mean_score = np.mean(scores)
        std_score = np.std(scores)

        # Require best match to be at least 2 std devs above mean
        statistical_threshold = mean_score + 2 * std_score

        if best_match['score'] >= statistical_threshold:
            # Best match is statistically significant
            threshold = min(threshold, best_match['score'] - 0.01)

    # Make assignment decision
    if best_match['score'] >= threshold:
        return best_match['cluster'].id, {
            'decision': 'assigned',
            'score': best_match['score'],
            'threshold': threshold,
            'components': best_match['components']
        }
    else:
        return None, {
            'decision': 'new_cluster',
            'reason': 'below_threshold',
            'best_score': best_match['score'],
            'threshold': threshold,
            'components': best_match['components']
        }
```

#### Implementation Checklist
- [ ] Create `clustering.py` file
- [ ] Implement `score_candidate()` function
- [ ] Implement `assign_article_to_cluster()` function
- [ ] Add cluster centroid field to StoryCluster model
- [ ] Add entity_histogram field to StoryCluster model
- [ ] Test scoring on known article pairs
- [ ] Tune scoring weights with labeled data
- [ ] Add comprehensive logging

#### Testing
- [ ] Unit test: Scoring correctness for known pairs
- [ ] Integration test: Correct cluster assignment
- [ ] A/B test: New scoring vs old fingerprinting
- [ ] Accuracy test: Precision/recall on test set
- [ ] Performance test: Scoring latency <5ms per candidate

#### Success Criteria
- ✅ Precision >90% (assigned pairs are truly related)
- ✅ Recall >85% (related articles are assigned together)
- ✅ Latency <5ms per candidate

---

### Component 8: Cluster Maintenance
**Status:** ⬜ NOT STARTED
**Files:** `Azure/functions/shared/cluster_maintenance.py` (new file)
**Dependencies:** Component 7
**Priority:** P2 (Medium - Phase 3)

#### Specification
```python
from datetime import datetime, timedelta
from typing import List, Optional
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

class ClusterMaintenance:
    """Periodic maintenance jobs for cluster quality"""

    def merge_similar_clusters(self, clusters: List[StoryCluster]) -> List[Tuple[str, str, str]]:
        """
        Merge clusters that are too similar

        Returns:
            List of (cluster1_id, cluster2_id, merged_id) tuples
        """
        merged = []

        # Compare all pairs
        for i, c1 in enumerate(clusters):
            for c2 in clusters[i+1:]:
                if self._should_merge(c1, c2):
                    merged_cluster = self._merge_clusters(c1, c2)
                    merged.append((c1.id, c2.id, merged_cluster.id))

        return merged

    def _should_merge(self, c1: StoryCluster, c2: StoryCluster) -> bool:
        """Check if two clusters should merge"""
        # Same category
        if c1.category != c2.category:
            return False

        # High embedding similarity
        cosine_sim = cosine_similarity(
            np.array(c1.embedding),
            np.array(c2.embedding)
        )
        if cosine_sim < 0.8:
            return False

        # High entity overlap
        entities1 = set(c1.entity_histogram.keys())
        entities2 = set(c2.entity_histogram.keys())
        entity_overlap = len(entities1.intersection(entities2)) / len(entities1.union(entities2))
        if entity_overlap < 0.6:
            return False

        # Time overlap
        time_overlap = self._calculate_time_overlap(c1, c2)
        if time_overlap < 0.5:
            return False

        return True

    def _merge_clusters(self, c1: StoryCluster, c2: StoryCluster) -> StoryCluster:
        """Merge two clusters into one"""
        # Keep the older cluster ID
        if c1.first_seen < c2.first_seen:
            base_cluster = c1
            merge_cluster = c2
        else:
            base_cluster = c2
            merge_cluster = c1

        # Merge article lists
        base_cluster.source_articles.extend(merge_cluster.source_articles)

        # Update centroid (weighted average)
        n1 = len(c1.source_articles)
        n2 = len(c2.source_articles)
        total = n1 + n2

        base_cluster.embedding = (
            (n1 * np.array(c1.embedding) + n2 * np.array(c2.embedding)) / total
        ).tolist()

        # Merge entity histograms
        for entity, count in merge_cluster.entity_histogram.items():
            base_cluster.entity_histogram[entity] = \
                base_cluster.entity_histogram.get(entity, 0) + count

        # Update timestamps
        base_cluster.first_seen = min(c1.first_seen, c2.first_seen)
        base_cluster.last_updated = max(c1.last_updated, c2.last_updated)

        # Update title if merge cluster has better title
        if len(merge_cluster.title) > len(base_cluster.title):
            base_cluster.title = merge_cluster.title

        return base_cluster

    def split_divergent_clusters(self, clusters: List[StoryCluster]) -> List[Tuple[str, List[str]]]:
        """
        Split clusters that have become too broad

        Returns:
            List of (original_cluster_id, [new_cluster_ids]) tuples
        """
        splits = []

        for cluster in clusters:
            if self._should_split(cluster):
                subclusters = self._split_cluster(cluster)
                new_ids = [sc.id for sc in subclusters]
                splits.append((cluster.id, new_ids))

        return splits

    def _should_split(self, cluster: StoryCluster) -> bool:
        """Check if cluster should be split"""
        # Need minimum size
        if len(cluster.source_articles) < 10:
            return False

        # Check temporal span
        time_span = cluster.last_updated - cluster.first_seen
        if time_span < timedelta(days=3):
            return False

        # Get article embeddings
        embeddings = self._get_article_embeddings(cluster.source_articles)
        if embeddings is None or len(embeddings) < 10:
            return False

        # Try 2-cluster split
        kmeans = KMeans(n_clusters=2, random_state=42).fit(embeddings)

        # Check silhouette score (measures cluster separation)
        silhouette = silhouette_score(embeddings, kmeans.labels_)

        # High silhouette = clear separation = should split
        return silhouette > 0.6

    def _split_cluster(self, cluster: StoryCluster) -> List[StoryCluster]:
        """Split cluster into subclusters"""
        embeddings = self._get_article_embeddings(cluster.source_articles)

        # K-means clustering
        kmeans = KMeans(n_clusters=2, random_state=42).fit(embeddings)

        # Create subclusters
        subclusters = []
        for k in range(2):
            indices = np.where(kmeans.labels_ == k)[0]
            articles = [cluster.source_articles[i] for i in indices]

            # Create new cluster
            subcluster = StoryCluster(
                id=f"{cluster.id}_split_{k}",
                category=cluster.category,
                source_articles=articles,
                embedding=kmeans.cluster_centers_[k].tolist(),
                # ... other fields
            )
            subclusters.append(subcluster)

        return subclusters

    def decay_old_clusters(self, clusters: List[StoryCluster]) -> List[str]:
        """
        Archive/decay old clusters

        Returns:
            List of archived cluster IDs
        """
        archived = []
        now = datetime.now()

        for cluster in clusters:
            days_since_update = (now - cluster.last_updated).days

            # Archive if:
            # - Single article AND >14 days old
            # - OR >30 days since last update
            if (len(cluster.source_articles) == 1 and days_since_update > 14) or \
               days_since_update > 30:
                archived.append(cluster.id)

        return archived
```

#### Implementation Checklist
- [ ] Create `cluster_maintenance.py` file
- [ ] Implement merge logic
- [ ] Implement split logic
- [ ] Implement decay/archival logic
- [ ] Create Azure Function timer trigger (hourly)
- [ ] Add maintenance metrics/logging
- [ ] Test merge/split correctness

#### Testing
- [ ] Unit test: Merge decision correctness
- [ ] Unit test: Split decision correctness
- [ ] Integration test: Full maintenance cycle
- [ ] Performance test: Maintenance runtime (<5 min for 10k clusters)

---

### Component 9: API ETag Support
**Status:** ⬜ NOT STARTED
**Files:** `Azure/api/app/routers/stories.py`
**Dependencies:** None
**Priority:** P1 (High - Phase 1)

#### Current Implementation
**File:** [Azure/api/app/routers/stories.py:179-294](../Azure/api/app/routers/stories.py)

No ETag support currently. iOS app fetches full story list every time.

#### Specification
```python
import hashlib
from fastapi import Header, Response, status
from typing import Optional

@router.get("/feed")
async def get_personalized_feed(
    category: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    if_none_match: Optional[str] = Header(None),  # ETag from client
    user: Dict[str, Any] = Depends(get_current_user),
    response: Response
):
    """
    Get personalized story feed with ETag support
    """
    # Get latest update timestamp
    latest_update = await cosmos_service.get_latest_cluster_update()

    # Generate ETag from latest update + user preferences
    etag_source = f"{latest_update.isoformat()}:{user['id']}:{category}:{limit}:{offset}"
    etag = hashlib.md5(etag_source.encode()).hexdigest()

    # Check If-None-Match header
    if if_none_match == etag:
        # Content hasn't changed
        response.status_code = status.HTTP_304_NOT_MODIFIED
        return Response(status_code=304)

    # Fetch stories (existing logic)
    cosmos_service.connect()
    stories = await cosmos_service.query_recent_stories(
        category=category,
        limit=limit * 3,
        offset=offset
    )

    # Filter and personalize (existing logic)
    # ...

    # Set response headers
    response.headers['ETag'] = etag
    response.headers['Cache-Control'] = 'max-age=300'  # 5 minutes
    response.headers['Last-Modified'] = latest_update.strftime('%a, %d %b %Y %H:%M:%S GMT')

    return story_responses
```

#### Implementation Checklist
- [ ] Add `if_none_match` header parameter to endpoints
- [ ] Implement ETag generation logic
- [ ] Add 304 Not Modified responses
- [ ] Add Cache-Control and Last-Modified headers
- [ ] Update iOS app to send If-None-Match header
- [ ] Test ETag caching behavior

#### Testing
- [ ] Unit test: ETag generation consistency
- [ ] Integration test: 304 responses work correctly
- [ ] iOS test: App cache updates properly
- [ ] Performance test: 304 response latency (<10ms)

#### Success Criteria
- ✅ Reduces unnecessary data transfer by 80%
- ✅ iOS app caching works correctly
- ✅ Stories update properly when content changes

---

## Progress Tracking

### Phase 1: Foundation & Quick Wins
**Target Completion:** Week 1
**Status:** ⬜ NOT STARTED

| Component | Status | Owner | Started | Completed | Notes |
|-----------|--------|-------|---------|-----------|-------|
| 1.1 SimHash Deduplication | ⬜ | - | - | - | |
| 1.2 Time-window Filtering | ⬜ | - | - | - | |
| 1.3 Adaptive Thresholds | ⬜ | - | - | - | |
| 1.4 Enable All RSS Feeds | ⬜ | - | - | - | |
| 1.5 iOS ETag Support | ⬜ | - | - | - | |
| 1.6 Basic Entity Linking | ⬜ | - | - | - | |

**Blockers:** None
**Risks:** None

---

### Phase 2: Semantic Embeddings
**Target Completion:** Week 2
**Status:** ⬜ NOT STARTED

| Component | Status | Owner | Started | Completed | Notes |
|-----------|--------|-------|---------|-----------|-------|
| 2.1 SentenceTransformers Deploy | ⬜ | - | - | - | |
| 2.2 FAISS Index | ⬜ | - | - | - | |
| 2.3 Hybrid Search | ⬜ | - | - | - | |
| 2.4 Embedding Pipeline | ⬜ | - | - | - | |
| 2.5 A/B Testing | ⬜ | - | - | - | |
| 2.6 Cutover | ⬜ | - | - | - | |

**Dependencies:** Phase 1 complete
**Blockers:** None
**Risks:** None

---

### Phase 3: Advanced Features
**Target Completion:** Week 3-4
**Status:** ⬜ NOT STARTED

| Component | Status | Owner | Started | Completed | Notes |
|-----------|--------|-------|---------|-----------|-------|
| 3.1 Event Signatures | ⬜ | - | - | - | |
| 3.2 Geographic Features | ⬜ | - | - | - | |
| 3.3 Cluster Maintenance | ⬜ | - | - | - | |
| 3.4 Wikidata Linking | ⬜ | - | - | - | |
| 3.5 Scoring Optimization | ⬜ | - | - | - | |
| 3.6 Multilingual Model | ⬜ | - | - | - | |

**Dependencies:** Phase 2 complete
**Blockers:** None
**Risks:** None

---

## Testing & Validation

### Test Data Sets

**1. Ground Truth Dataset (Hand-labeled)**
- 500 article pairs labeled as:
  - Same story (positive)
  - Different story (negative)
  - Syndicated/duplicate (near-duplicate)

**2. Edge Cases**
- [ ] Non-English articles
- [ ] Breaking news (rapid updates)
- [ ] Syndicated content (AP, Reuters)
- [ ] Similar but distinct stories (Sydney dentist vs Sydney stabbing)
- [ ] Long-tail topics (low entity overlap)

**3. Performance Benchmarks**
- [ ] 100k articles in index
- [ ] 1M articles in index
- [ ] 100 QPS sustained load

### Validation Metrics

**Clustering Quality:**
- **Precision**: % of assigned pairs that are truly related (target: >90%)
- **Recall**: % of related articles assigned together (target: >85%)
- **F1 Score**: Harmonic mean of precision and recall (target: >0.87)
- **Duplicate Rate**: % of articles marked as duplicates (target: <5%)

**Performance:**
- **Ingestion Latency**: Time from RSS poll to indexed (target: <10s P95)
- **Clustering Latency**: Time to assign article to cluster (target: <200ms P95)
- **API Latency**: Time to return story list (target: <500ms P95)
- **Index Search**: FAISS query time (target: <10ms P95)

**Production Metrics:**
- **New Stories/Day**: Number of unique story clusters created (target: 50-100)
- **Articles/Story**: Average articles per cluster (target: 3-5)
- **Story Lifetime**: Average time from first seen to last updated (baseline TBD)
- **Breaking News Latency**: Time from publish to detected as breaking (target: <30min)

---

## Rollback Strategy

### Feature Flags
All new components are controlled by feature flags in [config.py](../Azure/functions/shared/config.py):

```python
# Feature flags for clustering overhaul
CLUSTERING_USE_SIMHASH = os.getenv('CLUSTERING_USE_SIMHASH', 'false') == 'true'
CLUSTERING_USE_EMBEDDINGS = os.getenv('CLUSTERING_USE_EMBEDDINGS', 'false') == 'true'
CLUSTERING_USE_HYBRID_SEARCH = os.getenv('CLUSTERING_USE_HYBRID', 'false') == 'true'
CLUSTERING_USE_ADAPTIVE_THRESHOLD = os.getenv('CLUSTERING_USE_ADAPTIVE', 'false') == 'true'
CLUSTERING_USE_TIME_WINDOW = os.getenv('CLUSTERING_USE_TIME_WINDOW', 'false') == 'true'
```

### Rollback Procedures

**Phase 1 Rollback:**
1. Set all Phase 1 feature flags to `false`
2. Restart Azure Functions
3. Verify old clustering logic active
4. Monitor for 24 hours

**Phase 2 Rollback:**
1. Set `CLUSTERING_USE_EMBEDDINGS=false`
2. Set `CLUSTERING_USE_HYBRID=false`
3. Revert to fingerprint-based clustering
4. Delete embedding fields (optional)

**Phase 3 Rollback:**
1. Disable cluster maintenance job
2. Disable event signature extraction
3. System continues with Phase 2 features

### Rollback Triggers
- **Automatic:** Error rate >5% in clustering function
- **Manual:** Precision drops below 70%
- **Manual:** Latency P95 exceeds 2x baseline

---

## Success Metrics

### Target Metrics (Post-Implementation)

| Metric | Current | Phase 1 Target | Phase 2 Target | Phase 3 Target |
|--------|---------|---------------|----------------|----------------|
| New Stories/Day | 1-5 | 20-30 | 40-60 | 50-100 |
| Duplicate Rate | 15-20% | <10% | <7% | <5% |
| Clustering Precision | ~60% | 75% | 85% | 90% |
| Clustering Recall | ~50% | 70% | 80% | 85% |
| API Latency P95 | ~2s | <1s | <500ms | <500ms |
| Clustering Latency P95 | ~500ms | <300ms | <200ms | <200ms |
| False Positive Rate | ~20% | <10% | <5% | <3% |
| Articles/Story (avg) | 1.2 | 2.0 | 3.0 | 3.5 |

### Business Impact

**User Experience:**
- ✅ More unique stories in feed (50-100 vs 1-5)
- ✅ Less duplicate content (<5% vs 15-20%)
- ✅ Better story quality (higher precision)
- ✅ Faster load times (ETag caching)

**Operational:**
- ✅ Support 100+ RSS feeds without degradation
- ✅ Lower infrastructure costs (better caching)
- ✅ Easier debugging (comprehensive logging)
- ✅ Scalable architecture (can handle 10x growth)

**Competitive:**
- ✅ Clustering accuracy rivals Google News, Apple News
- ✅ Multilingual support (Phase 3)
- ✅ Real-time breaking news detection (<30min)

---

## Cost Estimates

### Azure Infrastructure (Monthly)

| Service | Current | Phase 1 | Phase 2 | Phase 3 | Notes |
|---------|---------|---------|---------|---------|-------|
| Azure Functions (Consumption) | $50 | $60 | $80 | $100 | More compute for embeddings |
| Container Instance (Model) | $0 | $0 | $100 | $100 | 4GB RAM, 2 vCPU |
| Cosmos DB | $150 | $160 | $180 | $200 | More storage for embeddings |
| Azure Storage (FAISS index) | $5 | $5 | $10 | $15 | Index storage |
| Application Insights | $10 | $10 | $15 | $15 | More telemetry |
| **Total** | **$215** | **$235** | **$385** | **$430** | +100% for production-ready |

### Development Costs (One-time)

| Phase | Engineering Time | Estimated Hours | Notes |
|-------|-----------------|-----------------|-------|
| Phase 1 | 3-5 days | 24-40h | Quick wins, minimal architecture changes |
| Phase 2 | 5-7 days | 40-56h | Embedding infrastructure, testing |
| Phase 3 | 10-14 days | 80-112h | Advanced features, optimization |
| **Total** | **3-4 weeks** | **144-208h** | Assumes single developer |

---

## Next Steps

### Immediate Actions (Before Starting Phase 1)

1. **[✅ COMPLETE] Review and approve this implementation plan**
2. **[ ] Set up test infrastructure**
   - Create test Cosmos DB container
   - Set up test RSS feeds
   - Prepare ground truth dataset
3. **[ ] Configure feature flags**
   - Add all feature flags to config.py
   - Set up environment variables in Azure
4. **[ ] Create git branch**
   - Branch: `feature/clustering-overhaul`
   - Protect main branch
5. **[ ] Schedule kickoff meeting**
   - Review plan
   - Assign ownership
   - Set milestones

### Weekly Check-ins

**Every Monday:**
- Review progress tracker
- Update component statuses
- Identify blockers
- Adjust timeline if needed

**Every Friday:**
- Review metrics
- Test completed components
- Plan next week's work

---

## Document Maintenance

**This document is a LIVING DOCUMENT.** Update it throughout the implementation:

### After Completing a Component:
1. Change status from ⬜ to ✅
2. Add completion date
3. Update "Notes" with any deviations from spec
4. Add link to PR or commit

### When Blocked:
1. Update status to ⚠️
2. Document blocker in "Notes"
3. Add to "Blockers" section
4. Escalate if >2 days blocked

### When Specs Change:
1. Update specification inline
2. Add note in "Notes" column
3. Update dependencies if affected

---

## Appendix

### Glossary

- **ANN**: Approximate Nearest Neighbor (fast similarity search)
- **BM25**: Best Matching 25 (keyword search algorithm)
- **Cosine Similarity**: Measure of vector similarity (0-1)
- **ETag**: HTTP header for caching
- **FAISS**: Facebook AI Similarity Search (vector index library)
- **Hamming Distance**: Number of differing bits between two hashes
- **Jaccard Similarity**: Set overlap metric
- **NER**: Named Entity Recognition
- **SimHash**: Locality-sensitive hashing for near-duplicate detection
- **Wikidata QID**: Unique identifier in Wikidata knowledge base

### References

- [SentenceTransformers Documentation](https://www.sbert.net/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss/wiki)
- [spaCy NER](https://spacy.io/usage/linguistic-features#named-entities)
- [SimHash Paper](https://www.cs.princeton.edu/courses/archive/spring04/cos598B/bib/CharikarEstim.pdf)
- [Azure Functions Python Guide](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python)

### Related Documents

- [POLICY_NO_FAKE_DATA.md](./POLICY_NO_FAKE_DATA.md) - Testing guidelines
- [TESTING_DECISION_TREE.md](./TESTING_DECISION_TREE.md) - Test strategy
- [EngineeringGuidelinesiOS.md](./EngineeringGuidelinesiOS.md) - iOS integration

---

**Document Version:** 1.0
**Created:** 2025-11-12
**Last Updated:** 2025-11-12
**Next Review:** 2025-11-19
