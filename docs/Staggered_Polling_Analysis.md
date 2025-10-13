# 🔄 Staggered Polling Analysis & Fix

**Diagnosed**: 2025-10-13 05:00 UTC  
**Priority**: **🔴 CRITICAL** - Major contributor to feed quality issues  
**Status**: ⚠️ **ISSUE IDENTIFIED** - Solution proposed

---

## 🚨 The Problem

### What's Actually Happening:

The staggered polling system IS working, but it's creating a **burst-then-silence pattern** instead of continuous flow:

**Timeline from Logs:**
```
04:49:44 - ✅ Polled 12 feeds (90 ready)
04:49:55 - ✅ Polled 12 feeds (71 ready)
04:50:00 - ✅ Polled 12 feeds (78 ready)
04:50:33 - ✅ Polled 12 feeds (59 ready)
04:50:40 - ✅ Polled 12 feeds (47 ready)
04:50:50 - ✅ Polled 12 feeds (35 ready)
04:51:00 - ✅ Polled 12 feeds (23 ready)
04:51:10 - ✅ Polled 11 feeds (11 ready)

Then from 04:52:00 onwards:
04:52:00 - ❌ "No feeds need polling this cycle"
04:52:10 - ❌ "No feeds need polling this cycle"
04:52:20 - ❌ "No feeds need polling this cycle"
04:52:30 - ❌ "No feeds need polling this cycle"
...for 3 minutes straight
```

**Pattern:**
- ⚡ 2 minutes of intense activity (polling 121 feeds)
- 😴 3 minutes of complete silence (waiting for cooldown)
- 🔄 Repeat

---

## 🔍 Root Cause Analysis

### Current Configuration:

```python
# function_app.py line 284
if not last_poll or (now - last_poll).total_seconds() >= 300:  # 5-minute cooldown
    feeds_to_poll.append(feed_config)

# function_app.py line 290
max_feeds_per_cycle = max(10, len(all_feed_configs) // 10)  # ~12 feeds per cycle
```

### The Math:

```
Total feeds: 121
Feeds per cycle: 12
Timer interval: 10 seconds

121 feeds / 12 feeds per cycle = ~10 cycles
10 cycles × 10 seconds = ~100 seconds (1.7 minutes)

Then all 121 feeds wait for 5-minute cooldown:
300 seconds - 100 seconds = 200 seconds (~3.3 minutes) of silence
```

**Result:** Burst-then-silence instead of continuous flow!

---

## 📊 Current vs. Desired Behavior

### Current (Broken):
```
Time:  0s    60s   120s  180s  240s  300s  360s  420s  480s
Feed:  ████████    ⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫    ████████    ⚫⚫⚫⚫⚫⚫
       ^burst      ^silence      ^burst      ^silence
       
Articles arrive in waves, not continuous stream
User sees: Nothing... Nothing... FLOOD... Nothing... FLOOD
```

### Desired (Continuous):
```
Time:  0s    60s   120s  180s  240s  300s  360s  420s  480s
Feed:  ██████████████████████████████████████████████████
       ^continuous flow
       
Articles arrive steadily
User sees: Constant stream of fresh news
```

---

## ✅ Solution Options

### **Option 1: Reduce Cooldown (Quick Fix)**

**Change:**
```python
# From 5 minutes to 2.5 minutes
if not last_poll or (now - last_poll).total_seconds() >= 150:  # 2.5-minute cooldown
```

**Result:**
```
121 feeds / 12 per cycle = 10 cycles = 100 seconds
Then 50 seconds of silence (150s - 100s)
Pattern: 1.7 min activity + 50s silence = 2.2 min total cycle
```

**Pros:**
- ✅ Minimal code change
- ✅ Reduces silence gap from 3 min to 50 seconds
- ✅ More frequent updates

**Cons:**
- ❌ Still has burst pattern (less severe)
- ❌ Higher API load (may hit rate limits)
- ❌ Doesn't fully solve the problem

**Rating:** 5/10 - Band-aid fix

---

### **Option 2: Poll Fewer Feeds Per Cycle (Better Distribution)**

**Change:**
```python
# From ~12 to 3-4 feeds per cycle
max_feeds_per_cycle = 4  # Fixed, not calculated
```

**Result:**
```
121 feeds / 4 per cycle = ~30 cycles
30 cycles × 10 seconds = 300 seconds (5 minutes)
Then immediate restart (no gap!)
Pattern: Continuous 5-minute cycle
```

**Pros:**
- ✅ Truly continuous flow (no silence gaps)
- ✅ Each feed polled every 5 minutes (predictable)
- ✅ Simple implementation

**Cons:**
- ❌ Less responsive to breaking news (5 min vs 2 min)
- ❌ Lower overall throughput

**Rating:** 7/10 - Good distribution, but slower

---

### **Option 3: Hybrid Approach (Best Balance)** ⭐ **RECOMMENDED**

**Change:**
```python
# Poll 5 feeds per cycle, 3-minute cooldown
max_feeds_per_cycle = 5
if not last_poll or (now - last_poll).total_seconds() >= 180:  # 3-minute cooldown
```

**Result:**
```
121 feeds / 5 per cycle = ~24 cycles
24 cycles × 10 seconds = 240 seconds (4 minutes)
Cooldown: 180 seconds (3 minutes)
Pattern: Continuous with overlapping cycles
```

**Timeline:**
```
Cycle 1 starts:   0s → 240s (polls feeds 1-121)
Cycle 2 starts: 180s → 420s (polls feeds 1-121 again)
Gap between:     60s overlap (continuous!)
```

**Pros:**
- ✅ True continuous flow (no silence periods)
- ✅ Each feed polled every 3-4 minutes (responsive)
- ✅ Better breaking news detection
- ✅ Balanced throughput
- ✅ Overlapping cycles ensure no gaps

**Cons:**
- ❌ Slightly more complex math

**Rating:** 9/10 - Best of all worlds

---

### **Option 4: Priority Queue (Most Sophisticated)**

**Change:**
```python
# Always poll feeds with oldest last_poll time
feeds_to_poll = sorted(
    [(f, feed_states.get(f.name, {}).get('last_poll', datetime.min)) 
     for f in all_feed_configs],
    key=lambda x: x[1]  # Sort by last_poll time
)
feed_configs = [f[0] for f in feeds_to_poll[:5]]  # Take 5 oldest
```

**Result:**
- Feeds naturally distributed over time
- No hard cooldown, just continuous oldest-first
- Self-balancing system

**Pros:**
- ✅ Truly continuous flow
- ✅ Self-optimizing
- ✅ No gaps or bursts possible
- ✅ Most elegant solution

**Cons:**
- ❌ More code changes required
- ❌ Harder to understand/debug

**Rating:** 10/10 - Perfect, but complex

---

## 🎯 Recommended Solution: **Option 3 (Hybrid)**

### Implementation:

```python
# function_app.py lines 280-291

# Poll if never polled OR if 3 minutes have passed (reduced from 5)
if not last_poll or (now - last_poll).total_seconds() >= 180:  # 3-minute cooldown
    feeds_to_poll.append(feed_config)

# Poll 5 feeds per cycle for continuous distribution
max_feeds_per_cycle = 5  # Fixed at 5 instead of calculated
feed_configs = feeds_to_poll[:max_feeds_per_cycle]
```

### Expected Results:

**Before (Current):**
```
Timeline: ████⚫⚫⚫████⚫⚫⚫████⚫⚫⚫
Articles: Burst... nothing... burst... nothing
User experience: Inconsistent, frustrating
Health check: "Only 6 cycles in 10 min" ⚠️
```

**After (Hybrid):**
```
Timeline: ████████████████████████████
Articles: Continuous steady stream
User experience: Fresh news every 30-60s
Health check: "24+ cycles in 10 min" ✅
```

**Metrics:**
- Articles per minute: **~15-20** (vs current 0-40 bursts)
- Max gap between articles: **30-60s** (vs current 3+ minutes)
- Feeds polled per hour: **15-20 times** per feed (vs current 12)
- User sees new story: **Every 30-60s** (vs every 3-5 min)

---

## 📐 Detailed Math: Option 3

### Cycle Calculations:

```
Total feeds: 121
Feeds per cycle: 5
Timer interval: 10 seconds
Cooldown: 180 seconds (3 minutes)

Full cycle time: 121 feeds / 5 per cycle = 24.2 cycles
24.2 cycles × 10 seconds = 242 seconds (4 minutes 2 seconds)

When feeds become eligible again: 180 seconds (3 minutes)
Gap analysis: 242s - 180s = 62s overlap (NO SILENCE!)
```

### Example Timeline:

```
Time     Action                           Feeds Ready
----     ------                           -----------
00:00    Poll feeds 1-5                   116
00:10    Poll feeds 6-10                  111
00:20    Poll feeds 11-15                 106
...
03:00    Feeds 1-5 eligible again!        +5
03:10    Poll feeds 116-120 + feed 1      1
03:20    Poll feeds 121, 2-5              5
03:30    Poll feeds 6-10                  10
...      Continuous forever               Never 0
```

**Key insight:** By 3:00 (when first feeds become eligible), we're still polling the tail end. Perfect overlap!

---

## 🔧 Implementation Plan

### Step 1: Code Changes

**File:** `Azure/functions/function_app.py`

```python
# Line 284 - Reduce cooldown from 5 to 3 minutes
if not last_poll or (now - last_poll).total_seconds() >= 180:  # 3-minute cooldown (was 300)
    feeds_to_poll.append(feed_config)

# Line 290 - Fixed feeds per cycle instead of calculated
max_feeds_per_cycle = 5  # Fixed at 5 for continuous distribution (was max(10, len(all_feed_configs) // 10))
```

### Step 2: Deploy

```bash
cd Azure/functions
func azure functionapp publish newsreel-func-51689 --python
```

### Step 3: Monitor (10 minutes after deploy)

```bash
cd Azure/scripts
./query-logs.sh custom "traces | where timestamp > ago(15m) | where message contains 'Polling' and message contains 'feeds this cycle' | project timestamp, message | order by timestamp desc | take 30"
```

**Expected output:**
```
Every 10 seconds: "Polling 5 feeds this cycle"
No "No feeds need polling" messages
```

### Step 4: Verify Continuous Flow

```bash
# Run health check
./analyze-system-health.sh 15m

# Expected:
# - Staggered polling: 60+ cycles in 10 min (vs current 6)
# - Feed diversity: 0.4+ score (vs current 0.12)
# - Articles: Steady stream, not bursts
```

---

## 📊 Performance Predictions

### Current System:
```
Cycle time:        5 minutes (with 3 min silence)
Active time:       40% (2 min active, 3 min silent)
Feeds per cycle:   12 (too many)
Throughput:        ~24 feeds/minute during burst, 0 during silence
User experience:   Inconsistent, frustrating bursts
```

### After Fix:
```
Cycle time:        3 minutes (continuous overlap)
Active time:       100% (always polling)
Feeds per cycle:   5 (well-distributed)
Throughput:        ~30 feeds/minute steady
User experience:   Fresh news every 30-60s
```

---

## 🎓 Why This Fixes Feed Quality

### Problem 1: Source Diversity
**Before:** All 121 feeds polled in 2 minutes → clustering sees all sources at once → hard to match articles
**After:** 5 feeds every 10 seconds → clustering has time to match as they arrive → better multi-source stories

### Problem 2: Stale Feed
**Before:** 3-minute gaps with no new content → users see "no updates"
**After:** Continuous flow → users always see fresh content

### Problem 3: Breaking News Detection
**Before:** If news breaks during 3-minute silence, delayed until next burst
**After:** Always polling → breaking news detected within 30-60s

### Problem 4: User Retention
**Before:** Open app → nothing new → 2 min later → flood of news → confusing
**After:** Open app → always something new → consistent experience → better retention

---

## 🧪 Testing Plan

### Test 1: Verify No Silence Gaps

```bash
# Query for "No feeds need polling" messages
./query-logs.sh custom "traces | where timestamp > ago(15m) | where message contains 'No feeds need polling' | count"

# Expected: 0 (or very rare)
```

### Test 2: Verify Continuous Polling

```bash
# Check polling frequency
./query-logs.sh custom "traces | where timestamp > ago(10m) | where message contains 'feeds this cycle' | summarize count() by bin(timestamp, 1m)"

# Expected: ~6 per minute (one every 10 seconds)
```

### Test 3: Verify Source Diversity

```bash
# Check unique sources per time window
./query-logs.sh source-diversity 15m | jq '.unique_sources'

# Expected: 30-40 sources (vs current 5-10)
```

### Test 4: User-Facing Test

1. Open Newsreel app
2. Pull to refresh
3. Wait 1 minute
4. Pull to refresh
5. Repeat for 10 minutes

**Expected:** New stories every 1-2 refreshes (vs current 5-10 refreshes)

---

## 🔮 Alternative: Option 4 (Future Enhancement)

If Option 3 doesn't fully solve the problem, implement priority queue:

```python
async def rss_ingestion_timer(timer: func.TimerRequest) -> None:
    # Get all feeds with their last poll times
    all_feeds = get_all_feeds()
    feed_states = await cosmos_client.get_feed_poll_states()
    now = datetime.now(timezone.utc)
    
    # Build priority list: (feed, time_since_poll)
    feed_priority = []
    for feed in all_feeds:
        last_poll = feed_states.get(feed.name, {}).get('last_poll')
        if last_poll:
            time_since_poll = (now - last_poll).total_seconds()
        else:
            time_since_poll = float('inf')  # Never polled = highest priority
        
        feed_priority.append((feed, time_since_poll))
    
    # Sort by time_since_poll (longest first)
    feed_priority.sort(key=lambda x: x[1], reverse=True)
    
    # Take top 5 (oldest)
    feeds_to_poll = [f[0] for f in feed_priority[:5]]
    
    logger.info(f"📰 Polling {len(feeds_to_poll)} oldest feeds (last poll: {feed_priority[0][1]/60:.1f}m ago)")
    
    # ... rest of function ...
```

**Benefits:**
- ✅ Truly self-balancing
- ✅ No hardcoded cooldowns
- ✅ Automatically adapts to any number of feeds
- ✅ Impossible to have silence gaps

---

## 📋 Summary

**Problem:** Burst-then-silence pattern (2 min activity, 3 min silence)  
**Root Cause:** Polling too many feeds per cycle (12), then 5-minute cooldown  
**Solution:** Poll 5 feeds per cycle, 3-minute cooldown = continuous overlap  
**Impact:** Continuous news flow, better source diversity, happier users  

**Next Step:** Implement Option 3 and monitor for 30 minutes ✅

---

## 📝 Deployment Checklist

- [ ] Update `function_app.py` line 284: Change 300 to 180
- [ ] Update `function_app.py` line 290: Change calculation to fixed `5`
- [ ] Deploy to Azure Functions
- [ ] Wait 10 minutes for function to restart
- [ ] Run health check
- [ ] Verify no "No feeds need polling" messages
- [ ] Check article flow in app
- [ ] Monitor for 30 minutes
- [ ] Document results

---

**Ready to implement Option 3?** This will dramatically improve feed quality! 🚀


