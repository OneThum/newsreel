# Category Filter Pull-to-Refresh Fix 🔄

**Date**: October 13, 2025  
**Issue**: Category filter not respected when pulling to refresh  
**Status**: Enhanced logging + defensive fixes implemented

---

## 🐛 The Problem

**User Report**: 
> "If I filter by selecting one of the selectors at the top of the app, say 'Technology' and then pull down to refresh, it will refresh not just the technology subset, but return me to showing all stories even while Technology is still selected above."

**Symptoms**:
1. Select "Technology" category
2. Pull down to refresh
3. Category chip still shows "Technology" as selected
4. BUT feed shows stories from ALL categories, not just Technology

---

## 🔍 Root Cause Analysis

The code flow **should** work correctly:

```swift
1. User selects "Technology"
   → categoryFilterBar binding updates
   → changeCategory(to: .technology) is called
   → selectedCategory = .technology
   → loadStories() fetches technology stories
   
2. User pulls to refresh
   → refresh() is called
   → loadStories(refresh: true) is called
   → Should use selectedCategory (.technology)
   → API: getFeed(category: .technology)
```

**The Theory**: Everything looks correct in the code, but there may be:
- Race condition with UI binding
- Backend returning wrong stories
- Cache interference
- Pagination state issue

---

## ✅ Fixes Implemented

### 1. Enhanced Logging (Diagnostic)

Added detailed logging throughout the refresh flow to diagnose the exact issue:

```swift
// In refresh()
log.log("🔄 Refreshing feed with category: \(selectedCategory?.displayName ?? "all")")

// In loadStories()
log.log("📡 Calling API with category: \(selectedCategory?.rawValue ?? "nil")")
log.log("📥 Received \(newStories.count) stories from API")
log.log("✅ Refreshed feed with \(stories.count) stories for category: \(selectedCategory?.displayName ?? "all")")
```

**What to look for in logs**:
- Does "Refreshing feed with category: Technology" appear?
- Does "Calling API with category: technology" appear?
- How many stories are returned?
- Do the returned stories have mixed categories?

### 2. Explicit Pagination Reset (Defensive)

```swift
func refresh(apiService: APIService) async {
    // Reset pagination state explicitly (defensive)
    currentPage = 0
    
    // Clear pending stories
    pendingNewStories.removeAll()
    pendingNewStoriesCount = 0
    newStoriesAvailable = false
    
    // Load stories for current category
    await loadStories(apiService: apiService, refresh: true)
}
```

**Why**: Ensures pagination state is clean before refresh, eliminating one possible source of issues.

### 3. Verification Logging in loadStories

```swift
// Log what category we're using BEFORE API call
log.log("Refresh: \(refresh), Category: \(selectedCategory?.displayName ?? "all"), Page: \(currentPage)")

// Log what we got AFTER API call
log.log("Received \(newStories.count) stories from API")
log.log("Refreshed feed with \(stories.count) stories for category: \(selectedCategory?.displayName ?? "all")")
```

---

## 🧪 How to Test

### Test Scenario 1: Basic Refresh

1. Open app (shows "All" stories)
2. Tap "Technology" category
   - ✅ **Expected**: Only technology stories appear
3. Pull down to refresh
   - ✅ **Expected**: Still only technology stories
   - ❌ **Bug**: All stories appear

**Check logs for**:
```
🔄 Refreshing feed with category: Technology
📡 Calling API with category: technology
📥 Received 20 stories from API
✅ Refreshed feed with 20 stories for category: Technology
```

### Test Scenario 2: Multiple Category Switches

1. Tap "Technology" → verify tech stories
2. Pull to refresh → verify still tech stories
3. Tap "Sports" → verify sports stories
4. Pull to refresh → verify still sports stories
5. Tap "All" → verify all stories
6. Pull to refresh → verify still all stories

### Test Scenario 3: Backend Verification

Check what the API is actually returning:

```bash
# Watch API logs during the test
# Check if the category parameter is being sent correctly
grep "GET /api/stories/feed" logs | grep "category=technology"
```

---

## 🔎 Debugging Guide

### If Issue Persists

**Step 1: Check iOS Logs**

Look for the log sequence during refresh:
```
🔄 Refreshing feed with category: [WHAT DOES THIS SAY?]
📡 Calling API with category: [WHAT DOES THIS SAY?]
📥 Received [HOW MANY?] stories from API
```

**Possible Findings**:

**A) Category is nil in logs**:
```
🔄 Refreshing feed with category: all
📡 Calling API with category: nil
```
→ **Problem**: selectedCategory binding is being lost
→ **Solution**: Issue with how binding is passed or race condition

**B) Category is correct but wrong stories returned**:
```
🔄 Refreshing feed with category: Technology
📡 Calling API with category: technology
📥 Received 20 stories from API (but they're mixed categories)
```
→ **Problem**: Backend not filtering correctly
→ **Solution**: Check backend query logic in cosmos_service.py

**C) Category is correct and right stories returned**:
```
🔄 Refreshing feed with category: Technology
📡 Calling API with category: technology
📥 Received 20 stories from API (all technology)
```
→ **Problem**: UI displaying wrong stories OR cache issue
→ **Solution**: Check if cached stories are interfering

---

### Step 2: Check Backend Logs

```bash
# Query Application Insights for story feed requests
az monitor app-insights query \
  --app newsreel-app-insights \
  --analytics-query "requests | where name contains 'feed' | project timestamp, url"
```

**Look for**:
- Are category parameters being received?
- What's the actual URL: `/api/stories/feed?category=technology`
- Are multiple requests happening (race condition)?

---

### Step 3: Check API Response

Add temporary logging in APIService.swift to see raw response:

```swift
let azureStories: [AzureStoryResponse] = try await request(...)
log.log("API returned stories with categories: \(azureStories.map { $0.category }.joined(separator: ", "))")
```

This will show if the API is actually returning mixed categories.

---

## 🎯 Likely Culprits (Ranked)

### 1. **Backend Query Issue** (Most Likely)

The backend might not be properly filtering by category.

**Check**: `Azure/api/app/services/cosmos_service.py`

```python
async def query_recent_stories(
    self,
    category: Optional[str] = None,  # ← Is this being respected?
    limit: int = 20,
    offset: int = 0
) -> List[Dict[str, Any]]:
    # ...
    if category:
        query = """
            SELECT * FROM c 
            WHERE c.category = @category
        """
        # ← Is this query executing correctly?
```

### 2. **Cache Interference** (Possible)

The cached stories from "All" feed might be showing before new stories load.

**Evidence to look for**:
- Brief flash of "All" stories then switching to "Technology"
- Log shows correct API call but UI shows wrong stories initially

**Solution**: Don't load from cache when category is selected

### 3. **Race Condition** (Less Likely)

The `selectedCategory` binding might be getting reset somehow during refresh.

**Evidence to look for**:
- Logs show `category: nil` or `category: all`
- Happens intermittently

### 4. **Polling Interference** (Unlikely)

The background polling might be fetching "All" stories and merging them.

**Evidence**: Logs show polling fetching mixed categories

---

## 🚀 Next Steps

### Immediate (Just Deployed)
- ✅ Enhanced logging to diagnose issue
- ✅ Defensive pagination reset

### After Testing (Based on Findings)

**If Backend Issue**:
```python
# Fix backend to properly filter by category
# Verify query is using category parameter correctly
```

**If Cache Issue**:
```swift
// Skip cache when category is selected
if selectedCategory != nil {
    // Don't load from cache, wait for API
}
```

**If Binding Issue**:
```swift
// Make category parameter explicit
func refresh(apiService: APIService, forCategory category: NewsCategory?) async {
    // Use passed category instead of relying on binding
}
```

---

## 📊 Success Criteria

### Fix is Complete When:

1. ✅ **Category Selection**: Tap "Technology" → see only tech stories
2. ✅ **Pull to Refresh**: Pull down → still see only tech stories
3. ✅ **Category Chip**: "Technology" stays selected (visual confirmation)
4. ✅ **Logs Confirm**: All logs show correct category throughout refresh
5. ✅ **Multiple Switches**: Works for all categories (Technology, Sports, Business, etc.)
6. ✅ **"All" Category**: Selecting "All" and refreshing shows all stories

---

## 💡 Prevention

### Code Improvements to Consider:

**1. Explicit Category Passing**:
```swift
// Instead of relying on binding
func refresh(apiService: APIService) async {
    await refresh(apiService: apiService, category: selectedCategory)
}

func refresh(apiService: APIService, category: NewsCategory?) async {
    // Use passed category parameter
}
```

**2. Category Verification**:
```swift
// After loading stories, verify they match expected category
if let category = selectedCategory {
    let wrongCategoryCount = stories.filter { $0.category != category }.count
    if wrongCategoryCount > 0 {
        log.log("⚠️ WARNING: \(wrongCategoryCount) stories don't match selected category!", category: .error)
    }
}
```

**3. UI Feedback**:
```swift
// Show loading indicator with category
if viewModel.isLoading, let category = viewModel.selectedCategory {
    ProgressView("Loading \(category.displayName)...")
}
```

---

## 🎉 Summary

**Problem**: Category filter not respected on pull-to-refresh

**Status**: Enhanced logging + defensive fixes deployed

**Next**: Test and analyze logs to identify root cause

**Expected**: Logs will reveal whether issue is:
- Backend not filtering correctly
- Cache interference
- Binding/race condition

The enhanced logging will make the root cause obvious! 🔍

