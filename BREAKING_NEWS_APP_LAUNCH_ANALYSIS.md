# Breaking News: App Launch Shows Empty Feed

## What Happened

The iOS app launched successfully with perfect authentication and real API connection, but revealed a critical issue:

```
[10:35:05.870] ✅ API Response: 200 for /api/stories/feed?offset=0&limit=20
   Size: 2 bytes
   Data: []
```

**The API returned an empty story list.**

---

## What This Means

### The Good News ✅
1. iOS app authentication is working perfectly
2. Firebase JWT tokens are being generated correctly
3. API connection is working (200 response)
4. No authentication errors

### The Bad News 🔴
1. API returned 0 stories
2. Data pipeline is completely broken
3. System can't show any news to users

---

## Root Cause Analysis

### Why Is The Feed Empty?

The feed endpoint filters stories:
```python
# From Azure/api/app/routers/stories.py
processed_stories = [
    story for story in stories 
    if story.get('status', 'MONITORING') != 'MONITORING'  # ← FILTERS OUT MONITORING
]

# If only MONITORING stories exist (1 source), they're all removed
if len(processed_stories) == 0:
    logger.warning("⚠️ Returning ZERO stories - clustering pipeline needs to process")
    return []  # Empty feed
```

### The Pipeline Steps (Where It's Broken):

```
1. RSS Ingestion (Azure Function)
   ↓
   Articles stored in raw_articles container
   ↓
2. Change Feed Trigger (StoryClusteringChangeFeed)
   ↓
   Process articles into story_clusters with status='MONITORING'
   ↓
3. Clustering Logic
   ↓
   ❌ BROKEN: Need 2+ sources for DEVELOPING, 3+ for BREAKING/VERIFIED
   ❌ BROKEN: Feed only shows DEVELOPING/BREAKING/VERIFIED stories
   ↓
4. API Feed Endpoint
   ↓
   ❌ Returns empty list (all stories still MONITORING)
   ↓
5. iOS App
   ↓
   🔴 Shows empty feed to user
```

---

## Possible Issues (In Order of Likelihood)

### 1. ❌ Articles Are Not Being Ingested (Most Likely)
**Symptom:** raw_articles container is empty
**Cause:** RSS ingestion function not running
**Check:** 
  - Azure Function App logs for RSS_Ingestion errors
  - Are articles in `raw_articles` container?
**Fix:** Debug and restart RSS ingestion

### 2. ❌ Change Feed Triggers Not Firing (Likely)
**Symptom:** Articles exist but no stories created
**Cause:** Cosmos DB change feed not working
**Check:**
  - Are leases container being created?
  - Are stories in `story_clusters` container?
  - Check Function App logs for trigger errors
**Fix:** 
  - Restart Function App
  - Check Cosmos DB settings for change feed

### 3. ❌ Clustering Not Working (Possible)
**Symptom:** Stories created but all in MONITORING status
**Cause:** No articles clustering together (fingerprinting/similarity issues)
**Check:**
  - Are stories in `story_clusters` with status='MONITORING'?
  - Do stories have only 1 source_article each?
**Fix:**
  - Debug fingerprinting logic
  - Adjust similarity thresholds
  - Check topic conflict detection

### 4. ❌ Story Statuses Not Transitioning (Less Likely)
**Symptom:** Stories in DEVELOPING/BREAKING but not appearing
**Cause:** Status update logic broken
**Check:**
  - Story statuses in database
  - API filtering logic
**Fix:** Debug status transition code

---

## How to Debug

### Step 1: Check Raw Articles
```bash
# Run diagnostic script with Azure CLI credentials set
export COSMOS_CONNECTION_STRING="your-connection-string"
python3 Azure/scripts/diagnose-clustering-pipeline.py
```

This will show:
- Total articles in raw_articles
- Total stories in story_clusters  
- Story status distribution
- Change feed lease status

### Step 2: Check Azure Function Logs
```bash
az functionapp logs tail --name newsreel-func-51689 --resource-group Newsreel-RG
```

Look for:
- RSS ingestion errors
- Change feed trigger logs
- Clustering errors

### Step 3: Query Cosmos DB Directly
```python
# If articles exist but stories don't:
# This means change feed triggers are not working

# If stories exist with status='MONITORING':
# This means clustering is not working
```

---

## Next Steps (In Priority Order)

### IMMEDIATE: Determine What's In The Database
1. Check if `raw_articles` is empty or has data
2. Check if `story_clusters` is empty or has data
3. If stories exist, check their statuses

### THEN: Fix Based on What You Find

**If raw_articles is empty:**
- RSS ingestion is not running
- Check Function App logs
- Restart RSS ingestion or deploy fixes

**If raw_articles has data but story_clusters is empty:**
- Change feed triggers are not firing
- Cosmos DB may not have change feed enabled
- Or leases container is broken

**If story_clusters has stories with status='MONITORING':**
- Clustering logic is not connecting articles
- All stories are 1-source orphans
- Need to debug fingerprinting/similarity

**If stories exist with status='DEVELOPING'/'BREAKING'/'VERIFIED':**
- Feed should be showing them
- Check API filtering logic
- Check if Cosmos DB query is working

---

## Testing Without Real Data

**DO NOT** use mock data to test. Use the diagnostic script with REAL Cosmos DB to see actual pipeline state.

The diagnostic script shows:
- Exact count of articles vs stories
- Status distribution
- Source counts
- Change feed health

This tells us exactly what's broken.

---

## Summary

The iOS app and API infrastructure are working perfectly. The issue is **data pipeline**: articles are either not being ingested, not being clustered, or not being shown in the feed.

The diagnostic script above will pinpoint which step is broken.

Run it to determine the root cause, then we can fix that specific component.

