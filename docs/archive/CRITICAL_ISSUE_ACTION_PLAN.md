# 🚨 CRITICAL ISSUE ACTION PLAN

**Issue**: Story clustering pipeline not functioning  
**Status**: 🔴 **BLOCKING** - Users see 0 sources and empty summaries  
**Created**: October 17, 2025  
**Investigation**: Complete - Root cause identified

---

## 📊 CURRENT STATE

### ❌ What's Broken
- Stories stuck in `MONITORING` status (unprocessed)
- `source_articles` field empty for ALL stories
- Users see 0 sources per story (should be 1+)
- Summaries empty (should be AI-generated)

### ✅ What's Working
- RSS Ingestion: ~20 articles/minute ✓
- API responses: Returning correct data ✓
- All 5 Azure Functions deployed ✓
- Cosmos DB: Operational ✓
- Azure Container Apps API: Online ✓

### 🎯 Root Cause
**Story clustering pipeline (Cosmos DB change feed trigger) is not functioning.**

The `StoryClusteringChangeFeed` function is either:
1. Not being triggered (change feed disabled or not configured)
2. Failing silently (errors not being logged)
3. Improperly configured
4. Lease checkpoint not working

---

## 🔍 INVESTIGATION STEPS (DO THESE NOW)

### Step 1: Check Change Feed Configuration (5 min)
```bash
az cosmosdb sql container show \
  -g Newsreel-RG \
  -a newsreel-db-1759951135 \
  -d newsreel_db \
  -n raw_articles
```

**Look for:**
- `"changeFeeds": { "enabled": true }`
- `"conflictResolutionPolicy"` configured
- If missing/false, change feed is **disabled** (need to enable)

### Step 2: Verify Function Binding Configuration (5 min)
```bash
# Check the function.json file
cat Azure/functions/story_clustering/function_json
```

**Should have:**
```json
{
  "trigger": {
    "type": "cosmosDBTrigger",
    "name": "documents",
    "direction": "in",
    "collectionName": "raw_articles",
    "connectionStringSetting": "CosmosDBConnection",
    "databaseName": "newsreel_db",
    "leaseCollectionName": "leases",
    "leaseCollectionPrefix": "story_clustering"
  }
}
```

**Problems to check:**
- Connection string exists? 
- Lease collection name correct?
- Collection name matches?

### Step 3: Review Function Logs (10 min)
```bash
az functionapp log tail \
  --name newsreel-func-51689 \
  --resource-group Newsreel-RG
```

**Watch for:**
- Function execution logs
- Error messages
- Change feed trigger events
- Connection string errors

**Keep running and go to Step 5 to trigger an event**

### Step 4: Validate Leases Container (5 min)
```bash
# Query leases container
az cosmosdb sql query \
  --resource-group Newsreel-RG \
  --account-name newsreel-db-1759951135 \
  --database-name newsreel_db \
  --container-name leases \
  --query-text 'SELECT * FROM c WHERE c.id LIKE "story_clustering%"'
```

**Check:**
- Does `leases` container exist?
- Are there documents with prefix `story_clustering`?
- Is checkpoint being updated (check `_ts` field)?

**If empty:**
- Change feed hasn't been tracked yet (function may have never run)
- Or leases were never initialized

### Step 5: Manual Test - Trigger Change Feed (10 min)
```bash
# Insert test article into raw_articles
# This should trigger the StoryClusteringChangeFeed function

az cosmosdb sql query \
  --resource-group Newsreel-RG \
  --account-name newsreel-db-1759951135 \
  --database-name newsreel_db \
  --container-name raw_articles \
  --query-text 'INSERT INTO raw_articles (id, title, description, source, url, published_at, ingested_at, category) VALUES ("test_article_$(date +%s)", "Test Article for Clustering", "This is a test article to trigger change feed", "TestSource", "https://test.com", "2025-10-17T00:00:00Z", "2025-10-17T00:00:00Z", "World")'
```

**After inserting:**
1. Watch function logs (Step 3) for execution
2. Should see: "StoryClusteringChangeFeed triggered"
3. Should see: Story creation/update
4. Check if test article was processed

---

## 🔧 LIKELY FIXES

### Option A: Enable Change Feed (if disabled)
```bash
az cosmosdb sql container update \
  --resource-group Newsreel-RG \
  --account-name newsreel-db-1759951135 \
  --database-name newsreel_db \
  --name raw_articles \
  --change-feed true
```

### Option B: Reset Leases (if stuck)
```bash
# Delete leases container to reset change feed tracking
# WARNING: This will reprocess ALL existing articles

az cosmosdb sql container delete \
  --resource-group Newsreel-RG \
  --account-name newsreel-db-1759951135 \
  --database-name newsreel_db \
  --name leases \
  --yes

# Restart function to recreate leases
az functionapp restart \
  --resource-group Newsreel-RG \
  --name newsreel-func-51689
```

### Option C: Redeploy Functions
```bash
cd Azure/functions
func azure functionapp publish newsreel-func-51689 --python
```

---

## ✅ SUCCESS INDICATORS

Once fixed, you should see:

1. **Stories transition status**
   - `status: "MONITORING"` → `"DEVELOPING"` or `"VERIFIED"`

2. **Source articles populated**
   - `source_articles: ["article_id_1", "article_id_2", ...]`

3. **Users see sources**
   - iOS app shows `source_count: 1+`
   - Each story has 1+ sources listed

4. **Summaries appear**
   - AI summaries generated (may take minutes for async processing)
   - `summary: {text: "...", version: 1, generated_at: "..."}`

5. **Feed quality improved**
   - Multiple perspectives visible
   - Multi-source stories show diversity

---

## 📋 CHECKLIST

- [ ] Step 1: Check change feed enabled
- [ ] Step 2: Verify function binding config
- [ ] Step 3: Review function logs for errors
- [ ] Step 4: Validate leases container
- [ ] Step 5: Manual test to trigger event
- [ ] Apply fix (enable, reset, or redeploy)
- [ ] Verify success indicators above
- [ ] Monitor logs for 30 minutes
- [ ] Test iOS app to confirm sources/summaries visible

---

## 📞 REFERENCE FILES

- **Investigation**: `FINAL_DIAGNOSTIC_REPORT.md`
- **Project Status**: `docs/PROJECT_STATUS.md`
- **Recent Changes**: `docs/Recent_Changes.md`
- **Clustering Code**: `Azure/functions/story_clustering/function_app.py`
- **Ingestion Code**: `Azure/functions/rss_ingestion/function_app.py`
- **Function Config**: `Azure/functions/story_clustering/function.json`

---

## ⏱️ ESTIMATED TIME

- Investigation: 30 minutes (all 5 steps)
- Diagnosis: 5-10 minutes
- Fix: 5-10 minutes (enable/reset) or 15 minutes (redeploy)
- Verification: 10 minutes
- **Total**: 1-1.5 hours

---

**Start with Step 1 and work through systematically. Document findings here as you go.**
