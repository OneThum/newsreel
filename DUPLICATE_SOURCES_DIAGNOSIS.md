# 🔍 Duplicate Sources Diagnosis & Test Plan

**Date**: October 13, 2025 10:45 UTC  
**Issue**: Feed card shows "16 sources" but detail view shows "1 source"  
**Status**: 🔬 DIAGNOSTIC LOGGING READY FOR TESTING

---

## 🎯 PROBLEM STATEMENT

**User Report**:
> "The summary card in the feed says 16 sources, but now when I click on the article it only shows the 1 source."

This indicates a critical disconnect somewhere in the data flow from backend → API → iOS app.

---

## 📊 WHAT WE KNOW

### From iOS App Logs (Previous Run):

```
✅ Feed loaded successfully: 20 stories
   Sources included: 18 sources in first story
```

**This is KEY**: The API **IS** returning sources! The log says "18 sources in first story".

But the user sees only 1 source in the detail view.

---

## 🔍 WHERE COULD THE PROBLEM BE?

There are **4 possible failure points**:

### **1. Backend Storage** ❓
- **Hypothesis**: Cosmos DB has duplicate articles (same source appearing multiple times)
- **Test**: Need to query database directly
- **Status**: ⏸️ Cosmos DB authentication issues prevented direct query

### **2. API Response** ❓
- **Hypothesis**: API returns duplicates in `sources` array
- **Test**: Check API `/feed` endpoint response
- **Status**: ⏸️ API requires Firebase authentication (can't test directly)

### **3. iOS Decoding** ❓
- **Hypothesis**: Something goes wrong when converting API JSON to Swift `Story` objects
- **Test**: Check logs from `[API DECODE]`
- **Status**: ✅ LOGGING ADDED - Ready to test

### **4. iOS Display** ❓
- **Hypothesis**: `Story` object has sources, but display logic fails
- **Test**: Check logs from `[STORY DETAIL INIT]` and `[DEDUPLICATION DEBUG]`
- **Status**: ✅ LOGGING ADDED - Ready to test

---

## ✅ DIAGNOSTIC LOGGING ADDED

I've added **3 levels of logging** to track the data flow:

### **Level 1: API Decoding** (`APIService.swift`)
When the feed response is decoded from JSON:

```swift
📦 [API DECODE] Story: story_xxx
   API returned 18 source objects
   Converted to 18 SourceArticle objects
   [1] ap - ID: ap_abc123
   [2] bbc - ID: bbc_def456
   [3] cnn - ID: cnn_ghi789
```

**This tells us**: Did the API send sources? Did iOS decode them correctly?

---

### **Level 2: Story Detail Init** (`StoryDetailView.swift`)
When you tap on a story to open it:

```swift
🔍 [STORY DETAIL INIT] Opening story: story_xxx
   sourceCount field: 18
   sources.count: 18
   sources: Associated Press, BBC, CNN, Reuters, ...
```

**This tells us**: Does the Story object have sources when the detail view opens?

---

### **Level 3: Multiple Perspectives Section** (`StoryDetailView.swift`)
When the section scrolls into view:

```swift
📋 [DEDUPLICATION DEBUG] Story: story_xxx
   Total source articles from API: 18
   Unique source count: 18
✅ [DEDUPLICATION] All sources unique
```

**This tells us**: Are the sources still there when trying to display them?

---

## 📱 HOW TO TEST

### **Step 1: Build and Run**
```bash
# In Xcode
⌘R to build and run
```

### **Step 2: Open Console.app**
```bash
# On Mac
Applications → Utilities → Console
```

### **Step 3: Filter Logs**
In Console.app, filter by:
```
"API DECODE" OR "STORY DETAIL INIT" OR "DEDUPLICATION"
```

### **Step 4: Open a Multi-Source Story**
In the Newsreel app:
1. Find a story with multiple sources (like the Russia/Ukraine story)
2. Tap to open it
3. Scroll to "Multiple Perspectives" section

### **Step 5: Read the Logs**
You'll see logs appear in this order:
1. `📦 [API DECODE]` - When feed loads
2. `🔍 [STORY DETAIL INIT]` - When you tap the story
3. `📋 [DEDUPLICATION DEBUG]` - When section appears

---

## 🔬 DIAGNOSTIC SCENARIOS

### **Scenario A: API Not Sending Sources**
```
⚠️ [API DECODE] Story: story_xxx - sources field is nil
📦 [API DECODE] Creating Story object with 0 sources
🔍 [STORY DETAIL INIT] sources.count: 0
⚠️ [STORY DETAIL INIT] sources array is EMPTY!
```

**Diagnosis**: Backend API bug - `sources` field is null in API response  
**Fix Location**: `Azure/api/app/routers/stories.py` - `map_story_to_response()`  
**Root Cause**: API not including sources array OR `include_sources=False`

---

### **Scenario B: API Sending Duplicates**
```
📦 [API DECODE] Story: story_xxx
   API returned 18 source objects
   Converted to 18 SourceArticle objects
⚠️ [API DECODE] API RETURNED DUPLICATES!
   Unique: 2, Total: 18
   'Associated Press' appears 12 times in API response
   'Reuters' appears 6 times in API response
```

**Diagnosis**: Backend deduplication not working  
**Fix Location**: `Azure/api/app/routers/stories.py` - deduplication logic (lines 79-100)  
**Root Cause**: `seen_sources` dictionary not working OR database has duplicates

---

### **Scenario C: iOS Decoding Bug**
```
📦 [API DECODE] Story: story_xxx
   API returned 18 source objects
   Converted to 1 SourceArticle objects  ← PROBLEM HERE!
📦 [API DECODE] Creating Story object with 1 sources
🔍 [STORY DETAIL INIT] sources.count: 1
```

**Diagnosis**: iOS `.map` conversion failing  
**Fix Location**: `Newsreel App/Newsreel/Services/APIService.swift` - `toStory()` method (line 664-672)  
**Root Cause**: Mapping logic error or data format mismatch

---

### **Scenario D: Story Object Loses Sources**
```
📦 [API DECODE] Creating Story object with 18 sources
🔍 [STORY DETAIL INIT] Opening story: story_xxx
   sourceCount field: 18
   sources.count: 0  ← PROBLEM HERE!
⚠️ [STORY DETAIL INIT] sources array is EMPTY!
```

**Diagnosis**: Sources lost between Story creation and view initialization  
**Fix Location**: Unknown - investigate Story initialization  
**Root Cause**: Memory issue or incorrect Story initialization

---

### **Scenario E: Display Logic Bug**
```
📦 [API DECODE] Creating Story object with 18 sources
🔍 [STORY DETAIL INIT] sources.count: 18
📋 [DEDUPLICATION DEBUG] Total: 0  ← PROBLEM HERE!
```

**Diagnosis**: `viewModel.story.sources` is empty even though Story has them  
**Fix Location**: `StoryDetailView.swift` - `StoryDetailViewModel`  
**Root Cause**: ViewModel not accessing sources correctly

---

### **Scenario F: Everything Working (Unlikely given user report)**
```
📦 [API DECODE] API returned 18 source objects
   Converted to 18 SourceArticle objects
📦 [API DECODE] Creating Story object with 18 sources
🔍 [STORY DETAIL INIT] sources.count: 18
   sources: AP, BBC, CNN, Reuters, Guardian, ...
📋 [DEDUPLICATION DEBUG] Total: 18, Unique: 18
✅ [DEDUPLICATION] All sources unique
```

**Diagnosis**: Everything is working!  
**Possible Explanation**: User was looking at an old story (before update-in-place fix)

---

## 🎯 MOST LIKELY SCENARIOS

Based on the iOS log showing "18 sources in first story", I suspect:

### **#1 Most Likely: API Sending Duplicates** (70% probability)
- API says "18 sources"
- But they're actually 18 copies of the same source
- iOS correctly receives 18, but they're all duplicates
- User sees "1 source" (or maybe the dedup section doesn't show)

### **#2 Second Most Likely: iOS Display Bug** (20% probability)
- API sends 18 sources correctly
- iOS decodes them correctly
- But display logic fails to show them

### **#3 Least Likely: Backend Storage** (10% probability)
- Database has duplicate articles
- API deduplication isn't working

---

## 📝 NEXT STEPS

### **Immediate (User Action Required)**:
1. ✅ Build and run iOS app in Xcode
2. ✅ Open Console.app and filter for diagnostic logs
3. ✅ Open a multi-source story
4. ✅ Copy and paste the logs here

### **After Getting Logs**:
1. 🔍 Identify which scenario matches the logs
2. 🔧 Fix the identified issue
3. ✅ Re-test to confirm fix
4. 🚀 Deploy if needed

---

## 🛠️ AVAILABLE DIAGNOSTIC TOOLS

### **1. iOS Diagnostic Logging** ✅
- Location: Already added to iOS app
- Usage: Build & run, check Console.app
- Tests: API decoding, Story initialization, display logic

### **2. API Check Script** ⏸️
- Location: `Azure/scripts/check-api-sources.sh`
- Usage: Can't run without Firebase auth token
- Tests: API response format and duplicates

### **3. Database Diagnostic Script** ⏸️
- Location: `Azure/scripts/diagnose-story-sources.py`
- Usage: Cosmos DB connection issues
- Tests: Database storage and clustering

---

## 🔬 HYPOTHESIS

My **strongest hypothesis** based on the evidence:

**The API is returning sources, but they're duplicates.**

Evidence:
- Log says "18 sources in first story" ✅
- User sees "16 sources" in feed card ✅
- User sees "1 source" in detail view ✅

This pattern suggests:
- API sends 16-18 source objects
- But they're all the same source repeated
- Feed card counts array length (16)
- Detail view deduplicates and shows unique count (1)

**If this is true**, the problem is in the backend clustering or API deduplication logic.

---

##  ⏭️ AFTER DIAGNOSIS

Once we identify the issue from the logs, I can:

1. **Fix the code** at the identified location
2. **Test the fix** using the same diagnostic logs
3. **Deploy** if it's a backend fix
4. **Rebuild** if it's an iOS fix
5. **Verify** the fix resolves the issue

The diagnostic logging gives us **complete visibility** into the data flow, so we can pinpoint the exact failure point.

---

**Status**: ✅ **READY FOR USER TESTING**

Please build the iOS app, open Console.app, tap on a multi-source story, and share the diagnostic logs!


