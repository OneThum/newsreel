# 🚨 API Deduplication Not Working - Investigation

**Date**: October 13, 2025 09:26 UTC  
**Issue**: iOS app still showing 10+ "Associated Press" entries for single-source story

---

## 📸 USER EVIDENCE

User provided screenshots showing:
- Story: "A man in Brazil turned his childhood dream into a small cinema for film lovers"
- Category: Entertainment
- Status: BREAKING
- **Problem**: "This story has been covered by 1 news sources"
- **But showing**: 10+ "Associated Press" entries in Multiple Perspectives

---

## 🔍 WHAT I JUST DEPLOYED (09:16 UTC)

**API Deduplication Logic** in `/Azure/api/app/routers/stories.py`:

```python
# Lines 79-100
source_docs = await cosmos_service.get_story_sources(source_ids)

# DEDUPLICATE by source name
seen_sources = {}  # source_name -> article
for source in source_docs:
    source_name = source.get('source', '')
    seen_sources[source_name] = source  # Keeps most recent

sources = [
    SourceArticle(...)
    for source in seen_sources.values()
]
```

**Expected**: Should deduplicate all Associated Press articles to 1 entry

**Reality**: Not working! Still showing 10+ entries

---

## 🤔 POSSIBLE ROOT CAUSES

### **Theory 1: Container Not Updated**

**Check**: Container image is `newsreelacr.azurecr.io/newsreel-api:latest` ✅

**Conclusion**: Container is correct, but maybe not restarted?

---

### **Theory 2: iOS App Caching**

**Possibility**: iOS app cached the response before fix

**Counter**: User would need to force-quit and reopen app

---

### **Theory 3: `source` Field is Different for Each Article**

**Critical Question**: What is `source.get('source', '')` actually returning?

**Possibilities**:
1. `'ap'` for all → Should deduplicate ✅
2. `'ap_001'`, `'ap_002'`, etc → Won't deduplicate ❌
3. `'Associated Press'` with extra chars → Won't deduplicate ❌

---

### **Theory 4: Backend Creating Multiple Article IDs (Known Issue)**

**We know**: Backend creates a new article ID for each update:
```
ap_20251013_100000_abc123  # Original
ap_20251013_100130_abc123  # Update 1
ap_20251013_100245_abc123  # Update 2
```

**Story cluster stores**: All 10 article IDs

**API fetches**: All 10 articles

**Deduplication**: Should collapse to 1... but isn't!

---

## 🔍 DEBUGGING NEEDED

### **Step 1: Check Database Structure**

Need to see what `source` field actually contains in raw_articles:

```bash
# Query one of these AP articles
az cosmosdb sql query --account-name newsreel-db-1759951135-centralus \
  --database-name newsreel-db \
  --container-name raw_articles \
  --query "SELECT c.id, c.source, c.title FROM c WHERE c.source LIKE '%ap%' LIMIT 5"
```

---

### **Step 2: Check API Response**

Test the API directly:

```bash
# Get story ID from user's screenshot (need to extract)
curl https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/api/stories/{story_id}
```

Check:
- How many sources in response?
- What are the `source` field values?

---

### **Step 3: Check Source Display Name Mapping**

File: `/Azure/api/app/utils/source_names.py`

```python
SOURCE_DISPLAY_NAMES = {
    'ap': 'Associated Press',
    'bbc': 'BBC News',
    ...
}
```

**Issue**: We're deduplicating by `source.get('source', '')` (raw ID like 'ap')

**Then**: We call `get_source_display_name()` which converts 'ap' → 'Associated Press'

**But**: If deduplication happens BEFORE display name conversion, this should work!

---

## 🎯 MOST LIKELY CAUSE

**Theory**: The API deduplication IS working, but the iOS app is showing cached data from BEFORE the fix was deployed.

**Evidence**:
- Container image is latest ✅
- Deployment completed 09:16 UTC
- User screenshot taken ~09:25 UTC
- iOS apps cache API responses

**Solution**: User needs to **force-quit and reopen app**, or wait for cache to expire

---

## 🔄 ALTERNATIVE EXPLANATION

**Theory**: The deduplication code has a bug

**Looking closer at line 86**:
```python
seen_sources[source_name] = source  # Overwrites older ones
```

**Wait!** If `source_name` is empty string `''` for any reason, ALL articles get the same key!

**Check**: Does every article have a `source` field? Or could some be missing?

```python
source_name = source.get('source', '')  # Returns '' if no 'source' field
```

If `source` field is missing → `source_name = ''` → All stored under same key → Only shows LAST one?

**But user shows 10+ entries**, so this isn't the issue.

---

## ✅ IMMEDIATE ACTION NEEDED

### **1. User: Force-Quit App**

Ask user to:
1. Force-quit Newsreel app (swipe up from app switcher)
2. Reopen app
3. Check if duplicate sources are gone

---

### **2. Check API Response Directly**

I need to:
1. Get a story ID that's showing duplicates
2. Query API directly
3. Verify deduplication is working server-side

---

### **3. Verify Container Restart**

Even though image is latest, container might not have restarted:

```bash
az containerapp revision list --name newsreel-api --resource-group newsreel-rg \
  --query "[].{name:name, created:properties.createdTime, active:properties.active}" -o table
```

Check if newest revision is from 09:16 UTC or later.

---

## 🚀 IF DEDUPLICATION STILL DOESN'T WORK

Then we MUST implement the **update-in-place** strategy from `/ARTICLE_UPDATE_IN_PLACE.md`:

1. Remove timestamp from article ID generation
2. Use UPSERT instead of CREATE
3. Backend stores only 1 article per source per story
4. No API deduplication needed!

**Benefit**: Fixes problem at the source, not as a band-aid

---

## 📋 QUESTIONS FOR USER

1. **Have you force-quit and reopened the app since 09:16 UTC?**
2. **Does this show 10 separate articles or just the same article repeated?**
3. **When you tap on each "Associated Press" entry, do they go to different URLs or the same URL?**

---

**Status**: ⚠️ **INVESTIGATING - USER FEEDBACK NEEDED**

Most likely cause: iOS app showing cached data from before fix.


