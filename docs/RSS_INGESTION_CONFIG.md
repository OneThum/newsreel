# 📡 RSS INGESTION CONFIGURATION

**Current Status**: ✅ **OPTIMIZED FOR CONTINUOUS FLOW**  
**Last Updated**: October 17, 2025

---

## 🎯 Current Configuration

### Schedule
- **Frequency**: Every 10 seconds
- **Pattern**: `*/10 * * * * *` (CRON expression)
- **Feeds per cycle**: 5 feeds
- **Result**: 1 new article ~every 3 seconds on average

### Why This Works Better
```
OLD APPROACH (Every 5 minutes):
  ❌ Poll 100 feeds all at once
  ❌ Massive spike of articles
  ❌ 5 minute gaps between updates
  ❌ "Lumpy" user experience

NEW APPROACH (Every 10 seconds):
  ✅ Poll 5 feeds per cycle
  ✅ Staggered article delivery
  ✅ ~3-second average article arrival
  ✅ Continuous "firehose" experience
  ✅ Better for real-time news
```

### Math
With ~100 feeds available:
```
Feeds per cycle: 5
Cycle duration: 10 seconds
Total feeds: 100

Time to poll all feeds: 100 ÷ 5 × 10s = 200s (3.3 minutes)
Feeds eligible per cycle: Based on 3-minute cooldown

Coverage pattern:
- Cycle 1 (0s): Feeds A,B,C,D,E polled
- Cycle 2 (10s): Feeds F,G,H,I,J polled
- ...
- Cycle 20 (200s): All feeds polled, A,B,C,D,E eligible again
- Result: Continuous polling with no silence gaps
```

---

## 📍 Implementation Location

### Active Configuration
**File**: `Azure/functions/function_app.py`  
**Lines**: 516-620+  
**Function**: `rss_ingestion_timer()`

### Key Code Section
```python
@app.function_name(name="RSSIngestion")
@app.schedule(schedule="*/10 * * * * *", arg_name="timer", run_on_startup=True)
async def rss_ingestion_timer(timer: func.TimerRequest) -> None:
    """RSS Ingestion - Runs every 10 seconds with staggered feed polling"""
    
    # ... determine feeds to poll ...
    
    # Poll 5 feeds per cycle for truly continuous distribution
    max_feeds_per_cycle = 5
    feed_configs = feeds_to_poll[:max_feeds_per_cycle]
    
    # ... fetch and process articles ...
```

---

## 🔧 Configuration Parameters

### Core Settings (from `config.py`)
```python
RSS_MAX_CONCURRENT = 5      # Concurrent feeds per cycle
RSS_TIMEOUT_SECONDS = 30    # Timeout for feed fetch
RSS_USER_AGENT = "Newsreel/1.0"
RSS_USE_ALL_FEEDS = False   # MVP mode (use all 10 feeds) vs Full (all 100)
```

### Feed Eligibility (Cool-down)
- **Cool-down period**: 3 minutes (180 seconds)
- **Rationale**: 
  - 100 feeds ÷ 5 per cycle × 10s = 200s (3.3 min) to complete cycle
  - 3-min cooldown creates overlap for continuous flow
  - Feeds become eligible during the polling cycle, not after

### Staggered Polling Algorithm
```python
# Each cycle:
1. Get all feed configurations
2. Check feed poll states (last_poll time)
3. Determine which feeds are eligible:
   - Never polled OR
   - Last polled > 3 minutes ago
4. Take first 5 eligible feeds
5. Poll them in parallel
6. Store new articles to Cosmos DB
7. Update poll state with current timestamp
```

---

## 📊 Performance Characteristics

### Articles Per Minute
```
Scenario 1: Average (5 articles per feed per cycle)
  5 feeds × 5 articles × 6 cycles/min = 150 articles/min

Scenario 2: High (10 articles per feed per cycle)
  5 feeds × 10 articles × 6 cycles/min = 300 articles/min

Scenario 3: Breaking News (15+ articles per feed)
  5 feeds × 15 articles × 6 cycles/min = 450 articles/min

RESULT: Continuous stream, 150-450 articles/min depending on news volume
```

### Response Time to Breaking News
```
Article published in feed → Newsreel ingested: 0-10 seconds
(Average 5 seconds)

Contrast with old 5-min approach:
Article published → Newsreel ingested: 0-5 minutes
(Average 2.5 minutes delay)

IMPROVEMENT: 15-30x faster response to breaking news
```

---

## 🔴 Legacy Configuration (Deprecated)

### Old Setup
**File**: `Azure/functions/rss_ingestion/function_app.py`  
**Schedule**: Every 5 minutes (`0 */5 * * * *`)  
**Feeds per cycle**: All 100+ feeds at once  
**Status**: ❌ **DEPRECATED** - Kept for reference only

### Why It Was Replaced
- ❌ Batch processing created lumpy updates
- ❌ 5-minute gaps between update cycles
- ❌ Poor response to breaking news (2.5 min average delay)
- ❌ Resource spike every 5 minutes
- ❌ Poor user experience (updates in clumps)

---

## ✅ Configuration Checklist

### Before Deployment
- [ ] Verify `*/10 * * * * *` schedule in CRON
- [ ] Verify `max_feeds_per_cycle = 5`
- [ ] Verify `3-minute` cooldown period
- [ ] Verify `RSS_MAX_CONCURRENT = 5`
- [ ] Verify `RSS_TIMEOUT_SECONDS = 30`

### After Deployment
- [ ] Monitor logs for "Polling X feeds this cycle"
- [ ] Verify ~6 cycles per minute appear in logs
- [ ] Check articles arriving at 0.3-3 second intervals
- [ ] Verify feed poll states updating in Cosmos DB
- [ ] Monitor for any "No feeds need polling" messages (should be rare)

### Monitoring Queries
```python
# Check feed ingestion rate
SELECT c.timestamp, COUNT(1) as articles
FROM c
WHERE c.container = 'raw_articles'
GROUP BY c.timestamp

# Check polling frequency
SELECT c.feed_name, c.last_poll, c.poll_count
FROM c
WHERE c.container = 'feed_poll_states'
ORDER BY c.last_poll DESC
```

---

## 🚀 Optimization Options

### For Even Faster Updates (10-15 seconds vs 10s):
```python
# Change schedule to every 10-15 seconds instead
@app.schedule(schedule="*/15 * * * * *")  # Every 15 seconds

# Reduce feeds per cycle to 2-3
max_feeds_per_cycle = 3

# Result: 1 feed every 5-6 seconds, slightly more spread out
```

### For Higher Throughput:
```python
# Increase feeds per cycle
max_feeds_per_cycle = 10

# Increase concurrent connections
RSS_MAX_CONCURRENT = 10

# Result: More articles but might overwhelm clustering pipeline
```

### For Lower Resource Usage:
```python
# Increase cycle interval
@app.schedule(schedule="*/30 * * * * *")  # Every 30 seconds

# Reduce feeds per cycle
max_feeds_per_cycle = 3

# Result: Articles every 20 seconds, lower load
```

---

## 📋 Troubleshooting

### Issue: Articles arriving in bursts, not continuous
**Cause**: Schedule not running every 10 seconds  
**Solution**: Check CRON expression: `*/10 * * * * *` (not `0 */5`)

### Issue: Large gaps between articles
**Cause**: Cooldown period too long or feeds exhausted  
**Solution**: Reduce cooldown from 3 minutes to 2 minutes (if adequate feed coverage)

### Issue: Too many failed feed fetches
**Cause**: Feeds per cycle too high or timeout too short  
**Solution**: Reduce `max_feeds_per_cycle` or increase `RSS_TIMEOUT_SECONDS`

### Issue: Clustering pipeline overwhelmed
**Cause**: Too many articles per cycle  
**Solution**: Reduce `max_feeds_per_cycle` from 5 to 3

---

## 🔄 Migration from Old to New Configuration

### Step 1: Deploy new function_app.py
```bash
cd Azure/functions
func azure functionapp publish newsreel-functions
```

### Step 2: Disable old function (optional)
```bash
# Rename old function name to mark as deprecated
# Or delete from rss_ingestion/function_app.py
```

### Step 3: Verify in logs
```bash
# Watch for "Polling X feeds this cycle" every 10 seconds
az functionapp log stream --name newsreel-functions --resource-group Newsreel-RG
```

### Step 4: Monitor for 5-10 minutes
- Verify 6+ polling cycles per minute
- Verify continuous article arrival
- Verify no "No feeds need polling" messages

---

## 📚 Related Documentation

- **Azure Functions Configuration**: `Azure/functions/README.md`
- **RSS Feed Strategy**: `docs/RSS_FEED_STRATEGY.md`
- **Clustering Pipeline**: `docs/CLUSTERING_IMPROVEMENTS.md`
- **System Architecture**: `README.md`

---

**Configuration Status**: ✅ **OPTIMIZED**  
**News Flow**: ✅ **CONTINUOUS (1 article ~every 3 seconds)**  
**User Experience**: ✅ **REAL-TIME NEWS UPDATES**

