# ✅ Comprehensive Diagnostic Logging Complete

**Date**: October 13, 2025 10:50 UTC  
**Issue**: Investigating duplicate sources / missing sources  
**Status**: ✅ READY FOR ITERATIVE TESTING

---

## 🎯 WHAT WAS ADDED

I've added **comprehensive programmatic diagnostic logging** throughout the iOS app to allow self-testing and iteration:

### **1. API Response Decoding** (`APIService.swift`)
- Logs how many sources the API sent
- Logs how many were successfully converted to Swift objects
- Detects duplicates in the API response
- Shows first 3 sources with IDs
- **Triggers**: When feed loads

### **2. Story Detail Initialization** (`StoryDetailView.swift`)
- Logs `sourceCount` field vs actual `sources.count`
- Shows all source names
- Detects duplicates in the Story object
- **Triggers**: When you tap on a story

### **3. Multiple Perspectives Section** (`StoryDetailView.swift`)
- Logs total sources from array
- Calculates unique source count
- Shows all source names
- Detects and reports duplicates with counts
- Shows first 5 article IDs and URLs
- **Triggers**: When "Multiple Perspectives" section scrolls into view

---

## 📱 HOW TO USE

### **Quick Test Flow**:

1. **Build & Run** iOS app in Xcode (`⌘R`)
2. **Open Console.app** on Mac
3. **Filter** by: `"API DECODE" OR "STORY DETAIL INIT" OR "DEDUPLICATION"`
4. **Tap a story** with multiple sources
5. **Read the logs** to see what's happening at each stage

---

## 🔍 WHAT THE LOGS TELL YOU

### **API Decode Logs** → Did API send sources?
```
📦 [API DECODE] Story: story_xxx
   API returned 18 source objects ← Did API send them?
   Converted to 18 SourceArticle objects ← Did iOS decode them?
```

### **Story Detail Init Logs** → Does Story object have sources?
```
🔍 [STORY DETAIL INIT] Opening story: story_xxx
   sourceCount field: 18 ← What does backend say?
   sources.count: 18 ← Does iOS have them?
```

### **Deduplication Debug Logs** → Are they displayed?
```
📋 [DEDUPLICATION DEBUG] Story: story_xxx
   Total source articles from API: 18 ← Still there?
   Unique source count: 18 ← How many unique?
✅ [DEDUPLICATION] All sources unique ← Any duplicates?
```

---

## 🔬 SELF-DIAGNOSTIC CAPABILITY

With these logs, you can now:

### ✅ **Identify the exact failure point**
- If `API DECODE` shows 0 sources → **API bug**
- If `API DECODE` shows duplicates → **Backend deduplication bug**
- If `STORY DETAIL INIT` shows 0 sources but API had them → **iOS decoding bug**
- If `DEDUPLICATION DEBUG` never fires → **Display logic bug**

### ✅ **Test fixes immediately**
- Make a change to the code
- Build and run
- Check if the logs change
- Iterate until fixed

### ✅ **Verify the fix**
- Once logs show correct behavior
- Manually verify in the UI
- Deploy if backend fix
- Done!

---

## 📊 DIAGNOSTIC SCRIPTS CREATED

### **1. iOS Diagnostic Logging** ✅ READY
- **Location**: iOS app (already added)
- **Usage**: Build & run, check Console.app
- **Tests**: Complete data flow from API → iOS → Display

### **2. API Source Check Script** ⏸️ AUTH REQUIRED
- **Location**: `Azure/scripts/check-api-sources.sh`
- **Usage**: Requires Firebase auth token
- **Tests**: API response format and duplicates
- **Note**: Can't run standalone, but iOS logs cover this

### **3. Database Diagnostic Script** ⏸️ CONNECTION ISSUES
- **Location**: `Azure/scripts/diagnose-story-sources.py`
- **Usage**: Cosmos DB connection had issues
- **Tests**: Database storage, clustering, API response
- **Note**: iOS + API logs provide same visibility

---

## 🎯 RECOMMENDED TESTING APPROACH

### **Phase 1: Identify the Bug** (Current)
1. Run iOS app with Console.app open
2. Open a multi-source story
3. Read the diagnostic logs
4. Identify which scenario matches (see `DUPLICATE_SOURCES_DIAGNOSIS.md`)

### **Phase 2: Fix the Bug**
Based on logs, fix at the identified location:
- **Backend API**: `Azure/api/app/routers/stories.py`
- **iOS Decoding**: `Newsreel App/Newsreel/Services/APIService.swift`
- **iOS Display**: `Newsreel App/Newsreel/Views/Components/StoryDetailView.swift`

### **Phase 3: Verify the Fix**
1. Rebuild/redeploy with fix
2. Run same test again
3. Check logs confirm fix
4. Manually verify in UI
5. Done!

---

## 💡 KEY INSIGHT

From your earlier iOS logs:
```
Sources included: 18 sources in first story
```

This tells us the API **IS** returning sources. The question is:

**Are they 18 unique sources or 18 duplicates of the same source?**

The new diagnostic logging will answer this definitively.

---

## 🚀 NEXT STEP

**Please build and run the iOS app, then share the Console logs when you open a multi-source story.**

The logs will tell us:
1. Exactly what the API sent
2. How iOS decoded it
3. What was displayed (or not displayed)

Then we can fix the identified issue and iterate until it works!

---

**Full diagnostic guide**: `/DUPLICATE_SOURCES_DIAGNOSIS.md`  
**Status**: ✅ **LOGGING COMPLETE - READY FOR USER TESTING**


