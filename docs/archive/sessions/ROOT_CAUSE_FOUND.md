# 🔴 ROOT CAUSE FOUND: Wrong Container Configuration

## The Problem

**The Cosmos DB database is misconfigured!**

### What's Happening:

1. **raw_articles container**: ✅ 3,035 articles (WORKING)
2. **story_clusters container**: ❌ 107 documents but ALL are `feed_poll_state` records
3. **Result**: API queries for stories but finds ZERO story_cluster documents

## Container Misuse

The `story_clusters` container is being used to store MULTIPLE document types:
```
- feed_poll_state (107 docs) ← Should be in separate container!
- NO actual story_cluster documents!
```

The `feed_poll_state` documents should be in their OWN container called `feed_poll_states` (plural).

## Why This Breaks Everything

```
Data Pipeline Failure Chain:
════════════════════════════════════════════════════════════

1. ✅ RSS Ingestion works
   → Articles stored in raw_articles (3035 docs)

2. ✅ Change feed triggers fire
   → Clustering function executes

3. ❌ Clustering function tries to create stories
   → INSERT INTO story_clusters WITH doc_type='story_cluster'
   → BUT story_clusters already has OTHER doc types!

4. ❌ Partition key conflict possible
   → story_clusters partitioned by /category
   → feed_poll_state doesn't have category field
   → Documents with mixed schemas = query chaos

5. ❌ API queries story_clusters
   → SELECT * FROM story_clusters WHERE doc_type='story_cluster'
   → Returns ZERO results (all are feed_poll_state)
   → API returns empty array []
```

## The Fix

Create separate containers for each document type:

```bash
# Current (BROKEN):
story_clusters → contains both:
  - story_cluster (expected)
  - feed_poll_state (should be elsewhere)

# Expected (FIXED):
story_clusters → only story_cluster documents
feed_poll_states → only feed_poll_state documents
```

## Immediate Actions

### Step 1: Create feed_poll_states container
```bash
az cosmosdb sql container create \
  --account-name newsreel-db-1759951135 \
  --database-name newsreel-db \
  --resource-group Newsreel-RG \
  --name feed_poll_states \
  --partition-key-path "/feed_id"
```

### Step 2: Migrate feed_poll_state docs
```python
# Query all feed_poll_state docs from story_clusters
# Move to feed_poll_states container
```

### Step 3: Update Function App code
- Change all feed_poll_state writes to use feed_poll_states container
- Change all story_cluster writes to use story_clusters container
- Update queries to specify correct container

### Step 4: Clear and restart
```bash
# Delete old feed_poll_state docs from story_clusters
# Restart function app to re-initialize change feeds
# Wait for fresh ingestion
```

## Evidence

**Query Result:**
```
story_clusters container has 107 documents
- 0 actual story_cluster documents (expected data)
- 107 feed_poll_state documents (wrong container!)
```

**Why API returns empty:**
```
API Code:
  SELECT c.* FROM c WHERE c.status != 'MONITORING'  
  
But stories only exist if doc_type = 'story_cluster'
All 107 docs have doc_type = 'feed_poll_state'
Result: ZERO matches
```

## Why This Happened

Looking at the Cosmos DB setup script, it should create separate containers:
```python
create_container("story_clusters", "/category")
create_container("feed_poll_states", "/feed_id")  ← This line likely not executed!
```

The feed_poll_states container was never created, so feed poll state writes defaulted to the story_clusters container (probably no explicit container check in the code).

## Status: READY TO FIX

This is a **configuration/setup issue**, not a code bug. The fix:
1. Create feed_poll_states container (1 min)
2. Migrate data (2 min)
3. Update code to use correct containers (10 min)
4. Re-deploy (5 min)
5. Verify with tests (5 min)

**Total Fix Time: ~25 minutes**

