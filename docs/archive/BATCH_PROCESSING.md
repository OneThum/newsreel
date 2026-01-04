# Batch Processing for AI Summarization

## Overview

Newsreel uses Anthropic's Message Batches API for cost-effective backfill summarization. This provides **50% cost savings** on backfill summaries while maintaining high-quality AI-generated content.

### Cost Comparison

| Processing Type | Model | Input Cost | Output Cost | Use Case |
|----------------|-------|------------|-------------|----------|
| **Real-time** | Haiku 4.5 | $1.00/MTok | $5.00/MTok | Breaking news, new stories |
| **Batch** | Haiku 4.5 | $0.50/MTok | $2.50/MTok | Backfill, older stories |

### Savings Example

For 1,000 backfill summaries per day:
- **Old cost (Sonnet 4)**: ~$7.50/day
- **New cost (Haiku 4.5 real-time)**: ~$2.50/day
- **With batch processing**: ~$1.25/day
- **Total savings**: ~83% reduction from original cost

## Architecture

### Two-Track Summarization

1. **Real-time (Change Feed Trigger)**
   - Processes new stories immediately as they're created/updated
   - Uses regular Messages API for instant results
   - Critical for breaking news and user experience
   - ~70-80% of summaries

2. **Batch Processing (Timer Trigger)**
   - Runs every 30 minutes
   - Processes older stories missing summaries
   - Uses Message Batches API with 50% discount
   - ~20-30% of summaries

### Workflow

```
Every 30 minutes:
  1. Check completed batches → Process results → Update stories
  2. Find stories needing summaries → Submit new batch → Track in Cosmos

Batch processing time: Typically 15-45 minutes
Results available for: 29 days
```

## Configuration

### Environment Variables

```bash
# Enable/disable batch processing (default: true)
BATCH_PROCESSING_ENABLED=true

# Already set - controls old backfill function (can disable now)
SUMMARIZATION_BACKFILL_ENABLED=false
```

### Config Settings

In `Azure/functions/shared/config.py`:

```python
BATCH_PROCESSING_ENABLED: bool = True  # Master switch
BATCH_MAX_SIZE: int = 500  # Max stories per batch
BATCH_BACKFILL_HOURS: int = 48  # Only process stories from last N hours
BATCH_POLL_INTERVAL_MINUTES: int = 30  # How often to check/submit
```

## Cosmos DB Setup

### New Container Required

The batch processing system requires a new Cosmos DB container:

**Container Name**: `batch_tracking`
**Partition Key**: `/batch_id`
**Purpose**: Track batch submissions and status

### Creating the Container

Using Azure Portal:
1. Go to your Cosmos DB account
2. Navigate to Data Explorer
3. Create new container:
   - Database: `newsreel-db`
   - Container ID: `batch_tracking`
   - Partition key: `/batch_id`
   - Throughput: 400 RU/s (can use shared database throughput)

Using Azure CLI:
```bash
az cosmosdb sql container create \
  --account-name YOUR_COSMOS_ACCOUNT \
  --database-name newsreel-db \
  --name batch_tracking \
  --partition-key-path /batch_id \
  --throughput 400
```

## Deployment

### 1. Deploy Updated Code

```bash
cd Azure/functions
func azure functionapp publish YOUR_FUNCTION_APP_NAME
```

### 2. Verify Deployment

Check that the new function appears:
```bash
az functionapp function list \
  --name YOUR_FUNCTION_APP_NAME \
  --resource-group YOUR_RESOURCE_GROUP
```

You should see: `BatchSummarizationManager`

### 3. Enable Batch Processing

If not enabled by default:
```bash
az functionapp config appsettings set \
  --name YOUR_FUNCTION_APP_NAME \
  --resource-group YOUR_RESOURCE_GROUP \
  --settings BATCH_PROCESSING_ENABLED=true
```

### 4. Disable Old Backfill (Optional)

Since batch processing replaces the old backfill:
```bash
az functionapp config appsettings set \
  --name YOUR_FUNCTION_APP_NAME \
  --resource-group YOUR_RESOURCE_GROUP \
  --settings SUMMARIZATION_BACKFILL_ENABLED=false
```

## Monitoring

### Batch Status Tracking

Query active batches:
```sql
SELECT * FROM c 
WHERE c.status = 'in_progress' 
ORDER BY c.created_at DESC
```

Query completed batches:
```sql
SELECT * FROM c 
WHERE c.status = 'completed' 
ORDER BY c.ended_at DESC
```

### Function Logs

Monitor the batch processing function:
```bash
func azure functionapp logstream YOUR_FUNCTION_APP_NAME --browser
```

Look for:
- `✅ Batch submitted:` - New batch created
- `Batch {id}: ended` - Batch processing complete
- `✅ Batch summary for {story_id}` - Individual story processed
- `✅ Completed batch {id}: N succeeded, M errored` - Batch summary

### Key Metrics

Track these in Application Insights:

**Batch Submission**:
- Number of batches submitted per day
- Stories per batch (should be near BATCH_MAX_SIZE)
- Time to submit batch

**Batch Processing**:
- Success rate (succeeded / total requests)
- Average processing time (created_at → ended_at)
- Cost per summary

**Overall Health**:
- Stories missing summaries (should trend down)
- Batch vs real-time summary ratio
- Daily AI costs

## Troubleshooting

### No Batches Being Submitted

**Check**:
1. Is `BATCH_PROCESSING_ENABLED=true`?
2. Are there stories needing summaries?
3. Check function logs for errors

**Query stories needing summaries**:
```sql
SELECT COUNT(1) as count FROM c 
WHERE (NOT IS_DEFINED(c.summary) OR c.summary = null)
AND ARRAY_LENGTH(c.source_articles) >= 1
AND c.status != 'MONITORING'
AND c.last_updated >= '2025-10-16T00:00:00Z'
```

### Batch Processing Slow

**Normal**: Most batches complete in <1 hour
**If >2 hours**: Check Anthropic API status

**Batches may process slower during**:
- High API demand
- Very large batches (>500 requests)

### High Error Rates

**Check batch results**:
```python
# In batch_tracking container
SELECT c.succeeded_count, c.errored_count, c.request_count
FROM c
WHERE c.status = 'completed'
ORDER BY c.ended_at DESC
```

**Common errors**:
- `invalid_request`: Request body issue (check prompt format)
- `rate_limit_error`: Hitting API limits (will retry automatically)
- `expired`: Batch took >24h (rare, indicates heavy load)

### Summaries Not Appearing

**Verify batch tracking**:
1. Check that batch status is 'completed'
2. Check succeeded_count > 0
3. Verify stories were updated in story_clusters

**Manual reprocess**:
If a batch failed, you can manually trigger:
```bash
# Wait for next scheduled run (every 30 min)
# Or restart the function app to trigger immediately
az functionapp restart --name YOUR_FUNCTION_APP_NAME
```

## Cost Optimization Tips

### 1. Adjust Backfill Window

Reduce `BATCH_BACKFILL_HOURS` if you have few missing summaries:
```python
BATCH_BACKFILL_HOURS: int = 24  # Instead of 48
```

### 2. Monitor Batch vs Real-time Ratio

Ideal split:
- Real-time: 70-80% (fresh stories)
- Batch: 20-30% (backfill)

If batch is >40%, you may have real-time summarization issues.

### 3. Use Prompt Caching

The batch implementation already uses ephemeral caching on system prompts.
Typical cache hit rate: 30-98% depending on traffic.

### 4. Reduce Batch Frequency

If backlog is small, reduce frequency:
```python
@app.schedule(schedule="0 0 */1 * * *", ...)  # Every hour instead of 30 min
```

## Migration from Old Backfill

### Recommended Approach

1. **Deploy batch processing** (both functions active)
2. **Monitor for 24 hours** (verify batches work)
3. **Disable old backfill** (`SUMMARIZATION_BACKFILL_ENABLED=false`)

### Rollback Plan

If batch processing has issues:
```bash
# Disable batch processing
az functionapp config appsettings set \
  --name YOUR_FUNCTION_APP_NAME \
  --settings BATCH_PROCESSING_ENABLED=false

# Re-enable old backfill
az functionapp config appsettings set \
  --name YOUR_FUNCTION_APP_NAME \
  --settings SUMMARIZATION_BACKFILL_ENABLED=true
```

## API References

- [Anthropic Batch API Docs](https://docs.anthropic.com/en/docs/build-with-claude/batch-processing)
- [Message Batches API Reference](https://docs.anthropic.com/en/api/creating-message-batches)

## FAQ

### Q: Will batch processing delay breaking news summaries?

**A**: No. Breaking news uses the real-time changefeed trigger and is processed immediately. Batch processing only handles backfill.

### Q: How long do batches take to process?

**A**: Typically 15-45 minutes. Maximum 24 hours before expiration.

### Q: Can I increase BATCH_MAX_SIZE above 500?

**A**: Yes, up to 100,000 requests or 256 MB. However, 500 is recommended for:
- Faster processing times
- Better error isolation
- More frequent result updates

### Q: What happens if a batch expires (>24 hours)?

**A**: Expired requests won't be charged. Stories will be picked up in the next batch submission.

### Q: Do batch results show in the admin dashboard?

**A**: Yes. Batch summaries include `cost_usd` and are counted in the 24h metrics with the 50% discount reflected.

### Q: Can I manually trigger a batch submission?

**A**: The function runs every 30 minutes automatically. You can restart the function app to trigger sooner, but this affects all functions.

## Summary

Batch processing provides significant cost savings for backfill summarization while maintaining the same quality as real-time summaries. The system is designed to be:

- **Automatic**: Runs every 30 minutes without intervention
- **Resilient**: Handles errors gracefully, retries failed batches
- **Efficient**: 50% cost reduction on backfill summaries
- **Transparent**: Full tracking and monitoring in Cosmos DB

Combined with the switch to Claude Haiku 4.5, you're now running at ~15-20% of the original cost while maintaining quality.

