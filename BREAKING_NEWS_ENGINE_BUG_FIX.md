# 🚨 CRITICAL: Breaking News Engine Bug Fixed

**Date**: October 13, 2025 08:55 UTC  
**Severity**: CRITICAL - Prevents breaking news detection  
**Status**: ✅ FIXED, awaiting deployment

---

## 🐛 THE BUG

### **Symptom**: No stories promoted to BREAKING since first deployment

**User observation**: Multiple Israel-related stories should have been flagged as breaking news, but weren't.

**Root cause**: `is_gaining_sources` was ALWAYS `False` due to a Python reference bug.

---

## 🔍 TECHNICAL DETAILS

### **The Code (WRONG)**:

```python
Line 733: source_articles = story.get('source_articles', [])  # Get reference to list
Line 745: source_articles.append(article.id)  # Append new article
Line 757: prev_source_count = len(story.get('source_articles', []))  # Count AFTER append!
Line 758: is_gaining_sources = len(source_articles) > prev_source_count  # 4 > 4 = False ❌
```

### **Why This Breaks**:

In Python, `story.get('source_articles', [])` returns a **reference** to the list, not a copy.

```python
story = {'source_articles': [1, 2, 3]}
source_articles = story.get('source_articles', [])  # REFERENCE, not copy
source_articles.append(4)  # Modifies story['source_articles'] in-place!

# Now story['source_articles'] = [1, 2, 3, 4]

prev_count = len(story.get('source_articles', []))  # Returns 4 (already modified!)
is_gaining = len(source_articles) > prev_count  # 4 > 4 = False ❌
```

**Result**: `is_gaining_sources` is ALWAYS `False`, preventing BREAKING promotion.

---

## 🔥 IMPACT

### **Breaking News Logic**:

```python
if verification_level >= 3:
    if time_since_first < timedelta(minutes=30):
        status = StoryStatus.BREAKING.value  # ✓ Works for NEW stories
    elif is_gaining_sources and time_since_update < timedelta(minutes=30):
        status = StoryStatus.BREAKING.value  # ❌ NEVER TRIGGERS (is_gaining always False)
```

**Stories affected**:
- ✅ **New stories** (< 30 min old, 3+ sources): Correctly promoted to BREAKING
- ❌ **Ongoing stories** (Gaza hostages, Israel conflicts): NOT promoted because `is_gaining_sources=False`

---

## ✅ THE FIX

### **Move `prev_source_count` calculation BEFORE append**:

```python
Line 733: source_articles = story.get('source_articles', [])
Line 736: prev_source_count = len(source_articles)  # ✓ Calculate BEFORE modifying
Line 745: source_articles.append(article.id)  # Now modifies after capturing prev count
Line 758: is_gaining_sources = len(source_articles) > prev_source_count  # 4 > 3 = True ✓
```

### **Example Flow After Fix**:

```python
story = {'source_articles': [1, 2, 3]}
source_articles = story.get('source_articles', [])  # [1, 2, 3]
prev_count = len(source_articles)  # 3 ✓
source_articles.append(4)  # [1, 2, 3, 4]
is_gaining = len(source_articles) > prev_count  # 4 > 3 = True ✓
```

---

## 📊 LOG EVIDENCE

### **Before Fix (WRONG)**:

```
08:41:50 | 📊 Status evaluation for story_X: sources=4→4, is_gaining=False
08:41:50 | 📊 Status evaluation for story_Y: sources=4→4, is_gaining=False
08:41:50 | 📊 Status evaluation for story_Z: sources=6→6, is_gaining=False
```

All stories show `X→X` (same count before/after), `is_gaining=False`.

**Why**: `prev_source_count` calculated AFTER append, so it already includes the new article.

### **After Fix (EXPECTED)**:

```
08:55:00 | 📊 Status evaluation for story_X: sources=3→4, is_gaining=True
08:55:01 | 🔥 Story promoted to BREAKING (actively developing): story_X - 3→4 sources
```

---

## 🎯 EXPECTED BEHAVIOR AFTER DEPLOYMENT

### **Scenario: Israel hostage story gains sources**

**Before (BROKEN)**:
```
10:00 | Story created: 3 sources → BREAKING ✓
10:05 | New source added (3→4) → is_gaining=False → VERIFIED ❌
10:10 | New source added (4→5) → is_gaining=False → VERIFIED ❌
```

**After (FIXED)**:
```
10:00 | Story created: 3 sources → BREAKING ✓
10:05 | New source added (3→4) → is_gaining=True → BREAKING ✓
10:10 | New source added (4→5) → is_gaining=True → BREAKING ✓
10:40 | No updates for 30 min → VERIFIED (BreakingNewsMonitor transitions)
```

---

## 🚀 DEPLOYMENT NEEDED

```bash
cd Azure/functions
func azure functionapp publish newsreel-func-51689 --python
```

**Restart recommended** to ensure code cache cleared.

---

## 🧪 VERIFICATION AFTER DEPLOYMENT

### **1. Check for True `is_gaining` values**:

```bash
./query-logs.sh custom "traces | where timestamp > ago(30m) | where message contains 'is_gaining=True' | project timestamp, message"
```

**Expected**: Should see `is_gaining=True` when stories gain sources.

### **2. Check for BREAKING promotions**:

```bash
./query-logs.sh custom "traces | where timestamp > ago(30m) | where message contains '🔥 Story promoted to BREAKING' | project timestamp, message"
```

**Expected**: Stories with 3+ sources gaining new sources should be promoted.

### **3. Monitor Israel-related stories**:

```bash
./query-logs.sh custom "traces | where timestamp > ago(1h) | where message contains 'israel' or message contains 'gaza' or message contains 'hostage' | where message contains 'BREAKING' | project timestamp, message"
```

**Expected**: Actively developing Israel stories should show BREAKING status.

---

## 📝 LESSONS LEARNED

### **1. Python List References Are Dangerous**

When working with dicts from databases, always be aware that:
```python
my_list = dict['list_field']  # This is a REFERENCE, not a copy
my_list.append(x)  # This MODIFIES the original dict!
```

**Safe pattern**:
```python
prev_count = len(dict['list_field'])  # Capture count FIRST
my_list = dict['list_field']
my_list.append(x)
is_gaining = len(my_list) > prev_count  # Now correct
```

### **2. Log Decision Factors for Debugging**

The detailed logging at line 773 was CRITICAL for diagnosing this:
```python
logger.info(
    f"📊 Status evaluation: sources={prev}→{curr}, is_gaining={is_gaining}"
)
```

Without this, the bug would have been invisible.

### **3. Integration Tests Needed**

This bug would have been caught by a test that:
1. Creates a story with 3 sources
2. Adds a 4th source
3. Asserts `is_gaining_sources=True`
4. Asserts status changed to `BREAKING`

---

## 🔗 RELATED ISSUES

- **Gaza story headline not updating**: Separate issue (threshold-based triggers)
- **Source diversity blocking**: Separate issue (fixed earlier)
- **Breaking News Monitor crash**: Separate issue (ORDER BY clause)

This bug is independent and affects ALL ongoing breaking news detection.

---

## ⚠️ CRITICAL PRIORITY

**This bug prevents the core feature** (breaking news detection) from working for ongoing stories.

**Impact**:
- Major breaking news (hostage releases, conflicts, disasters) not flagged
- Users miss critical updates
- Competitive disadvantage vs other news apps

**Deploy ASAP**.


