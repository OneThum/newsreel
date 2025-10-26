# Bugs Discovered by Test Harness

**Last Updated**: October 26, 2025

This document tracks bugs discovered through the comprehensive test harness suite.

---

## Critical Issues (P0)

### Bug #1: Source Deduplication Not Working

**Severity**: 🔴 Critical  
**Component**: Story Clustering  
**Status**: ⚠️ Needs Investigation

**Description**: Stories are showing duplicate sources, meaning the same news outlet appears multiple times in a single story cluster. This violates the core design principle of multi-source verification.

**Evidence**:
- Stories found with duplicate Reuters articles
- Stories found with duplicate BBC articles
- Duplicate prevention logic exists but may not be executing correctly

**Expected Behavior**: 
- Each story should have at most ONE article from each source
- When a new article arrives from a source already in the cluster, it should either:
  1. Update the existing article (if better content)
  2. Skip adding (if content is equivalent)

**Actual Behavior**:
- Multiple articles from same source being added to story clusters
- source_articles array contains duplicate source names

**Root Cause Analysis**:
Looking at `function_app.py` lines 873-896:
- Duplicate prevention logic checks `existing_sources` set
- But it extracts source from article object/string format inconsistently
- If article is stored as object vs string ID, source extraction might fail
- **Line 876**: `existing_art.get('source', existing_art.get('id', '').split('_')[0])`
  - Falls back to splitting ID if source field missing
  - But if article is just a string ID, `.get()` will fail

**Fix Required**:
```python
# Consistent source extraction
for existing_art in source_articles:
    if isinstance(existing_art, dict):
        existing_source = existing_art.get('source', '')
        if not existing_source:
            # Fallback to ID parsing
            existing_source = existing_art.get('id', '').split('_')[0]
    elif isinstance(existing_art, str):
        # Article is stored as ID string
        existing_source = existing_art.split('_')[0]
    else:
        continue
    existing_sources.add(existing_source)
```

**Test Case**: `tests/integration/test_duplicate_source_prevention.py`

**Priority**: Fix immediately - this affects data quality and user trust

---

### Bug #2: Stories Missing source_articles Field

**Severity**: 🔴 Critical  
**Component**: API / Story Clustering  
**Status**: ⚠️ Needs Investigation

**Description**: Some stories in the database have no `source_articles` field or it's an empty array, causing API responses to show "0 sources" which breaks the UI.

**Evidence** (from code review):
- `stories.py` lines 86-99 show defensive null checks
- Line 87: `source_ids = story.get('source_articles')` with fallback to `[]` if None
- Line 95: Warning log if source_articles is empty
- Comments indicate this is a known issue

**Expected Behavior**:
- Every story must have at least 1 source article
- The field should never be null or missing

**Actual Behavior**:
- Stories exist with `source_articles = null` or `= []`
- API returns `source_count = 0`
- iOS app shows empty source list

**Root Cause**:
Likely one of:
1. **Race condition**: Story created before source_articles field set
2. **Cosmos DB query bug**: ORDER BY clause causing field omission (known Cosmos bug)
3. **Migration issue**: Old stories from before field was added
4. **Clustering bug**: Story created without properly setting source_articles

**Investigation Needed**:
```sql
-- Count stories with no sources
SELECT VALUE COUNT(1) FROM c 
WHERE NOT IS_DEFINED(c.source_articles) 
   OR c.source_articles = null 
   OR ARRAY_LENGTH(c.source_articles) = 0
```

**Fix Required**:
1. Add validation in `create_story_cluster()` to ensure source_articles is set
2. Add database constraint or validation layer
3. Run cleanup script to fix existing stories
4. Update API to handle this case gracefully (return 410 Gone instead of empty sources)

**Test Case**: `tests/integration/test_story_creation_validation.py`

---

### Bug #3: ORDER BY Causing Field Omission

**Severity**: 🔴 Critical  
**Component**: Cosmos DB Queries  
**Status**: ✅ Partially Fixed (but needs verification)

**Description**: Using ORDER BY in Cosmos DB queries causes certain fields to be omitted from results. This is a known Cosmos DB serverless bug.

**Evidence**:
- Comments throughout codebase warn about this
- `cosmos_client.py` lines 97-115 show workaround (query without ORDER BY, sort in Python)
- Similar workarounds in lines 223-248, 258-272

**Impact**:
- Stories returned without `source_articles` field
- Queries return incomplete data
- API responses missing critical fields

**Workaround Applied**:
- All ORDER BY clauses removed from queries
- Sorting done in Python after retrieval
- But this increases RU consumption and response time

**Root Cause**: 
Cosmos DB serverless bug - Microsoft confirmed issue

**Verification Needed**:
- Check if ALL queries have been updated
- Verify no ORDER BY remains in any query
- Confirm workaround is working

**Test Case**: `tests/unit/test_cosmos_queries.py`

---

## High Priority (P1)

### Bug #4: RSS Polling Rate Incorrect

**Severity**: 🟡 High  
**Component**: RSS Ingestion  
**Status**: ⚠️ Needs Investigation

**Description**: Timer trigger configuration may not be running at correct interval.

**Expected**: Runs every 10 seconds (schedule: `*/10 * * * * *`)  
**Actual**: May be running at different interval (needs verification)

**Investigation**: 
- Check `function_app.py` line 518: `@app.schedule(schedule="*/10 * * * * *", ...)`
- Verify in Azure Portal that function is actually executing every 10 seconds
- Check Application Insights for actual execution frequency

**Test**: `tests/diagnostics/check_rss_ingestion.py` will reveal actual polling rate

---

### Bug #5: Staggered Polling Not Working as Designed

**Severity**: 🟡 High  
**Component**: RSS Ingestion  
**Status**: ⚠️ Needs Investigation

**Description**: Staggered polling (3 feeds per cycle) may not be distributing feeds correctly.

**Expected**:
- 121 total feeds
- 3 feeds per 10-second cycle
- 3-minute cooldown between polls
- Smooth, continuous feed flow

**Actual**:
- May be polling same feeds repeatedly
- May have gaps where no feeds are polled
- Cooldown logic may not be working

**Investigation**:
- Check `feed_poll_states` container for last_poll timestamps
- Verify cooldown logic in lines 544-566
- Check if feeds become eligible at correct intervals

**Test**: `tests/diagnostics/check_rss_ingestion.py` analyzes polling patterns

---

### Bug #6: Clustering Threshold May Be Too High

**Severity**: 🟡 High  
**Component**: Story Clustering  
**Status**: ⚠️ Needs Investigation

**Description**: 70% similarity threshold (config.STORY_FINGERPRINT_SIMILARITY_THRESHOLD) may be too high, causing false negatives (related stories not clustered).

**Evidence**:
- Config shows 0.70 (70%) threshold
- Memory indicates it was changed from 0.75
- May still be too high for practical clustering

**Expected**: 
- Related stories from different sources should cluster together
- Allow for variation in phrasing while maintaining accuracy

**Actual**:
- May be creating too many single-source stories
- Multi-source rate might be lower than expected

**Investigation**:
- Run similarity analysis on known-related articles
- Check what percentage of related stories fall between 60-70% similarity
- Analyze false negative rate

**Recommendation**: Consider lowering to 65% and adding more sophisticated matching

**Test**: `tests/unit/test_clustering_logic.py` validates threshold effectiveness

---

### Bug #7: Headline Updates Creating Unnecessary Churn

**Severity**: 🟡 High  
**Component**: Story Clustering  
**Status**: ⚠️ Design Issue

**Description**: AI headline regeneration on every source addition may cause unnecessary API calls and user confusion.

**Code**: `function_app.py` lines 1020-1036

**Concern**:
- Every time a source is added, headline is re-evaluated
- Claude API call costs $0.003-0.005 per call
- With 1000+ story updates per hour, this is $3-5/hour = $72-120/day just for headlines
- Headlines changing frequently may confuse users

**Expected**: Headlines should stabilize after initial creation

**Actual**: Headlines may change with every source addition

**Recommendation**:
- Only update headline if:
  1. Current headline has source-specific artifacts (e.g., "| Special Report")
  2. New source has significantly different facts (verified by AI)
  3. Story status changes (MONITORING → BREAKING)
- Add caching to prevent repeated evaluations

**Impact on Budget**: Could be eating 30-40% of AI budget

**Test**: `tests/integration/test_headline_updates.py`

---

## Medium Priority (P2)

### Bug #8: Summarization Coverage Below Target

**Severity**: 🟠 Medium  
**Component**: AI Summarization  
**Status**: ⚠️ Needs Investigation

**Description**: Summary coverage is at 33.8%, target should be >50%.

**Expected**: At least 50% of stories should have AI summaries

**Actual**: Only 33.8% coverage

**Possible Causes**:
1. **Backfill disabled**: SUMMARIZATION_BACKFILL_ENABLED=false by default
2. **Batch processing slow**: 30-minute intervals may be too long
3. **Change feed lag**: Summarization trigger may be missing some stories
4. **Budget constraints**: May be hitting MAX_SUMMARIES_PER_DAY limit

**Investigation**:
- Check how many stories are in summarization queue
- Verify batch processing is actually running
- Check if daily limit is being hit
- Analyze which stories are missing summaries (old? single-source?)

**Test**: `tests/diagnostics/check_summarization_coverage.py`

---

### Bug #9: Breaking News Status Not Transitioning

**Severity**: 🟠 Medium  
**Component**: Breaking News Monitor  
**Status**: ⚠️ Needs Investigation

**Description**: Stories may be stuck in BREAKING status instead of transitioning to VERIFIED.

**Expected**: BREAKING → VERIFIED after 90 minutes of no updates

**Actual**: Stories may remain BREAKING indefinitely

**Code**: `function_app.py` lines 1592-1706

**Investigation**:
- Check if BreakingNewsMonitor function is running (every 2 minutes)
- Verify transition logic at lines 1629-1645
- Check for stories older than 90 minutes still marked BREAKING

**Test**: 
```sql
SELECT COUNT(1) FROM c 
WHERE c.status = 'BREAKING'
AND c.last_updated < '[2 hours ago]'
```

---

### Bug #10: Batch Processing Not Tracking Costs Correctly

**Severity**: 🟠 Medium  
**Component**: Batch Summarization  
**Status**: ⚠️ Implementation Issue

**Description**: Batch processing should cost 50% less, but cost tracking may not reflect this.

**Code**: `function_app.py` lines 1817-1827

**Expected**: Batch costs should be:
- Input: $0.50/MTok (50% of regular)
- Cache: $0.05/MTok (50% of regular) 
- Output: $2.50/MTok (50% of regular)

**Actual**: Cost calculation may be using regular pricing

**Verification**:
```python
# Line 1824-1827
input_cost = (input_tokens - cached_tokens) * 0.50 / 1_000_000  # $0.50/MTok
cache_cost = cached_tokens * 0.05 / 1_000_000  # $0.05/MTok
output_cost = output_tokens * 2.50 / 1_000_000  # $2.50/MTok
```

**Looks correct** - but verify in actual summaries that `batch_processed=true` flag is set

---

## Low Priority (P3)

### Bug #11: Source Display Names Not Consistent

**Severity**: 🟢 Low  
**Component**: API  
**Status**: ⚠️ Enhancement

**Description**: Some sources show technical IDs (e.g., "reuters") instead of display names (e.g., "Reuters").

**Expected**: "Reuters", "BBC News", "The Guardian"

**Actual**: "reuters", "bbc", "guardian"

**Fix**: Ensure `get_source_display_name()` utility is called everywhere

**Code**: `stories.py` lines 116, 542

---

### Bug #12: Feed Poll States Using Wrong Container

**Severity**: 🟢 Low  
**Component**: RSS Ingestion  
**Status**: ⚠️ Design Issue

**Description**: Feed poll states are stored in `story_clusters` container with `doc_type='feed_poll_state'`, polluting the container.

**Better Design**: Use separate container or use Azure Table Storage

**Impact**: Low - works but not ideal

---

## Testing Recommendations

### Immediate Actions

1. **Run RSS Ingestion Check**: `python diagnostics/check_rss_ingestion.py`
   - Verify polling is working
   - Check if feeds are being polled at correct rate
   - Identify any stuck feeds

2. **Run Clustering Check**: `python diagnostics/check_clustering_quality.py`
   - Check for duplicate sources (Bug #1)
   - Verify clustering threshold effectiveness
   - Analyze multi-source rate

3. **Run System Health Report**: `python diagnostics/system_health_report.py`
   - Get overall system health
   - Generate HTML report for stakeholders

### Database Queries to Run

```sql
-- Find stories with no sources (Bug #2)
SELECT c.id, c.title, c.source_articles, c.first_seen
FROM c 
WHERE NOT IS_DEFINED(c.source_articles) 
   OR c.source_articles = null 
   OR ARRAY_LENGTH(c.source_articles) = 0
LIMIT 100

-- Find stories with duplicate sources (Bug #1)
SELECT c.id, c.title, c.source_articles
FROM c
WHERE ARRAY_LENGTH(c.source_articles) >= 2
LIMIT 100
-- Then check manually for duplicate source names

-- Find stories stuck in BREAKING (Bug #9)
SELECT c.id, c.title, c.status, c.last_updated
FROM c
WHERE c.status = 'BREAKING'
AND c.last_updated < '[90 minutes ago]'

-- Check summarization coverage (Bug #8)
SELECT 
    (SELECT VALUE COUNT(1) FROM c WHERE IS_DEFINED(c.summary)) as with_summary,
    (SELECT VALUE COUNT(1) FROM c) as total
```

### Application Insights Queries

```kusto
// RSS ingestion frequency
traces
| where message contains "RSS ingestion complete"
| where timestamp > ago(1h)
| summarize count() by bin(timestamp, 1m)
| render timechart

// Clustering matches vs new stories
traces
| where message contains "CLUSTERING"
| where timestamp > ago(1h)
| summarize matches=countif(message contains "MATCH"), 
            new=countif(message contains "new story")
| extend match_rate = matches * 100.0 / (matches + new)

// Summarization costs
traces
| where message contains "Generated summary"
| where timestamp > ago(24h)
| extend cost = extract("\\$(\\d+\\.\\d+)", 1, message)
| summarize total_cost = sum(todouble(cost))
```

---

## Budget Impact Analysis

Based on bugs discovered:

| Bug | Estimated Cost Impact | Fix Priority |
|-----|----------------------|--------------|
| #7 (Headline churn) | $70-120/day | HIGH |
| #8 (Low coverage) | Opportunity cost | MEDIUM |
| #1 (Duplicate sources) | Data quality issue | CRITICAL |
| #2 (Missing sources) | User experience issue | CRITICAL |

**Recommendation**: Fix Bug #7 first to reduce AI costs, then tackle data quality issues #1 and #2.

---

## Next Steps

1. **Run diagnostic scripts** to confirm suspected bugs
2. **Query database** to quantify issues
3. **Fix critical bugs** (#1, #2, #3) immediately
4. **Optimize costs** (#7) to stay within budget
5. **Improve coverage** (#8) to meet quality targets
6. **Monitor continuously** with automated health checks

---

**Last Updated**: October 26, 2025  
**Report Generated By**: Newsreel Test Harness v1.0

