# CRITICAL SYSTEM DIAGNOSIS

**Date**: November 9, 2025, 1:13 PM UTC
**Status**: 🔴 **CRITICAL ISSUES IDENTIFIED**

---

## Executive Summary

The Newsreel backend has a **critical data pipeline failure**:
- ✅ RSS ingestion IS working (1,654 articles/hour)
- ✅ API IS running and responsive
- ✅ Cosmos DB IS connected and has data
- ❌ **Story clustering NOT working** (0 stories created in last hour)
- ❌ **37,658 unprocessed articles** (26-day backlog!)
- ❌ Azure Functions appear to be NOT deployed or NOT running

**Result**: Users see NO new stories, NO AI summaries, NO clustering. App appears broken.

---

## Root Cause Analysis

### What's Working ✅

**1. RSS Ingestion**
- Status: ✅ ACTIVE
- Rate: 299 articles/minute (expected: ~18/min)
- Sources: 38 active sources
- Latest article: 0 seconds ago
- Quality: 96.3% complete articles

**2. REST API**
- Status: ✅ RUNNING
- URL: https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io
- Health check: 200 OK
- Cosmos DB: Connected

**3. Database (Cosmos DB)**
- Status: ✅ CONNECTED
- Endpoint: newsreel-db-1759951135.documents.azure.com
- Articles: 37,658+ (with 26-day backlog)
- Stories: 1,515 total (all old - last story created >1 hour ago)

### What's Broken ❌

**1. Story Clustering Pipeline**
- Status: ❌ NOT RUNNING
- Stories created in last hour: **0**
- Stories created in last 24 hours: **0**
- Unprocessed articles: **37,658**
- Oldest unprocessed: **26 days old**

**Impact**: No new stories = users see stale feed

**2. Azure Functions**
- Status: ❌ NOT FOUND in current Azure subscription
- Search result: Zero Newsreel resources in subscription
- Expected functions:
  - RSS polling function
  - Story clustering function (change feed trigger)
  - AI summarization function
  - Breaking news monitor

**Impact**: No clustering, no AI summaries, no breaking news detection

**3. AI Summarization**
- Status: ❌ NOT RUNNING (dependent on clustering)
- Stories analyzed: 0 recent stories
- Coverage: 0% (no new summaries)

**Impact**: No AI summaries for any new content

---

## Detailed Diagnostic Results

### RSS Ingestion Check

```
Articles in last hour: 1,654
Articles in last 10 minutes: 1,585
Average articles per minute: 299.6
Unique sources: 38

Top sources:
- Guardian: 189 articles (11.4%)
- DW: 148 articles (8.9%)
- Telegraph: 119 articles (7.2%)
- Independent: 111 articles (6.7%)
- The Hill: 101 articles (6.1%)

Article quality:
- Complete: 96.3%
- With content: 95.6%
- With fingerprint: 100%

✓ RSS ingestion is WORKING
```

### Clustering Check

```
Total stories in database: 1,515
Stories created in last hour: 0
Stories created in last 24 hours: 0

Status distribution:
- MONITORING: 1,477 (97.5%) ← Single-source stories
- DEVELOPING: 26 (1.7%)
- VERIFIED: 12 (0.8%)
- BREAKING: 0 (0.0%)

Unprocessed articles: 37,658
Oldest unprocessed: 26 days (2,298,561 seconds)

✗ Story clustering is NOT WORKING
```

### Azure Resources Check

```
Azure subscription: d4abcc64-9e59-4094-8d89-10b5d36b6d4c
Resource groups found: 1 (MavTranscribe-RG only)

Search for "newsreel" resources:
- Function Apps: 0
- Container Apps: 0 (but API is accessible)
- Cosmos DB: 0 (but DB is accessible)
- Resource Groups: 0

✗ No Newsreel resources in current subscription
```

**Hypothesis**: Resources exist in a DIFFERENT Azure subscription or were deleted

---

## Impact on Users

### iOS App Experience

**What users see**:
1. ❌ **Stale feed** - No new stories appearing
2. ❌ **No AI summaries** - No summaries being generated
3. ❌ **No multi-source stories** - All stories are single-source
4. ❌ **No breaking news** - Breaking news detection not running
5. ⚠️ **Performance issues** - iPhone heating up, jerky scrolling

**What users expect**:
- Fresh stories every few minutes
- AI summaries on verified stories
- Multi-source story clusters
- Breaking news alerts
- Smooth scrolling performance

**Reality**: App appears fundamentally broken

---

## Why This Happened

### Possible Causes

1. **Azure Functions Never Deployed**
   - Functions exist in code but not deployed to Azure
   - Deployment scripts not run
   - Missing infrastructure

2. **Azure Functions Deleted**
   - Resources were deleted (cost management?)
   - Accidental deletion
   - Subscription cleanup

3. **Wrong Azure Subscription**
   - Logged into wrong subscription
   - Resources exist elsewhere
   - Need to switch subscription context

4. **Azure Functions Stopped/Disabled**
   - Functions exist but are stopped
   - Triggers disabled
   - Service plan scaled to zero

---

## Critical Path to Fix

### Immediate Actions (Today)

**1. Verify Azure Subscription Context**
```bash
# Check current subscription
az account show

# List all subscriptions
az account list --output table

# Switch to correct subscription if needed
az account set --subscription "Newsreel Subscription"
```

**2. Search for Newsreel Resources**
```bash
# Search all resources
az resource list --query "[?contains(name, 'newsreel')]"

# Search function apps
az functionapp list --output table

# Search container apps
az containerapp list --output table
```

**3. If Resources Don't Exist → Deploy Infrastructure**
```bash
cd Azure/infrastructure
terraform init
terraform plan
terraform apply
```

**4. If Resources Exist → Check Function Status**
```bash
# Check function app
az functionapp show --name newsreel-func-XXXXX --resource-group YourRG

# Check if functions are running
az functionapp function list --name newsreel-func-XXXXX --resource-group YourRG

# Check function logs
az functionapp logs tail --name newsreel-func-XXXXX --resource-group YourRG
```

**5. Enable Change Feed Trigger**
The clustering function uses Cosmos DB change feed. Verify:
```python
# In function_app.py, check for:
@app.cosmos_db_trigger(
    connection="COSMOS_CONNECTION_STRING",
    database_name="newsreel-db",
    container_name="articles",
    create_lease_container_if_not_exists=True
)
```

---

## iOS App Performance Issues

### Symptoms
- iPhone heating up during use
- Jerky/laggy scrolling
- High CPU/battery usage

### Likely Causes

1. **Infinite Loop / Polling**
   - App polling API too frequently
   - No debouncing on scroll events
   - Unnecessary re-renders

2. **Memory Leaks**
   - Images not being released
   - Observers not being removed
   - Retained cycles

3. **Inefficient Rendering**
   - Too many views in hierarchy
   - Complex gradients/shadows
   - Not using lazy loading

4. **Background Tasks**
   - Network requests on main thread
   - Heavy computation during scroll
   - No throttling

### Investigation Needed
- Profile app with Instruments (Time Profiler, Allocations)
- Check network traffic frequency
- Review main thread work during scroll
- Examine view hierarchy complexity

---

## Action Plan

### Phase 1: Restore Backend (Critical - Today)

**Priority 1**: Get clustering working
1. Find/deploy Azure Functions
2. Verify change feed trigger is configured
3. Monitor clustering starts processing backlog
4. Verify new stories being created

**Priority 2**: Verify AI summarization
1. Check summarization function is deployed
2. Verify Anthropic API key is configured
3. Monitor summaries being generated
4. Check batch processing is working

**Priority 3**: Clear backlog
1. 37,658 unprocessed articles need clustering
2. May need to run manual backfill
3. Or let system catch up gradually

### Phase 2: Fix iOS Performance (Today/Tomorrow)

**Priority 1**: Profile the app
1. Use Xcode Instruments
2. Identify CPU hotspots
3. Find memory leaks
4. Check network patterns

**Priority 2**: Fix identified issues
1. Reduce main thread work
2. Implement proper debouncing
3. Fix memory leaks
4. Optimize rendering

**Priority 3**: Test on device
1. Verify heating is resolved
2. Confirm smooth scrolling
3. Check battery usage is reasonable

### Phase 3: Verify End-to-End (Next Week)

1. RSS → Articles → Clustering → Stories → API → iOS App
2. AI summarization working
3. Breaking news detection working
4. User experience is smooth

---

## Next Immediate Steps

1. **Check Azure Subscription**
   ```bash
   az account list --output table
   ```

2. **Search for Newsreel Resources**
   ```bash
   az resource list | grep newsreel
   ```

3. **If No Resources → Deploy Infrastructure**
   - Review `Azure/infrastructure/` Terraform config
   - Deploy all Azure Functions
   - Verify deployment

4. **If Resources Found → Debug Why Not Working**
   - Check function logs
   - Verify triggers are enabled
   - Check configuration

5. **Profile iOS App**
   - Open Instruments
   - Run Time Profiler
   - Identify performance bottlenecks

---

## Estimated Time to Fix

**Backend (Critical)**:
- If infrastructure needs deployment: 2-4 hours
- If just configuration issue: 30 minutes - 1 hour
- Backlog processing: 1-2 days (automatic, gradual)

**iOS Performance**:
- Profiling: 30 minutes
- Fixes: 2-4 hours (depends on root cause)
- Testing: 1 hour

**Total**: 1-2 days to fully restore system

---

## Summary

**Current State**:
- ✅ Data is being ingested (1,654 articles/hour)
- ❌ Data is NOT being processed (0 stories/hour)
- ❌ Users see stale/broken app
- ❌ iOS app has performance issues

**Root Cause**:
- Azure Functions NOT running/deployed
- Story clustering pipeline completely stopped
- 26-day backlog of unprocessed articles

**Impact**:
- App fundamentally doesn't work for users
- No new content appearing
- Performance problems make it unusable

**Priority**:
Fix backend FIRST (restore clustering), then fix iOS performance

**Status**: 🔴 CRITICAL - Requires immediate attention

---

**Next Action**: Verify Azure subscription and locate/deploy Azure Functions
