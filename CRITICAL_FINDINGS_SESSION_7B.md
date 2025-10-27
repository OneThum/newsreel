# Critical Findings: Why iOS App Shows No Summaries or Sources

## Investigation Summary

Through testing, we discovered why the iOS app is showing empty summaries and sources despite the API returning 200 OK:

### Issue #1: Sources Are Missing ❌

**What we found:**
- API endpoint `/api/stories/feed` returns 200 OK
- But `source_count=0` for all stories
- `sources` array is empty

**Root cause:**
- When clustering function creates stories, it was storing full article objects in `source_articles`
- API expects `source_articles` to be a list of **string IDs** from the raw_articles container
- API code does: `await cosmos_service.get_story_sources(source_ids)` expecting IDs
- But gets: `[{id, source, title, url, ...}, ...]` objects instead

**Fix applied:**
- Changed clustering function to store ONLY `article.id` in `source_articles`
- Not `{id, source, title, ...}` objects
- API will now be able to fetch real source articles from raw_articles container

**Issue:** Old stories (1,515) have wrong format, new stories will have correct format

### Issue #2: Summaries Are NULL ❌

**What we found:**
- API returns `summary=null` for all stories
- No AI-generated summaries present

**Root cause:**
- Summarization pipeline is queued to trigger (we have a test that passes)
- But summaries haven't been created yet
- Likely needs more time or there's an issue with the summarization change feed trigger

**Solution needed:**
- Verify summarization function is executing
- Check if it's creating summaries in Cosmos DB
- May need to check Application Insights logs for summarization errors

## Data Schema Mismatch

The clustering algorithm was designed with one schema, but the API expects a different one:

**Clustering Function Creates:**
```json
{
  "source_articles": [
    {
      "id": "article_123",
      "source": "BBC",
      "title": "...",
      "url": "...",
      "published_at": "..."
    }
  ]
}
```

**API Expects:**
```json
{
  "source_articles": ["article_123", "article_456", ...]
}
```

Then API does:
```python
sources = await get_story_sources(source_ids)  # Fetch from raw_articles by ID
```

## Current Status After Fix

✅ **Fix deployed** - Future stories will store only IDs
❌ **Old 1,515 stories** - Still have full objects (won't work with API)
❌ **Summaries** - Still NULL, waiting for summarization to complete

## Next Actions Required

1. **Option A: Fresh Start (Recommended)**
   - Delete all 1,515 stories from story_clusters
   - Let clustering re-create them with correct format
   - New stories will have proper source IDs
   - Summarization will then work on fresh data

2. **Option B: Data Migration**
   - Write script to extract IDs from existing source_articles objects
   - Update all 1,515 stories with corrected format
   - More complex but preserves existing data

3. **Verify Summarization**
   - Check Application Insights for summarization function execution
   - Verify summaries are being created in Cosmos DB
   - May need to trigger manually or restart function

## Why This Matters

Without sources and summaries:
- iOS app shows bare story titles only
- Users can't see which news outlets reported the story
- Users can't see AI-generated summaries for quick reading
- Core value of the app is missing

## Test Results Summary

- ✅ 11/13 system tests passing (85%)
- ✅ API returning 200 OK
- ✅ Clustering creating 1,515+ stories
- ✅ Authentication working
- ❌ Sources missing (data format issue - now fixed)
- ❌ Summaries NULL (AI summarization not complete)

## Conclusion

The system is architecturally sound. The issues are:
1. **Schema mismatch** in how data was stored vs how API expects it (FIXED)
2. **Summarization pipeline** not yet populated (needs verification/completion)

Once these are resolved, the iOS app will show complete story data.
