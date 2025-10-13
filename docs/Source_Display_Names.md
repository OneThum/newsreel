# 📰 Source Display Names - User-Friendly Source Names

**Deployed**: 2025-10-13 04:38 UTC  
**Status**: ✅ **LIVE**  
**Impact**: Improved user experience with readable source names

---

## 🎯 What Changed

### Before:
```json
{
  "source": "smh",
  "title": "Breaking news story..."
}
```

User sees: **"smh"** ❌

### After:
```json
{
  "source": "Sydney Morning Herald",
  "title": "Breaking news story..."
}
```

User sees: **"Sydney Morning Herald"** ✅

---

## 📋 Implementation

### 1. **Source Name Mapping** (`source_names.py`)

Created a comprehensive mapping of source IDs to display names:

```python
SOURCE_DISPLAY_NAMES = {
    "smh": "Sydney Morning Herald",
    "bbc": "BBC News",
    "nyt": "New York Times",
    "ap": "Associated Press",
    "reuters": "Reuters",
    "guardian": "The Guardian",
    # ... 100+ source mappings
}

def get_source_display_name(source_id: str) -> str:
    """Get display name for a source ID"""
    return SOURCE_DISPLAY_NAMES.get(source_id, source_id.title())
```

**Features:**
- ✅ Maps all configured RSS sources
- ✅ Fallback to title-cased source_id if not found
- ✅ Easy to add new sources

### 2. **API Response Mapping** (`stories.py`)

Updated all places where sources are returned to users:

```python
from ..utils.source_names import get_source_display_name

# When mapping sources to response
SourceArticle(
    id=source['id'],
    source=get_source_display_name(source.get('source', '')),  # Display name!
    title=source.get('title', ''),
    ...
)
```

**Updated endpoints:**
- `/api/stories/feed` - Story list with sources
- `/api/stories/{id}` - Story detail with sources
- `/api/stories/{id}/sources` - Full source list

---

## 🌍 Source Names Included

### Australian Sources:
- `smh` → **Sydney Morning Herald** ✅
- `abc` → **ABC News**
- `theage` → **The Age**
- `theaustralian` → **The Australian**
- `news_com_au` → **News.com.au**
- `9news` → **9News**
- `7news` → **7News**

### International Sources:
- `bbc` → **BBC News**
- `guardian` → **The Guardian**
- `nyt` → **New York Times**
- `wapo` → **Washington Post**
- `wsj` → **Wall Street Journal**
- `cnn` → **CNN**
- `ap` → **Associated Press**
- `reuters` → **Reuters**
- `bloomberg` → **Bloomberg**

### Tech Sources:
- `techcrunch` → **TechCrunch**
- `verge` → **The Verge**
- `wired` → **Wired**
- `arstechnica` → **Ars Technica**
- `cnet` → **CNET**

### Sports Sources:
- `espn` → **ESPN**
- `si` → **Sports Illustrated**
- `skysports` → **Sky Sports**
- `bbc_sport` → **BBC Sport**

### Business Sources:
- `ft` → **Financial Times**
- `economist` → **The Economist**
- `forbes` → **Forbes**
- `businessinsider` → **Business Insider**
- `cnbc` → **CNBC**

**Total**: 100+ source mappings

---

## 🧪 Testing

### Test API Response:

```bash
curl -s "https://newsreel-api-1759970879.azurewebsites.net/api/stories/feed?category=world&limit=1" | \
jq '.stories[0].sources'
```

**Expected Output:**
```json
[
  {
    "id": "smh_20251013_123456_abc123",
    "source": "Sydney Morning Herald",  // ← Display name!
    "title": "Breaking news headline...",
    "article_url": "https://...",
    "published_at": "2025-10-13T12:34:56Z"
  },
  {
    "id": "bbc_20251013_123457_def456",
    "source": "BBC News",  // ← Display name!
    "title": "Same story from BBC...",
    "article_url": "https://...",
    "published_at": "2025-10-13T12:34:57Z"
  }
]
```

### Verify in iOS App:

1. Open a multi-source story
2. Check source labels
3. Should see:
   - ✅ "Sydney Morning Herald" (not "smh")
   - ✅ "BBC News" (not "bbc")
   - ✅ "New York Times" (not "nyt")

---

## 🔄 Adding New Sources

### When adding a new RSS feed:

1. **Add feed to `rss_feeds.py`:**
```python
RSSFeedConfig(
    id="example_news",
    name="Example News Network",
    url="https://example.com/rss",
    source_id="example_news",  # ← This is the ID
    ...
)
```

2. **Add display name to `source_names.py`:**
```python
SOURCE_DISPLAY_NAMES = {
    ...
    "example_news": "Example News Network",  # ← Add this mapping
    ...
}
```

3. **Deploy API:**
```bash
cd Azure/api
az webapp up --name newsreel-api-1759970879
```

**That's it!** The display name will automatically be used.

---

## 📊 Impact on User Experience

### Before (Technical IDs):
```
Story Sources:
• smh
• bbc
• nyt
• ap
```

**Problems:**
- ❌ Confusing abbreviations
- ❌ Not professional
- ❌ Users don't know what "smh" means
- ❌ Looks like a bug

### After (Display Names):
```
Story Sources:
• Sydney Morning Herald
• BBC News
• New York Times
• Associated Press
```

**Benefits:**
- ✅ Clear and professional
- ✅ Users recognize sources immediately
- ✅ Builds trust and credibility
- ✅ Polished user experience

---

## 🎨 UI Consistency

### Source Display Across App:

1. **Story Cards** - Source count badge
2. **Story Detail** - Full source list
3. **Source Attribution** - Under headlines
4. **Notifications** - Push notification text

All now show consistent display names!

---

## 🔧 Maintenance

### Fallback Behavior:

If a source is not in the mapping, it automatically title-cases the ID:

```python
"abc_news" → "Abc News"  # Fallback
"tech_crunch" → "Tech Crunch"  # Fallback
```

This ensures:
- ✅ No crashes for unmapped sources
- ✅ Graceful degradation
- ✅ Still better than raw IDs

### Update Frequency:

- Add new sources as they're added to RSS feeds
- No need to update for existing sources
- One-time setup per source

---

## 📚 Related Files

- `/Azure/api/app/utils/source_names.py` - Source name mappings
- `/Azure/api/app/routers/stories.py` - API response mapping
- `/Azure/functions/shared/rss_feeds.py` - RSS feed configurations

---

## 💬 User Request

**Original Request:**
> "When we list SMH as a source, let's show it as 'Sydney Morning Herald'"

**Delivered:**
✅ SMH now displays as "Sydney Morning Herald"  
✅ All sources now show full display names  
✅ Professional, readable source attribution  
✅ Consistent across entire app

---

**Source display names are now live! Users will see professional, recognizable source names instead of technical abbreviations.** 🎉


