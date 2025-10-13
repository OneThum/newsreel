# 🌅 START HERE - Morning Debugging Guide

**Date**: October 14, 2025  
**Issue**: Duplicate/Missing Sources Bug  
**Status**: ✅ READY TO DEBUG

---

## ⚡ QUICK START (5 Minutes)

### **Option A: iOS App Test** (RECOMMENDED)

This will give us the most information:

```
1. Open Xcode
2. Build & Run Newsreel app (⌘R)
3. Open Console.app
4. Filter by: "DEDUPLICATION"
5. Tap on a multi-source story
6. Share the Console logs
```

**Why this is best**: iOS logs show the complete data flow from API → Display

---

### **Option B: Check Backend Logs**

See if backend created duplicates overnight:

```bash
cd "/Users/davemac/Library/CloudStorage/OneDrive-OneThumSoftware/One Thum Software/Newsreel/Azure/scripts"

az monitor app-insights query \
  --app newsreel-insights \
  --resource-group newsreel-rg \
  --analytics-query "traces | where timestamp > ago(12h) | where message contains 'DUPLICATE SOURCES' | summarize count()"
```

**If this returns > 0**: Backend is creating duplicates  
**If this returns 0**: Backend is clean, problem is in API or iOS

---

## 📊 WHAT I SET UP OVERNIGHT

### ✅ **Enhanced Backend Logging**
- Real-time duplicate detection in story clustering
- Logs every article addition with source diversity stats
- **Deployed**: Running on Azure Functions now
- **Check**: Azure Application Insights logs

### ✅ **iOS Diagnostic Logging**
- Tracks API response decoding
- Monitors Story object initialization
- Detects display rendering issues
- **Status**: Code added, needs app rebuild
- **Check**: Console.app when running iOS app

### ✅ **Automated Monitoring Tools**
- Scripts to check Azure logs
- API response validators
- Database diagnostic tools
- **Status**: Ready to run
- **Check**: `Azure/scripts/` directory

---

## 📁 KEY FILES

### **Read First**:
1. 🌅 `GOOD_MORNING_SUMMARY.md` - Complete overnight summary
2. 🔍 `DUPLICATE_SOURCES_DIAGNOSIS.md` - Diagnostic scenarios
3. 🌙 `OVERNIGHT_MONITORING_SETUP.md` - System architecture

### **Code Changes**:
1. `Azure/functions/function_app.py` - Enhanced logging (deployed)
2. `Newsreel App/Newsreel/Services/APIService.swift` - API decode logging
3. `Newsreel App/Newsreel/Views/Components/StoryDetailView.swift` - Display logging

### **Scripts**:
1. `Azure/scripts/overnight-monitor.sh` - Simple monitoring
2. `Azure/scripts/automated-monitor.py` - Advanced monitoring
3. `Azure/scripts/check-api-sources.sh` - API checker

---

## 🎯 EXPECTED OUTCOMES

### **Scenario 1: Backend Creating Duplicates**
```
Backend logs show: "DUPLICATE SOURCES" warnings
```
→ **I can fix immediately** (backend code)

---

### **Scenario 2: API Not Deduplicating**
```
Backend logs: Clean
iOS logs: API RETURNED DUPLICATES!
```
→ **I can fix immediately** (API code)

---

### **Scenario 3: iOS Decoding Issue**
```
Backend logs: Clean
iOS logs: API sent 18, iOS has 1
```
→ **I'll provide exact fix** (iOS code change)

---

### **Scenario 4: iOS Display Issue**
```
Backend logs: Clean
iOS logs: iOS has 18, screen shows 1
```
→ **I'll provide exact fix** (iOS UI change)

---

## ⚡ FASTEST PATH TO RESOLUTION

1. **Run iOS app with Console.app open** (5 min)
2. **Open a multi-source story**
3. **Share the logs**
4. **I identify the exact issue** (instant)
5. **I implement the fix** (5-30 min depending on location)
6. **Deploy or rebuild** (2-5 min)
7. **Test and verify** (2 min)

**Total time**: 15-45 minutes from start to verified fix

---

## 💬 HOW TO SHARE LOGS

### **From Console.app**:

1. Select all the log lines with [DEDUPLICATION] or [API DECODE]
2. Copy (⌘C)
3. Paste here in chat

### **What I need to see**:

```
📦 [API DECODE] Story: story_xxx
   API returned X source objects
   Converted to Y SourceArticle objects
   
🔍 [STORY DETAIL INIT] Opening story: story_xxx
   sourceCount field: A
   sources.count: B
   sources: [list of sources]
   
📋 [DEDUPLICATION DEBUG] Story: story_xxx
   Total source articles from API: C
   Unique source count: D
```

The numbers X, Y, A, B, C, D will tell me exactly where the problem is.

---

## 🚀 I'M READY TO FIX THIS

Everything is set up for rapid debugging. The comprehensive logging will show us:

- ✅ What the backend stored
- ✅ What the API sent
- ✅ What iOS decoded
- ✅ What was displayed

One of these will show the issue, and I'll fix it immediately.

---

**Next step**: Run the iOS app test and share the Console logs! 🔍

---

## 📞 IF YOU HAVE QUESTIONS

- "How do I open Console.app?" → Applications → Utilities → Console
- "What should I filter for?" → Type `DEDUPLICATION` in the search box
- "Which story should I open?" → Any story that shows multiple sources in the feed
- "Do I need to rebuild?" → Yes, to get the iOS diagnostic logging

---

Good morning! Let's fix this bug! ☕


