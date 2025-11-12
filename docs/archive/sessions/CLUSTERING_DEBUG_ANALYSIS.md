# Clustering Debug Analysis & Fix Plan

## Problem Statement
System test `test_clustering_is_working` is failing because:
- **Issue**: 0 multi-source clustered stories found
- **Symptom**: Stories are being created, but articles from different sources aren't clustering together
- **Root Cause**: To be determined

## Code Analysis of Clustering Logic

### Clustering Flow (function_app.py)

1. **Article Arrives**: Raw article triggers change feed
2. **Fingerprint Match** (Line 784):
   - Query stories by fingerprint
   - If found → update existing story
   - If not found → try fuzzy matching

3. **Fuzzy Matching** (Lines 789-884):
   - Query recent stories in same category (limit 500)
   - Calculate text similarity
   - Compare to threshold (75% by default)
   - Check for topic conflicts

4. **Update Story** (Lines 894-1073):
   - Add article ID to source_articles list
   - Update verification_level, timestamps, status
   - Log everything

5. **Create Story** (Lines 1085-1116):
   - If no match found, create new story
   - Initial verification_level = 1
   - Store source_articles as list of IDs

## Possible Issues & Root Causes

### Issue 1: Fingerprint Mismatch
**Hypothesis**: Different articles about the same event aren't getting the same fingerprint

**Evidence to Check**:
- Are fingerprints generated consistently?
- Are title normalizations working?
- Is entity extraction working?

**Code Location**: `shared/utils.py` - `generate_story_fingerprint()`

**Fix Strategy**: 
```python
# Current: Very aggressive (3 words max)
# Problem: May be TOO aggressive - missing stories with slightly different titles
key_words = [w for w in words 
             if len(w) > 3  
             and w not in stop_words 
             and w not in action_verbs][:3]  # Only 3 words!

# Issue: "Trump announces new climate policy" → fingerprint "trump climate policy"
#        "President unveils environmental initiative" → fingerprint "president environmental"
#        NO MATCH even though same story!
```

### Issue 2: Fuzzy Matching Too Strict
**Hypothesis**: Text similarity threshold of 75% is too high for real-world variation

**Code Location**: `function_app.py` lines 816-828

**Problem**: Articles with ~70% similarity won't cluster even if they're clearly same story

### Issue 3: Category Mismatch
**Hypothesis**: Articles categorized differently aren't being compared

**Evidence**: `query_recent_stories(category=article.category, limit=500)` 
- Only queries same category
- If categorization is inconsistent, articles never compared

### Issue 4: Change Feed Not Triggering
**Hypothesis**: The change feed trigger might not be working on raw_articles

**Evidence**: 
- Lease container exists?
- Is change feed enabled on raw_articles container?
- Are articles being inserted?

### Issue 5: Topic Conflict False Positives
**Hypothesis**: `has_topic_conflict()` preventing valid clustering

**Code Location**: `function_app.py` lines 824, 861
- Two similar titles rejected if they "conflict" topically
- Might be too aggressive

## Testing Strategy

### Test 1: Verify Fingerprints
```python
# Create 2 articles about same event with different wording
article1 = "Trump announces new climate policy"
article2 = "President unveils environmental initiative"

# Get fingerprints
fp1 = generate_story_fingerprint(article1, [])
fp2 = generate_story_fingerprint(article2, [])

# Should match or be very close
assert fp1 == fp2, f"Fingerprints don't match: {fp1} vs {fp2}"
```

### Test 2: Verify Text Similarity
```python
similarity = calculate_text_similarity(article1, article2)
# Should be >= 0.75 if this is truly the same story
assert similarity >= 0.65, f"Similarity too low: {similarity}"
```

### Test 3: Verify Category Assignment
```python
# Check if articles about same event get same category
cat1 = categorize_article(title1, desc1, url1)
cat2 = categorize_article(title2, desc2, url2)
assert cat1 == cat2, f"Different categories: {cat1} vs {cat2}"
```

### Test 4: Check Cosmos DB Data
```sql
-- Count stories by source_articles length
SELECT 
  ARRAY_LENGTH(c.source_articles) as num_sources,
  COUNT(*) as story_count
FROM c
GROUP BY ARRAY_LENGTH(c.source_articles)
ORDER BY num_sources DESC

-- Result should show:
--   num_sources: 1, count: 100
--   num_sources: 2, count: 50
--   num_sources: 3+, count: 20
-- If all are 1, clustering is broken
```

## Most Likely Root Cause

Based on code analysis, the most likely issue is:

**🎯 Fingerprint Generation is TOO AGGRESSIVE**

Current logic:
- Takes title: "Trump announces new climate policy"
- Filters to 3+ char words: ["trump", "announces", "climate", "policy"]
- Removes action verbs: ["trump", "climate", "policy"]
- Takes only 3: ["trump", "climate", "policy"]

But then:
- Takes title: "President unveils climate initiative" 
- Filters: ["president", "unveils", "climate", "initiative"]
- Removes action verbs: ["president", "climate", "initiative"]
- Takes only 3: ["president", "climate", "initiative"]

**Result**: Completely different fingerprints even though both are climate policy stories!

The entity-based fallback (line 850+) requires:
- Similarity > 70% AND
- 3+ shared entities AND
- No topic conflict

But this is a fuzzy fallback, not a primary matching mechanism.

## Solution

### Fix 1: Improve Fingerprint Generation
Focus on SEMANTIC similarity, not exact word matching.

```python
def generate_story_fingerprint(title: str, entities: List[Entity]) -> str:
    # Include entities as PRIMARY signal, not secondary
    entity_keywords = [e.text.lower() for e in entities if e.type in ['PERSON', 'ORG', 'LOCATION']]
    
    # Normalize title - keep important words
    words = title.lower().split()
    
    # Remove only ultra-common words
    core_words = [w for w in words if len(w) > 4 and w not in stop_words][:5]  # 5 words, not 3
    
    # Combine entities + title keywords
    all_keywords = sorted(set(entity_keywords + core_words))[:3]
    
    return '_'.join(all_keywords)
```

### Fix 2: Lower Similarity Threshold
```python
# Change from 75% to 70% for initial matching
STORY_FINGERPRINT_SIMILARITY_THRESHOLD = 0.70
```

### Fix 3: Improve Categorization
Ensure articles about same event get same category.

### Fix 4: Test Multi-Source Clustering
Add explicit test that creates multiple articles and validates they cluster together.

---

## Implementation Plan (Session 10)

1. **Analyze Current Behavior** (30 min)
   - Check actual fingerprints being generated
   - Check similarity scores between known-same articles
   - Verify category assignments

2. **Fix Fingerprint Generation** (30 min)
   - Improve entity extraction
   - Balance specificity vs. breadth
   - Add logging for debugging

3. **Test & Validate** (30 min)
   - Create integration test for multi-source clustering
   - Run system tests
   - Verify fix works

4. **Deploy & Monitor** (30 min)
   - Commit changes
   - Deploy to Azure
   - Monitor for improvements

