# Newsreel API Test Harness

**Complete diagnostic and testing suite for Newsreel backend**

**Status**: ✅ **Phase 1 Complete** - Diagnostics ready to use, critical bugs identified

---

## Quick Start (5 Minutes)

```bash
cd Azure/tests
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your COSMOS_CONNECTION_STRING
./run_all_diagnostics.sh
open reports/health_report.html
```

**That's it!** You'll have a complete health report with:
- RSS ingestion status
- Clustering quality analysis  
- System metrics dashboard
- Bug identification

---

## What This Provides

### ✅ Immediate Diagnostics (Run Now)

**4 diagnostic scripts** that identify issues in seconds:

1. **`check_rss_ingestion.py`** - Is RSS polling working? (10s cycle, 3 feeds)
2. **`check_clustering_quality.py`** - Are duplicates prevented? Multi-source rate?
3. **`system_health_report.py`** - HTML dashboard with all metrics
4. **`analyze_azure_logs.py`** - 13 pre-written Azure queries

**Run all**: `./run_all_diagnostics.sh`

### ✅ Unit Tests (Ready to Use)

**2 test suites** with 20+ test classes:

1. **`test_rss_parsing.py`** - RSS parsing, HTML cleaning, spam detection
2. **`test_clustering_logic.py`** - Similarity, topic conflicts, thresholds

**Run**: `pytest unit/ -v`

### ✅ Integration Tests (Phase 2 Complete)

**4 test suites** testing component interactions:

1. **`test_rss_to_clustering.py`** - RSS → Clustering pipeline (15 tests)
2. **`test_clustering_to_summarization.py`** - Clustering → AI summary (12 tests)
3. **`test_breaking_news_lifecycle.py`** - Breaking news workflow (11 tests)
4. **`test_batch_processing.py`** - Batch summarization (10 tests)

**Run**: `pytest integration/ -v`

### ✅ Bug Documentation (Review Now)

**`reports/BUGS_DISCOVERED.md`** contains:
- **12 bugs identified** through code review
- **Root cause analysis** for each
- **Proposed fixes** with code examples
- **$1,800-3,000/month savings** potential

**Critical bugs**:
- 🔴 **Bug #1**: Duplicate sources in stories
- 🔴 **Bug #2**: Stories missing sources  
- 🟡 **Bug #7**: $70-120/day wasted on headline updates

---

## Directory Structure

```
tests/
├── README.md                 # This file ⭐
├── QUICK_START.md            # 5-minute detailed guide
├── run_all_diagnostics.sh   # Run all health checks ⭐
├── requirements.txt          # Dependencies
├── pytest.ini                # Test configuration
├── conftest.py               # Shared fixtures
│
├── diagnostics/              # Diagnostic scripts ⭐
│   ├── check_rss_ingestion.py
│   ├── check_clustering_quality.py
│   ├── system_health_report.py
│   └── analyze_azure_logs.py
│
├── unit/                     # Unit tests (Phase 1)
│   ├── test_rss_parsing.py
│   └── test_clustering_logic.py
│
├── integration/              # Integration tests (Phase 2) ⭐
│   ├── __init__.py
│   ├── fixtures.py                  # Shared test data
│   ├── test_rss_to_clustering.py
│   ├── test_clustering_to_summarization.py
│   ├── test_breaking_news_lifecycle.py
│   └── test_batch_processing.py
│
└── reports/                  # Generated reports
    ├── BUGS_DISCOVERED.md           # Bug analysis ⭐
    └── health_report.html           # Visual dashboard
```

---

## Usage

### 1. Install Dependencies

```bash
cd Azure/tests
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:
```bash
cp .env.example .env
```

Add required credentials:
```bash
COSMOS_CONNECTION_STRING="AccountEndpoint=https://..."
COSMOS_DATABASE_NAME="newsreel-db"
```

### 3. Run Diagnostics (Primary Use)

```bash
# Run all diagnostics ⭐
./run_all_diagnostics.sh

# Or individually:
python diagnostics/check_rss_ingestion.py
python diagnostics/check_clustering_quality.py
python diagnostics/system_health_report.py

# View HTML report
open reports/health_report.html
```

### 4. Run Tests (Optional)

```bash
# All unit tests (Phase 1)
pytest unit/ -v

# All integration tests (Phase 2)
pytest integration/ -v

# Run specific test file
pytest unit/test_rss_parsing.py -v
pytest integration/test_rss_to_clustering.py -v

# Run all tests
pytest -v

# With coverage
pytest --cov=../functions --cov-report=html
```

---

## What You'll Learn

### RSS Ingestion Health

**Expected**:
- Articles per minute: 10-15
- Unique sources: 10+
- Processing lag: <1 minute
- Polling every 10 seconds

**If broken**:
- ✗ No articles = RSS stopped
- ✗ <5 sources = Feed diversity issue
- ✗ Lag >5 min = Clustering bottleneck

### Clustering Quality

**Expected**:
- Multi-source rate: 20-40%
- Average sources per story: 1.5-2.5
- No duplicate sources
- Status distribution: mostly VERIFIED/DEVELOPING

**If broken**:
- ✗ Duplicate rate >10% = Prevention failing
- ✗ Multi-source <15% = Threshold too high
- ✗ MONITORING >50% = Too many single-source stories

### Summarization Coverage

**Expected**:
- Coverage: 30-50%
- Generation time: <5 seconds
- Cost: $5-10/day
- AI refusal rate: <5%

**If broken**:
- ✗ Coverage <20% = Backfill disabled or slow
- ✗ High refusals = Content quality issues
- ✗ Cost >$15/day = Check headline churn bug

---

## Critical Findings

### 🔴 Bug #1: Duplicate Sources (P0)
**Issue**: Same news source appearing multiple times in story clusters  
**Location**: `function_app.py` lines 873-896  
**Impact**: Violates multi-source verification principle  
**Fix**: Consistent source extraction logic

### 🔴 Bug #2: Missing Sources (P0)
**Issue**: Stories with no sources or empty array  
**Location**: Throughout `stories.py`  
**Impact**: API returns "0 sources", breaks iOS app  
**Fix**: Add validation, cleanup existing data

### 🟡 Bug #7: Headline Churn (P1)
**Issue**: Regenerating headlines on every source addition  
**Location**: `function_app.py` lines 1020-1036  
**Impact**: **$70-120/day wasted** ($1,800-3,000/month)  
**Fix**: Add caching, only update when necessary

### 🟠 Bug #8: Low Coverage (P2)
**Issue**: Only 33.8% summary coverage vs 50% target  
**Impact**: Poor user experience  
**Fix**: Enable backfill or increase batch frequency

---

## Diagnostic Tools

### RSS Ingestion Checker

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

### Clustering Quality Checker

```bash
python diagnostics/check_clustering_quality.py
```

**Checks**:
- ✓ Multi-source clustering rate
- ✓ Duplicate source detection ⚠️ Known issue
- ✓ Status distribution
- ✓ Clustering accuracy sampling
- ✓ Fingerprint collisions

**Output**: Detailed analysis with statistics

### System Health Report

```bash
python diagnostics/system_health_report.py
```

**Generates**:
- HTML dashboard at `reports/health_report.html`
- Database metrics (articles, stories, coverage)
- Performance analysis (response times, costs)
- Component health (RSS, clustering, summarization)

**Output**: Visual dashboard + JSON data

### Azure Log Analysis

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

## Unit Tests

### RSS Parsing Tests

**File**: `unit/test_rss_parsing.py`

**Test Classes** (12 total):
- `TestHTMLCleaning` - Strip tags, entities, whitespace
- `TestEntityExtraction` - Location/event/keyword extraction
- `TestArticleCategorization` - Category detection
- `TestSpamDetection` - Filter promotional content
- `TestTextTruncation` - Word boundary truncation
- `TestIDGeneration` - Deterministic article IDs
- `TestStoryFingerprinting` - Consistent fingerprints
- `TestDateParsing` - RFC 822 date handling

**Run**: `pytest unit/test_rss_parsing.py -v`

### Clustering Logic Tests

**File**: `unit/test_clustering_logic.py`

**Test Classes** (8 total):
- `TestTextSimilarity` - Similarity calculations
- `TestTopicConflictDetection` - Prevent false clustering
- `TestClusteringThresholds` - 70% threshold validation
- `TestStoryMatching` - Fingerprint + fuzzy matching
- `TestDuplicateSourcePrevention` - Source deduplication
- `TestClusteringPerformance` - Speed benchmarks

**Run**: `pytest unit/test_clustering_logic.py -v`

---

## Azure Application Insights Queries

Run `python diagnostics/analyze_azure_logs.py` to get these queries:

### RSS Ingestion
```kusto
traces
| where message contains "RSS ingestion complete"
| where timestamp > ago(1h)
| summarize count() by bin(timestamp, 1m)
| render timechart
```

### Clustering Matches
```kusto
traces
| where message contains "CLUSTERING"
| where timestamp > ago(1h)
| summarize 
    matches = countif(message contains "MATCH"),
    new = countif(message contains "new story")
| extend match_rate = matches * 100.0 / (matches + new)
```

### Summarization Costs
```kusto
traces
| where message contains "Generated summary"
| where timestamp > ago(24h)
| extend cost = extract("\\$([0-9.]+)", 1, message)
| summarize 
    total_cost = sum(todouble(cost)),
    summary_count = count()
```

### Error Summary
```kusto
traces
| where severityLevel >= 3
| where timestamp > ago(24h)
| summarize count() by severityLevel, operation_Name
| order by count_ desc
```

---

## Integration Tests (Phase 2)

**Status**: ✅ **Complete** - 48 tests across 4 suites

### Test Suites

1. **RSS → Clustering** (`test_rss_to_clustering.py`) - 15 tests
   - New article → cluster creation
   - Similar article clustering
   - Duplicate source prevention
   - Performance benchmarks

2. **Clustering → Summarization** (`test_clustering_to_summarization.py`) - 12 tests
   - VERIFIED story → AI summary
   - Real-time vs batch flows
   - Cost tracking (50% batch savings)

3. **Breaking News Lifecycle** (`test_breaking_news_lifecycle.py`) - 11 tests
   - Status transitions (VERIFIED → BREAKING)
   - Notification workflows
   - Lifecycle management

4. **Batch Processing** (`test_batch_processing.py`) - 10 tests
   - Batch creation and submission
   - Result processing
   - Cost optimization

**Run**: `pytest integration/ -v`

**See**: `PHASE_2_SUMMARY.md` for complete documentation

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

# Azure (Optional - for automated log querying)
AZURE_SUBSCRIPTION_ID="..."
AZURE_APP_INSIGHTS_ID="..."
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
    slow: Slow tests (> 1 minute)
```

---

## Next Steps

### Immediate (Today)
1. ✅ Run: `./run_all_diagnostics.sh`
2. ✅ Review: `reports/health_report.html`  
3. ✅ Read: `reports/BUGS_DISCOVERED.md`

### This Week (2-3 days)
4. Fix Bug #1 (duplicate sources)
5. Fix Bug #2 (missing sources)
6. Fix Bug #7 (headline churn) - **saves $60-100/day**

### Ongoing
7. Run diagnostics weekly
8. Monitor Azure Application Insights
9. Track cost reduction

---

## ROI Analysis

**Investment**:
- Setup: 5 minutes
- Review findings: 30 minutes  
- Fix critical bugs: 2-3 days

**Return**:
- **Cost savings**: $1,800-3,000/month (headline churn fix)
- **Data quality**: Correct sources in all stories
- **User experience**: API returns complete data
- **Visibility**: Know exactly what's working/broken

**Payback**: Immediate (cost savings alone justify effort)

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

---

## Future Phases (Not Yet Implemented)

### Phase 2: Integration Tests
- RSS → Clustering integration
- Clustering → Summarization flow
- Breaking news lifecycle tests
- Batch processing validation

### Phase 3: End-to-End Tests
- Full article lifecycle
- API client flows
- Multi-component workflows

### Phase 4: Performance Tests
- RSS concurrency (100+ feeds)
- Clustering speed benchmarks
- API load testing
- Database throughput

---

## Support

**Documentation**:
- This file - Complete reference
- `QUICK_START.md` - Step-by-step setup
- `reports/BUGS_DISCOVERED.md` - Detailed bug analysis
- `../TESTING_EXECUTIVE_SUMMARY.md` - Executive overview

**Azure Resources**:
- Portal: https://portal.azure.com
- Application Insights: Check logs for real-time issues
- Cosmos DB: Data Explorer for queries

**Contact**: dave@onethum.com

---

## Summary

This test harness provides **immediate actionable diagnostics** to identify and fix critical bugs:

✅ **Ready to use** - Setup in 5 minutes  
✅ **Identifies bugs** - 12 bugs documented with fixes  
✅ **Saves money** - $1,800-3,000/month potential savings  
✅ **Improves quality** - Find duplicate sources, missing data  
✅ **Tracks performance** - RSS rate, clustering quality, AI costs  

**Start here**: `./run_all_diagnostics.sh`

**Then fix**: Bugs #1, #2, #7 (critical issues with high ROI)

---

**Version**: 1.0 (Phase 1 Complete)  
**Last Updated**: October 26, 2025  
**Status**: ✅ Production Ready

