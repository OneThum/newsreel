# 🔍 Enhanced Deduplication Diagnostic Logging

**Date**: October 13, 2025 10:30 UTC  
**Status**: ✅ READY FOR TESTING

---

## 🚨 PROBLEM IDENTIFIED

**User Report**: Feed card shows "16 sources", but detail view shows only "1 source"

**Hypothesis**: The `sources` array is not being populated correctly during API decoding, OR the sources are being lost somewhere between the feed and the detail view.

---

## 📝 DIAGNOSTIC LOGGING ADDED

### **1. API Decoding (APIService.swift)**

Added logging **immediately after** the API response is converted to `SourceArticle` objects:

```swift
// 🔍 DEDUPLICATION DIAGNOSTIC LOGGING
if let sources = sources {
    Logger.api.info("📦 [API DECODE] Story: \(id)")
    Logger.api.info("   API returned \(sources.count) source objects")
    Logger.api.info("   Converted to \(sourceArticles.count) SourceArticle objects")
    
    // Check for duplicates in API response
    let sourceNames = sources.map { $0.source }
    let uniqueNames = Set(sourceNames)
    if uniqueNames.count != sourceNames.count {
        Logger.api.warning("⚠️ [API DECODE] API RETURNED DUPLICATES!")
        Logger.api.warning("   Unique: \(uniqueNames.count), Total: \(sourceNames.count)")
        
        // Log duplicate counts
        let counts = Dictionary(grouping: sourceNames, by: { $0 }).mapValues { $0.count }
        let duplicates = counts.filter { $0.value > 1 }
        for (name, count) in duplicates {
            Logger.api.warning("   '\(name)' appears \(count) times in API response")
        }
    }
    
    // Log first 3 source names
    for (index, source) in sources.prefix(3).enumerated() {
        Logger.api.debug("   [\(index+1)] \(source.source) - ID: \(source.id)")
    }
} else {
    Logger.api.warning("⚠️ [API DECODE] Story: \(id) - sources field is nil")
}
```

**Logs before Story creation**:
```swift
Logger.api.debug("📦 [API DECODE] Creating Story object with \(sourceArticles.count) sources")
```

---

### **2. Story Detail View Init (StoryDetailView.swift)**

Added logging when a story detail view is opened:

```swift
// 🔍 DEDUPLICATION DIAGNOSTIC LOGGING
Logger.ui.info("🔍 [STORY DETAIL INIT] Opening story: \(story.id)")
Logger.ui.info("   sourceCount field: \(story.sourceCount)")
Logger.ui.info("   sources.count: \(story.sources.count)")

if story.sources.isEmpty {
    Logger.ui.warning("⚠️ [STORY DETAIL INIT] sources array is EMPTY!")
} else {
    let sourceNames = story.sources.map { $0.displayName }
    Logger.ui.info("   sources: \(sourceNames.joined(separator: ", "))")
    
    // Check for duplicates
    let uniqueNames = Set(sourceNames)
    if uniqueNames.count != sourceNames.count {
        Logger.ui.warning("⚠️ [STORY DETAIL INIT] DUPLICATES in sources array!")
        Logger.ui.warning("   Unique: \(uniqueNames.count), Total: \(sourceNames.count)")
    }
}
```

---

### **3. Multiple Perspectives Section (StoryDetailView.swift)**

*Already added in previous change*

Logs when the "Multiple Perspectives" section is displayed:
- Total sources from API
- Unique source count
- All source names
- Duplicate detection
- First 5 article IDs and URLs

---

## 🎯 WHAT THESE LOGS WILL TELL US

### **Scenario 1: API Not Sending Sources** ❌

```
⚠️ [API DECODE] Story: story_123 - sources field is nil
📦 [API DECODE] Creating Story object with 0 sources
🔍 [STORY DETAIL INIT] Opening story: story_123
   sourceCount field: 16
   sources.count: 0
⚠️ [STORY DETAIL INIT] sources array is EMPTY!
```

**Diagnosis**: API isn't including sources in the response, even though `source_count` says 16. **API bug**.

---

### **Scenario 2: API Sending Duplicates** ❌

```
📦 [API DECODE] Story: story_123
   API returned 16 source objects
   Converted to 16 SourceArticle objects
⚠️ [API DECODE] API RETURNED DUPLICATES!
   Unique: 2, Total: 16
   'Associated Press' appears 12 times in API response
   'Reuters' appears 4 times in API response
📦 [API DECODE] Creating Story object with 16 sources
🔍 [STORY DETAIL INIT] Opening story: story_123
   sourceCount field: 16
   sources.count: 16
   sources: Associated Press, Associated Press, Associated Press, ...
⚠️ [STORY DETAIL INIT] DUPLICATES in sources array!
```

**Diagnosis**: API is sending duplicate sources. **Backend deduplication failed**.

---

### **Scenario 3: iOS Decoding Error** ❌

```
📦 [API DECODE] Story: story_123
   API returned 16 source objects
   Converted to 1 SourceArticle objects  ← Problem here!
📦 [API DECODE] Creating Story object with 1 sources
🔍 [STORY DETAIL INIT] Opening story: story_123
   sourceCount field: 16
   sources.count: 1
```

**Diagnosis**: Something went wrong during the `.map` conversion. **iOS decoding bug**.

---

### **Scenario 4: Everything Working** ✅

```
📦 [API DECODE] Story: story_123
   API returned 16 source objects
   Converted to 16 SourceArticle objects
   [1] ap - ID: ap_abc123
   [2] bbc - ID: bbc_def456
   [3] cnn - ID: cnn_ghi789
📦 [API DECODE] Creating Story object with 16 sources
🔍 [STORY DETAIL INIT] Opening story: story_123
   sourceCount field: 16
   sources.count: 16
   sources: Associated Press, BBC, CNN, Reuters, Guardian, ...
📋 [DEDUPLICATION DEBUG] Story: story_123
   Total source articles from API: 16
   Unique source count: 16
✅ [DEDUPLICATION] All sources unique
```

**Diagnosis**: Everything is working correctly!

---

## 📱 HOW TO TEST

1. **Build and run the iOS app** in Xcode (⌘R)
2. **Open Console.app** on your Mac
3. **Filter by** "API DECODE" or "STORY DETAIL INIT" or "DEDUPLICATION"
4. **Open a story** that shows multiple sources (like the Russia/Ukraine story)
5. **Watch the logs** in Console

---

## 🔍 KEY LOGS TO LOOK FOR

### **When Feed Loads**:
```
📦 [API DECODE] Story: story_xxx
   API returned X source objects
   Converted to Y SourceArticle objects
```

### **When You Tap on Story**:
```
🔍 [STORY DETAIL INIT] Opening story: story_xxx
   sourceCount field: X
   sources.count: Y
```

### **When "Multiple Perspectives" Section Appears**:
```
📋 [DEDUPLICATION DEBUG] Story: story_xxx
   Total source articles from API: X
   Unique source count: Y
```

---

## 🎯 WHAT WE'RE LOOKING FOR

**The million-dollar question**:

1. Does `API DECODE` log show 16 sources converted?
2. Does `STORY DETAIL INIT` log show 16 sources in the array?
3. Does `DEDUPLICATION DEBUG` log show 16 sources when section appears?

If **ANY** of these show a different number, we've found where the sources are being lost!

---

## 📊 POSSIBLE OUTCOMES

| API DECODE | STORY DETAIL INIT | DEDUPLICATION DEBUG | Diagnosis |
|------------|-------------------|---------------------|-----------|
| 16 sources | 16 sources | 16 sources | ✅ **Working!** |
| nil sources | 0 sources | - | ❌ **API not sending sources** |
| 16 sources | 1 source | 1 source | ❌ **iOS decoding bug** |
| 16 sources (duplicates) | 16 sources (duplicates) | 16 sources (duplicates) | ❌ **Backend deduplication failed** |
| 16 sources | 0 sources | - | ❌ **Story object not created correctly** |

---

**Status**: ✅ **ENHANCED LOGGING READY - AWAITING USER TEST**

Please build, run, open a multi-source story, and share the console logs!

The logs will tell us **exactly** where the sources are being lost.


