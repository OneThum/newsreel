# 📝 Article Update-in-Place Strategy

**Date**: October 13, 2025  
**Status**: ⚠️ DESIGN PROPOSAL

---

## 🎯 USER REQUEST

**Problem**: "If CNN publishes an article and updates it 10 times, we get 10 separate records in the database. This wastes storage and creates 100 source stories from 10 sources (each with 10 updates), instead of just 10."

**Proposed Solution**: **Update-in-place** - Overwrite the existing article record with each update, keeping only the latest version.

---

## 📊 CURRENT BEHAVIOR

### **Article ID Generation**:

```python
# shared/utils.py
def generate_article_id(source: str, url: str, published_at: datetime) -> str:
    timestamp = published_at.strftime("%Y%m%d_%H%M%S")  # ← Includes seconds!
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"{source}_{timestamp}_{url_hash}"
```

**Example**:
```
Original:  cnn_20251013_100000_abc12345
Update 1:  cnn_20251013_100130_abc12345  # ← Different timestamp, same URL
Update 2:  cnn_20251013_100245_abc12345
...
Update 10: cnn_20251013_103000_abc12345
```

**Result**: 10 separate article records in database ❌

---

### **Article Storage**:

```python
# cosmos_client.py
async def create_raw_article(self, article: RawArticle):
    container.create_item(body=article.model_dump(mode='json'))  # Fails if exists
```

**Behavior**:
- Uses `create_item()` which throws `CosmosResourceExistsError` if article exists
- If error, logs "Article already exists" and skips
- **BUT** because article ID includes timestamp, same URL with new timestamp = new article

---

## ✅ PROPOSED SOLUTION

### **1. Change Article ID to URL-Based Only**:

```python
# shared/utils.py
def generate_article_id(source: str, url: str, published_at: datetime) -> str:
    """Generate unique article ID based on source + URL only (no timestamp)
    
    This ensures:
    - Same URL from same source = same article ID
    - Updates overwrite existing record instead of creating duplicates
    - Database stays lean and efficient
    """
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]  # Longer hash for uniqueness
    return f"{source}_{url_hash}"
```

**Example**:
```
Original:  cnn_abc123456789
Update 1:  cnn_abc123456789  # ← Same ID, will UPSERT
Update 2:  cnn_abc123456789
...
Update 10: cnn_abc123456789
```

**Result**: 1 article record (always latest version) ✅

---

### **2. Change Create to Upsert**:

```python
# cosmos_client.py
async def upsert_raw_article(self, article: RawArticle) -> Dict[str, Any]:
    """Create or update raw article (upsert)
    
    If article exists: Updates with latest title, description, content
    If article is new: Creates new record
    
    This implements update-in-place for same-source article updates.
    """
    try:
        container = self._get_container(config.CONTAINER_RAW_ARTICLES)
        
        # UPSERT: Create if new, update if exists
        result = container.upsert_item(body=article.model_dump(mode='json'))
        
        logger.info(f"Upserted raw article: {article.id}")
        return result
    except Exception as e:
        logger.error(f"Failed to upsert raw article {article.id}: {e}")
        raise
```

---

### **3. Track First Seen vs Last Updated**:

```python
# shared/models.py
class RawArticle(BaseModel):
    id: str
    source: str
    title: str
    # ... existing fields ...
    published_at: datetime  # Original publication timestamp from RSS
    fetched_at: datetime    # When WE first saw it
    updated_at: datetime    # When WE last updated it (for upserts)
```

**Logic**:
- `published_at`: From RSS feed (article's original publication date)
- `fetched_at`: Set once when first created, never changed
- `updated_at`: Updated on every upsert

---

## 📊 IMPACT ANALYSIS

### **Storage Savings**:

**Before (Current)**:
```
CNN article updated 10 times = 10 database records
10 sources × 10 updates each = 100 records

Daily: ~1000 articles × 5 updates avg = 5,000 records/day
Monthly: 150,000 records
```

**After (Proposed)**:
```
CNN article updated 10 times = 1 database record (overwritten)
10 sources × 1 current version = 10 records

Daily: ~1000 articles = 1,000 records/day
Monthly: 30,000 records
```

**Savings**: **80% reduction** in article storage! 🎉

---

### **Story Clustering Impact**:

**Before**:
```
Story has 3 sources (CNN, BBC, Reuters)
Each source updates 10 times
source_articles = ['cnn_1', 'cnn_2', ..., 'cnn_10', 'bbc_1', ..., 'reuters_10']
Total: 30 article IDs
API had to deduplicate to show "3 sources"
```

**After**:
```
Story has 3 sources
Each source has 1 current article (overwritten on updates)
source_articles = ['cnn_abc', 'bbc_def', 'reuters_ghi']
Total: 3 article IDs
API shows "3 sources" naturally ✅
```

**Benefit**: No need for API deduplication logic!

---

### **Query Performance**:

**Before**:
```sql
SELECT * FROM c WHERE c.story_cluster_id = 'story_123'
Returns: 30 articles for 3 sources
```

**After**:
```sql
SELECT * FROM c WHERE c.story_cluster_id = 'story_123'
Returns: 3 articles for 3 sources
```

**10x faster** for typical multi-source story!

---

## ⚠️ CONSIDERATIONS

### **1. Loss of Update History**

**Trade-off**: Can't track how article evolved over time

**User's Position**: "Each update is self-sufficient" → History not needed

**Acceptable**: ✅ News apps care about current state, not version history

---

### **2. Partition Key Strategy**

**Current**: `published_date` (e.g., "2025-10-13")

**Issue**: If article is updated next day, `published_at` might change?

**Solution**: Use `fetched_at` date for partition key (never changes)

```python
partition_key = article.fetched_at.strftime('%Y-%m-%d')
```

---

### **3. Story Cluster References**

**Current**: Story clusters store array of article IDs

**Impact**: When article is updated, same ID still valid ✅

**No migration needed**: Existing story clusters continue to work

---

### **4. Changefeed for Clustering**

**Current**: Changefeed triggers on article creation/update

**Impact**: Upserts trigger changefeed, so clustering still works ✅

**Benefit**: Fewer changefeed events (1 instead of 10 per update)

---

## 🚀 IMPLEMENTATION PLAN

### **Phase 1: Core Changes**

1. **Update `generate_article_id()`** to remove timestamp
2. **Rename/update `create_raw_article()` to `upsert_raw_article()`**
3. **Add `updated_at` field to `RawArticle` model**
4. **Update RSS ingestion to use upsert**

### **Phase 2: Clean Up**

5. **Remove API deduplication logic** (no longer needed)
6. **Update clustering to expect 1 article per source**

### **Phase 3: Migration** (Optional)

7. **Deduplicate existing articles** by URL (one-time cleanup)

---

## 📝 CODE CHANGES

### **File 1: `shared/utils.py`**

```python
def generate_article_id(source: str, url: str, published_at: datetime) -> str:
    """Generate unique article ID based on source + URL only
    
    NO TIMESTAMP - Same URL from same source = same article ID
    This enables update-in-place for article updates.
    """
    # Use longer hash for better uniqueness without timestamp
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    return f"{source}_{url_hash}"
```

---

### **File 2: `shared/models.py`**

```python
class RawArticle(BaseModel):
    # ... existing fields ...
    published_at: datetime  # From RSS feed
    fetched_at: datetime    # When we first saw it (immutable)
    updated_at: datetime    # When we last updated it (for upserts)
```

---

### **File 3: `shared/cosmos_client.py`**

```python
async def upsert_raw_article(self, article: RawArticle) -> Dict[str, Any]:
    """Create or update raw article (upsert)"""
    try:
        container = self._get_container(config.CONTAINER_RAW_ARTICLES)
        
        # Set updated_at timestamp
        article_dict = article.model_dump(mode='json')
        article_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        # UPSERT: Create if new, update if exists
        result = container.upsert_item(body=article_dict)
        
        logger.info(f"Upserted raw article: {article.id}")
        return result
    except Exception as e:
        logger.error(f"Failed to upsert raw article {article.id}: {e}")
        raise
```

---

### **File 4: `function_app.py`** (RSS Ingestion)

```python
# Line 600: Change from create to upsert
result = await cosmos_client.upsert_raw_article(article)  # ← Changed
if result:
    new_articles += 1  # Note: This counts upserts too
    source_distribution[feed_config.name] += 1
```

---

### **File 5: `api/app/routers/stories.py`** (SIMPLIFY)

```python
# BEFORE: API had to deduplicate
seen_sources = {}
for source in source_docs:
    source_name = source.get('source', '')
    seen_sources[source_name] = source  # Keep one per source
sources = list(seen_sources.values())

# AFTER: No deduplication needed! Already 1 per source
sources = [
    SourceArticle(
        id=source['id'],
        source=get_source_display_name(source.get('source', '')),
        title=source.get('title', ''),
        article_url=source.get('article_url', ''),
        published_at=datetime.fromisoformat(...)
    )
    for source in source_docs  # Already deduplicated by database!
]
```

---

## ✅ BENEFITS SUMMARY

| Aspect | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Storage** | 5,000 articles/day | 1,000 articles/day | 80% reduction |
| **Query Speed** | 30 articles/story | 3 articles/story | 10x faster |
| **API Logic** | Complex deduplication | Simple mapping | Cleaner code |
| **Bandwidth** | More data transferred | Less data | Cost savings |
| **Code Complexity** | API must dedupe | Database is truth | Simpler |

---

## 🧪 TESTING PLAN

### **Test 1: Same Article Updated**

1. Publish CNN article → Check DB (1 record)
2. Update same CNN article → Check DB (still 1 record, title changed)
3. Verify story cluster has 1 CNN article ID

### **Test 2: Different Articles from Same Source**

1. Publish CNN article A → Check DB (1 record)
2. Publish CNN article B (different URL) → Check DB (2 records)
3. Verify different article IDs

### **Test 3: Story Clustering**

1. Create story with CNN + BBC + Reuters
2. Each source updates their article
3. Verify story still has 3 article IDs (not 6)

---

## 📅 DEPLOYMENT TIMELINE

**Estimated Effort**: 2-4 hours

1. **Code Changes**: 30 min
2. **Testing**: 1 hour
3. **Deployment**: 15 min
4. **Verification**: 30 min
5. **API Cleanup**: 30 min (remove deduplication)

---

## ❓ QUESTIONS FOR USER

1. **Partition Key**: Should we use `fetched_at` date instead of `published_at` for partition key?
2. **Migration**: Should we deduplicate existing articles or just apply to new ones?
3. **Logging**: Should we log when an article is updated vs created?
4. **Priority**: Implement now or after breaking news verification?

---

**Status**: ⚠️ **AWAITING USER CONFIRMATION**

This is a significant architectural improvement. Please confirm:
- ✅ Approach makes sense
- ✅ Ready to proceed with implementation
- ✅ Any concerns about loss of update history


