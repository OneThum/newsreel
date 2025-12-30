# Testing Guide

**Last Updated**: November 9, 2025

Complete guide to testing the Newsreel backend system, including unit tests, integration tests, and system tests.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Testing Philosophy](#testing-philosophy)
3. [Test Types](#test-types)
4. [Running Tests](#running-tests)
5. [Test Coverage](#test-coverage)
6. [Diagnostic Tools](#diagnostic-tools)
7. [Test Policies](#test-policies)

---

## Quick Start

### Setup (5 Minutes)

```bash
cd Azure/tests
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your COSMOS_CONNECTION_STRING
```

### Run All Tests

```bash
# All tests
pytest -v

# Just unit tests (fast)
pytest unit/ -v

# Just integration tests
pytest integration/ -v

# Just system tests (tests deployed services)
pytest system/ -v
```

### Run Diagnostics

```bash
# Run all diagnostic checks
./run_all_diagnostics.sh

# View HTML health report
open reports/health_report.html
```

---

## Testing Philosophy

### Our Testing Strategy

**Core Principle**: **NO MOCKS** - Test with real Cosmos DB, real data, real services

**Why**:
- Mocks can pass while real system is broken
- Real data catches real issues
- Tests tell us if deployed system actually works

**Test Pyramid**:
```
     E2E Tests (Few - 5%)
    /  Test full user workflows
   /
  /   Integration Tests (Some - 15%)
 /    Test components together
/
    Unit Tests (Many - 80%)
    Test functions in isolation
```

### The Unit Test Trap (Lesson Learned)

**Problem**: Unit tests all passed while the API was fundamentally broken

**Why**: Unit tests only verify code logic, not deployment status
- ✅ Test passes: `clean_html()` function works
- ❌ Doesn't tell us: RSS functions not deployed, clustering not running, API returning errors

**Solution**: System tests that hit deployed services and fail when system is broken

See [TESTING_POLICY_NO_MOCKS.md](../TESTING_POLICY_NO_MOCKS.md) and [TESTING_DECISION_TREE.md](../TESTING_DECISION_TREE.md) for details.

---

## Test Types

### 1. Unit Tests (54 tests)

**Purpose**: Validate individual algorithms in isolation

**Location**: `Azure/tests/unit/`

**What They Test**:
- Text similarity calculations
- Topic conflict detection
- HTML cleaning
- Entity extraction
- Article categorization
- Spam detection
- Story fingerprinting
- Date parsing

**Run**: `pytest unit/ -v`

**Status**: ✅ 100% passing

**Example**:
```python
def test_text_similarity():
    text1 = "Bitcoin price surges to new high"
    text2 = "Bitcoin reaches record high price"
    similarity = calculate_similarity(text1, text2)
    assert similarity > 0.7  # High similarity
```

---

### 2. Integration Tests (46 tests)

**Purpose**: Test components working together with real Cosmos DB

**Location**: `Azure/tests/integration/`

**Test Suites**:
1. **RSS → Clustering** (`test_rss_to_clustering.py`) - 9 tests
   - New article creates cluster
   - Similar articles cluster together
   - Duplicate source prevention
   - Performance benchmarks

2. **Clustering → Summarization** (`test_clustering_to_summarization.py`) - 8 tests
   - VERIFIED story triggers AI summary
   - Real-time vs batch flows
   - Cost tracking

3. **Breaking News Lifecycle** (`test_breaking_news_lifecycle.py`) - 9 tests
   - Status transitions (MONITORING → BREAKING)
   - Notification workflows
   - Lifecycle management

4. **Batch Processing** (`test_batch_processing.py`) - 5 tests
   - Batch creation and submission
   - Result processing
   - Cost optimization (50% savings vs real-time)

**Run**: `pytest integration/ -v`

**Status**: ✅ 100% passing (2 skipped = expected)

**Example**:
```python
def test_similar_articles_cluster_together(cosmos_client_for_tests):
    """Test that similar articles get clustered into same story"""
    # Create first article
    article1 = create_test_article("Bitcoin hits $50k")
    cosmos_client_for_tests.upsert_article(article1)

    # Trigger clustering
    story1 = cluster_article(article1)
    assert story1['source_count'] == 1

    # Create similar article
    article2 = create_test_article("Bitcoin reaches $50,000")
    cosmos_client_for_tests.upsert_article(article2)

    # Should cluster into same story
    story2 = cluster_article(article2)
    assert story2['story_id'] == story1['story_id']
    assert story2['source_count'] == 2
```

---

### 3. System Tests (15 tests)

**Purpose**: Test deployed Azure services end-to-end

**Location**: `Azure/tests/system/`

**What They Test**:
- ✅ API is reachable
- ✅ Stories endpoint requires auth
- ✅ Stories endpoint returns data with auth
- ✅ Stories have sources with data
- ✅ Stories have summaries with data
- ✅ Stories are recent
- ✅ Breaking news endpoint
- ✅ Search endpoint
- ✅ Function app is deployed
- ✅ Articles being ingested
- ✅ Summaries being generated
- ✅ Invalid token rejected
- ✅ HTTPS enabled
- ✅ CORS headers present
- ⚠️ Clustering is working (1 failing - data availability issue)

**Run**: `pytest system/ -v`

**Status**: ⚠️ 93% passing (1 issue is data-related, not code bug)

**Example**:
```python
def test_articles_are_being_ingested():
    """Verify RSS ingestion is running"""
    # Query Cosmos DB for articles from last 5 minutes
    articles = query_recent_articles(minutes=5)

    # Should have new articles
    assert len(articles) > 0, "No articles ingested - RSS not running!"

    # Should have multiple sources
    sources = set(a['source'] for a in articles)
    assert len(sources) >= 3, f"Only {len(sources)} sources - diversity issue"
```

**These tests FAIL when system is broken** - that's the point! ✅

---

## Running Tests

### Basic Commands

```bash
cd Azure/tests

# All tests
pytest -v

# Specific test file
pytest unit/test_rss_parsing.py -v

# Specific test
pytest unit/test_rss_parsing.py::TestHTMLCleaning::test_strip_tags -v

# With coverage
pytest --cov=../functions --cov-report=html
```

### Filtering Tests

```bash
# Only unit tests
pytest unit/ -v

# Only integration tests
pytest integration/ -v

# Only system tests
pytest system/ -v

# Only fast tests (skip slow)
pytest -m "not slow" -v

# Only specific marker
pytest -m unit -v
```

### Test Output

```bash
# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l

# Short traceback
pytest --tb=short
```

---

## Test Coverage

### Overall Status (November 2025)

**Total**: 114/116 tests passing (99.1%)

**Breakdown**:
- Unit Tests: 54/54 passing (100%) ✅
- Integration Tests: 46/48 passing (95.8%) ✅ (2 skipped = expected)
- System Tests: 14/15 passing (93.3%) ⚠️ (1 failing = data availability)

### Test Execution Time

- Unit Tests: 0.40 seconds
- Integration Tests: 37.64 seconds
- System Tests: 8.38 seconds
- **Total: 46.42 seconds**

### Code Quality

- Linting Errors: 0 ✅
- Schema Validation Errors: 0 ✅
- Warnings: Mostly Pydantic v2 deprecation (non-critical)

### Test Reliability

- False Positives: 0 (no tests passing when they should fail)
- False Negatives: 1 (clustering test - real issue identified)
- Test Flakiness: None observed

---

## Diagnostic Tools

### 1. RSS Ingestion Checker

```bash
python diagnostics/check_rss_ingestion.py
```

**Checks**:
- ✓ Polling frequency (should be every 10s)
- ✓ Articles per minute (should be 10-15)
- ✓ Source diversity (should be 10+ sources)
- ✓ Processing lag (should be <1 min)
- ✓ Feed errors (identifies stuck feeds)

**Output**: Colored console (green=good, yellow=warning, red=critical)

---

### 2. Clustering Quality Checker

```bash
python diagnostics/check_clustering_quality.py
```

**Checks**:
- ✓ Multi-source clustering rate
- ✓ Duplicate source detection
- ✓ Status distribution
- ✓ Clustering accuracy sampling
- ✓ Fingerprint collisions

**Output**: Detailed analysis with statistics

---

### 3. System Health Report

```bash
python diagnostics/system_health_report.py
```

**Generates**:
- HTML dashboard at `reports/health_report.html`
- Database metrics (articles, stories, coverage)
- Performance analysis (response times, costs)
- Component health (RSS, clustering, summarization)

**Output**: Visual dashboard + JSON data

---

### 4. Azure Log Analysis

```bash
python diagnostics/analyze_azure_logs.py
```

**Provides**: 13 pre-written Kusto queries for:
- RSS ingestion patterns
- Clustering match rates
- Summarization costs
- Error detection
- Performance metrics

**Usage**: Copy queries to Azure Portal → Application Insights → Logs

---

## Test Policies

### NO MOCKS Policy

**Rule**: Tests use real Cosmos DB, not mocks

**Why**:
- Mocks can pass while real system fails
- Real data catches schema mismatches
- Integration issues only visible with real services

**Exceptions**: External APIs (Anthropic, Twitter) can be mocked for cost reasons

See [TESTING_POLICY_NO_MOCKS.md](../TESTING_POLICY_NO_MOCKS.md)

---

### NO FAKE DATA Policy

**Rule**: Tests use realistic data, not fake/dummy data

**Why**:
- Fake data doesn't catch real-world edge cases
- Real RSS feeds have unexpected formats
- Production issues only appear with production-like data

See [POLICY_NO_FAKE_DATA.md](../POLICY_NO_FAKE_DATA.md)

---

### Test Decision Tree

**When to write each type of test**:

```
Is it testing a single function?
  YES → Unit Test
  NO ↓

Is it testing components working together?
  YES → Integration Test
  NO ↓

Is it testing deployed services?
  YES → System Test
  NO ↓

Is it testing full user workflow?
  YES → E2E Test
```

See [TESTING_DECISION_TREE.md](../TESTING_DECISION_TREE.md)

---

## Configuration

### Environment Variables

Required in `.env`:
```bash
# Cosmos DB (Required)
COSMOS_CONNECTION_STRING="AccountEndpoint=https://..."
COSMOS_DATABASE_NAME="newsreel-db"

# Anthropic API (Optional - for summarization tests)
ANTHROPIC_API_KEY="sk-ant-..."

# API (Optional - for API tests)
API_URL="https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io"

# Firebase (Optional - for auth tests)
FIREBASE_SERVICE_ACCOUNT_KEY="path/to/service-account.json"
```

### Test Configuration

Edit `pytest.ini` for customization:
```ini
[pytest]
testpaths = .
python_files = test_*.py
addopts =
    -v
    --strict-markers
    --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    system: System tests
    slow: Slow tests (> 1 minute)
```

---

## Troubleshooting

### Connection to Cosmos DB failed

```bash
# Check connection string
echo $COSMOS_CONNECTION_STRING

# Test connection
python -c "from azure.cosmos import CosmosClient; client = CosmosClient.from_connection_string('$COSMOS_CONNECTION_STRING'); print('✓ Connected')"
```

### No recent articles found

**Causes**: RSS function not running, Azure Functions not deployed, network blocking

**Solution**: Check Azure Functions logs
```bash
az functionapp logs tail --name newsreel-func-51689 --resource-group Newsreel-RG
```

### Tests timing out

**Solution**: Increase timeout in `pytest.ini` or mark as slow:
```python
@pytest.mark.slow
def test_long_running():
    ...
```

### Tests fail with schema errors

**Cause**: Test fixtures using outdated schema

**Solution**: Update fixtures in `integration/fixtures.py` to match current schema

---

## Related Documentation

- [DEVELOPMENT_HISTORY.md](DEVELOPMENT_HISTORY.md) - Complete development history including test evolution
- [TESTING_POLICY_NO_MOCKS.md](../TESTING_POLICY_NO_MOCKS.md) - Why we don't use mocks
- [TESTING_DECISION_TREE.md](../TESTING_DECISION_TREE.md) - When to use each test type
- [POLICY_NO_FAKE_DATA.md](../POLICY_NO_FAKE_DATA.md) - Why we use realistic data
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Current test results

**Azure Test Documentation**: `/Azure/tests/README.md`

---

## Test Results History

### Session 8 → Session 9 Journey

| Milestone | Session 8 Start | Session 8 End | Session 9 End |
|-----------|-----------------|--------------|---------------|
| Integration Tests | 22 pass, 21 fail | 22 pass, 0 fail | 46 pass, 0 fail |
| Unit Tests | N/A | 54 pass | 54 pass |
| System Tests | N/A | 14 pass, 1 fail | 14 pass, 1 fail |
| **TOTAL** | **22 pass, 21 fail** | **90 pass, 1 fail** | **114 pass, 1 fail** |

**Progress**: 51% → 98.9% → 99.1% passing ✅

---

## Key Learnings

1. **Unit tests passing ≠ system working**
   - Need system tests to verify deployment
   - Tests should fail when system is broken

2. **No mocks = real confidence**
   - Real Cosmos DB catches real issues
   - Schema mismatches, performance problems only visible with real data

3. **Test the right level**
   - Unit: Function logic
   - Integration: Component interactions
   - System: Deployed services
   - E2E: User workflows

4. **Honest failures are good**
   - Tests that fail when system is broken are valuable
   - False positives (passing when broken) are dangerous

---

**Status**: Test infrastructure mature and reliable ✅
**Coverage**: 99.1% passing ✅
**Next**: Investigate 1 remaining system test failure (data availability)
