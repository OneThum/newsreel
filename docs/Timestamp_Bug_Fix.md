# 🐛 Timestamp Bug - "Just now" for Old Stories

**Issue**: Stories showing "Just now" timestamp even though they're hours old  
**Root Cause**: Summarization functions incorrectly updating `last_updated`  
**Type**: **Cloud-side bug**  
**Priority**: **CRITICAL** - Breaks user trust in timestamps

---

## 🔍 The Problem

### User Report:
> "If I tap on World or another category in the Newsreel feed, I see stories that I saw an hour ago with 'Just now' as the time stamp, even though there's one source and no UPDATED flag."

### What's Happening:

**1. Story created 2 hours ago:**
```
first_seen: 2025-10-13 04:00:00
last_updated: 2025-10-13 04:00:00
publishedAt: 2025-10-13 04:00:00
Status: MONITORING (1 source)
```

**2. Summarization runs (05:30):**
```python
# function_app.py lines 960-964
await cosmos_client.update_story_cluster(
    story_data['id'],
    story_data['category'],
    {'summary': summary, 'last_updated': datetime.now(timezone.utc).isoformat()}  # ❌ BUG!
)
```

**3. Story now has:**
```
first_seen: 2025-10-13 04:00:00
last_updated: 2025-10-13 05:30:00  # ❌ Updated to NOW!
publishedAt: 2025-10-13 04:00:00
Status: MONITORING (still 1 source)
```

**4. iOS app displays:**
```swift
// Story.swift lines 132-138
if isRecentlyUpdated, let lastUpdated = lastUpdated {
    referenceDate = lastUpdated  // Uses 05:30 instead of 04:00!
}
```

**Result:** Story shows "Just now" even though it's 2 hours old! ❌

---

## 🎯 Root Cause

### **`last_updated` should ONLY change when:**
1. ✅ New source is added (story gains verification)
2. ✅ Status changes (MONITORING → DEVELOPING → BREAKING)
3. ✅ Story transitions (BREAKING → VERIFIED)

### **`last_updated` should NOT change when:**
1. ❌ Summary is generated (first time)
2. ❌ Summary is regenerated (with more sources)
3. ❌ Summary is backfilled
4. ❌ Story is read from database
5. ❌ Story is queried by API

---

## 📍 Bug Locations

### **Bug #1: Summarization ChangeFeed (line 960-964)**
```python
# After generating summary:
await cosmos_client.update_story_cluster(
    story_data['id'],
    story_data['category'],
    {'summary': summary, 'last_updated': datetime.now(timezone.utc).isoformat()}
    #                     ↑ BUG: Updates timestamp even though no new sources!
)
```

**Impact:** Every story that gets a summary appears as "Just now"

---

### **Bug #2: Summarization Backfill (line 1168-1171)**
```python
# When backfilling summaries:
await cosmos_client.update_story_cluster(story_id, category, {
    'summary': summary,
    'last_updated': datetime.now(timezone.utc).isoformat()
    #                ↑ BUG: Resets timestamp for old stories!
})
```

**Impact:** Old stories (hours/days old) appear as "Just now" when backfill runs

---

## ✅ The Fix

### **Remove `last_updated` from summary updates:**

**Change #1 (Summarization ChangeFeed):**
```python
# Before:
await cosmos_client.update_story_cluster(
    story_data['id'],
    story_data['category'],
    {'summary': summary, 'last_updated': datetime.now(timezone.utc).isoformat()}
)

# After:
await cosmos_client.update_story_cluster(
    story_data['id'],
    story_data['category'],
    {'summary': summary}  # Don't update last_updated!
)
```

**Change #2 (Summarization Backfill):**
```python
# Before:
await cosmos_client.update_story_cluster(story_id, category, {
    'summary': summary,
    'last_updated': datetime.now(timezone.utc).isoformat()
})

# After:
await cosmos_client.update_story_cluster(story_id, category, {
    'summary': summary  # Don't update last_updated!
})
```

---

## 🎓 Understanding `last_updated`

### **What it means:**
"When was this story last updated with NEW INFORMATION (sources, status, etc.)"

### **What it does NOT mean:**
"When did we last touch this database record"

### **Example Timeline:**

**Correct behavior:**
```
04:00 - Story created (BBC) → last_updated: 04:00
04:30 - Summary generated → last_updated: 04:00 (unchanged!)
05:00 - CNN adds source → last_updated: 05:00 (changed!)
05:30 - Summary regenerated → last_updated: 05:00 (unchanged!)
06:00 - AP adds source → last_updated: 06:00 (changed!)
```

**Current (broken) behavior:**
```
04:00 - Story created (BBC) → last_updated: 04:00
04:30 - Summary generated → last_updated: 04:30 ❌ (changed incorrectly!)
05:00 - CNN adds source → last_updated: 05:00 ✅
05:30 - Summary regenerated → last_updated: 05:30 ❌ (changed incorrectly!)
06:00 - AP adds source → last_updated: 06:00 ✅
```

---

## 📊 Impact Analysis

### **Affected Stories:**
- **ALL stories** that get summaries
- **Especially** single-source stories (now getting summaries)
- **Especially** old stories processed by backfill

### **User Impact:**
- Loss of trust in timestamps
- Confusion about story age
- Can't tell fresh news from old news
- "Just now" becomes meaningless

### **Feed Impact:**
- Feed sorting uses `max(first_seen, last_updated)`
- Stories with updated summaries jump to top
- Old stories incorrectly appear fresh
- True breaking news gets buried

---

## 🧪 Test Cases

### **Test 1: New Story with Summary**

**Setup:**
- Create story at 10:00
- Generate summary at 10:30

**Expected:**
- `last_updated`: 10:00 (unchanged)
- Timestamp: "30m ago" (using first_seen)

**Current (broken):**
- `last_updated`: 10:30 ❌
- Timestamp: "Just now" ❌

---

### **Test 2: Old Story Gets New Source**

**Setup:**
- Story created at 08:00
- New source added at 10:00
- Summary regenerated at 10:05

**Expected:**
- `last_updated`: 10:00 (from new source)
- Timestamp: "5m ago" ✅ (correctly shows as fresh)

**Current (broken):**
- `last_updated`: 10:05 ❌ (from summary, not source!)
- Timestamp: "Just now" ❌

---

### **Test 3: Backfill on Old Stories**

**Setup:**
- Story created yesterday at 10:00
- Backfill runs today at 14:00

**Expected:**
- `last_updated`: Yesterday 10:00 (unchanged)
- Timestamp: "1d ago"

**Current (broken):**
- `last_updated`: Today 14:00 ❌
- Timestamp: "Just now" ❌

---

## 📋 Deployment Plan

### **Step 1: Fix Code**
- Remove `last_updated` from both summarization functions
- Keep `last_updated` ONLY in clustering (when sources added)

### **Step 2: Deploy**
```bash
cd Azure/functions
func azure functionapp publish newsreel-func-51689 --python
```

### **Step 3: Verify**
```bash
# Wait 5 minutes after deploy
# Check that new summaries don't update timestamps

cd Azure/scripts
./query-logs.sh custom "traces | where timestamp > ago(10m) | where message contains 'Generating summary' | project timestamp, message | take 10"

# Verify no "last_updated" in summary updates
```

### **Step 4: Monitor**
- Check iOS app after 10 minutes
- Verify timestamps are accurate
- Confirm old stories don't show "Just now"

---

## 🔍 How to Verify Fix

### **In Logs:**
```bash
# Should see summaries being generated WITHOUT timestamp updates
./query-logs.sh custom "traces | where timestamp > ago(30m) | where message contains 'summary' | project timestamp, message | order by timestamp desc | take 20"

# Look for: "Generating summary for story X"
# Should NOT see: "last_updated" being set
```

### **In iOS App:**
1. Open app, note timestamp of a story
2. Wait 10 minutes (for summarization to run)
3. Pull to refresh
4. Verify timestamp hasn't changed to "Just now"

### **Via API:**
```bash
# Query a story before and after summarization
# Verify last_updated doesn't change

# Before summarization:
curl "https://newsreel-api.../api/stories/[story_id]" | jq '.last_updated'

# Wait for summarization...

# After summarization:
curl "https://newsreel-api.../api/stories/[story_id]" | jq '.last_updated'

# Should be SAME timestamp!
```

---

## 💡 Related Issues

### **Issue 1: Feed Sorting**
If `last_updated` changes on summary, stories jump in feed order.

**Fix:** Already fixed by fixing timestamp bug.

---

### **Issue 2: UPDATED Badge**
iOS shows UPDATED badge if `last_updated` significantly different from `first_seen`.

**Current behavior:** Old stories get UPDATED badge after summarization.  
**After fix:** Only stories with new sources get UPDATED badge. ✅

---

### **Issue 3: Breaking News Detection**
Breaking news logic uses `time_since_update` to detect active development.

**Current behavior:** Summary generation resets the timer!  
**After fix:** Only real updates (new sources) reset the timer. ✅

---

## 📝 Summary

**Problem:** Summarization incorrectly updates `last_updated` timestamp  
**Symptom:** Stories show "Just now" even when hours old  
**Root Cause:** Two lines of code setting `last_updated` when generating summaries  
**Fix:** Remove `last_updated` from summary update calls  
**Impact:** Critical - affects ALL stories, breaks user trust  
**Deployment:** 5-minute fix, immediate impact  

---

**This is a critical bug that needs immediate fixing!** 🔴


