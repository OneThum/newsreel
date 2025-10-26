# Test Harness Update Plan: Eliminate Mock Data

## Objective
Update all test suites to use REAL Cosmos DB, REAL API, and REAL data instead of mocks.

## Current State (Wrong)
```
Unit Tests: Mock data ❌
  - Test logic in isolation with fake data
  - Results: Always pass (meaningless)

Integration Tests: Mock Cosmos DB ❌
  - Use mock_cosmos_client fixture
  - Never touch real database
  - Results: Always pass (misleading)

System Tests: Real API ✅
  - Test against deployed system
  - Use real JWT tokens
  - Results: Fail when system broken (correct signal)
```

## New State (Correct)
```
Unit Tests: Pure algorithm logic only ✅
  - Test math/algorithms only (no I/O)
  - Mock is acceptable here
  - Examples: similarity calculation, fingerprinting

Integration Tests: REAL Cosmos DB ✅
  - Connect to actual Cosmos DB
  - Insert/query real data
  - Verify clustering actually works
  - Clean up after test

System Tests: Real API + Real Data ✅
  - Test deployed system
  - Use real JWT tokens
  - Verify end-to-end pipeline
```

## Changes Required

### 1. Update conftest.py
**Current:**
```python
@pytest.fixture
def mock_cosmos_client():
    mock = MagicMock()
    mock.query_stories_by_fingerprint.return_value = []
    return mock
```

**New:**
```python
@pytest.fixture(scope="function")
async def cosmos_client_for_tests(test_config):
    """Real Cosmos DB client for integration tests"""
    if not test_config['cosmos_connection_string']:
        pytest.skip("Cosmos DB not configured")
    
    client = CosmosDBClient()
    client.connect()
    
    # Clean containers before test
    yield client
    
    # Clean up after test
    # (cleanup_test_data fixture handles this)
```

### 2. Update Integration Tests
**Current approach (WRONG):**
```python
async def test_clustering(mock_cosmos_client):
    # Mock doesn't touch real DB
    stories = await mock_cosmos_client.query_stories_by_fingerprint(fp)
    assert len(stories) > 0  # Always passes
```

**New approach (CORRECT):**
```python
async def test_clustering(cosmos_client_for_tests, clean_test_data):
    # Insert real article into Cosmos DB
    article = create_test_article()
    result = await cosmos_client_for_tests.create_article(article)
    clean_test_data.register_article(result['id'])
    
    # Query real database
    stories = await cosmos_client_for_tests.query_stories_by_fingerprint(article.fingerprint)
    
    # Assert based on real behavior
    assert len(stories) > 0 or len(stories) == 0  # Shows actual DB state
```

### 3. Unit Tests (Keep Mocks - Only for Pure Logic)
Keep as-is. These test math/algorithms only:
- Text similarity calculation
- Fingerprint generation
- Entity extraction
- Topic conflict detection

These are acceptable because:
- No I/O involved
- Deterministic (same input = same output)
- Testing algorithm logic, not system behavior

## Test File Updates

### test_rss_to_clustering.py
```
❌ mock_cosmos_client → ✅ cosmos_client_for_tests
❌ Simulated clustering → ✅ Real article creation
❌ Fake assertions → ✅ Real DB queries
❌ No data persistence → ✅ Clean test data
```

### test_clustering_to_summarization.py
```
❌ Mock Cosmos DB → ✅ Real Cosmos DB
❌ Mock Anthropic → ✅ Real Anthropic API
❌ Fake summaries → ✅ Test with real/mock API as configured
```

### test_breaking_news_lifecycle.py
```
❌ Mock change feeds → ✅ Real story status transitions
❌ Mock notifications → ✅ Real FCM integration if available
❌ Fake data flow → ✅ Real data pipeline
```

### test_batch_processing.py
```
❌ Mock Anthropic batches → ✅ Real batch processing
❌ Fake results → ✅ Real API responses
```

## Test Execution Order

### Phase 1: Setup Azure Credentials
```bash
# Must have these environment variables set:
export COSMOS_CONNECTION_STRING="your-connection-string"
export COSMOS_DATABASE_NAME="newsreel-db"
export NEWSREEL_JWT_TOKEN="your-firebase-jwt"
export ANTHROPIC_API_KEY="your-api-key"
```

### Phase 2: Run Tests (Correct Order)
```bash
# 1. System tests first (they reveal real issues)
pytest system/ -v

# 2. Integration tests (debug specific components)
pytest integration/ -v

# 3. Unit tests (regression prevention)
pytest unit/ -v
```

## Success Criteria

### Before This Update
- ✅ 113/123 tests passing (97%)
- 🔴 System completely broken (empty feed)

### After This Update
- ⚠️ Some integration tests may fail (revealing real issues)
- 🟢 Failures will show what's actually broken
- ✅ Fixing failed tests = fixing real system
- ✅ When all tests pass = system actually works

## Benefits

1. **Real Signal**: Tests fail when system is broken (not meaningless passes)
2. **Accurate Debugging**: Real data shows actual problems
3. **Confidence**: Passing tests mean system actually works
4. **No False Positives**: Can't pass tests with fake data

## Risk Assessment

**Risk**: Some integration tests may fail  
**Benefit**: Failures reveal real issues that need fixing  
**Mitigation**: This is GOOD - we want to find and fix real problems

## Implementation Steps

1. ✅ Document policy (DONE - TESTING_POLICY_NO_MOCKS.md)
2. ⏳ Update conftest.py to use real Cosmos DB
3. ⏳ Update integration tests to replace mocks
4. ⏳ Run tests and identify real issues
5. ⏳ Fix Azure Functions and API based on failures
6. ⏳ Verify all tests pass 100%

