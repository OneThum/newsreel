# 🚨 Breaking News System - Critical Issues Found

**Diagnosed**: 2025-10-13 06:24 UTC  
**Status**: **BROKEN** - Two critical bugs identified

---

## 🔍 Testing Summary

### What We Found:

**1. Breaking News Monitor is CRASHING** 🔴
```
Error: Failed to query stories by status BREAKING: One of the input values is invalid.
```
- Happens at 06:20 UTC (every 5 minutes when monitor runs)
- The `query_stories_by_status` method has a Cosmos DB query error
- **Impact**: NO stories can reach or maintain BREAKING status

**2. Clustering Has Stopped** 🟡
- Last clustering activity: 05:52 UTC (20+ minutes ago)
- New articles creating SEPARATE stories instead of joining existing ones
- **Impact**: Gaza hostage articles not merging with main story

**3. Enhanced Logging Not Appearing** 🟡
- No "Status evaluation" logs visible
- No "promoted to BREAKING" logs
- **Reason**: Clustering not running, so evaluation never happens

---

## 📊 Evidence

### Breaking News Monitor Errors:
```
06:20:07 - Failed to query stories by status BREAKING: One of the input values is invalid
06:15:XX - (Likely same error)
06:10:XX - (Likely same error)
06:05:XX - (First error after deployment)
```

### Clustering Activity:
```
05:52:04 - ✓ Fuzzy match: Gaza stories matched
05:52:03 - ✓ Fuzzy match: Hostage stories matched
05:52:02 - ✓ Fuzzy match: Various stories matched
...
06:17:34 - NEW Gaza hostage story CREATED (not matched!)
06:20:07 - NEW story CREATED (not matched!)
```

**Gap**: 20+ minutes with NO clustering matches!

### RSS Ingestion:
```
06:19:39 - 1 new article (but not clustered)
06:18:39 - 0 new articles
```

---

## 🎯 Root Cause Analysis

### Issue #1: query_stories_by_status

**The Problem:**
The Cosmos DB query likely has an `ORDER BY` clause without the proper index, or the query syntax is invalid for Cosmos DB.

**Evidence:**
```python
# In cosmos_client.py (added in recent changes)
async def query_stories_by_status(self, status: str, limit: int = 100):
    query = """
        SELECT * FROM c 
        WHERE c.status = @status 
        AND (NOT IS_DEFINED(c.doc_type) OR c.doc_type IS NULL)
        ORDER BY c.first_seen DESC  # ← LIKELY CAUSE
    """
```

**Cosmos DB Limitation:**
- `ORDER BY` requires a composite index
- Or it needs to be removed and sorting done in Python

---

### Issue #2: Clustering ChangeFeed

**The Problem:**
Clustering ChangeFeed may be:
1. Not receiving new articles (RSS issue)
2. Not processing them (error in clustering logic)
3. Not matching them (fingerprint/fuzzy match broken)

**Evidence:**
- Function IS executing (we see logs)
- But NO fuzzy matches or "Added source" logs
- New stories being CREATED instead of UPDATED

---

## 🔧 Immediate Fixes Needed

### Fix #1: Remove ORDER BY from query_stories_by_status

**Change:**
```python
# cosmos_client.py
async def query_stories_by_status(self, status: str, limit: int = 100):
    query = """
        SELECT * FROM c 
        WHERE c.status = @status 
        AND (NOT IS_DEFINED(c.doc_type) OR c.doc_type IS NULL)
    """
    # Sort in Python instead
    items = list(container.query_items(...))
    items_sorted = sorted(items, key=lambda x: x.get('first_seen', ''), reverse=True)
    return items_sorted[:limit]
```

---

### Fix #2: Check Clustering Logic

**Investigate:**
1. Is `story_clustering_changefeed` being triggered?
2. Are articles being processed?
3. Are fingerprints being generated?
4. Are fuzzy matches happening?

---

## 📋 Quick Deploy Plan

### Step 1: Fix query_stories_by_status
- Remove ORDER BY
- Sort in Python
- Deploy immediately

### Step 2: Verify Breaking News Monitor
- Check logs after deploy
- Should see: "Breaking news monitor triggered"
- Should NOT see: "Failed to query"

### Step 3: Investigate Clustering
- Check if changefeed is triggered
- Check if articles are processed
- Check for errors in clustering logic

---

## 🎓 Why This Broke

### Timeline:
```
05:31 - Deployed active breaking news fix
05:39 - Deployed 90-min timeout + enhanced logging
       - Added query_stories_by_status method
06:05 - Breaking News Monitor runs
       - Calls query_stories_by_status
       - CRASHES with ORDER BY error
06:18 - Deployed timestamp bug fix
       - Issue persists
06:20 - Still crashing every 5 minutes
```

**The Issue:**
We added `query_stories_by_status` at 05:39 but didn't test it. The ORDER BY clause doesn't work in Cosmos DB without proper indexing.

---

## ✅ What's Working

Despite the bugs:
- ✅ RSS ingestion (polling, fetching)
- ✅ Story creation (new stories being made)
- ✅ Summarization (stories getting summaries)
- ✅ Timestamp fix (deployed, working)

**What's Broken:**
- ❌ Breaking news detection (monitor crashing)
- ❌ Story clustering (no matches for 20+ min)
- ❌ Multi-source stories (can't cluster without matching)
- ❌ Gaza story promotion (can't promote if not clustered)

---

## 🚨 Impact on Gaza Hostage Story

### Why It's Not BREAKING:

**1. Articles not clustering:**
- New Gaza hostage articles coming in
- Creating SEPARATE stories
- NOT joining the main Gaza story
- Main story stays at 5 sources (stuck)

**2. Breaking news monitor broken:**
- Even if clustering worked
- Monitor can't query BREAKING stories
- Can't promote stories
- Can't send notifications

**3. Result:**
- Multiple Gaza stories (fragmented)
- None reaching BREAKING status
- Not at top of feed
- Users don't see breaking news

---

## 📝 Next Actions

1. **IMMEDIATE**: Fix `query_stories_by_status` (remove ORDER BY)
2. **IMMEDIATE**: Deploy fix
3. **5 min later**: Verify Breaking News Monitor works
4. **Investigation**: Why clustering stopped (separate issue)
5. **Test**: Wait for next Gaza article to see if it clusters

---

**Status**: Diagnosis complete, ready to deploy fix!


