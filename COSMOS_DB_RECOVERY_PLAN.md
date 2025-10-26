# Cosmos DB Recovery Plan

## Critical Issue Summary

The deployed Newsreel system is non-functional because the Cosmos DB database and containers are missing from Azure. This is causing all system tests to fail with "Owner resource does not exist" errors.

### Impact
- ❌ API cannot access any data
- ❌ Function App clustering trigger cannot process articles
- ❌ No stories available for users
- ❌ RSS ingestion pipeline blocked

---

## Root Cause Analysis

1. **Database Missing**: The `newsreel` database does not exist in the Cosmos DB account
2. **No Containers**: Required containers (raw_articles, story_clusters, etc.) are not created
3. **No Initialization**: Database initialization was not performed during deployment
4. **Configuration Remains Set**: Function App has correct connection string configured

---

## Recovery Plan

### Phase 1: Verify Prerequisites
- [x] Azure CLI installed and authenticated
- [x] Access to resource group: `Newsreel-RG`
- [x] Cosmos DB account exists: `newsreel-db-1759951135`
- [x] Function App exists: `newsreel-func-51689`

### Phase 2: Create Database & Containers

**Action Items:**

1. **Run Database Setup Script**
   ```bash
   cd Azure/scripts
   bash setup-cosmos-db.sh
   ```
   
   This script will:
   - Verify Cosmos DB account exists
   - Create `newsreel` database with 4000 RU/s
   - Create all required containers with correct partition keys:
     - `raw_articles` (partition: /category)
     - `story_clusters` (partition: /category)
     - `user_profiles` (partition: /user_id)
     - `user_interactions` (partition: /user_id)
     - `batch_tracking` (partition: /id)
     - `feed_poll_states` (partition: /feed_id)
     - `leases` (partition: /id)

2. **Expected Output**
   ```
   ✅ Cosmos DB account found
   ✅ Database created/verified
   ✅ All containers created/verified
   ✅ Setup Complete!
   ```

### Phase 3: Verify Connection

**Action Items:**

1. **Run Verification Script**
   ```bash
   cd Azure/scripts
   bash verify-cosmos-connection.sh
   ```
   
   This script will:
   - Verify database exists
   - Check all containers exist
   - Verify Function App configuration
   - Test Python connection to Cosmos DB
   - Count items in raw_articles

2. **Expected Output**
   ```
   ✅ Database exists: newsreel
   ✅ All containers verified
   ✅ COSMOS_CONNECTION_STRING is set
   ✅ Successfully connected to database
   ✅ Verification Complete!
   ```

### Phase 4: Restart Services

**Action Items:**

1. **Restart Function App**
   ```bash
   az functionapp restart --name newsreel-func-51689 --resource-group Newsreel-RG
   ```
   - Ensures Function App picks up database changes
   - Resets change feed triggers
   - Clears any stale connections

2. **Monitor Function App**
   ```bash
   # Watch for RSS ingestion
   az functionapp log tail --name newsreel-func-51689 --resource-group Newsreel-RG
   ```

### Phase 5: Test Data Ingestion

**Action Items:**

1. **Wait for First Articles**
   - RSS polling runs every 10 seconds
   - Should see articles in `raw_articles` within 30 seconds
   - Expected: 5-10 articles per cycle

2. **Monitor Change Feed Trigger**
   - Change feed should fire when articles arrive
   - Should see stories in `story_clusters`
   - Expected: Stories created when 2+ sources match

3. **Run System Tests**
   ```bash
   cd Azure/tests
   pytest system/test_deployed_api.py::TestDeployedAPI -v
   ```

### Phase 6: Verify Full Pipeline

**Action Items:**

1. **Test API Endpoint**
   ```bash
   curl -H 'Authorization: Bearer <JWT_TOKEN>' \
     https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/api/stories/feed
   ```
   - Should return 200 status
   - Should include stories with summaries

2. **Run Full Test Suite**
   ```bash
   cd Azure/tests
   pytest -v --json-report --json-report-file=reports/.report.json
   ```
   - All tests should pass

---

## Timeline Estimate

| Phase | Task | Duration | Status |
|-------|------|----------|--------|
| 1 | Verify Prerequisites | 2 min | ✅ Complete |
| 2 | Create Database & Containers | 3 min | ⏳ Ready |
| 3 | Verify Connection | 2 min | ⏳ Ready |
| 4 | Restart Services | 2 min | ⏳ Ready |
| 5 | Test Data Ingestion | 5 min | ⏳ Ready |
| 6 | Verify Full Pipeline | 5 min | ⏳ Ready |
| **Total** | **Complete Recovery** | **~20 min** | ⏳ **Ready** |

---

## Rollback Plan

If issues occur during recovery:

1. **Database Issues**: Delete and recreate database
   ```bash
   az cosmosdb sql database delete --account-name newsreel-db-1759951135 \
     --resource-group Newsreel-RG --name newsreel
   bash setup-cosmos-db.sh
   ```

2. **Connection Issues**: Verify Function App settings
   ```bash
   az functionapp config appsettings list --name newsreel-func-51689 \
     --resource-group Newsreel-RG
   ```

3. **Trigger Issues**: Restart Function App
   ```bash
   az functionapp restart --name newsreel-func-51689 --resource-group Newsreel-RG
   ```

---

## Success Criteria

✅ **System is fully functional when:**

1. Database exists and contains containers
2. Function App can connect to database
3. Articles appear in raw_articles within 30 seconds
4. Stories appear in story_clusters within 1 minute
5. API returns stories with summaries
6. All system tests pass

---

## Documentation References

- [Azure Setup Guide](/docs/Azure_Setup_Guide.md)
- [Cosmos DB Documentation](https://docs.microsoft.com/en-us/azure/cosmos-db/)
- [Azure Functions Bindings](https://docs.microsoft.com/en-us/azure/azure-functions/functions-triggers-bindings?tabs=csharp)

---

## Next Steps After Recovery

Once the system is back online:

1. Set up monitoring and alerts
2. Review and optimize costs
3. Plan for production readiness
4. Document lessons learned
5. Implement automated database backup
