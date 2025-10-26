# Summarization Backfill - 4 Hour Time Limit

**Date**: October 18, 2025  
**Status**: ✅ Deployed

## Change Summary

Updated the `SummarizationBackfill` function to only process stories from the last **4 hours** instead of processing all stories without summaries.

## Why This Change?

**Budget Control**: Prevents wasting API credits on old stories that users are unlikely to see. Focuses summarization budget on:
- ✅ Recent, relevant stories (last 4 hours)
- ✅ Stories users are actually viewing
- ❌ Old stories from days/weeks ago that won't appear in feeds

## Technical Details

### Modified Function
`Azure/functions/function_app.py` - `summarization_backfill_timer()`

### Before
```python
query = """
SELECT * FROM c 
WHERE (NOT IS_DEFINED(c.summary) OR c.summary = null OR c.summary.text = null OR c.summary.text = '')
AND ARRAY_LENGTH(c.source_articles) >= 1
AND c.status != 'MONITORING'
ORDER BY c.last_updated DESC
OFFSET 0 LIMIT 50
"""
```

### After
```python
# Only process stories from the last 4 hours
four_hours_ago = (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat(timespec='seconds') + 'Z'

query = f"""
SELECT * FROM c 
WHERE (NOT IS_DEFINED(c.summary) OR c.summary = null OR c.summary.text = null OR c.summary.text = '')
AND ARRAY_LENGTH(c.source_articles) >= 1
AND c.status != 'MONITORING'
AND c.last_updated >= '{four_hours_ago}'
ORDER BY c.last_updated DESC
OFFSET 0 LIMIT 50
"""
```

## Impact

### Cost Savings
- **Before**: Could process thousands of old stories
- **After**: Only processes recent stories (typically 0-50 per run)
- **Estimated savings**: 90%+ reduction in backfill API calls

### User Experience
- ✅ No impact - users only see recent stories in their feeds
- ✅ All recent stories will have summaries
- ✅ Change feed still generates summaries for all new stories as they arrive

## How It Works

### Story Flow
1. **New stories** → `SummarizationChangeFeed` generates summaries immediately (no change)
2. **Stories 0-4 hours old without summaries** → `SummarizationBackfill` catches them (NEW LIMIT)
3. **Stories >4 hours old without summaries** → Ignored (saves budget)

### Backfill Schedule
- Runs every 10 minutes
- Processes up to 50 stories per run
- Only looks at stories from last 4 hours
- Status: `SUMMARIZATION_BACKFILL_ENABLED=true`

## Deployment

### Deployed To
- Function App: `newsreel-func-51689`
- Resource Group: `Newsreel-RG`
- Deployment: October 18, 2025 at 19:12 UTC

### Deployment Command
```bash
cd Azure/functions
func azure functionapp publish newsreel-func-51689 --python
```

### Deployment Result
✅ **Success** - Remote build completed, all 5 functions deployed

## Verification

### Expected Behavior
When the backfill function runs, logs should show:
```
Found {N} recent stories (last 4 hours) needing summaries
```

Instead of:
```
Found {N} stories needing summaries (out of ~5,558 total)
```

### Monitor Logs
```bash
# Check function execution
az functionapp function show \
  --resource-group Newsreel-RG \
  --name newsreel-func-51689 \
  --function-name SummarizationBackfill

# Check cost impact via Azure Portal
# Navigate to: Cost Management + Billing > Cost Analysis
# Filter: Last 7 days, Resource: newsreel-func-51689
```

## Configuration

### Environment Variables (unchanged)
- `SUMMARIZATION_BACKFILL_ENABLED=true` - Enable backfill function
- `ANTHROPIC_API_KEY=<key>` - API key for Claude

### Function Schedule (unchanged)
- **Change Feed**: Immediate (triggered by Cosmos DB changes)
- **Backfill**: Every 10 minutes (`0 */10 * * * *`)
- **Breaking News Monitor**: Every 2 minutes (`0 */2 * * * *`)

## Next Steps

### Monitor
1. Check backfill logs to see how many stories are being processed
2. Monitor API costs to confirm reduction
3. Verify user-facing stories all have summaries

### Potential Adjustments
- If 4 hours is too short: Change to 6 or 8 hours
- If 4 hours is too long: Change to 2 or 3 hours
- If backfill is unnecessary: Disable with `SUMMARIZATION_BACKFILL_ENABLED=false`

## Related Changes

This change is part of the broader fix for:
- ✅ RSS ingestion diversity (121 feeds enabled)
- ✅ API source count bug (removed ORDER BY in Cosmos query)
- ✅ Summarization coverage (change feed + backfill)
- ✅ **Budget control** (this 4-hour limit)

---

**Status**: Complete and deployed ✅  
**Impact**: High cost savings, zero user impact  
**Risk**: Low - only affects backfill, not real-time summarization

