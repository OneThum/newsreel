# 📊 Project Status - INVESTIGATION IN PROGRESS

**Last Updated**: October 17, 2025  
**Status**: 🔴 **CRITICAL ISSUE** - Story clustering pipeline not functioning

---

## ⚠️ CURRENT BLOCKING ISSUE

### The Problem
Users are seeing **zero sources** and **empty summaries** for all stories, despite:
- RSS feeds being ingested successfully
- Articles stored in database
- API returning data correctly

### Evidence
- **All stories** have status: `MONITORING` (unprocessed)
- **All stories** have `source_articles: []` (empty)
- **All stories** have `summary: {text: "", version: 0}`
- **No status transitions** to DEVELOPING/VERIFIED occurring
- **No source deduplication** happening

### What IS Working ✅
| Component | Status | Evidence |
|-----------|--------|----------|
| RSS Ingestion | ✅ Working | ~20 articles/minute being stored |
| Azure Functions | ✅ Deployed | All 5 functions running: newsreel-func-51689 |
| API Endpoint | ✅ Working | Returns stories correctly (but incomplete data) |
| Cosmos DB | ✅ Operational | Connection verified, data accessible |
| Environment Vars | ✅ Configured | COSMOS_CONNECTION_STRING, ANTHROPIC_API_KEY, etc. |

### What IS NOT Working ❌
| Component | Status | Impact |
|-----------|--------|--------|
| Story Clustering | ❌ Failing | Stories not converted from MONITORING → DEVELOPING |
| Source Deduplication | ❌ Failing | `source_articles` not being populated |
| Change Feed Trigger | ❌ Unknown | May be disabled or not triggering |
| Story Status Updates | ❌ Failing | No progression through status pipeline |

---

## 🔍 Root Cause Analysis

**The clustering pipeline (triggered by Cosmos DB change feed) is either:**

1. **Not Triggering**: Change feed disabled on `raw_articles` container or lease checkpoints not working
2. **Failing Silently**: Change feed triggering but function execution failing without proper logging
3. **Configuration Issue**: Change feed binding not set up correctly in function bindings
4. **Lease Problem**: `leases` container not properly tracking change feed position

---

## 🏗️ Infrastructure Status

### Verified Components
- ✅ **Azure Function App**: `newsreel-func-51689` (Python 3.11, running)
- ✅ **5 Functions Deployed**:
  - RSSIngestion (Timer: every 5 min)
  - StoryClusteringChangeFeed (Cosmos trigger) - **SUSPECTED FAILURE POINT**
  - SummarizationChangeFeed (Cosmos trigger)
  - SummarizationBackfill
  - BreakingNewsMonitor (Timer: every 2 min)
- ✅ **Code Fully Implemented**: All functions have complete logic
- ✅ **Azure Container Apps API**: Healthy and responding
- ✅ **Cosmos DB**: Operational and accessible

---

## 📋 Next Steps to Diagnose & Fix

### Phase 1: Verify Change Feed Configuration (5 min)
```bash
# Check if change feed is enabled on raw_articles
az cosmosdb sql container show \
  -g Newsreel-RG \
  -a newsreel-db-1759951135 \
  -d newsreel_db \
  -n raw_articles
```

### Phase 2: Review Function Binding (5 min)
- Verify `Azure/functions/story_clustering/function_json`
- Confirm Cosmos DB change feed trigger configuration
- Check if connection string is bound correctly

### Phase 3: Check Function Logs (10 min)
```bash
# Get real-time function app logs
az functionapp log tail \
  --name newsreel-func-51689 \
  --resource-group Newsreel-RG
```

### Phase 4: Validate Leases Container (5 min)
- Verify `leases` container exists in Cosmos DB
- Check if change feed checkpoint is being updated
- May need to reset leases to trigger reprocessing

### Phase 5: Manual Test (10 min)
- Manually insert test article into `raw_articles`
- Watch for change feed trigger in function logs
- Verify if `story_clustering` function executes
- Check if story created with proper status

---

## 📊 Historical Context

Previous issues (all resolved):
- ✅ Duplicate sources bug (Oct 13)
- ✅ Clustering false positives (Oct 13)
- ✅ Missing summaries (Oct 14)
- ✅ Azure Functions reliability (Oct 14)

**Current issue** appears to be different from previous bugs - this is a **pipeline blockage** at the clustering stage.

---

## 📁 Documentation References

- **Investigation Details**: `FINAL_DIAGNOSTIC_REPORT.md`
- **Azure Setup**: `docs/Azure_Setup_Guide.md`
- **Clustering Logic**: `Azure/functions/story_clustering/function_app.py`
- **Ingestion Logic**: `Azure/functions/rss_ingestion/function_app.py`
- **API Code**: `Azure/api/app/routers/stories.py`

---

## 🎯 Success Criteria

Once fixed:
1. ✅ Stories transition from MONITORING → DEVELOPING/VERIFIED
2. ✅ `source_articles` field populated with article IDs
3. ✅ Users see 1+ sources per story
4. ✅ Summaries generated and displayed
5. ✅ Feed displays multi-source stories correctly

