# Testing Decision Tree - Quick Reference

## When You Need to Write a Test

Start here and follow the tree:

```
┌─────────────────────────────────────┐
│ I need to write a test              │
└────────────┬────────────────────────┘
             │
             ▼
    ┌────────────────────┐
    │ What am I testing? │
    └─────┬──────────────┘
          │
    ┌─────┴──────────────────────────────────┐
    │                                        │
    ▼                                        ▼
┌─────────────────────────┐      ┌──────────────────────────┐
│ SYSTEM BEHAVIOR         │      │ PURE ALGORITHM           │
│ (Does the API work?)    │      │ (Does the math work?)    │
│ (Does data flow?)       │      │ (Is logic correct?)      │
│ (Is clustering on?)     │      │ (No side effects)        │
└────────┬────────────────┘      └──────────┬───────────────┘
         │                                  │
         ▼                                  ▼
  ┌─────────────────────┐        ┌──────────────────────┐
  │ USE REAL DATA       │        │ UNIT TEST OK        │
  │                     │        │ (Mock is fine here) │
  │ System Test:        │        │                     │
  │ ✅ Real API        │        │ Examples:           │
  │ ✅ Real JWT        │        │ - Similarity calc   │
  │ ✅ Real DB         │        │ - Fingerprint gen   │
  │ ✅ Real functions  │        │ - Text parsing      │
  │                     │        └──────────────────────┘
  │ Result:             │
  │ Ground truth for    │
  │ system health       │
  └─────────────────────┘
```

---

## Quick Decision Matrix

| What am I testing? | Example | Use Real Data? | Mock OK? |
|---|---|---|---|
| Does the API return stories? | `test_stories_endpoint_returns_data` | ✅ YES | ❌ NO |
| Are stories being clustered? | `test_clustering_is_working` | ✅ YES | ❌ NO |
| Are articles in the database? | `test_articles_in_cosmos` | ✅ YES | ❌ NO |
| Is RSS ingestion running? | `test_rss_ingestion` | ✅ YES | ❌ NO |
| Does similarity calculation work? | `test_text_similarity` | ❌ NO | ✅ YES |
| Is fingerprinting consistent? | `test_fingerprint_generation` | ❌ NO | ✅ YES |
| Does categorization logic work? | `test_article_categorization` | ❌ NO | ✅ YES |
| Do entities extract correctly? | `test_entity_extraction` | ❌ NO | ✅ YES |

---

## If You're Testing System Behavior

### ✅ DO THIS

```python
# Real system test with real data
def test_clustering_is_working(api_base_url, auth_headers):
    # Use REAL API
    response = requests.get(
        f"{api_base_url}/api/stories/feed?limit=20",
        headers=auth_headers  # Real JWT token
    )
    
    # Get REAL data
    stories = response.json()
    
    # Test with REAL data
    multi_source = [s for s in stories if len(s.get('sources', [])) > 1]
    assert len(multi_source) > 0
```

### ❌ DON'T DO THIS

```python
# Mock API hides real problems
@patch('requests.get')
def test_clustering_is_working(mock_get):
    # Fake API response
    mock_get.return_value.json.return_value = {
        'stories': [{'id': 'fake', 'sources': [1, 2, 3]}]
    }
    
    # Test always passes with fake data
    stories = requests.get('/api/stories/feed').json()
    assert len(stories) > 0  # Always true (fake data)
```

---

## If You're Testing Algorithm Logic

### ✅ DO THIS

```python
# Unit test for pure algorithm (mocks are fine)
def test_text_similarity():
    # This is deterministic math, no side effects
    score = calculate_similarity("text1", "text2")
    
    # Assert mathematical properties
    assert 0 <= score <= 1
    assert score == calculate_similarity("text1", "text2")  # Deterministic
```

### ❌ DON'T DO THIS

```python
# Don't mock system components even for algorithm tests
@patch('CosmosClient')
def test_text_similarity(mock_cosmos):
    # Unnecessary mock for algorithm test
    mock_cosmos.query_items.return_value = [fake_data]
    
    score = calculate_similarity("text1", "text2")
    assert score > 0.5
```

---

## The Three Levels of Testing

### Level 1: System Tests ⭐ HIGHEST PRIORITY
```
Location: Azure/tests/system/test_deployed_api.py
Data: REAL from deployed system
What: Does the system work end-to-end?
Mock: NOTHING
Result: If this fails = system is broken (true signal)
```

### Level 2: Integration Tests 
```
Location: Azure/tests/integration/
Data: REAL where possible (Cosmos DB, Firebase)
What: Do components work together?
Mock: Only external services if absolutely required
Result: Helps debug specific components
```

### Level 3: Unit Tests
```
Location: Azure/tests/unit/
Data: Test data (synthetic is OK)
What: Does this function work correctly?
Mock: OK for isolated algorithm testing
Result: Catches regressions, prevents breaking existing logic
```

---

## Before You Commit Code

**Checklist:**

```
□ All system tests pass (or explain why not)
□ No mock data used for system/integration tests
□ System tests use REAL Cosmos DB, REAL API, REAL JWT
□ Unit tests only mock pure algorithms
□ Integration tests use real databases where possible
□ No mocking of components in your own system
□ If a test uses @patch or MagicMock, ask why?
```

---

## Red Flags (Don't Do These)

🚩 **Your test uses `@patch('Cosmos')` or `@patch('requests')`**
   → Stop. Use real system instead. This hides problems.

🚩 **Your integration test passes all mock tests but API is broken**
   → Expected. Mocks hide real issues. Run system tests instead.

🚩 **97% of tests pass but system is broken**
   → Classic mock problem. Check system tests (they should fail).

🚩 **Your test is checking if your own system component works with fake data**
   → Problem. Use real data from real system instead.

🚩 **You're mocking the database in an integration test**
   → Problem. Use real Cosmos DB connection instead.

---

## The Golden Rule

**"When in doubt, test against the real deployed system."**

- Real system = truth
- Mock data = lies (even if they pass)
- System tests fail? Good, now you know what's broken
- System tests pass? Great, system works

---

## Real World Example

### Scenario: You think clustering is working

**With Mock Tests (Wrong):**
```
✅ test_similar_article_clusters_with_existing
✅ test_duplicate_source_prevented
✅ test_entity_based_matching
✅ 12 more mocked clustering tests

Conclusion: Clustering works!
Reality: 🔴 Clustering completely broken (no stories exist)
```

**With System Test (Right):**
```
❌ test_clustering_is_working
   AssertionError: No clustered stories

Conclusion: Clustering broken or no data flowing
Next Step: Check if articles in database
Then: Check if change feed triggers firing
Then: Fix the real problem
```

### The Result

Mock approach → Find out too late from angry users
System test approach → Find out immediately from automated test

---

## Running Tests Properly

```bash
# ✅ Run system tests first (most important)
cd Azure/tests
pytest system/ -v

# ✅ Then integration tests (debugging)
pytest integration/ -v

# ✅ Finally unit tests (regression prevention)
pytest unit/ -v

# ❌ DON'T report: "97% tests passing = system good"
# ✅ DO report: System tests status (they reveal truth)
```

---

## Conclusion

**Remember: Mock test success ≠ System success**

```
Mock Tests Pass     System Tests Pass    Conclusion
✅ 100%             ❌ 30%              🔴 System broken
✅ 100%             ✅ 100%             🟢 System working
❌ 50%              ✅ 100%             🟢 System working, code has bugs
❌ 50%              ❌ 30%              🔴 Multiple issues
```

Trust the system tests. They tell the truth.

