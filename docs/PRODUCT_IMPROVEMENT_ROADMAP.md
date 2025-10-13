# Newsreel Product Improvement Roadmap
**Date**: October 13, 2025  
**Status**: Strategic Planning

## 🎯 Executive Summary

This roadmap addresses 5 critical issues preventing Newsreel from delivering optimal user experience:

1. **Category Mislabeling** - Inaccurate content categorization
2. **Source Clumping** - 10+ articles from same provider in feed
3. **Inefficient Polling** - Mismatched update cycles (30s client vs 5min backend)
4. **Update Intelligence** - Can't distinguish "new source" from "significant update"
5. **Insufficient Logging** - Can't debug production issues

---

## 📊 CURRENT STATE ASSESSMENT

### Architecture Overview
```
RSS Sources (100+)
    ↓
Azure Function: RSS Ingestion (every 5 min)
    ↓
Cosmos DB: raw_articles
    ↓
Azure Function: Story Clustering (change feed)
    ↓
Cosmos DB: story_clusters
    ↓
Azure Function: Summarization (change feed + backfill every 10 min)
    ↓
FastAPI: Stories API
    ↓
iOS App (polls every 30s)
```

### Current Logging Status

#### ✅ What Exists:
- **Backend**: Basic Python `logging` with timestamps
- **API**: FastAPI request logging
- **iOS**: No structured logging (just print statements)

#### ❌ What's Missing:
- No correlation IDs across services
- No performance metrics
- No structured logs for querying
- No feed diversity tracking
- No categorization confidence scores
- No distributed tracing

---

## 🏗️ IMPLEMENTATION PHASES

---

## **PHASE 1: OBSERVABILITY FOUNDATION** 🔴 CRITICAL
**Timeline**: 1-2 days  
**Effort**: Low  
**Impact**: **CRITICAL** - Enables all future improvements

### Why This First?
> "You can't fix what you can't measure. Without proper logging, you're flying blind."

### Implementation:

#### 1.1 Backend Structured Logging ✅ **DONE**
- Created `Azure/functions/shared/logger.py`
- Provides:
  - Correlation IDs
  - Performance timing
  - Event categorization
  - Application Insights integration

#### 1.2 iOS Structured Logging ✅ **DONE**
- Created `Newsreel App/Newsreel/Services/LoggingService.swift`
- Features:
  - OSLog integration (for Instruments)
  - Category-based logging
  - Performance measurement
  - Source diversity tracking

#### 1.3 Integrate Structured Logging
**Update these files:**

**`Azure/functions/function_app.py`:**
```python
# Add at top:
from shared.logger import get_logger

# Replace all logger instances:
logger = get_logger(__name__)

# In RSS ingestion:
with logger.operation("rss_ingestion", feed_count=len(feed_configs)):
    for feed_result in feed_results:
        logger.log_rss_fetch(
            source=feed_config.name,
            success=True,
            article_count=len(feed.entries),
            duration_ms=fetch_duration_ms
        )

# In clustering:
logger.log_article_processed(
    article_id=article.id,
    source=article.source,
    category=article.category,
    fingerprint=article.story_fingerprint,
    matched_story=bool(stories)
)

logger.log_story_cluster(
    story_id=story_id,
    action="created" if is_new else "updated",
    source_count=len(source_articles),
    category=category,
    fingerprint=fingerprint,
    title=title
)
```

**`Azure/api/app/routers/stories.py`:**
```python
from shared.logger import get_logger

logger = get_logger(__name__)

# In get_personalized_feed:
logger.log_feed_diversity(
    total_stories=len(story_responses),
    unique_sources=len(set(s.source.name for s in story_responses)),
    source_distribution={...}
)
```

**Expected Output After Phase 1:**
```
[INFO] RSS Fetch: BBC - 23 articles in 234ms (status: 200)
[INFO] Article Processed: bbc_20251013_123456_a1b2c3 → matched=True, category=politics
[INFO] Story Cluster: updated - story_politics_abc123 (3 sources)
[INFO] Summary Generated: story_politics_abc123 (142 words in 1,234ms)
[INFO] Feed Diversity: 15 sources across 20 stories
```

---

## **PHASE 2: FEED DIVERSITY** 🟠 HIGH PRIORITY
**Timeline**: 1 day  
**Effort**: Medium  
**Impact**: Immediate UX improvement

### Problem:
```
Current Feed:
1. BBC - Story A
2. BBC - Story B  
3. BBC - Story C
4. BBC - Story D
5. BBC - Story E
⋮
10. BBC - Story J
```

### Solution: Source-Weighted Feed Algorithm

Create `Azure/api/app/services/feed_service.py`:
```python
"""Smart Feed Generation with Source Diversity"""
from typing import List, Dict, Any
from collections import defaultdict
import random

class FeedService:
    """
    Generates diverse feeds using source distribution algorithm
    
    Algorithm:
    1. Group stories by source
    2. Round-robin distribution with quality weighting
    3. Ensure no more than 2 consecutive stories from same source
    """
    
    def diversify_feed(self, stories: List[Dict[str, Any]], limit: int = 20) -> List[Dict[str, Any]]:
        """
        Apply source diversity to feed
        
        Rules:
        - No more than 2 consecutive stories from same source
        - Prioritize high-verification stories
        - Maintain temporal relevance (recent stories favored)
        """
        
        # Group by primary source
        stories_by_source = defaultdict(list)
        for story in stories:
            source = story.get('primary_source', 'unknown')
            stories_by_source[source].append(story)
        
        # Round-robin with anti-clumping
        diversified = []
        source_queues = {src: stories[:] for src, stories in stories_by_source.items()}
        last_source = None
        consecutive_count = 0
        
        while len(diversified) < limit and any(source_queues.values()):
            # Available sources (excluding last if consecutive_count >= 2)
            available_sources = [
                src for src, queue in source_queues.items()
                if queue and (src != last_source or consecutive_count < 2)
            ]
            
            if not available_sources:
                # Reset if stuck
                available_sources = [src for src, queue in source_queues.items() if queue]
                consecutive_count = 0
            
            if not available_sources:
                break
            
            # Pick source (weighted by verification level)
            source = self._select_source(available_sources, source_queues)
            story = source_queues[source].pop(0)
            diversified.append(story)
            
            # Track consecutive
            if source == last_source:
                consecutive_count += 1
            else:
                consecutive_count = 1
                last_source = source
        
        return diversified
    
    def _select_source(self, available_sources: List[str], 
                      source_queues: Dict[str, List]) -> str:
        """Select next source weighted by story quality"""
        
        # Calculate weights based on verification level of next story
        weights = []
        for source in available_sources:
            next_story = source_queues[source][0]
            verification = next_story.get('verification_level', 1)
            
            # Higher verification = higher weight
            # 1 source = weight 1
            # 2-3 sources = weight 2  
            # 4+ sources = weight 3
            weight = min(verification, 3)
            weights.append(weight)
        
        # Weighted random selection
        return random.choices(available_sources, weights=weights, k=1)[0]
```

**Update `Azure/api/app/routers/stories.py`:**
```python
from ..services.feed_service import FeedService

feed_service = FeedService()

@router.get("/feed", response_model=List[StoryDetailResponse])
async def get_personalized_feed(...):
    # ... existing code ...
    
    # Get MORE stories than needed
    stories = await cosmos_service.query_recent_stories(
        category=category,
        limit=limit * 3,  # Get 3x for diversity algorithm
        offset=offset
    )
    
    # Apply diversity
    diversified_stories = feed_service.diversify_feed(stories, limit=limit)
    
    # Map to response
    story_responses = []
    for story in diversified_stories:
        story_response = await map_story_to_response(story, user, include_sources=True)
        story_responses.append(story_response)
    
    # LOG DIVERSITY METRICS
    source_dist = {}
    for story in story_responses:
        src = story.source.name
        source_dist[src] = source_dist.get(src, 0) + 1
    
    logger.log_feed_diversity(
        total_stories=len(story_responses),
        unique_sources=len(source_dist),
        source_distribution=source_dist
    )
    
    return story_responses
```

**Expected Outcome:**
```
Diverse Feed:
1. BBC - Story A
2. Reuters - Story B
3. Guardian - Story C
4. NYT - Story D
5. BBC - Story E      ← BBC returns (but not consecutive 3x)
6. AP - Story F
7. CNN - Story G
...
```

---

## **PHASE 3: SMART POLLING** 🟡 MEDIUM PRIORITY
**Timeline**: 0.5 days  
**Effort**: Low  
**Impact**: Reduces API calls by 83%

### Problem:
- iOS polls every 30s
- Backend updates every 5 min
- 10 unnecessary API calls per backend update

### Solution: Last-Modified + Adaptive Polling

#### 3.1 Add Last-Modified Endpoint

**`Azure/api/app/routers/stories.py`:**
```python
@router.get("/feed/last-modified")
async def get_feed_last_modified(
    category: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Returns timestamp of most recent feed update
    Allows client to poll efficiently
    """
    cosmos_service.connect()
    
    # Query most recent story update time
    query = "SELECT TOP 1 c.last_updated FROM c"
    if category:
        query += f" WHERE c.category = '{category}'"
    query += " ORDER BY c.last_updated DESC"
    
    results = list(cosmos_service.story_clusters_container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    
    last_modified = results[0]['last_updated'] if results else datetime.now(timezone.utc).isoformat()
    
    return {
        "last_modified": last_modified,
        "category": category
    }
```

#### 3.2 Update iOS Polling Logic

**`Newsreel App/Newsreel/Views/MainAppView.swift`:**
```swift
class FeedViewModel: ObservableObject {
    // ...existing properties...
    private var lastKnownUpdate: Date?
    private var pollInterval: TimeInterval = 30 // Start at 30s
    
    func startPolling(apiService: APIService) {
        stopPolling()
        
        pollingTimer = Task {
            while !Task.isCancelled {
                // Adaptive interval (30s → 2min if no updates)
                try? await Task.sleep(nanoseconds: UInt64(pollInterval * 1_000_000_000))
                guard !Task.isCancelled else { break }
                
                await checkForNewStories(apiService: apiService)
            }
        }
    }
    
    private func checkForNewStories(apiService: APIService) async {
        do {
            // Check last-modified first (lightweight)
            let lastModified = try await apiService.getFeedLastModified(category: selectedCategory)
            
            // Compare with our known timestamp
            if let lastKnown = lastKnownUpdate, lastModified <= lastKnown {
                // No updates - increase poll interval
                pollInterval = min(pollInterval * 1.2, 120) // Max 2 minutes
                log.logFeedOperation("No new stories, backing off to \(Int(pollInterval))s")
                return
            }
            
            // Updates available!
            lastKnownUpdate = lastModified
            pollInterval = 30 // Reset to 30s
            
            await MainActor.run {
                newStoriesAvailable = true
            }
            
            log.logFeedOperation("New stories detected!")
            
        } catch {
            log.logError(error, context: "checkForNewStories")
        }
    }
}
```

**Expected Behavior:**
```
Time 0:00 - Poll (30s interval)
Time 0:30 - Poll - No updates → interval = 36s
Time 1:06 - Poll - No updates → interval = 43s
Time 1:49 - Poll - No updates → interval = 52s
Time 2:41 - Poll - No updates → interval = 62s
Time 3:43 - Poll - No updates → interval = 74s
Time 4:57 - Poll - No updates → interval = 89s
Time 6:26 - Poll - UPDATES FOUND → interval = 30s (reset)
```

**Impact:** Reduces API calls from ~120/hour to ~15/hour

---

## **PHASE 4: IMPROVED CATEGORIZATION** 🟢 MEDIUM PRIORITY
**Timeline**: 1 day  
**Effort**: Medium  
**Impact**: Better content discovery

### Current Issues:
- Keyword matching too simplistic
- No confidence scores
- No multi-category support
- "Technology" catches too many business/politics stories

### Solution: Multi-Signal Categorization

**Update `Azure/functions/shared/utils.py`:**
```python
from typing import Tuple, Dict, List
import re

def categorize_article_enhanced(title: str, description: str, url: str, 
                                source: str) -> Tuple[str, float, Dict[str, float]]:
    """
    Enhanced categorization with confidence scoring
    
    Returns:
        (primary_category, confidence, all_scores)
    """
    text = f"{title} {description}".lower()
    
    # Multi-signal scoring
    url_score = _score_by_url(url)
    keyword_score = _score_by_keywords(text)
    source_score = _score_by_source(source)
    
    # Combine scores (weighted average)
    combined_scores = {}
    for category in ['politics', 'tech', 'business', 'sports', 'world', 'science', 'health']:
        combined_scores[category] = (
            url_score.get(category, 0) * 0.4 +
            keyword_score.get(category, 0) * 0.4 +
            source_score.get(category, 0) * 0.2
        )
    
    # Get top category
    if not combined_scores or max(combined_scores.values()) < 0.3:
        return 'general', 0.0, combined_scores
    
    primary_category = max(combined_scores, key=combined_scores.get)
    confidence = combined_scores[primary_category]
    
    # Log categorization decision
    logger.log_categorization(
        article_id="",  # Will be set by caller
        title=title,
        url=url,
        category=primary_category,
        score=confidence,
        method="multi-signal"
    )
    
    return primary_category, confidence, combined_scores


def _score_by_url(url: str) -> Dict[str, float]:
    """Score categories based on URL patterns"""
    url_lower = url.lower()
    scores = {}
    
    # URL-based hints (strong signal)
    url_patterns = {
        'sports': ['sports', 'espn', 'sport', 'nba', 'nfl', 'mlb', 'soccer', 'football'],
        'politics': ['politics', 'political', 'elections', 'government', 'white-house'],
        'tech': ['tech', 'technology', 'techcrunch', 'wired', 'verge', 'arstechnica'],
        'business': ['business', 'markets', 'finance', 'bloomberg', 'wsj', 'economy'],
        'world': ['world', 'international', 'global'],
        'science': ['science', 'research', 'nature', 'scientific'],
        'health': ['health', 'medical', 'medicine', 'wellness']
    }
    
    for category, patterns in url_patterns.items():
        if any(pattern in url_lower for pattern in patterns):
            scores[category] = 1.0
    
    return scores


def _score_by_keywords(text: str) -> Dict[str, float]:
    """Score categories based on weighted keywords"""
    # ... existing keyword logic but return scores dict ...
    scores = {}
    
    for category, keyword_tiers in categories.items():
        score = 0
        score += sum(3 for keyword in keyword_tiers.get('high', []) if keyword in text)
        score += sum(2 for keyword in keyword_tiers.get('medium', []) if keyword in text)
        score += sum(1 for keyword in keyword_tiers.get('low', []) if keyword in text)
        
        # Normalize to 0-1
        scores[category] = min(score / 10.0, 1.0)
    
    return scores


def _score_by_source(source: str) -> Dict[str, float]:
    """Score categories based on known source specializations"""
    source_categories = {
        'espn': {'sports': 1.0},
        'techcrunch': {'tech': 1.0},
        'bloomberg': {'business': 0.8, 'tech': 0.2},
        'politico': {'politics': 1.0},
        'nature': {'science': 1.0},
        # ... add more source mappings ...
    }
    
    return source_categories.get(source.lower(), {})
```

**Expected Improvement:**
```
Before: "Apple announces new privacy policy"
  → Category: tech (keyword: "apple")
  → Incorrect (should be: politics/business)

After:  "Apple announces new privacy policy"
  → URL: /politics/privacy → politics: 1.0
  → Keywords: policy (medium) → politics: 0.4, business: 0.2
  → Combined: politics: 0.68, business: 0.16, tech: 0.08
  → Category: politics (confidence: 68%)
  → ✅ Correct!
```

---

## **PHASE 5: UPDATE INTELLIGENCE** 🔵 HIGH PRIORITY
**Timeline**: 1 day  
**Effort**: High  
**Impact**: Better feed freshness

### Problem:
When a new source is added to existing story:
- Should it bump to top of feed?
- Or just add as additional source?

### Current Behavior:
```
Time 10:00 - Story created: "Trump announces policy" (1 source)
Time 10:15 - New source added: "Trump announces policy" (2 sources)
  → last_updated: 10:15
  → Feed position: Top (bumps existing stories)
  
Problem: Minor updates push major news down
```

### Solution: Significance-Based Ranking

**Add to `Azure/functions/function_app.py`:**
```python
def calculate_update_significance(story: Dict, new_article: RawArticle) -> float:
    """
    Calculate how significant an update is
    
    Returns score 0-1:
    - 0.0-0.3: Minor update (just another source)
    - 0.3-0.7: Moderate update (adds new information)
    - 0.7-1.0: Major update (breaking development)
    """
    
    # Factors:
    # 1. Time since last update
    last_updated = datetime.fromisoformat(story['last_updated'].replace('Z', '+00:00'))
    time_delta = datetime.now(timezone.utc) - last_updated
    
    # Fresh story (<1 hour) - new source = minor update
    if time_delta.total_seconds() < 3600:
        time_factor = 0.2
    # Older story (>6 hours) - new source = significant
    elif time_delta.total_seconds() > 21600:
        time_factor = 0.8
    else:
        # Linear scale between 1-6 hours
        time_factor = 0.2 + (time_delta.total_seconds() - 3600) / 18000 * 0.6
    
    # 2. Title divergence (new info vs same info)
    existing_title = story.get('title', '')
    title_similarity = calculate_text_similarity(existing_title, new_article.title)
    
    # High similarity (>0.8) = same info = minor update
    # Low similarity (<0.5) = new angle = major update
    if title_similarity > 0.8:
        info_factor = 0.2
    elif title_similarity < 0.5:
        info_factor = 0.9
    else:
        info_factor = 0.5
    
    # 3. Source count increase
    current_source_count = len(story.get('source_articles', []))
    
    # 1→2 sources: significance boost
    # 5→6 sources: less significant
    if current_source_count == 1:
        source_factor = 0.8
    elif current_source_count < 5:
        source_factor = 0.5
    else:
        source_factor = 0.3
    
    # Combined score (weighted average)
    significance = (
        time_factor * 0.4 +
        info_factor * 0.4 +
        source_factor * 0.2
    )
    
    logger.debug(
        f"Update significance: {significance:.2f} "
        f"(time={time_factor:.2f}, info={info_factor:.2f}, source={source_factor:.2f})"
    )
    
    return significance


# In clustering function:
if stories:
    # Update existing story
    story = stories[0]
    
    # Calculate significance
    significance = calculate_update_significance(story, article)
    
    # Update timestamp based on significance
    update_data = {
        'source_articles': source_articles,
        'source_count': len(source_articles),
        'last_source_added': article.source,
        'last_source_added_at': datetime.now(timezone.utc).isoformat(),
        'update_significance': significance
    }
    
    # Only bump last_updated if significant
    if significance > 0.5:
        update_data['last_updated'] = datetime.now(timezone.utc).isoformat()
        logger.info(f"✨ Significant update ({significance:.2f}) - bumping to top")
    else:
        logger.info(f"Minor update ({significance:.2f}) - preserving position")
    
    await cosmos_client.update_story_cluster(story_id, category, update_data)
```

**Expected Behavior:**
```
Time 10:00 - Story: "Trump policy" (1 source) - Top of feed
Time 10:15 - Add source: "Trump policy" (2 sources, similar headline)
  → Significance: 0.3 (minor) → Don't bump
  → Feed position: Same (other breaking news stays on top)

Time 16:00 - Add source: "Trump policy UPDATED with reactions" (3 sources, new info)
  → Significance: 0.8 (major) → Bump to top!
  → Feed position: Top (this is a development)
```

---

## 📈 METRICS TO TRACK

After implementation, monitor these metrics:

### Feed Quality Metrics:
```sql
-- Source Diversity (target: >10 unique sources in top 20)
SELECT 
    COUNT(DISTINCT primary_source) as unique_sources,
    COUNT(*) as total_stories
FROM feed_served
WHERE served_at > NOW() - INTERVAL '1 hour'

-- Categorization Confidence (target: >70% average)
SELECT 
    category,
    AVG(confidence) as avg_confidence,
    COUNT(*) as count
FROM articles_categorized
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY category

-- Update Significance Distribution
SELECT 
    CASE 
        WHEN significance < 0.3 THEN 'minor'
        WHEN significance < 0.7 THEN 'moderate'
        ELSE 'major'
    END as update_type,
    COUNT(*) as count
FROM story_updates
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY update_type
```

### Performance Metrics:
```
- API response time (target: <500ms)
- RSS fetch success rate (target: >95%)
- Clustering match rate (target: >60%)
- Summary generation time (target: <2s)
- iOS feed refresh time (target: <1s)
```

---

## 🚀 DEPLOYMENT PLAN

### Phase 1: Deploy Logging (Day 1)
```bash
# Deploy backend
cd Azure/functions
func azure functionapp publish newsreel-func-51689

cd ../api
az containerapp up --name newsreel-api --resource-group newsreel-rg

# Test logging
curl https://newsreel-api.xxx/api/diagnostics/logs | jq
```

### Phase 2: Deploy Feed Diversity (Day 2)
```bash
# Deploy API changes
cd Azure/api
az containerapp up --name newsreel-api --resource-group newsreel-rg

# Monitor source distribution
curl https://newsreel-api.xxx/api/stories/feed | \
  jq '[.[] | .source.name] | group_by(.) | map({source: .[0], count: length})'
```

### Phase 3: Deploy Smart Polling (Day 2)
```bash
# Deploy API endpoint
# Deploy iOS app
# Monitor API call reduction in Application Insights
```

### Phase 4: Deploy Better Categorization (Day 3)
```bash
# Deploy functions
# Monitor categorization confidence
# Review logs for miscategorizations
```

### Phase 5: Deploy Update Intelligence (Day 3)
```bash
# Deploy functions
# Monitor feed freshness vs noise ratio
```

---

## 📊 SUCCESS METRICS

Track weekly to measure improvement:

| Metric | Before | Target | How to Measure |
|--------|--------|--------|----------------|
| Unique sources in top 20 | 3-5 | 12-15 | Feed API logs |
| Categorization accuracy | ~60% | >85% | Manual review + confidence scores |
| API calls per hour | ~120 | ~20 | Application Insights |
| Feed diversity score | 0.25 | >0.65 | Shannon entropy of source distribution |
| User session length | 2min | 5min | Firebase Analytics |

---

## 🎓 LEARNING OPPORTUNITIES

### After Phase 1 (Logging):
- Review Application Insights dashboards
- Identify slowest operations
- Find categorization errors

### After Phase 2 (Diversity):
- Calculate Shannon entropy of feed
- User feedback on source variety
- A/B test diversity levels

### After Phase 3 (Polling):
- Monitor API cost reduction
- Measure battery impact
- Track notification delay

### After Phase 4 (Categorization):
- Review miscategorized stories
- Build training dataset for future ML model
- Add more source-category mappings

### After Phase 5 (Updates):
- Analyze feed freshness
- Balance major news vs noise
- User engagement per story age

---

## 🔮 FUTURE ENHANCEMENTS (Post-MVP)

### Machine Learning Categorization
- Train classifier on labeled dataset
- Use BERT/DistilBERT for semantic understanding
- Deploy as Azure ML endpoint

### Personalization Engine
- User interest modeling
- Collaborative filtering
- Topic diversification

### Real-time Push
- Replace polling with WebSockets/SignalR
- Instant breaking news delivery
- Cost: ~$30-50/month for SignalR

### Advanced Clustering
- Use sentence transformers for semantic similarity
- Multi-document summarization
- Timeline extraction (developing story tracking)

---

## 💰 COST IMPACT

All phases within [[memory:6046921]] $150/month Azure budget:

| Phase | Cost Impact |
|-------|-------------|
| Phase 1 (Logging) | +$5/month (Application Insights) |
| Phase 2 (Diversity) | $0 (compute only) |
| Phase 3 (Polling) | -$10/month (fewer API calls) |
| Phase 4 (Categorization) | +$2/month (slightly more compute) |
| Phase 5 (Updates) | $0 (compute only) |
| **TOTAL** | **-$3/month** (net savings!) |

---

## 📞 NEXT STEPS

1. **Review this roadmap** - Any questions? Priorities to adjust?
2. **Phase 1 Implementation** - Deploy logging today
3. **Monitor for 24 hours** - See what logs reveal
4. **Phase 2 Implementation** - Fix source diversity tomorrow
5. **Iterate** - Use logs to guide remaining phases

---

**Questions? Let's discuss specific phases or dive deeper into any section.**

