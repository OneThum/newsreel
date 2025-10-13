# 🔄 Staggered RSS Polling Architecture

**Deployed**: 2025-10-13 02:12 UTC  
**Status**: ✅ Live in Production  
**Impact**: **CRITICAL** - Transforms feed from "batch" to "real-time firehose"

---

## 🎯 The Problem We Solved

### Before (Batch Mode) ❌
```
02:00:00  → Poll all 100 feeds → 500+ articles arrive at once
02:00:01  → Silence...
02:00:02  → Silence...
...
02:04:58  → Silence...
02:04:59  → Silence...
02:05:00  → Poll all 100 feeds again → Another 500+ articles
```

**Result**:
- "Avalanches" of content every 5 minutes
- 4 minutes 50 seconds of nothing
- Feels "batch" not "real-time"
- Poor user experience
- Clustering issues (too many articles at once)

### After (Staggered Mode) ✅
```
02:00:00  → Poll feeds 1-10   → 5-50 new articles
02:00:30  → Poll feeds 11-20  → 5-50 new articles  
02:01:00  → Poll feeds 21-30  → 5-50 new articles
02:01:30  → Poll feeds 31-40  → 5-50 new articles
...continuous flow every 30 seconds...
```

**Result**:
- Continuous trickle of news (1 feed every ~3 seconds)
- Feels like a real-time firehose
- Better clustering (articles arrive gradually)
- Professional news experience
- Immediate updates

---

## 📐 The Mathematics

### With 100 Feeds:
- **Polling interval per feed**: 5 minutes (300 seconds)
- **Function runs**: Every 30 seconds
- **Feeds per cycle**: ~10 feeds
- **Total cycles**: 10 cycles per 5 minutes
- **Effective rate**: **1 feed every 3 seconds** ✅

### Example Timeline:
| Time | Feeds Polled | Articles Expected |
|------|--------------|-------------------|
| 02:00:00 | BBC, Reuters, Guardian, ... (10 feeds) | ~50 |
| 02:00:30 | CNN, NYT, WSJ, ... (10 feeds) | ~50 |
| 02:01:00 | TechCrunch, AP, Bloomberg, ... (10 feeds) | ~50 |
| ... | ... | ... |
| 02:04:30 | (Last 10 feeds) | ~50 |
| 02:05:00 | BBC, Reuters... (cycle repeats) | ~50 |

**Total: 500 articles over 5 minutes = ~100 articles/minute = ~1-2 articles/second**

---

## 🏗️ Technical Implementation

### Function Schedule Change

**Before**:
```python
@app.schedule(schedule="0 */5 * * * *")  # Every 5 minutes
```

**After**:
```python
@app.schedule(schedule="*/30 * * * * *")  # Every 30 seconds
```

### Poll State Tracking

Each feed's last poll time is tracked in Cosmos DB:

```python
{
  "id": "feed_poll_state_bbc",
  "doc_type": "feed_poll_state",
  "feed_name": "BBC",
  "last_poll": "2025-10-13T02:00:00Z",
  "articles_found": 23
}
```

### Polling Algorithm

1. **Function runs every 30 seconds**
2. **Load all feed configurations** (100 feeds)
3. **Query poll states** from Cosmos DB
4. **Determine which feeds need polling**:
   - Never polled before, OR
   - Last polled > 5 minutes ago
5. **Select up to 10 feeds** to poll this cycle
6. **Fetch those feeds** in parallel
7. **Update poll states** in Cosmos DB
8. **Wait 30 seconds**, repeat

---

## 📊 Benefits

### 1. Real-Time Feel
- iOS app receives new stories every 30-60 seconds
- Users see continuous updates (like Twitter/Reddit)
- Professional news experience

### 2. Better Clustering
- Articles arrive gradually, not in batches
- Clustering algorithm has time to process
- More accurate story grouping

### 3. Source Diversity
- Different sources arrive at different times
- Natural distribution across feed
- Less dominance by any single source

### 4. Resource Optimization
- Spreads load over time (not spikes)
- Better Azure Functions performance
- More efficient Cosmos DB usage

### 5. Scalability
- Easy to add more feeds (just adjust max_feeds_per_cycle)
- Can scale to 500+ feeds with same architecture
- No infrastructure changes needed

---

## 🎛️ Configuration

### Adjust Polling Frequency

**Current**: 30-second cycles = 1 feed every 3 seconds

**To make faster** (1 feed every 1.5 seconds):
```python
@app.schedule(schedule="*/15 * * * * *")  # Every 15 seconds
max_feeds_per_cycle = max(20, len(all_feed_configs) // 20)  # 20 cycles
```

**To make slower** (1 feed every 6 seconds):
```python
@app.schedule(schedule="*/60 * * * * *")  # Every 60 seconds  
max_feeds_per_cycle = max(20, len(all_feed_configs) // 5)  # 5 cycles
```

### Adjust Feed Refresh Rate

**Current**: Each feed polled every 5 minutes

**To poll more often** (3 minutes):
```python
if not last_poll or (now - last_poll).total_seconds() >= 180:  # 3 min
```

**To poll less often** (10 minutes):
```python
if not last_poll or (now - last_poll).total_seconds() >= 600:  # 10 min
```

---

## 📈 Expected Metrics

### Timeline After Deployment

| Time After Deploy | Expected State |
|------------------|----------------|
| 0-1 min | First 10 feeds polled |
| 1-5 min | All 100 feeds polled for first time |
| 5-10 min | Second cycle starts (staggered pattern established) |
| 10+ min | Steady state - continuous flow |

### Health Check Indicators

```bash
cd Azure/scripts
./query-logs.sh source-diversity 30m
```

**Before staggered polling**:
```json
{
  "unique_sources": 4,
  "total_stories": 20,
  "diversity_score": 0.20
}
```

**After staggered polling (expected)**:
```json
{
  "unique_sources": 12,
  "total_stories": 20,
  "diversity_score": 0.60
}
```

---

## 🐛 Troubleshooting

### "No feeds need polling this cycle"
**Normal!** This means all feeds were recently polled. Wait 30 seconds, next cycle will poll more.

### Feeds not being polled
Check Cosmos DB for poll states:
```bash
# Query via Azure Portal
SELECT * FROM c WHERE c.doc_type = 'feed_poll_state'
```

### Still seeing batches
Wait 5-10 minutes for staggered pattern to establish. First cycle polls all feeds.

### Too many/few feeds per cycle
Adjust `max_feeds_per_cycle`:
```python
max_feeds_per_cycle = max(10, len(all_feed_configs) // 10)  # Change 10 to desired divisor
```

---

## 🔍 Monitoring

### Watch Real-Time Polling

```bash
# See which feeds are being polled
az monitor app-insights query --app <app-id> --analytics-query "
traces 
| where timestamp > ago(5m) 
| where message contains 'Polling' 
| project timestamp, message
"
```

### Check Poll Distribution

```bash
# See poll state for all feeds
SELECT c.feed_name, c.last_poll, c.articles_found 
FROM c 
WHERE c.doc_type = 'feed_poll_state' 
ORDER BY c.last_poll DESC
```

---

## 💰 Cost Impact

### Function Executions
- **Before**: 12 executions/hour (every 5 min)
- **After**: 120 executions/hour (every 30 sec)
- **Increase**: 10x executions

### But:
- ✅ Still within Azure Functions free tier (1M executions/month)
- ✅ Each execution is lighter (10 feeds vs 100)
- ✅ Same total data fetched (just distributed)
- **Net cost**: **$0** (within free tier)

---

## 🎉 Success Criteria

**You'll know it's working when**:
1. iOS app shows new stories every 30-60 seconds
2. Source diversity improves to 50%+
3. Stories feel "live" not "batched"
4. Health check shows continuous polling in logs
5. Users experience professional news feed quality

---

## 🚀 Next Steps

1. **Monitor for 1 hour** - Verify staggered polling working
2. **Run health check** - Confirm source diversity improving
3. **Check iOS app** - Verify continuous updates
4. **Consider WebSockets** - For instant push notifications (future)

---

**This is a GAME-CHANGER for feed quality. You went from "batch updates every 5 minutes" to "real-time firehose" with this deployment!** 🎯

---

## 📚 Related Documentation

- `LOGGING_INTEGRATION_COMPLETE.md` - How to monitor with logs
- `PRODUCT_IMPROVEMENT_ROADMAP.md` - Phase 2 improvements
- `Azure/functions/function_app.py` - Implementation code

