# Feed Diagnosis: Single Source & No Summaries Issue 🔍

**Date**: October 13, 2025  
**Issue**: All stories from single source (News.com.au), no summaries, no feed updates  
**Status**: Diagnosed - Multiple Issues Identified

---

## 🐛 The Problem

**User Report** (Screenshot):
- All 3 stories show "7m ago" (same timestamp)
- All show "No summary available"
- All show "1 source"
- All appear to be from "Newscomau" (News.com.au)
- Feed hasn't updated in 6+ minutes

**This is NOT normal behavior** - Expected:
- Stories from multiple sources (BBC, Reuters, CNN, etc.)
- Mix of 1, 2, 3+ source stories
- Most stories should have summaries
- New stories every 10-30 seconds (continuous flow)

---

## 🔍 Possible Root Causes

### 1. **RSS Feed Failures** (Most Likely)

**Theory**: Most RSS feeds are failing or returning 304 (Not Modified), only News.com.au is working.

**Evidence**:
- Only one source appearing
- All stories same timestamp (from single batch)
- No diversity

**Causes**:
- Network issues reaching RSS feeds
- RSS feed URLs changed/broken
- Rate limiting from feed providers
- DNS resolution failures
- Timeout issues (RSS_TIMEOUT_SECONDS too low)

**How to Verify**:
```bash
# Check Azure Function logs for RSS fetch errors
az monitor log-analytics query \
  --workspace newsreel-logs \
  --analytics-query "traces | where message contains 'RSS' or message contains 'Feed' | take 100"
```

---

### 2. **Spam Filter Too Aggressive** (Possible)

**Theory**: The spam filter I just deployed is blocking legitimate news.

**Evidence**:
- Deployment happened ~15 minutes ago
- Timing matches when issue started
- Only News.com.au stories getting through

**Spam Filter Patterns** (from `utils.py`):
```python
r'\d+\s+best.*(?:deals|products|buys|items)'
r'(?:best|top)\s+\d+.*(?:deals|to shop|to buy)'
# etc.
```

**Risk Analysis**:
- Patterns are fairly specific (require "deals", "products", "to shop", etc.)
- **Unlikely** to block: "Trump announces policy", "Ukraine conflict updates"
- **Could block**: "Top 10 economic indicators" (if pattern too broad)

**User's Stories Show**:
- "'In danger:' Aussies not having enough children" - **NOT spam**
- "Get tested if you've visited this dentist" - **NOT spam**
- "Tears after family's unthinkable tragedy" - **NOT spam**

**None of these match spam patterns**, so spam filter is likely NOT the issue.

---

### 3. **Summarization Changefeed Failure** (Likely)

**Theory**: Cosmos DB changefeed for summarization is not triggering.

**Evidence**:
- ALL stories show "No summary available"
- Summarization should trigger within seconds
- This is a separate issue from single-source

**Causes**:
- Changefeed lease container issues
- Cosmos DB connection problems
- Anthropic API failures
- Content validation blocking summaries

**Recent Code Changes**:
```python
# I added this to skip content-less articles
if not has_content:
    logger.info(f"Skipping summary for story - no article content available")
    continue
```

**Could this be blocking?**
- If News.com.au RSS only has titles (no description/content)
- Then summarization would skip these stories
- This would explain "No summary available"

---

### 4. **Feed Polling Staggering Issue** (Possible)

**Theory**: Staggered polling is too aggressive, missing most feeds.

**Current Logic**:
```python
# Poll if 5 minutes have passed
if (now - last_poll).total_seconds() >= 300:
    feeds_to_poll.append(feed_config)

# But only poll max 3-4 feeds per cycle
max_feeds_per_cycle = max(3, len(all_feed_configs) // 30)
feed_configs = feeds_to_poll[:max_feeds_per_cycle]
```

**With 100 feeds**:
- 100 feeds / 30 cycles = ~3 feeds per 10-second cycle
- Each feed polled every 5 minutes
- **But**: If only 3-4 feeds ready per cycle, others wait

**Could cause**: Temporary clustering around one source if that source updates frequently while others return 304.

---

### 5. **Cosmos DB Write Failures** (Possible)

**Theory**: Articles are being fetched but failing to write to Cosmos DB.

**Evidence**:
- Would explain single source (only some writes succeeding)
- Would explain no diversity

**Causes**:
- Serverless tier throttling
- Connection issues
- Duplicate ID conflicts

---

## 🧪 Diagnostic Steps

### Step 1: Check Function Health

```bash
# Check if functions are running
az functionapp list-functions \
  --name newsreel-func-51689 \
  --resource-group newsreel-rg
```

### Step 2: Check Recent RSS Activity

```bash
# Query for RSS fetch logs (if Application Insights is set up)
# Look for:
# - How many feeds polled?
# - How many succeeded?
# - How many articles fetched?
# - Any error messages?
```

### Step 3: Test RSS Feeds Manually

```bash
# Test a few feeds directly
curl -s "https://feeds.reuters.com/reuters/topNews" | grep "<item>" | wc -l
curl -s "http://feeds.bbci.co.uk/news/world/rss.xml" | grep "<item>" | wc -l
curl -s "https://rss.cnn.com/rss/cnn_topstories.rss" | grep "<item>" | wc -l
```

### Step 4: Check Cosmos DB

```bash
# Query Cosmos DB directly to see:
# - How many articles in last 15 minutes?
# - How many sources?
# - How many stories?
```

### Step 5: Check Summarization

```bash
# Look for summarization changefeed logs
# Check if it's triggering
# Check for errors
```

---

## ✅ Immediate Fixes

### Fix 1: Temporarily Disable Spam Filter (Test)

To test if spam filter is the issue:

```python
# In function_app.py, comment out spam filter check
# Filter out spam/promotional content
# if is_spam_or_promotional(title, description, article_url):
#     logger.info(f"🚫 Filtered spam/promotional content: {title[:80]}...")
#     return None
```

**Deploy and wait 10 minutes**, check if diversity improves.

---

### Fix 2: Relax Content Validation for Summarization

The content validation might be too strict:

```python
# In function_app.py, SummarizationChangeFeed
# BEFORE (current):
has_content = any(
    article.get('content') or article.get('description')
    for article in articles
)
if not has_content:
    logger.info(f"Skipping summary - no article content available")
    continue

# AFTER (more lenient):
# Try to summarize even with minimal content
# The fallback summary will handle it
```

**Change**:
```python
# Remove this check entirely - let fallback summary handle it
# The refusal detection + fallback will create basic summaries
```

---

### Fix 3: Add Aggressive Logging

Add detailed logging to see what's happening:

```python
# In RSSIngestion function
logger.info(f"📰 Starting RSS poll cycle")
logger.info(f"Total feeds configured: {len(all_feed_configs)}")
logger.info(f"Feeds ready to poll: {len(feeds_to_poll)}")
logger.info(f"Polling {len(feed_configs)} feeds this cycle")

for feed_config in feed_configs:
    logger.info(f"  → Polling: {feed_config.name}")
    
# After fetch:
logger.info(f"Fetched {len(feed_results)} feeds successfully")
logger.info(f"Total articles: {total_articles}, New: {new_articles}")
logger.info(f"Sources with new content: {list(source_distribution.keys())}")
```

---

### Fix 4: Force Full Re-Poll

Reset the feed poll state to force all feeds to be polled:

```python
# In Cosmos DB, delete or update feed_poll_states
# This will force all feeds to be polled immediately
```

Or add a manual trigger:

```python
@app.function_name(name="ForceFullPoll")
@app.route(route="admin/force-poll", auth_level=func.AuthLevel.FUNCTION)
async def force_full_poll(req: func.HttpRequest) -> func.HttpResponse:
    """Force poll all RSS feeds immediately"""
    # Clear feed_poll_states
    # Trigger full poll
    return func.HttpResponse("Full poll triggered", status_code=200)
```

---

### Fix 5: Increase Feeds Per Cycle

Temporarily increase feeds polled per cycle:

```python
# BEFORE:
max_feeds_per_cycle = max(3, len(all_feed_configs) // 30)  # ~3-4 feeds

# AFTER (temporary):
max_feeds_per_cycle = max(10, len(all_feed_configs) // 10)  # ~10 feeds

# This will poll more feeds per cycle, improving diversity
```

---

## 🎯 Quick Action Plan

### Immediate (Next 10 minutes)

1. **Deploy logging enhancements** to see what's happening
2. **Remove content validation** from summarization (let it try anyway)
3. **Increase feeds per cycle** to 10 temporarily

### Short-term (Next hour)

4. **Monitor logs** to see feed diversity
5. **Check Cosmos DB** for actual story count and sources
6. **Test spam filter** by temporarily disabling

### Medium-term (Next day)

7. **Add feed health monitoring** to admin dashboard
8. **Implement feed retry logic** for failed feeds
9. **Add alerting** for low source diversity

---

## 📊 Expected Behavior vs. Actual

### Expected (Normal Operation)

**RSS Ingestion** (every 10 seconds):
- Poll 3-4 feeds
- Mix of sources (BBC, Reuters, CNN, etc.)
- Each feed returns 5-20 articles
- ~50-100 new articles per minute across all feeds

**Story Clustering** (immediate):
- Articles clustered by topic
- Stories with 1, 2, 3+ sources
- Diverse categories

**Summarization** (within 5 seconds):
- Stories get summaries
- 80%+ stories should have summaries
- "No summary available" only for very new/minimal content

**Feed Display**:
- Diverse sources
- Mix of timestamps (some "Just now", some "2m ago", etc.)
- Stories update continuously

### Actual (Current Issue)

**RSS Ingestion**:
- ❌ Only News.com.au appearing
- ❌ All same timestamp
- ❌ No diversity

**Story Clustering**:
- ❌ All single-source stories
- ❌ No multi-source verification

**Summarization**:
- ❌ No summaries at all
- ❌ ALL show "No summary available"

**Feed Display**:
- ❌ Static, not updating
- ❌ Single source only
- ❌ 6+ minutes without new content

---

## 🚨 Critical Issues Summary

### Issue 1: Single Source Feed
**Severity**: CRITICAL  
**Impact**: Complete loss of source diversity  
**Likely Cause**: RSS feed failures or poll state issues  
**Fix**: Increase feeds per cycle + add logging

### Issue 2: No Summaries
**Severity**: HIGH  
**Impact**: Poor user experience  
**Likely Cause**: Content validation too strict  
**Fix**: Remove content validation check

### Issue 3: No Feed Updates
**Severity**: HIGH  
**Impact**: Stale content  
**Likely Cause**: Poll cycle issues or Cosmos DB writes failing  
**Fix**: Force full re-poll

---

## 💡 Long-term Prevention

### 1. Feed Health Monitoring

Add to admin dashboard:
```swift
struct FeedHealth {
    let totalFeeds: Int
    let activeFeeds: Int
    let failedFeeds: Int
    let lastSuccessfulPoll: Date
    let sourceDiversity: Double  // 0-1 score
}
```

### 2. Automatic Retry Logic

```python
# If feed fails, retry with exponential backoff
if response.status != 200:
    retry_count = feed_states[feed_config.name].get('retry_count', 0)
    if retry_count < 3:
        # Add to retry queue
        pass
```

### 3. Alerting

```python
# Alert if source diversity drops below threshold
if unique_sources < 5:
    # Send alert
    logger.error(f"ALERT: Low source diversity: {unique_sources} sources")
```

### 4. Fallback Mode

```python
# If diversity drops, temporarily increase polling frequency
if diversity_score < 0.3:
    max_feeds_per_cycle *= 3  # Poll 3x more feeds
```

---

## 🎉 Next Steps

**What I'll do now**:

1. ✅ Create fixes for content validation
2. ✅ Add aggressive logging
3. ✅ Increase feeds per cycle temporarily
4. ✅ Deploy updates
5. ✅ Monitor for 10-15 minutes
6. ✅ Report back on improvements

**What you should see in 10-15 minutes**:
- Stories from multiple sources (BBC, Reuters, CNN, etc.)
- Mix of 1, 2, 3+ source stories
- More stories with summaries
- Continuous feed updates

Let me implement these fixes now! 🚀

