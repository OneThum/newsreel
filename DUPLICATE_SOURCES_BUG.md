# 🐛 Duplicate Sources Display Bug

**Date**: October 13, 2025  
**Severity**: CRITICAL - User-facing bug  
**Status**: Root cause identified

---

## 🔍 THE PROBLEM

**User sees**:
```
"This story has been covered by 1 news sources"

Multiple Perspectives:
- CNN (Read this perspective)
- CNN (Read this perspective)
- CNN (Read this perspective)
- CNN (Read this perspective)
- CNN (Read this perspective)
- CNN (Read this perspective)
- CNN (Read this perspective)
- CNN (Read this perspective)
```

**This is wrong!** User expects to see:
- Unique sources only (1 CNN entry, not 8)
- Or if showing multiple articles from same source, clear indication it's the same source

---

## 🚨 ROOT CAUSE

### **Backend Logic (CORRECT)**:

```python
# function_app.py - Allows multiple articles from same source
source_articles = ['cnn_001', 'cnn_002', 'cnn_003', ...]  # Multiple CNN article IDs
source_count = len(set([get_source_name(id) for id in source_articles]))  # Counts unique sources = 1
```

### **API/iOS Display (WRONG)**:

The API returns **ALL articles** in the `sources` array, and iOS displays **ALL of them** without deduplicating by source name.

```json
{
  "sources": [
    {"id": "cnn_001", "source": "CNN", "title": "Breaking news..."},
    {"id": "cnn_002", "source": "CNN", "title": "Updated: Breaking news..."},
    {"id": "cnn_003", "source": "CNN", "title": "Latest: Breaking news..."},
    ...
  ]
}
```

**iOS displays all 8 entries as separate "perspectives"** even though they're all CNN.

---

## 📊 TWO INTERPRETATION ISSUES

### **Issue 1: Source Count vs Article Count Confusion**

**Backend stores**:
- `source_articles`: ['cnn_001', 'cnn_002', 'cnn_003', ...] (8 article IDs)
- Displayed as: "1 news sources" (correct - unique source count)

**But iOS shows**: 8 entries (incorrect - showing all articles)

---

### **Issue 2: What Should "Multiple Perspectives" Mean?**

**Option A: Different Sources**
```
Multiple Perspectives (3 sources):
- CNN: Breaking news
- BBC: Israel confirms release  
- Reuters: 7 hostages freed
```

**Option B: All Articles (including updates from same source)**
```
Multiple Perspectives (8 articles from 1 source):
- CNN: Breaking news (10:00 AM)
- CNN: Updated: 7 hostages (10:15 AM)
- CNN: Latest: Trump arrives (10:30 AM)
...
```

**Current behavior**: Neither! Shows 8 CNN entries with identical labels.

---

## ✅ RECOMMENDED FIX

### **Short-term (API fix)**:

**Deduplicate sources in API response** - Only return one article per unique source:

```python
# Azure/api/app/routers/stories.py

# BEFORE (returns all articles):
sources = [
    SourceArticle(id=source['id'], source=source['source'], ...)
    for source in source_docs
]

# AFTER (returns one per unique source):
seen_sources = set()
sources = []
for source in source_docs:
    source_name = source.get('source', '')
    if source_name not in seen_sources:
        sources.append(SourceArticle(
            id=source['id'],
            source=get_source_display_name(source_name),
            title=source.get('title', ''),
            ...
        ))
        seen_sources.add(source_name)
```

---

### **Long-term (Better UX)**:

**Group by source with expansion**:

```
Multiple Perspectives (3 sources, 12 articles):

📰 CNN (8 articles)
  ⌄ Tap to see all CNN coverage
  
📰 BBC (2 articles)
  ⌄ Tap to see all BBC coverage
  
📰 Reuters (2 articles)
  ⌄ Tap to see all Reuters coverage
```

**On expansion**:
```
📰 CNN (8 articles)
  > Breaking news... (10:00 AM)
  > Updated: 7 hostages... (10:15 AM)
  > Latest: Trump arrives... (10:30 AM)
  ...
```

---

## 🔧 IMMEDIATE FIX (API)

```python
# File: Azure/api/app/routers/stories.py
# Function: map_story_to_response

# Around line 54-71

# Get sources if requested
sources = []
if include_sources:
    source_ids = story.get('source_articles', [])
    if source_ids:
        source_docs = await cosmos_service.get_story_sources(source_ids)
        
        # DEDUPLICATE by source name - only show one article per unique source
        seen_sources = {}  # source_name -> article
        for source in source_docs:
            source_name = source.get('source', '')
            
            # Keep the first article from each source (could be most recent instead)
            if source_name not in seen_sources:
                seen_sources[source_name] = source
        
        # Convert to SourceArticle responses
        sources = [
            SourceArticle(
                id=source['id'],
                source=get_source_display_name(source.get('source', '')),
                title=source.get('title', ''),
                article_url=source.get('article_url', ''),
                published_at=datetime.fromisoformat(
                    source.get('published_at', '').replace('Z', '+00:00')
                )
            )
            for source in seen_sources.values()
        ]
```

---

## 🎯 EXPECTED BEHAVIOR AFTER FIX

### **Scenario: CNN posts 8 updates about same story**

**Before (WRONG)**:
```
"1 news sources"
- CNN (8 duplicate entries)
```

**After (CORRECT)**:
```
"1 news sources"
- CNN (1 entry, most recent or first article)
```

### **Scenario: Multi-source story**

**Before (WRONG)**:
```
"3 news sources"
- CNN (8 entries)
- BBC (2 entries)
- Reuters (2 entries)
Total displayed: 12 entries
```

**After (CORRECT)**:
```
"3 news sources"
- CNN (1 entry)
- BBC (1 entry)  
- Reuters (1 entry)
Total displayed: 3 entries
```

---

## 💡 ALTERNATIVE: Show Article Count

If we want to preserve the ability to see all articles:

```
"3 news sources (12 articles)"

Multiple Perspectives:
- CNN (8 articles) > Tap to see all
- BBC (2 articles) > Tap to see all
- Reuters (2 articles) > Tap to see all
```

---

## 🚀 DEPLOYMENT NEEDED

1. **API Changes**: Update `stories.py` to deduplicate sources
2. **API Rebuild**: Rebuild and redeploy container app
3. **iOS Changes** (optional): Improve grouping/expansion UI

---

## 📝 WHY THIS HAPPENED

**Context**: We recently fixed the "source diversity blocking" bug where stories were stuck at low source counts.

**The fix**: Allow multiple articles from the same source (e.g., AP updates a story 3 times)

**Unintended consequence**: All those articles now appear as separate "perspectives" in iOS

**Lesson**: Need to distinguish between:
- **Backend storage**: All article IDs (for tracking updates)
- **API response**: Unique sources only (for display)
- **iOS display**: Clear presentation of source diversity

---

## 🔍 HOW TO VERIFY

### **Check current behavior**:
```bash
# Query a multi-article story
curl -H "Authorization: Bearer $TOKEN" \
  "https://newsreel-api.azurewebsites.net/api/stories/{story_id}"

# Look at sources array length vs source_count
```

### **After fix**:
```bash
# sources array length should match source_count
# (or be close if we choose most recent article per source)
```

---

**Status**: ⚠️ **CRITICAL FIX NEEDED**

This is a user-facing bug that makes the app look broken. Needs immediate deployment.


