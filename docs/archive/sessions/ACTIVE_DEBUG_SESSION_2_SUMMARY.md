# Active Debug Session 2: Authentication Fixed, Clustering Blocked

## Status
- ✅ Authentication FIXED - API now returns 200 instead of 401
- ❌ Clustering STILL NOT WORKING - story_clusters has 0 real story documents
- ⏳ Articles still being ingested (3,065 raw articles)
- ⏳ Feed poll states in wrong container (still in story_clusters, not feed_poll_states)

## What Was Done
1. ✅ Deployed updated API with Firebase token fallback
2. ✅ Fixed 401 auth error by allowing anonymous Firebase tokens  
3. ✅ API now authenticating users and returning 200 OK responses
4. ✅ Created feed_poll_states container for proper data separation
5. ❌ Migration incomplete - old feed_poll_state docs still in story_clusters

## Current Test Results
- System test now runs without auth errors
- API responds with 200 status code
- But returns empty array (no stories)
- Root cause: Zero story documents in story_clusters

## Next Session Priority
1. CRITICAL: Force delete the 107 feed_poll_state documents from story_clusters
2. Restart Function App to reinitialize clustering
3. Monitor if clustering function creates story documents
4. Run tests again to verify end-to-end pipeline

## Key Insight
The clustering function may not be triggering on raw articles because story_clusters container is "polluted" with feed_poll_state documents. Need to clean it completely and let the function recreate stories fresh.

## Commands for Next Session
```bash
# Clean the container completely
python3 Azure/scripts/cleanup_all_articles.py  # Use this to delete story_clusters docs

# Or manually clear:
az cosmosdb sql container delete \
  --name story_clusters \
  --database-name newsreel-db \
  --account-name newsreel-db-1759951135 \
  --resource-group Newsreel-RG

# Recreate it:
az cosmosdb sql container create \
  --name story_clusters \
  --database-name newsreel-db \
  --account-name newsreel-db-1759951135 \
  --resource-group Newsreel-RG \
  --partition-key-path "/category"

# Restart Function App
az functionapp restart --name newsreel-func-51689 --resource-group Newsreel-RG

# Wait and test
sleep 60
cd Azure/tests
pytest system/test_deployed_api.py::TestDeployedAPI::test_stories_endpoint_returns_data_with_auth -v
```

## Status: 70% → Need Clustering Fix
