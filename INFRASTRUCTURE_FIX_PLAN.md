# Infrastructure Fix Plan: Getting All Tests to 100% Pass

## Current Status
```
iOS App Launch Results:
  ✅ Authentication: Working
  ✅ API Connection: Working
  ❌ Data Flow: Empty (0 stories)

Test Results:
  ✅ 54 unit tests: 100% passing
  ✅ 59 integration tests: 100% passing (with mocks)
  ❌ 13 system tests: 31% passing (4 failing)

Real System Status:
  🔴 Data pipeline completely broken
```

## Root Cause: Data Pipeline Broken

### Pipeline Flow (Expected)
```
RSS Feeds (100 sources)
    ↓ (Every 10-15 seconds, poll 2-3 feeds)
raw_articles container (articles stored with processed=false)
    ↓ (Change feed trigger: StoryClusteringChangeFeed)
Clustering Logic
    ↓ (Group similar articles)
story_clusters container (stories with status=MONITORING/DEVELOPING/BROKEN/VERIFIED)
    ↓ (API feed endpoint)
API returns stories with status != MONITORING
    ↓
iOS App displays news
```

### Diagnosis Steps

**Step 1: Determine What's In The Database**

Use diagnostic script:
```bash
export COSMOS_CONNECTION_STRING="your-connection-string"
export COSMOS_DATABASE_NAME="newsreel-db"
python3 Azure/scripts/diagnose-clustering-pipeline.py
```

This will show:
- [ ] Total articles in raw_articles
- [ ] Total stories in story_clusters
- [ ] Story status distribution
- [ ] Change feed lease status

**Step 2: Identify The Problem**

Based on diagnostic output:

**Scenario A: raw_articles is EMPTY**
```
Problem: RSS ingestion not running
Evidence: 0 articles in database
Action: Fix RSS ingestion function
```

**Scenario B: raw_articles has data, story_clusters is EMPTY**
```
Problem: Change feed triggers not firing
Evidence: Articles exist but no stories created
Action: Fix Cosmos DB change feed triggers
```

**Scenario C: story_clusters has stories, all status=MONITORING**
```
Problem: Clustering not working (articles not grouping)
Evidence: All stories have 1 source (single article)
Action: Fix clustering logic (fingerprinting/similarity)
```

**Scenario D: Stories exist with DEVELOPING/BREAKING/VERIFIED**
```
Problem: API filtering or other issue
Evidence: Data flows but API shows empty
Action: Debug API feed endpoint
```

## Fix Procedures (In Priority Order)

### Fix #1: RSS Ingestion (Most Likely Broken)

**Symptoms:**
- raw_articles container is empty
- No articles in database at all

**Root Causes:**
- Azure Function App not deployed
- RSS ingestion function not running
- Function has errors
- RSS feeds not configured

**Fix Steps:**

1. **Check Function App Status**
```bash
# Check if function app exists and is running
az functionapp show --name newsreel-func-51689 --resource-group Newsreel-RG

# Check if function is enabled
az functionapp function show --name newsreel-func-51689 --function-name RssIngestionTimer \
  --resource-group Newsreel-RG
```

2. **Check Function Logs**
```bash
# Stream logs to see errors
az functionapp logs tail --name newsreel-func-51689 --resource-group Newsreel-RG

# Look for:
# - Connection string errors
# - RSS feed parsing errors
# - Cosmos DB write errors
# - Timer trigger not firing
```

3. **Verify Configuration**
```bash
# Check environment variables
az functionapp config appsettings list --name newsreel-func-51689 \
  --resource-group Newsreel-RG | grep -i "COSMOS\|RSS"
```

Required settings:
- COSMOS_CONNECTION_STRING
- COSMOS_DATABASE_NAME
- ANTHROPIC_API_KEY
- RSS feed URLs

4. **Deploy/Update Function App**
```bash
# If not deployed, deploy it
cd Azure/functions
func azure functionapp publish newsreel-func-51689

# Check if it's running
az functionapp logs tail --name newsreel-func-51689 --resource-group Newsreel-RG
```

5. **Trigger RSS Ingestion Manually**
```python
# If timer-based trigger is not working, manually trigger it
# Run this script to insert test articles
python3 Azure/tests/scripts/test-rss-ingestion.py
```

---

### Fix #2: Change Feed Triggers (If Articles Exist But No Stories)

**Symptoms:**
- raw_articles has articles
- story_clusters is empty
- No errors in logs

**Root Causes:**
- Leases container doesn't exist
- Change feed not enabled on raw_articles
- StoryClusteringChangeFeed function crashed
- Cosmos DB access issues

**Fix Steps:**

1. **Verify Leases Container Exists**
```bash
# Check if leases container exists in Cosmos DB
az cosmosdb sql container show --account-name newsreel-db-1759951135 \
  --database-name newsreel-db --name leases --resource-group Newsreel-RG
```

2. **Create Leases Container If Missing**
```bash
# Run setup script
bash Azure/scripts/setup-cosmos-db.sh

# This creates the leases container if it doesn't exist
```

3. **Check Change Feed Status**
```bash
# Verify raw_articles container has change feed enabled
az cosmosdb sql container show --account-name newsreel-db-1759951135 \
  --database-name newsreel-db --name raw_articles --resource-group Newsreel-RG | \
  grep -i "changefeed\|changeFeedPolicy"
```

4. **Restart Function App**
```bash
# Restart to re-initialize triggers
az functionapp restart --name newsreel-func-51689 --resource-group Newsreel-RG

# Wait 30 seconds then check logs
az functionapp logs tail --name newsreel-func-51689 --resource-group Newsreel-RG
```

5. **Check For Trigger Errors**
```
Look for in logs:
- "StoryClusteringChangeFeed" starting
- "Processing X documents for clustering"
- Any exceptions or errors
```

---

### Fix #3: Clustering Logic (If All Stories are MONITORING)

**Symptoms:**
- story_clusters has stories
- All stories have status='MONITORING'
- All stories have only 1 source_article

**Root Causes:**
- Fingerprinting not matching articles
- Similarity threshold too high
- Topic conflict detection too strict
- Articles not similar enough

**Fix Steps:**

1. **Check Clustering Logs**
```bash
az functionapp logs tail --name newsreel-func-51689 --resource-group Newsreel-RG | \
  grep -i "clustering\|fingerprint\|similarity"
```

2. **Analyze Log Output**
Look for:
- Fingerprint generation working?
- Similarity scores being calculated?
- Articles being matched?
- Why matches are rejected?

3. **Adjust Thresholds (if needed)**
```python
# In Azure/functions/shared/config.py:
STORY_FINGERPRINT_SIMILARITY_THRESHOLD: float = 0.70  # Adjust if too strict
```

4. **Enable Debug Logging**
```python
# In Azure/functions/function_app.py:
logger.info(f"Similarity: {similarity:.3f} vs threshold {threshold}")
```

5. **Analyze Specific Articles**
```python
# Check what fingerprints are generated for same-story articles
from functions.shared.utils import generate_story_fingerprint, extract_simple_entities

article1_title = "President Announces Climate Plan"
article2_title = "President Unveils Climate Initiative"

entities1 = extract_simple_entities(article1_title)
entities2 = extract_simple_entities(article2_title)

fp1 = generate_story_fingerprint(article1_title, entities1)
fp2 = generate_story_fingerprint(article2_title, entities2)

print(f"FP1: {fp1}")
print(f"FP2: {fp2}")
print(f"Match: {fp1 == fp2}")
```

---

### Fix #4: API Feed Endpoint (If Stories Exist But API Shows Empty)

**Symptoms:**
- story_clusters has stories
- story_clusters has stories with status != 'MONITORING'
- API still returns empty list

**Root Causes:**
- API filtering logic broken
- Cosmos DB query failing
- API not connecting to database

**Fix Steps:**

1. **Check API Logs**
```bash
# Container Logs for API
az acr logs show --registry newsreelregistry --image newsreel-api:latest
```

2. **Test API Query Directly**
```python
# Run this to test Cosmos DB query from API
from Azure.api.app.services.cosmos_service import cosmos_service

cosmos_service.connect()
stories = cosmos_service.query_recent_stories(limit=20)
print(f"Stories from API: {len(stories)}")
```

3. **Check Filtering Logic**
Look at `Azure/api/app/routers/stories.py` line 221-237:
```python
processed_stories = [
    story for story in stories 
    if story.get('status', 'MONITORING') != 'MONITORING'
]
```

If this filters out ALL stories, it means all stories have status='MONITORING'.

4. **Verify Connection String**
```bash
az functionapp config appsettings list --name newsreel-func-51689 \
  --resource-group Newsreel-RG | grep COSMOS_CONNECTION_STRING
```

---

## Test Verification Order

After fixing each component, run tests in this order:

```bash
# 1. Run diagnostic to confirm data is flowing
export COSMOS_CONNECTION_STRING="your-string"
python3 Azure/scripts/diagnose-clustering-pipeline.py

# 2. Run system tests (real API/data)
cd Azure/tests
pytest system/ -v

# 3. Run integration tests (real Cosmos DB)
pytest integration/ -v

# 4. Run unit tests (for regression)
pytest unit/ -v

# 5. Test iOS app
# Launch iOS app in simulator/device
# Check if feed shows stories
```

## Expected Outcomes

### After Each Fix

**Fix #1: RSS Ingestion**
- raw_articles will have 1000+ articles
- Logs will show "Articles ingested"
- Diagnostic script shows article count > 0

**Fix #2: Change Feed**
- story_clusters will have 100-500 stories
- Most will have status != 'MONITORING'
- Logs will show "Clustering X documents"

**Fix #3: Clustering Logic**
- Stories will have 2+ sources
- Status will be DEVELOPING/BREAKING/VERIFIED
- Diagnostic shows proper distribution

**Fix #4: API Feed**
- API returns 20+ stories per call
- iOS app shows news feed
- System tests pass

## Success Criteria: 100% Tests Passing

```
✅ System tests: 13/13 passing
   - API reachable
   - Stories returned
   - Clustering working
   - Summaries generated

✅ Integration tests: 59/59 passing
   - All with REAL Cosmos DB
   - Real data pipeline
   - No mocks

✅ Unit tests: 54/54 passing
   - Algorithm verification
   - Regression prevention

✅ iOS App
   - Shows populated news feed
   - All stories have proper metadata
   - No empty states

TOTAL: 126/126 tests (100%)
```

## Debug Checklist

Before each fix attempt:

- [ ] Azure credentials configured
- [ ] Can connect to Cosmos DB
- [ ] Can access Function App logs
- [ ] Function App is deployed
- [ ] Container images built and pushed
- [ ] Environment variables set correctly

After each fix:

- [ ] Run diagnostic script
- [ ] Check Function App logs for errors
- [ ] Run system tests
- [ ] Verify data is flowing
- [ ] Check iOS app displays news

