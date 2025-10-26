# Backend Testing Focus: Complete Data Pipeline Validation

## Objective
**Run test harnesses against the API until we have:**
- ✅ Fully clustered stories (2+ sources per story)
- ✅ Fully categorized stories (correct category assigned)
- ✅ Fully summarized stories (AI summaries generated)
- ✅ Fully sourced stories (all source articles linked)
- ✅ Frequently updating stories (as RSS feeds reinforce with new articles)

## Scope
- **What to test:** Data pipeline, clustering, summarization, API response quality
- **What to ignore:** iOS app display (will fix later)
- **Success criteria:** API returns production-quality stories, fully formed and updating

---

## Data Pipeline Validation Checklist

### Stage 1: RSS Ingestion ✅ Must Pass
```
✅ Raw articles being inserted into raw_articles container
✅ Articles have correct fingerprints
✅ Articles have proper metadata (source, category, title, etc)
✅ Articles marked as processed=false before clustering
✅ All 100 RSS sources being polled regularly (not just 1-2)
```

### Stage 2: Change Feed Triggers ✅ Must Pass
```
✅ Change feed trigger firing when articles inserted
✅ StoryClusteringChangeFeed processing documents
✅ Leases container created and tracking progress
✅ No trigger errors in logs
```

### Stage 3: Story Clustering ✅ Must Pass
```
✅ Stories being created in story_clusters container
✅ Articles matching by fingerprint
✅ Articles matching by similarity (fuzzy title matching)
✅ Stories with 2+ sources (DEVELOPING status)
✅ Stories with 3+ sources (BREAKING/VERIFIED status)
✅ Each story has proper status transitions
```

### Stage 4: Story Status Lifecycle ✅ Must Pass
```
✅ New stories start as MONITORING (1 source)
✅ Stories transition to DEVELOPING (2 sources)
✅ Stories transition to BREAKING (3+ sources, <30 min old)
✅ Stories transition to VERIFIED (3+ sources, >30 min old)
✅ BreakingNewsMonitor updating statuses correctly
```

### Stage 5: Summarization ✅ Must Pass
```
✅ Stories needing summaries identified correctly
✅ AI summaries generated via Anthropic
✅ Summaries stored in story_clusters
✅ Summary quality acceptable (multi-sentence, informative)
```

### Stage 6: API Feed Endpoint ✅ Must Pass
```
✅ Returns stories with status != MONITORING
✅ All required fields present (title, summary, sources, category, etc)
✅ Sources properly linked (with source_name from display names)
✅ Stories properly formatted for consumption
```

### Stage 7: Story Reinforcement ✅ Must Pass
```
✅ New RSS articles adding to existing stories
✅ Story metadata updating (last_updated, source_count)
✅ Status maintained correctly as sources grow
✅ No duplicate sources in same story
```

---

## Testing Strategy

### Test Execution Order (One at a Time)

```
1️⃣  Diagnostic Check
    Run: diagnose-clustering-pipeline.py
    Verify: Which stage is broken
    
    If articles empty → Fix RSS ingestion
    If stories empty → Fix change feeds
    If stories all MONITORING → Fix clustering
    If API empty → Fix API query

2️⃣  System Tests (Against Real API)
    Run: pytest system/ -v
    Expected: All 13 passing
    Look for: Actual data flowing

3️⃣  Integration Tests (Real Cosmos DB)
    Run: pytest integration/ -v
    Expected: All 59 passing with real data
    Look for: Component interactions work

4️⃣  Unit Tests (Regression)
    Run: pytest unit/ -v
    Expected: All 54 passing
    Look for: No logic regressions
```

### Testing After Each Fix

After applying each fix:

```bash
# 1. Quick verification with diagnostic script
python3 Azure/scripts/diagnose-clustering-pipeline.py

# 2. Check logs for errors
az functionapp logs tail --name newsreel-func-51689 --resource-group Newsreel-RG

# 3. Run system tests
cd Azure/tests
pytest system/ -v

# 4. Check for specific data issues
pytest system/test_deployed_api.py::TestDataPipeline -v

# 5. If passed, run integration tests
pytest integration/ -v
```

---

## Data Pipeline Stages & Validation

### Stage 1: RSS Ingestion (Every 10-15 Seconds)

**What happens:**
- Timer trigger runs every 10-15 seconds
- Polls 2-3 RSS sources per cycle
- Parses entries
- Creates RawArticle records
- Stores in Cosmos DB raw_articles container

**Test what's created:**
```sql
-- Cosmos DB Query
SELECT TOP 100 c.id, c.source, c.title, c.processed, c._ts 
FROM c 
WHERE c.published_at > "NOW-1hour"
ORDER BY c._ts DESC
```

**Expected results:**
- ✅ Multiple articles per minute
- ✅ Various sources represented
- ✅ Articles have fingerprints
- ✅ processed = false

**If broken:**
- ❌ No articles appearing
- ❌ Ingestion function not running
- ❌ Connection string issue
- ❌ RSS parsing error

**Fix: See INFRASTRUCTURE_FIX_PLAN.md Scenario A**

---

### Stage 2: Change Feed Triggers

**What happens:**
- Change feed listener watches raw_articles
- When articles inserted, trigger fires
- StoryClusteringChangeFeed processes documents
- Change feed leases track progress

**Test what's created:**
```sql
-- Check leases
SELECT * FROM c LIMIT 10
-- (from leases container)

-- Check stories created
SELECT TOP 100 c.id, c.status, c.source_articles, c._ts 
FROM c 
WHERE c._ts > "NOW-1hour"
ORDER BY c._ts DESC
```

**Expected results:**
- ✅ Leases container updated regularly
- ✅ Stories appearing in story_clusters
- ✅ No errors in Function App logs

**If broken:**
- ❌ Articles exist but no stories
- ❌ Leases container missing
- ❌ Change feed disabled
- ❌ Trigger function crashed

**Fix: See INFRASTRUCTURE_FIX_PLAN.md Scenario B**

---

### Stage 3: Story Clustering

**What happens:**
- Articles compared by fingerprint
- Fingerprint matches → same story
- No fingerprint match → fuzzy text similarity
- Similarity > 75% + no topic conflict → cluster
- Stories created with status MONITORING (1 source)

**Test what's created:**
```sql
-- Check story clustering
SELECT c.id, c.status, ARRAY_LENGTH(c.source_articles) as source_count, c.title
FROM c
WHERE ARRAY_LENGTH(c.source_articles) >= 1
ORDER BY ARRAY_LENGTH(c.source_articles) DESC

-- Should see:
-- - Stories with 1 source (MONITORING)
-- - Stories with 2+ sources (DEVELOPING)
-- - Stories with 3+ sources (BREAKING/VERIFIED)
```

**Expected results:**
- ✅ Stories with multiple sources
- ✅ Status distribution: mostly 2-3 sources
- ✅ No duplicate sources per story

**If broken:**
- ❌ All stories have 1 source (MONITORING only)
- ❌ No clustering happening
- ❌ Similarity threshold too high
- ❌ Fingerprinting broken

**Fix: See INFRASTRUCTURE_FIX_PLAN.md Scenario C**

---

### Stage 4: Story Status Lifecycle

**What happens:**
- Stories created with MONITORING status
- As sources added: MONITORING → DEVELOPING → BREAKING/VERIFIED
- Breaking news monitor updates statuses
- Stories tracked over time

**Test what's happening:**
```
Check story_clusters for status distribution:
- Count by status
- Age of BREAKING stories
- Transitions over time
```

**Expected results:**
- ✅ Proper status distribution
- ✅ BREAKING stories < 30 minutes old
- ✅ Smooth transitions

**If broken:**
- ❌ Stuck in MONITORING
- ❌ No status transitions
- ❌ BREAKING news too old

**Fix: Check breaking_news_monitor function logs**

---

### Stage 5: Summarization

**What happens:**
- Stories identify as needing summaries
- Anthropic Claude API generates summaries
- Summaries stored in story_clusters
- Costs tracked

**Test what's happening:**
```sql
-- Check summaries
SELECT c.id, c.title, c.summary, c.status
FROM c
WHERE c.summary != null AND c.summary != ""
ORDER BY c._ts DESC
LIMIT 20
```

**Expected results:**
- ✅ 50%+ of stories have summaries
- ✅ Summaries are 2+ sentences
- ✅ Summaries mention key details

**If broken:**
- ❌ No summaries generated
- ❌ Summaries empty or null
- ❌ Anthropic API key missing

**Fix: Check summarization function logs**

---

### Stage 6: API Feed Endpoint

**What happens:**
- API queries story_clusters
- Filters out MONITORING stories (incomplete)
- Returns DEVELOPING/BREAKING/VERIFIED only
- Includes full source information

**Test what's returned:**
```bash
# Call real API
curl -H "Authorization: Bearer $JWT_TOKEN" \
  "https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/api/stories/feed?limit=20"
```

**Expected results:**
```json
[
  {
    "id": "story_123",
    "title": "Full story title",
    "summary": "Multi-sentence summary",
    "status": "DEVELOPING",
    "category": "world",
    "sources": [
      {"source": "reuters", "source_name": "Reuters", ...},
      {"source": "bbc", "source_name": "BBC News", ...}
    ]
  }
]
```

**If broken:**
- ❌ Empty array returned
- ❌ Missing fields
- ❌ Wrong source names
- ❌ MONITORING stories included

**Fix: See INFRASTRUCTURE_FIX_PLAN.md Scenario D**

---

### Stage 7: Story Reinforcement

**What happens:**
- New RSS articles reference same event
- Fingerprint matches existing story
- Article added to story's sources
- Story updated (last_updated, source_count)
- Status may change based on new source count

**Test what's happening:**
```
1. Note a story with 2 sources at time T
2. Wait 5-10 minutes
3. Query same story at time T+10
4. Verify:
   - source_count increased (or stayed same)
   - last_updated timestamp newer
   - Status appropriate for source count
```

**Expected results:**
- ✅ Stories growing with new sources
- ✅ Updates coming frequently
- ✅ No duplicate sources

**If broken:**
- ❌ Stories never grow
- ❌ Same sources repeated
- ❌ No reinforcement happening

**Fix: Check fingerprinting and clustering logic**

---

## Test Commands by Stage

```bash
# Run all tests
cd Azure/tests

# Stage 1-7 Integration (Real Cosmos DB)
pytest integration/ -v -k "rss or clustering or summarization or breaking or batch"

# Stage 1-7 System (Real API)
pytest system/ -v

# Specific stage tests
pytest system/test_deployed_api.py::TestDataPipeline::test_articles_being_ingested -v
pytest system/test_deployed_api.py::TestDataPipeline::test_clustering_is_working -v
pytest system/test_deployed_api.py::TestDataPipeline::test_summaries_being_generated -v
```

---

## Success Criteria: Complete Data Pipeline

### Data Flowing End-to-End ✅
```
RSS Feeds → raw_articles → clustering → story_clusters → API → complete stories
```

### Story Quality Metrics ✅
```
- Average sources per story: 2.5+
- Stories with summaries: 80%+
- Story refresh rate: Every 30 seconds (new/updated)
- Status distribution: MONITORING 20%, DEVELOPING 30%, BREAKING 30%, VERIFIED 20%
```

### API Response Quality ✅
```
- Response time: < 1 second
- Stories per page: 20+
- All required fields present
- Source names correct (not IDs)
- No MONITORING stories in feed
```

### Test Pass Rate ✅
```
- System tests: 13/13 passing (100%)
- Integration tests: 59/59 passing (100%)
- Unit tests: 54/54 passing (100%)
Total: 126/126 passing (100%)
```

---

## Monitoring & Validation

### Daily Checks
```bash
# Run diagnostic
python3 Azure/scripts/diagnose-clustering-pipeline.py

# Check key metrics
- Article count today
- Story count today
- Average sources per story
- % stories with summaries

# Run system tests
pytest system/ -v
```

### Weekly Deep Dives
```bash
# Full integration test suite
pytest integration/ -v

# Check specific clustering
- Are similar articles clustering?
- Are topic conflicts detected?
- Is similarity threshold working?

# Check summarization
- Summary quality
- Summary lengths
- Cost per summary
```

### Data Quality Dashboard (Nice to Have)
```
Monitor:
- Article ingestion rate
- Story clustering rate
- Clustering accuracy
- Summary generation rate
- API response times
- Feed story counts
```

---

## Troubleshooting by Symptom

### Symptom: No articles in raw_articles
**Root cause:** RSS ingestion not running
**Debug:**
```bash
az functionapp logs tail --name newsreel-func-51689 | grep -i "ingestion\|error"
```
**Fix:** See INFRASTRUCTURE_FIX_PLAN.md Scenario A

### Symptom: Articles exist, no stories
**Root cause:** Change feed triggers not working
**Debug:**
```bash
az functionapp logs tail --name newsreel-func-51689 | grep -i "clustering\|changefeed"
```
**Fix:** See INFRASTRUCTURE_FIX_PLAN.md Scenario B

### Symptom: All stories have 1 source
**Root cause:** Clustering not matching articles
**Debug:**
```bash
# Check similarity being calculated
az functionapp logs tail | grep -i "similarity\|fingerprint"

# Check specific articles
query_articles_by_category("world")
# Manually check if similar titles are matching
```
**Fix:** Adjust fingerprint logic or similarity threshold

### Symptom: Stories exist but API returns empty
**Root cause:** API filtering removing all stories
**Debug:**
```python
# Test query directly
from Azure.api.app.services.cosmos_service import cosmos_service
cosmos_service.connect()
stories = cosmos_service.query_recent_stories(limit=20)
print(f"Raw: {len(stories)}")

# Check filtering
filtered = [s for s in stories if s.get('status') != 'MONITORING']
print(f"Filtered: {len(filtered)}")
```
**Fix:** See INFRASTRUCTURE_FIX_PLAN.md Scenario D

---

## Next Steps

1. **Run diagnostic script** to identify broken stage
2. **Apply appropriate fix** from INFRASTRUCTURE_FIX_PLAN.md
3. **Verify fix** by re-running diagnostic
4. **Test with system tests** to confirm data flowing
5. **Iterate** until all 7 stages passing
6. **Run full test suite** until 126/126 passing

---

**Focus: Get complete, production-quality stories flowing through the API before considering iOS app.**

