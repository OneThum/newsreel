# Active Debug Session 6: API Session Token Issue Identified

## 🎯 Session Achievements

### ✅ Fixed Function App Bug
- Fixed `log_story_cluster()` parameter mismatch
- Removed invalid `unique_sources` parameter
- Added missing `action`, `fingerprint`, `title` parameters
- Function App now logs properly

### ✅ Root Cause Analysis: API 500 Error
**Error**: `CosmosResourceNotFoundError: The read session is not available for the input session token`

**Root Cause**: 
- Cosmos DB client in API Container is creating session tokens
- When multiple concurrent requests use same client, tokens become invalid
- Session consistency layer can't find read session from token

### ✅ Implemented Solution
Added retry mechanism in `query_recent_stories()`:
1. Catch `CosmosResourceNotFoundError`
2. Reset Cosmos DB client connection
3. Recreate container proxies
4. Retry query with fresh connection
5. If retry fails, surface error

## 📊 Pipeline Status

```
✅ RSS Ingestion      (RSSIngestion function)
   ↓ 100 feeds, 10 second cycle
✅ Raw Articles       (3,298 articles in Cosmos DB)
   ↓ change feed trigger
✅ Story Clustering   (StoryClusteringChangeFeed function)
   ↓ 523 story clusters created
⚠️  API Layer         (500 error - session token issue)
   ↓
❌ iOS App            (cannot query stories)
```

## 🔍 Technical Details

### Session Token Error Sequence
1. API Container App starts
2. CosmosClient created, session consistency enabled
3. First request queries Cosmos DB successfully
4. Concurrent request #2 uses same client
5. Cosmos DB returns different session token for request #2
6. Client tries to use old token, gets "read session not available"

### Why It Happens
- Azure Cosmos DB SDK uses session consistency by default
- Single client instance with concurrent requests = token collisions
- Solution: Either disable session consistency OR reset client on error

### Fix Applied
- Added exception handler for `CosmosResourceNotFoundError`
- Resets all connection state on session error
- Retry creates fresh connection for new request
- Isolates session tokens per attempt

## 📝 Files Modified

- `Azure/api/app/services/cosmos_service.py`
  - Added retry mechanism to `query_recent_stories()`
  - Resets client on session token error
  
- `Azure/functions/function_app.py`
  - Fixed `log_story_cluster()` call parameters

## 🚀 What's Next

1. **Rebuild & Deploy API**
   - Build Docker image with session fix
   - Push to Azure Container Registry
   - Update Container App with new image

2. **Test API**
   - Verify `/api/stories/feed` returns stories
   - Check response time
   - Monitor for session token errors

3. **Verify Summarization**
   - Check if summarization change feed triggered
   - Verify AI summaries created for 523 stories

4. **Full Test Suite**
   - Run all integration tests
   - Run system tests
   - Achieve 100% pass rate

## 📈 Session Progress

- Session 1-3: Infrastructure fixes (54% → 70%)
- Session 4: Bugs identified (75%)
- Session 5: Clustering breakthrough (85%)
- **Session 6: API root cause found + fix implemented (87%)**
- Session 7: Deploy fix + complete testing (goal: 95%+)

## ⏰ Time Estimate for Session 7

- Deploy API: 10-15 minutes
- Test API: 5 minutes
- Fix any remaining issues: 10-20 minutes
- Run full test suite: 5-10 minutes
- Total: ~30-50 minutes

**Next milestone**: **90%** - API fully working, ready for production
**Final milestone**: **100%** - All tests passing, clustering + summarization + API complete

## 🎓 Lessons Learned

1. **Session Consistency Issues**: When using Cosmos DB SDK in API servers, be careful with client reuse across concurrent requests
2. **Silent Failures**: Exception handling that swallows errors makes debugging harder
3. **Systematic Approach**: Test → Logs → Database → Root Cause → Fix → Verify

The core data pipeline is solid. API just needs session management fix.
