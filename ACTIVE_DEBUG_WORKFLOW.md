# Active Debug Workflow: Test → Logs → Fix → Repeat

## Mission
Run test harnesses continuously, observe logs, identify issues, apply fixes, verify results. **Keep iterating until 100% pass rate.**

---

## The Cycle (Repeat Until All Tests Pass)

```
1. RUN TESTS
   ↓
2. CAPTURE FAILURES
   ↓
3. CHECK LOGS
   ↓
4. IDENTIFY ISSUE
   ↓
5. APPLY FIX
   ↓
6. RE-RUN TESTS
   ↓
   All passing? → Done!
   Still failing? → Back to step 3
```

---

## Step 1: Run Tests (And Capture Output)

### System Tests First (Real API)
```bash
cd Azure/tests
pytest system/ -v 2>&1 | tee system_test_output.log
```

**What to look for:**
- ❌ Which tests fail?
- 🔍 What's the error message?
- 📊 How many passed vs failed?

### Integration Tests (Real Cosmos DB)
```bash
pytest integration/ -v 2>&1 | tee integration_test_output.log
```

### Unit Tests (Quick regression check)
```bash
pytest unit/ -v 2>&1 | tee unit_test_output.log
```

---

## Step 2: Capture Test Failures

Save test output for analysis:
```bash
# Capture ONLY failures
pytest system/ -v 2>&1 | grep -E "FAILED|ERROR|assert" > failures.txt

# Run again with more verbose output
pytest system/ -v --tb=long 2>&1 | tee full_test_output.log
```

**Key failure patterns to look for:**
```
❌ No stories returned (empty array)
❌ No articles in database
❌ Change feed trigger not firing
❌ Clustering not working (all MONITORING)
❌ Summaries not generated
❌ API filtering removing all stories
```

---

## Step 3: Check Azure Function Logs

```bash
# Stream logs to terminal
az functionapp logs tail --name newsreel-func-51689 --resource-group Newsreel-RG

# Save logs to file
az functionapp logs tail --name newsreel-func-51689 --resource-group Newsreel-RG > function_logs.txt 2>&1 &

# Search for specific errors
az functionapp logs tail --name newsreel-func-51689 --resource-group Newsreel-RG | grep -i "error\|exception\|failed"

# Search for specific components
az functionapp logs tail --name newsreel-func-51689 --resource-group Newsreel-RG | grep -i "ingestion"
az functionapp logs tail --name newsreel-func-51689 --resource-group Newsreel-RG | grep -i "clustering"
az functionapp logs tail --name newsreel-func-51689 --resource-group Newsreel-RG | grep -i "changefeed"
```

**What to look for in logs:**
```
🔴 Connection refused → Cosmos DB not reachable
🔴 Invalid connection string → Environment variable wrong
🔴 No articles processed → RSS ingestion not running
🔴 No change feed → Trigger not firing
🔴 Clustering error → Logic broken
🔴 Anthropic error → API key missing or invalid
```

---

## Step 4: Diagnostic Script (Quick Status Check)

```bash
# Set environment variables
export COSMOS_CONNECTION_STRING="your-connection-string"
export COSMOS_DATABASE_NAME="newsreel-db"

# Run diagnostic
python3 Azure/scripts/diagnose-clustering-pipeline.py
```

**Output will show:**
```
Raw Articles: 0 articles
  ❌ Problem: RSS ingestion broken
  
Raw Articles: 5000+ articles, but 0 stories
  ❌ Problem: Change feed triggers not firing
  
Stories: 500, but all MONITORING (1 source each)
  ❌ Problem: Clustering not working
  
Stories: 200+ with proper sources, but API returns empty
  ❌ Problem: API filtering or query broken
```

---

## Step 5: Identify The Broken Component

### Decision Tree:

```
System tests failing?
│
├─ "No articles"
│  └─ RSS Ingestion broken
│     Check: Function running?
│     Check: Connection string valid?
│     Check: RSS feeds reachable?
│
├─ "No stories"
│  └─ Change feed triggers broken
│     Check: Leases container exists?
│     Check: Change feed enabled on raw_articles?
│     Check: Function logs for errors?
│
├─ "All stories have 1 source"
│  └─ Clustering broken
│     Check: Fingerprinting working?
│     Check: Similarity threshold too high?
│     Check: Topic conflict blocking matches?
│
├─ "Stories exist but API returns empty"
│  └─ API filtering broken
│     Check: Query returning stories?
│     Check: Filter logic correct?
│     Check: Status distribution OK?
│
└─ "Summaries missing"
   └─ Summarization broken
      Check: Anthropic API key set?
      Check: Function running?
      Check: Cost tracking?
```

---

## Step 6: Apply Fix (Based on Identified Issue)

### For RSS Ingestion Issues:

**Check if function running:**
```bash
az functionapp function show --name newsreel-func-51689 \
  --function-name RssIngestionTimer --resource-group Newsreel-RG
```

**Check connection string:**
```bash
az functionapp config appsettings list --name newsreel-func-51689 \
  --resource-group Newsreel-RG | grep COSMOS_CONNECTION_STRING
```

**Check for parsing errors:**
```bash
az functionapp logs tail --name newsreel-func-51689 --resource-group Newsreel-RG | grep -i "parsing\|rss\|feed"
```

**Fix: Deploy latest code**
```bash
cd Azure/functions
func azure functionapp publish newsreel-func-51689 --build remote
```

---

### For Change Feed Trigger Issues:

**Verify leases container:**
```bash
# This should show leases container details
az cosmosdb sql container show --account-name newsreel-db-1759951135 \
  --database-name newsreel-db --name leases --resource-group Newsreel-RG
```

**If leases doesn't exist, create it:**
```bash
bash Azure/scripts/setup-cosmos-db.sh
```

**Restart function to re-initialize triggers:**
```bash
az functionapp restart --name newsreel-func-51689 --resource-group Newsreel-RG
```

**Check for change feed errors:**
```bash
az functionapp logs tail --name newsreel-func-51689 --resource-group Newsreel-RG | grep -i "changefeed\|lease"
```

---

### For Clustering Issues:

**Check clustering logs:**
```bash
az functionapp logs tail --name newsreel-func-51689 --resource-group Newsreel-RG | grep -i "clustering\|fingerprint\|similarity"
```

**Possible fixes:**
- Adjust similarity threshold in `config.py`
- Check topic conflict detection
- Enable debug logging for fingerprinting
- Verify entity extraction working

**Deploy updated config:**
```bash
cd Azure/functions
func azure functionapp publish newsreel-func-51689 --build remote
```

---

### For API Feed Issues:

**Test query directly:**
```python
# Run in Python
from Azure.api.app.services.cosmos_service import cosmos_service
cosmos_service.connect()
stories = cosmos_service.query_recent_stories(limit=20)
print(f"Raw stories: {len(stories)}")

# Check filtering
filtered = [s for s in stories if s.get('status') != 'MONITORING']
print(f"After filtering: {len(filtered)}")
```

**Check API logs:**
```bash
# Container Logs (if in Container Apps)
az containerapp logs show --name newsreel-api \
  --resource-group Newsreel-RG --tail 100
```

**Common fixes:**
- Verify Cosmos DB connection in API
- Check if query is working
- Verify filter logic
- Ensure status field exists in stories

---

## Step 7: Verify Fix Worked

After applying fix:

```bash
# 1. Re-run diagnostic
python3 Azure/scripts/diagnose-clustering-pipeline.py

# 2. Check logs for success
az functionapp logs tail --name newsreel-func-51689 --resource-group Newsreel-RG

# 3. Re-run failed tests
cd Azure/tests
pytest system/ -v

# 4. Check specific test that was failing
pytest system/test_deployed_api.py::TestDataPipeline::test_clustering_is_working -v
```

**Success indicators:**
```
✅ Diagnostic shows improvement
✅ Logs show no new errors
✅ Tests passing (or more tests passing than before)
✅ Data visible in Cosmos DB
```

---

## Common Issues & Quick Fixes

### Issue: "No articles in raw_articles"

**Diagnosis:**
```bash
# Check if ingestion function exists
az functionapp function list --name newsreel-func-51689 --resource-group Newsreel-RG | grep -i ingestion

# Check logs for errors
az functionapp logs tail --name newsreel-func-51689 --resource-group Newsreel-RG | grep -i "error\|exception"
```

**Quick fixes to try (in order):**
1. Verify connection string: `az functionapp config appsettings list`
2. Check RSS feeds are valid and reachable
3. Deploy latest code: `func azure functionapp publish`
4. Check logs for specific error message
5. Restart function app: `az functionapp restart`

---

### Issue: "Articles exist but no stories"

**Diagnosis:**
```bash
# Verify leases container exists
az cosmosdb sql container show --account-name newsreel-db-1759951135 \
  --database-name newsreel-db --name leases --resource-group Newsreel-RG

# Check change feed errors
az functionapp logs tail --name newsreel-func-51689 --resource-group Newsreel-RG | grep -i "changefeed"
```

**Quick fixes to try (in order):**
1. Create leases container: `bash Azure/scripts/setup-cosmos-db.sh`
2. Restart function app: `az functionapp restart --name newsreel-func-51689`
3. Check logs for clustering errors
4. Deploy latest code
5. Wait 1-2 minutes and check again (change feeds can be slow to initialize)

---

### Issue: "All stories have 1 source (MONITORING only)"

**Diagnosis:**
```bash
# Check clustering logs
az functionapp logs tail --name newsreel-func-51689 --resource-group Newsreel-RG | grep -i "clustering\|similarity"

# Get count of stories by status
# (Run in Cosmos DB Query Explorer)
SELECT c.status, COUNT(1) as count FROM c GROUP BY c.status
```

**Quick fixes to try (in order):**
1. Check similarity threshold: `grep STORY_FINGERPRINT_SIMILARITY_THRESHOLD Azure/functions/shared/config.py`
2. If threshold too high, lower it (try 0.65 instead of 0.75)
3. Check fingerprinting logic: search for similar titles manually
4. Enable debug logging for similarity scoring
5. Deploy updated config and restart

---

### Issue: "Stories exist but API returns empty"

**Diagnosis:**
```bash
# Test Cosmos DB query
python3 -c "
from Azure.api.app.services.cosmos_service import cosmos_service
cosmos_service.connect()
stories = cosmos_service.query_recent_stories(limit=5)
print(f'Total: {len(stories)}')
for s in stories:
    print(f'{s.get(\"id\")}: {s.get(\"status\")}')"

# Check API logs
az container logs --name newsreel-api-pod --resource-group Newsreel-RG
```

**Quick fixes to try (in order):**
1. Check if stories have status != MONITORING
2. Verify API has proper Cosmos DB connection string
3. Test API query endpoint directly
4. Check if filter logic is removing all stories
5. Deploy latest API code

---

## Logging Strategy for Debugging

### Enable Debug Logging Temporarily

In `Azure/functions/shared/config.py`:
```python
LOG_LEVEL = "DEBUG"  # Change from "INFO"
```

Then redeploy:
```bash
func azure functionapp publish newsreel-func-51689 --build remote
```

### Search Logs for Specific Issues

```bash
# RSS ingestion progress
az functionapp logs tail | grep "Articles ingested"

# Clustering matching
az functionapp logs tail | grep "Similarity:"

# Change feed processing
az functionapp logs tail | grep "Processing X documents"

# Errors
az functionapp logs tail | grep "ERROR\|Exception"

# Specific pattern
az functionapp logs tail | grep -i "what you're looking for"
```

---

## Iteration Checklist

For each cycle through the fix loop:

- [ ] Run tests and capture output
- [ ] Identify which tests fail
- [ ] Check function logs for errors
- [ ] Run diagnostic script
- [ ] Match symptoms to issue (see decision tree)
- [ ] Apply appropriate fix
- [ ] Re-run tests to verify
- [ ] Document the issue and fix
- [ ] If still failing, repeat from step 3

---

## Final Success State

When everything is working:

```
✅ System tests: 13/13 passing
✅ Integration tests: 59/59 passing  
✅ Unit tests: 54/54 passing
✅ Diagnostic shows:
   - 1000+ articles ingested
   - 500+ stories in clusters
   - Proper status distribution
   - Stories with 2-3 sources average
✅ API returns 20+ complete stories
✅ Stories updating every 30 seconds
```

---

## Tools & Commands Reference

```bash
# Quick diagnostic
python3 Azure/scripts/diagnose-clustering-pipeline.py

# Run tests
cd Azure/tests && pytest system/ -v

# Check logs
az functionapp logs tail --name newsreel-func-51689 --resource-group Newsreel-RG

# Deploy after fix
cd Azure/functions && func azure functionapp publish newsreel-func-51689 --build remote

# Restart function
az functionapp restart --name newsreel-func-51689 --resource-group Newsreel-RG

# Setup Cosmos DB containers
bash Azure/scripts/setup-cosmos-db.sh

# Query Cosmos DB (from Python)
python3 -c "from functions.shared.cosmos_client import CosmosDBClient; client = CosmosDBClient(); client.connect()"
```

---

**Keep iterating until all tests pass and the API returns perfect data!**

