# 🔥 Breaking News Test Plan - Live Testing with Gaza Hostage Release

**Created**: 2025-10-13 05:39 UTC  
**Test Story**: Gaza Hostage Release (ongoing)  
**Story ID**: `story_20251012_084423_58f041ad44cd`  
**Status**: 🟢 **TESTING IN PROGRESS**

---

## 🎯 Test Objectives

### Primary Goal:
Verify that the Israel/Gaza hostage release story (happening RIGHT NOW) is properly detected as breaking news and displayed prominently in the feed.

### Success Criteria:
1. ✅ Story promoted to BREAKING when new sources add articles
2. ✅ Story stays BREAKING for up to 90 minutes after last update
3. ✅ Story resurfaces to TOP of feed on every update
4. ✅ Users see 🚨 BREAKING badge
5. ✅ Status transitions to VERIFIED after 90 min of no updates

---

## 📊 Configuration Changes

### Deployed (05:39 UTC):

**1. Extended Breaking News Duration:**
```python
# Before: 30 minutes
# After: 90 minutes

if time_since_update >= timedelta(minutes=90):
    # Transition BREAKING → VERIFIED
```

**Why:** Major breaking news (hostage releases, elections, disasters) develops over hours, not minutes. 90 minutes allows multiple update cycles while story is actively developing.

**2. Extended Active Development Window:**
```python
# Before: 15 minutes
# After: 30 minutes

elif is_gaining_sources and time_since_update < timedelta(minutes=30):
    status = StoryStatus.BREAKING.value
```

**Why:** Some sources report slower than others. 30-minute window catches all major sources while story is fresh.

**3. Enhanced Logging:**
```python
logger.info(
    f"📊 Status evaluation: sources={prev}→{new}, "
    f"age={age}m, last_update={idle}m ago, "
    f"current_status={status}, is_gaining={gaining}"
)
```

**Why:** Real-time visibility into status evaluation decisions for debugging.

---

## 🧪 Test Scenarios

### Scenario 1: Story Promotion to BREAKING

**Setup:**
- Story exists: "Gaza ceasefire problem" (created Oct 12)
- Current status: VERIFIED
- Current sources: 5

**Expected Behavior:**
- New source adds article (e.g., Reuters)
- `is_gaining_sources = True`
- `time_since_update = 0-30 minutes`
- Status: VERIFIED → BREAKING 🔥
- Story jumps to top of feed
- Log: "🔥 Story promoted to BREAKING (actively developing)"

**Test Commands:**
```bash
# Check if promotion happened
./check-story-now.sh story_20251012_084423_58f041ad44cd

# Expected: "Current Status: BREAKING"
```

---

### Scenario 2: Story Stays BREAKING During Development

**Setup:**
- Story status: BREAKING
- Multiple sources adding articles over time

**Expected Behavior:**
- Story receives new article every 10-30 minutes
- Each update: `last_updated` timestamp changes
- Status: BREAKING (maintained)
- Story stays at top of feed
- Log: "→ Keeping BREAKING status (actively updated story)"

**Test Commands:**
```bash
# Monitor in real-time (updates every 30 seconds)
./monitor-breaking-news.sh

# Watch for:
# - "Added [source] source → X total"
# - "Status: BREAKING (continues)"
```

---

### Scenario 3: Story Transitions to VERIFIED

**Setup:**
- Story status: BREAKING
- No new sources for 90 minutes

**Expected Behavior:**
- 90 minutes pass with no updates
- BreakingNewsMonitor runs (every 5 min)
- Detects: `time_since_update >= 90 minutes`
- Status: BREAKING → VERIFIED
- Story stays visible but badge changes
- Log: "🔄 Status transition: BREAKING → VERIFIED (idle: 90m)"

**Test Commands:**
```bash
# Check for transition
./query-logs.sh custom "traces | where timestamp > ago(2h) | where message contains 'Status transition' and message contains 'story_20251012_084423_58f041ad44cd' | project timestamp, message"

# Expected: "Status transition: BREAKING → VERIFIED - No updates for 90 minutes"
```

---

### Scenario 4: Feed Ordering

**Setup:**
- Multiple stories in feed
- Gaza story gets updated

**Expected Behavior:**
- Before update: Gaza story on page 2-3
- New source added: `last_updated` changes
- Feed re-sorts by `max(first_seen, last_updated)`
- Gaza story moves to position #1
- User sees story at top on next refresh

**Test Commands:**
```bash
# Check feed order via API (requires auth)
# Or check in iOS app
```

---

## 🔍 Monitoring Tools

### Real-Time Monitor (Recommended):
```bash
cd /Users/davemac/Library/CloudStorage/OneDrive-OneThumSoftware/One\ Thum\ Software/Newsreel/Azure/scripts

# Start continuous monitoring (updates every 30s)
./monitor-breaking-news.sh
```

**Output includes:**
- Latest story status
- Recent source additions
- Breaking news monitor activity
- Status transitions

---

### Quick Status Check:
```bash
# Get current status of Gaza story
./check-story-now.sh story_20251012_084423_58f041ad44cd
```

**Output includes:**
- Current status (BREAKING/VERIFIED)
- Source count
- Time since last update
- Recommendations

---

### Manual Queries:

**Check Story Status Evolution:**
```bash
./query-logs.sh custom "traces | where timestamp > ago(30m) | where message contains 'story_20251012_084423_58f041ad44cd' | where message contains 'Status evaluation' or message contains 'promoted to BREAKING' or message contains 'Story Cluster:' | project timestamp, message | order by timestamp desc | take 20"
```

**Check Breaking News Promotions:**
```bash
./query-logs.sh custom "traces | where timestamp > ago(30m) | where message contains '🔥' or message contains 'promoted to BREAKING' | project timestamp, message | order by timestamp desc | take 10"
```

**Check Status Transitions:**
```bash
./query-logs.sh custom "traces | where timestamp > ago(2h) | where message contains '🔄 Status transition' | project timestamp, message | order by timestamp desc | take 10"
```

---

## 📋 Test Checklist

### Phase 1: Immediate (5-10 minutes after deploy)
- [ ] Function restarted (check logs)
- [ ] RSS polling active (check for new articles)
- [ ] Status evaluation logging visible
- [ ] Gaza story still being updated

### Phase 2: Active Development (next 30-60 minutes)
- [ ] Gaza story promoted to BREAKING (if new source added)
- [ ] Status evaluation shows correct decision factors
- [ ] Story appears at top of feed
- [ ] BREAKING badge visible in app
- [ ] `last_updated` timestamp changing on updates

### Phase 3: Transition (after 90 min of no updates)
- [ ] Story transitions to VERIFIED
- [ ] Transition logged correctly
- [ ] Badge changes in app
- [ ] Story remains visible but not "breaking"

### Phase 4: Re-activation (if new developments)
- [ ] If story gets new source after transition
- [ ] Story re-promoted to BREAKING
- [ ] Cycle can repeat multiple times

---

## 📊 Expected Timeline

Based on current behavior (05:39 UTC):

**05:39** - Deployment complete, function restarting  
**05:41** - Function active, RSS polling resumes  
**05:45** - Next potential story update (if new source reports)  
**05:45** - Status evaluation logged  
**05:45** - Story promoted to BREAKING (if conditions met)  
**05:46** - Story visible at top of feed  
**07:15** - Story transitions to VERIFIED (if no updates for 90 min)

---

## 🎓 What We're Testing

### Core Hypothesis:
**"Actively developing stories should be marked as BREAKING and stay visible at the top of the feed, regardless of when they were originally created."**

### Key Assumptions:
1. ✅ RSS feeds reporting on Gaza hostage release
2. ✅ Multiple sources (AP, Reuters, BBC, CNN, etc.)
3. ✅ Clustering working (articles merged into one story)
4. ✅ Sources adding articles over time (not all at once)

### Variables:
- **Independent:** New sources adding articles
- **Dependent:** Story status (BREAKING vs VERIFIED)
- **Control:** Story age, source count, update frequency

### Metrics:
- Time to promotion (seconds from new source to BREAKING)
- Duration of BREAKING status (minutes)
- Number of updates while BREAKING
- Transition timing (minutes idle before VERIFIED)

---

## 🐛 Troubleshooting

### Issue: Story Not Promoted to BREAKING

**Check:**
1. Is story gaining sources? `is_gaining_sources = True`?
2. Was last update recent? `time_since_update < 30 min`?
3. Does story have 3+ sources? `verification_level >= 3`?
4. Are new articles being added? Check RSS logs
5. Is clustering working? Check for "Added [source]" logs

**Debug Commands:**
```bash
# Check status evaluation logs
./query-logs.sh custom "traces | where timestamp > ago(10m) | where message contains 'Status evaluation' and message contains 'story_20251012_084423_58f041ad44cd' | project timestamp, message"

# Check recent source additions
./query-logs.sh custom "traces | where timestamp > ago(30m) | where message contains 'Added' and message contains 'story_20251012_084423_58f041ad44cd' | project timestamp, message | order by timestamp desc"
```

---

### Issue: Story Not Visible at Top of Feed

**Check:**
1. Is `last_updated` timestamp changing?
2. Is API sorting by `max(first_seen, last_updated)`?
3. Are there newer stories pushing it down?
4. Is app caching old feed data?

**Debug:**
- Check API response directly
- Force app refresh (pull-to-refresh)
- Verify story `last_updated` field

---

### Issue: Story Transitions Too Early

**Check:**
1. Is 90-minute timeout configured correctly?
2. Is BreakingNewsMonitor using `time_since_update`?
3. Are new sources still being added?

**Debug:**
```bash
# Check transition logs
./query-logs.sh custom "traces | where timestamp > ago(2h) | where message contains 'Status transition' | project timestamp, message | order by timestamp desc"
```

---

## 📈 Success Metrics

### Quantitative:
- **Story visibility**: Should be position #1 when BREAKING
- **Status duration**: BREAKING for 30-90 minutes (depending on updates)
- **Update frequency**: New sources every 10-30 minutes
- **Transition accuracy**: VERIFIED after exactly 90 min idle

### Qualitative:
- **User experience**: Story is prominent and obvious
- **Badge accuracy**: BREAKING badge matches status
- **Feed relevance**: Most important news at top
- **Timeliness**: Updates appear quickly (< 1 min delay)

---

## 🔄 Iteration Plan

### If Test Fails:

**1. Diagnose Root Cause**
- Check logs for error messages
- Verify configuration deployed correctly
- Test individual components (RSS, clustering, status logic)

**2. Adjust Parameters**
- Increase/decrease timeouts
- Modify status evaluation logic
- Add more logging

**3. Redeploy & Retest**
- Deploy fix immediately
- Monitor with real-time tools
- Verify fix within 5-10 minutes

**4. Document Findings**
- Update this test plan
- Document any edge cases
- Improve monitoring tools

---

## 💡 Future Enhancements

### Phase 2: Advanced Testing

**1. Multiple Breaking Stories**
- Test with 2-3 simultaneous breaking news events
- Verify feed ordering is correct
- Check for resource contention

**2. Edge Cases**
- Very old story (weeks) getting sudden update
- Story with 20+ sources
- Rapid updates (new source every minute)
- Slow updates (new source every hour)

**3. Performance**
- Measure API response time
- Check database query efficiency
- Monitor function execution time

**4. User Impact**
- A/B test different timeout values
- Measure user engagement with breaking news
- Track click-through rates on BREAKING stories

---

## 📝 Test Log

| Time (UTC) | Event | Status | Notes |
|------------|-------|--------|-------|
| 05:39 | Deployed 90-min timeout | ✅ | Function restarting |
| 05:41 | Function active | ⏳ | Waiting for next update |
| ... | | | |

---

## 🎯 Next Actions

1. **Start monitoring** (run `./monitor-breaking-news.sh`)
2. **Wait for next update** (Gaza story actively developing)
3. **Verify promotion** (story should become BREAKING)
4. **Check feed** (story should be at top)
5. **Monitor duration** (should stay BREAKING for 30-90 min)
6. **Verify transition** (should become VERIFIED after 90 min idle)
7. **Document results** (update this file with findings)

---

**Test is ACTIVE! Monitor the Gaza hostage release story over the next 2-3 hours.** 🔥


