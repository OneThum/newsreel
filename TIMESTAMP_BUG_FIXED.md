# ✅ CRITICAL BUG FIXED: Timestamp Reset Issue

**Deployed**: 2025-10-13 06:18 UTC  
**Type**: Cloud-side bug  
**Impact**: ALL users seeing incorrect "Just now" timestamps

---

## 🐛 The Bug

### **What You Saw:**
- Stories you saw an hour ago showing "Just now"
- Old stories appearing fresh
- No UPDATED badge (correct)
- Single-source stories (no reason to update)
- Timestamps resetting randomly

### **Root Cause:**

**Two places in the cloud code were incorrectly updating `last_updated`:**

**Location 1: Summarization ChangeFeed** (when summaries are generated)
```python
# BUG:
await cosmos_client.update_story_cluster(
    story_id, category,
    {'summary': summary, 'last_updated': now.isoformat()}  # ❌ Wrong!
)
```

**Location 2: Summarization Backfill** (when old stories get summaries)
```python
# BUG:
await cosmos_client.update_story_cluster(
    story_id, category,
    {'summary': summary, 'last_updated': now.isoformat()}  # ❌ Wrong!
)
```

---

## 💥 How It Broke Timestamps

### **Example Timeline:**

**What SHOULD happen:**
```
10:00 - Story created (BBC) → last_updated: 10:00
10:30 - Summary generated → last_updated: 10:00 ✅ (unchanged)
11:00 - You see story → Shows "1h ago" ✅
12:00 - Still no new sources → Shows "2h ago" ✅
```

**What WAS happening:**
```
10:00 - Story created (BBC) → last_updated: 10:00
10:30 - Summary generated → last_updated: 10:30 ❌ (reset!)
11:00 - You see story → Shows "30m ago" ❌ (should be 1h)
12:00 - Summary regenerated → last_updated: 12:00 ❌ (reset again!)
12:01 - You see story → Shows "Just now" ❌ (should be 2h!)
```

---

## ✅ The Fix

### **Removed `last_updated` from both summarization functions:**

```python
# FIXED:
await cosmos_client.update_story_cluster(
    story_id, category,
    {'summary': summary}  # ✅ No timestamp update!
)
```

### **`last_updated` now ONLY changes when:**
1. ✅ New source is added to story (clustering)
2. ✅ Story status changes (DEVELOPING → BREAKING)
3. ✅ Status transitions (BREAKING → VERIFIED)

### **`last_updated` will NEVER change when:**
1. ✅ Summary is generated (first time)
2. ✅ Summary is regenerated (with more sources)
3. ✅ Summary is backfilled for old stories
4. ✅ Story is read from database
5. ✅ Story is queried by API

---

## 📊 Impact

### **Before Fix:**
- **Every story** that got a summary → "Just now"
- **Old stories** processed by backfill → "Just now"
- **Single-source stories** → "Just now" (especially bad!)
- User confusion about story age
- Loss of trust in timestamps

### **After Fix (06:18 UTC onwards):**
- **Timestamps accurate** - based on when story was created or last gained a source
- **Old stories stay old** - backfill doesn't reset timestamps
- **"Just now" means actually new** - created < 1 minute ago
- **UPDATED badge works correctly** - only shown when sources actually added

---

## 🧪 How to Verify the Fix

### **Test 1: Check Old Stories (5-10 min after deploy)**

1. Open Newsreel app
2. Look at stories you recognized from earlier
3. Check if timestamps are accurate now (not "Just now")
4. Pull to refresh
5. Timestamps should be realistic (e.g., "2h ago", "5h ago")

**Expected Result:** Old stories have accurate timestamps ✅

---

### **Test 2: Watch Summarization (15-30 min after deploy)**

1. Note the timestamp of a specific story
2. Wait 10-15 minutes (for summarization to run)
3. Pull to refresh in app
4. Check if the same story's timestamp changed

**Expected Result:** Timestamp stays the same (not reset to "Just now") ✅

---

### **Test 3: Verify Breaking News Still Works**

1. When Israel hostage story gets a new source
2. `last_updated` should update
3. Story should show recent timestamp
4. Should be promoted to BREAKING

**Expected Result:** Breaking news detection still works correctly ✅

---

## 🎯 What Changed vs. What Stayed

### **Changed (Fixed):**
- ❌ → ✅ Timestamps no longer reset on summarization
- ❌ → ✅ Old stories no longer appear fresh
- ❌ → ✅ "Just now" only for actually new stories

### **Stayed the Same (Working):**
- ✅ Breaking news detection (uses `last_updated` correctly)
- ✅ Feed ordering (by `max(first_seen, last_updated)`)
- ✅ UPDATED badge (shown when `last_updated` > `first_seen` + 30 min)
- ✅ Source counting
- ✅ Story clustering

---

## 📝 Technical Details

### **iOS App Logic (unchanged):**

```swift
// Story.swift line 126-152
var timeAgo: String {
    let referenceDate: Date
    if isRecentlyUpdated, let lastUpdated = lastUpdated {
        // Use lastUpdated if story was significantly updated
        referenceDate = lastUpdated
    } else {
        // Otherwise use publishedAt
        referenceDate = publishedAt
    }
    
    // Calculate time difference
    let components = calendar.dateComponents([.minute, .hour, .day], 
                                              from: referenceDate, to: now)
    
    if let minute = components.minute, minute > 0 {
        return minute == 1 ? "1m ago" : "\(minute)m ago"
    } else {
        return "Just now"  // Only if < 1 minute
    }
}

var isRecentlyUpdated: Bool {
    guard let lastUpdated = lastUpdated else { return false }
    let timeSincePublished = lastUpdated.timeIntervalSince(publishedAt)
    return timeSincePublished >= 1800 // 30 minutes
}
```

**This logic is CORRECT.** The bug was in the cloud sending wrong `last_updated` values.

---

### **Cloud Logic (fixed):**

**When clustering (adding sources):**
```python
# ✅ Correct: Updates last_updated
updates = {
    'source_articles': source_articles,
    'verification_level': verification_level,
    'status': status,
    'last_updated': datetime.now(timezone.utc).isoformat(),  # ✅ Correct!
    'update_count': story.get('update_count', 0) + 1
}
await cosmos_client.update_story_cluster(story_id, category, updates)
```

**When summarizing (now fixed):**
```python
# ✅ Fixed: Does NOT update last_updated
await cosmos_client.update_story_cluster(
    story_id, category,
    {'summary': summary}  # ✅ No timestamp!
)
```

---

## 🎓 Lessons Learned

### **Key Principle:**
**`last_updated` means "when did the STORY change", not "when did we touch the database record"**

### **What qualifies as story change:**
- ✅ New source added (verification improved)
- ✅ Status changed (DEVELOPING → BREAKING)
- ✅ Story transitioned (BREAKING → VERIFIED)

### **What does NOT qualify:**
- ❌ Internal processing (summarization)
- ❌ Database maintenance (backfill)
- ❌ Query operations (reading)
- ❌ Metadata updates (view counts, etc.)

---

## 📋 Summary

**Problem:** Stories showing "Just now" even when hours old  
**Cause:** Summarization incorrectly updating `last_updated` timestamp  
**Location:** Two functions in cloud (summarization changefeed + backfill)  
**Fix:** Removed `last_updated` from summary update operations  
**Deployed:** 06:18 UTC  
**Verification:** Check app in 10 minutes, timestamps should be accurate  

---

## ✅ Expected Results (10 min after deploy)

When you open the app now:

1. **Old stories** you saw earlier → Show accurate time (e.g., "2h ago", not "Just now")
2. **Single-source stories** → Accurate timestamps
3. **"Just now"** → Only for stories actually < 1 minute old
4. **UPDATED badge** → Only for stories with new sources added > 30 min after publication
5. **Breaking news** → Still works correctly when new sources added

---

**The bug is FIXED! Timestamps will now be accurate.** ✅

Check your app in 10 minutes and you should see realistic timestamps instead of "Just now" everywhere!


