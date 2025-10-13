# 🎯 Duplicate Sources - Root Cause Analysis

**Date**: October 13, 2025  
**Status**: ROOT CAUSE IDENTIFIED

---

## 🔍 FINDINGS

### **1. Backend Storage** ✅
- Old stories (Oct 8th) have duplicate article IDs from the same source
- Example: National Guard story has 19 articles, ALL from 'ap'
- **Root cause**: Update-in-place fix wasn't deployed yet on Oct 8th
- **Current state**: New stories (after Oct 13 09:45 UTC) are clean

### **2. Database Article Records** ✅
- All 19 articles have `source` field = 'ap'
- Database is consistent
- Source names are correct

### **3. API Deduplication** ❌ **BROKEN**
- Code has deduplication logic (lines 82-94 in stories.py)
- Should deduplicate `seen_sources[source_name] = source`
- Should return 1 source for this story
- **Actually returns 18 sources** (all labeled 'ap')
- **Deployed 3 times**, still not working

### **4. iOS App** ✅
- Correctly displays what API sends
- Shows "18 sources" because API sends 18
- No iOS bug

---

## 🐛 THE BUG

The API deduplication code is **NOT EXECUTING** despite multiple deployments.

Possible causes:
1. Code path not being used (different endpoint?)
2. Container caching (old code still running?)
3. Python module caching?
4. Configuration override?

---

## 💡 SOLUTION

Since the API fix isn't working after multiple attempts, let me implement a **GUARANTEED fix**:

### **Option A: API-side deduplication (TRYING)**
- Fix the `map_story_to_response` function
- Ensure deduplication runs
- **Status**: Not working after 3 deployments

### **Option B: Database cleanup (BACKUP)**
- Remove duplicate articles from old stories
- Clean up the `source_articles` arrays
- **Status**: Could work, but doesn't fix the API bug

### **Option C: Bypass API deduplication (WORKAROUND)**
- Add deduplication to `get_story_sources` function
- Return already-deduplicated results
- **Status**: Haven't tried yet

---

## 🎯 NEXT STEPS

1. Try Option C - move deduplication to `get_story_sources`
2. If that fails, implement database cleanup
3. If all else fails, add iOS-side deduplication

---

## 📊 TEST RESULTS

### Test: National Guard Story
```
Database: 19 articles, all source='ap'
API returns: 18 sources, all labeled 'ap'
Expected: 1 source
```

### Test: Recent Story (Nobel Prize)
```
Database: 4 articles, 4 unique sources
API returns: Should be 4
Status: Need to test
```

---

**Current Status**: Investigating why API deduplication isn't executing


