# Critical Timestamp Bug Fixed - October 17, 2025

## Problem
Old stories were appearing at the top of the iOS app feed with recent timestamps (e.g., "1 min" or "32 min" ago), even though they were actually hours or days old. This was causing the feed to show stale news as if it were breaking news.

## Root Cause
The **summarization Azure Function** was incorrectly updating the `last_updated` field every time it added or updated a summary. This caused all stories to get the same `last_updated` timestamp when they were batch-summarized, making old stories appear fresh.

### Example of the Problem
All three stories had identical `last_updated` timestamps:
```json
{
  "id": "story_20251013_094104_337977",
  "first_seen": "2025-10-13T09:20:47Z",
  "last_updated": "2025-10-13T12:22:05.175483Z"
},
{
  "id": "story_20251013_091838_2ef831",
  "first_seen": "2025-10-13T09:00:00Z",
  "last_updated": "2025-10-13T12:22:05.175483Z"
},
{
  "id": "story_20251013_070525_23eac1",
  "first_seen": "2025-10-13T06:57:50Z",
  "last_updated": "2025-10-13T12:22:05.175483Z"
}
```

Note how all three stories have the exact same `last_updated` timestamp, even though they have different `first_seen` times. This happened when the summarization function processed all three stories in a batch and updated their timestamps.

## Fix Applied

### File: `Azure/functions/summarization/function_app.py`

**Before (line 249-254):**
```python
# Update story with summary
updates = {
    'summary': summary.model_dump(mode='json'),
    'version_history': version_history,
    'last_updated': datetime.now(timezone.utc).isoformat()  # ❌ WRONG!
}
```

**After:**
```python
# Update story with summary
# NOTE: Do NOT update last_updated here - that field is only for source updates
# Otherwise old stories with new summaries appear at top of feed
updates = {
    'summary': summary.model_dump(mode='json'),
    'version_history': version_history
    # ✅ last_updated removed - only updated when NEW SOURCES are added
}
```

## Expected Behavior

The `last_updated` field should ONLY be updated when:
1. ✅ A new source article is added to the story (via story clustering)
2. ✅ The story status changes (e.g., MONITORING → DEVELOPING → BREAKING)
3. ✅ The story title or content is updated due to new information

The `last_updated` field should NOT be updated when:
1. ❌ A summary is generated or updated
2. ❌ User interactions occur (likes, saves, views)
3. ❌ Internal metadata changes

## Deployment
✅ Deployed to Azure Function App `newsreel-func-51689` on October 17, 2025 at 21:23 UTC

All 5 Azure Functions confirmed running:
- BreakingNewsMonitor
- RSSIngestion
- StoryClusteringChangeFeed
- SummarizationBackfill
- SummarizationChangeFeed ← **This function was fixed**

## Impact
- ✅ Feed will now show stories in correct chronological order based on when sources were last added
- ✅ Old stories will no longer appear as "1 min ago" just because they got a summary
- ✅ Breaking news will correctly appear at the top of the feed
- ✅ Story freshness indicators will be accurate

## Related Fix
Also fixed in this session:
- **iOS App**: `APIService.swift` line 712 - Removed `example.com` fallback for article URLs, now properly validates and uses source URLs or a better fallback.

## Testing
To verify the fix is working:
1. Wait for new stories to be ingested (RSS runs every 5 minutes)
2. Check the `/api/stories/breaking` endpoint
3. Verify that `last_updated` timestamps are different for different stories
4. Open iOS app and confirm feed shows stories in correct order
5. Verify "time ago" labels are accurate

## Status
✅ **FIXED and DEPLOYED**

