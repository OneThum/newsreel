# Active Debug Session 1: Root Cause Analysis

## Date
October 26, 2025 - Real system testing with Azure CLI

## Critical Finding from API Logs

**API is working correctly** but **returning zero stories** because:

```
[COSMOS] query_recent_stories returned 0 items
[FEED] Query returned 0 stories
[FEED] Filtered: 0 → 0 stories (removed MONITORING status)
[FEED] No processed stories available after filtering!
[FEED] Pipeline Issue: NO stories have been clustered yet
[FEED] Returning EMPTY feed instead of incomplete MONITORING stories
[FEED] Returning ZERO stories - clustering pipeline needs to process articles
```

**This is NOT an API problem. This is a DATA PIPELINE problem.**

## Root Cause: Empty Database

The Cosmos DB `story_clusters` container has **ZERO stories**.

This means one or more of these are broken:

### Stage 1: RSS Ingestion
- ❌ Articles not being ingested into `raw_articles`
- ❌ Or ingestion is running but failing silently

### Stage 2: Change Feed Triggers
- ❌ Change feed not firing on new articles
- ❌ Or firing but clustering function not being triggered

### Stage 3: Clustering
- ❌ Clustering function running but not creating stories
- ❌ Or clustering function not running at all

## Test Results Analysis

| Component | Status | Conclusion |
|-----------|--------|-----------|
| API Container App | ✅ Running | No issue |
| Function App | ✅ Running | No issue |
| Cosmos DB Connection | ✅ Working | API can query it |
| Authentication | ✅ Working | All auth tests pass |
| Data in DB | ❌ ZERO stories | **ROOT CAUSE** |

## Investigation Priority

### CRITICAL: Check if RSS ingestion is even running

```bash
# List all functions in the app
az functionapp function list --name newsreel-func-51689 --resource-group Newsreel-RG

# Show details of RssIngestionTimer function
az functionapp function show --name newsreel-func-51689 \
  --function-name RssIngestionTimer --resource-group Newsreel-RG
```

### CRITICAL: Check if any raw articles exist

Need to query Cosmos DB directly (with connection string from Function App)

### CRITICAL: Check if leases container exists

For change feed triggers to work, leases container MUST exist

### CRITICAL: Check clustering logs

If articles exist but no stories, clustering function is broken

## Expected Database State

If system working:
```
raw_articles: 1000+ documents (growing every 10-15 seconds)
story_clusters: 200+ documents (1 story per 5 articles)
leases: 10+ documents (change feed progress tracking)
```

Actual state:
```
raw_articles: ??? (need to check)
story_clusters: 0 documents
leases: ??? (need to check)
```

## Next Immediate Actions

1. Get COSMOS_CONNECTION_STRING from Function App settings
2. Query raw_articles to see if any exist
3. Check if leases container exists
4. Check Function App execution logs for errors
5. Determine if problem is:
   - A) Articles not being ingested
   - B) Leases/triggers not working
   - C) Clustering failing silently

## Commands Needed

```bash
# Get connection string
COSMOS_CONN=$(az functionapp config appsettings list --name newsreel-func-51689 \
  --resource-group Newsreel-RG --query "[?name=='COSMOS_CONNECTION_STRING'].value" -o tsv)

# Query raw articles
python3 << 'PYTHON'
import os
from azure.cosmos import CosmosClient

conn = os.getenv('COSMOS_CONN')
client = CosmosClient.from_connection_string(conn)
db = client.get_database_client('newsreel-db')
container = db.get_container_client('raw_articles')

count = list(container.query_items("SELECT VALUE COUNT(1) FROM c", enable_cross_partition_query=True))[0]
print(f"Raw articles: {count}")

if count > 0:
    sample = list(container.query_items("SELECT * FROM c OFFSET 0 LIMIT 1", enable_cross_partition_query=True))[0]
    print(f"Sample: {sample}")
PYTHON
```

