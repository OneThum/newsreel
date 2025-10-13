# Story Timestamp Architecture

**Critical System Component**  
**Last Updated**: 2025-10-13

---

## 🎯 Overview

Newsreel tracks **two distinct timestamps** for every story:

1. **`first_seen`** - When the news broke (story created)
2. **`last_updated`** - When the story last changed (sources added, status changed)

These timestamps are **fundamental** to the breaking news system.

---

## ⏰ The Two Timestamps

### **1. `first_seen` - When News Broke**

**Definition:**
- Set when story cluster is **first created**
- **NEVER changes** after creation
- Represents when this news event entered our system

**Use Cases:**
```python
# Sort feed by breaking news time
stories.sort(key=lambda s: s['first_seen'], reverse=True)

# Check story age
age = now - datetime.fromisoformat(story['first_seen'])

# Determine if newly created
if time_since_first < timedelta(minutes=30):
    status = StoryStatus.BREAKING
```

**Example Timeline:**
```
06:00:00 - Story created (first_seen = 06:00:00)
06:05:00 - Source added (first_seen = 06:00:00) ← unchanged
06:10:00 - Source added (first_seen = 06:00:00) ← unchanged
06:15:00 - Source added (first_seen = 06:00:00) ← unchanged
```

---

### **2. `last_updated` - When Story Changed**

**Definition:**
- Set to `now()` when story is **created**
- **Updated** whenever story **gains sources** or **changes status**
- **NOT updated** when summaries are generated (critical!)
- Represents the last time this story had **new information**

**Use Cases:**
```python
# Detect actively developing stories
time_since_update = now - datetime.fromisoformat(story['last_updated'])

# Keep BREAKING if actively updated
if is_gaining_sources and time_since_update < timedelta(minutes=30):
    status = StoryStatus.BREAKING

# Transition BREAKING → VERIFIED if stale
if time_since_update >= timedelta(minutes=90):
    status = StoryStatus.VERIFIED

# Show "UPDATED" badge in iOS
if last_updated - first_seen >= timedelta(minutes=30):
    show_updated_badge = True
```

**Example Timeline:**
```
06:00:00 - Story created (last_updated = 06:00:00)
06:05:00 - Source added  (last_updated = 06:05:00) ← updated
06:10:00 - Source added  (last_updated = 06:10:00) ← updated
06:15:00 - Summary generated (last_updated = 06:10:00) ← NOT updated!
06:20:00 - No new sources  (last_updated = 06:10:00) ← unchanged
```

---

## 🔄 How Timestamps Are Managed

### **Story Creation** (`StoryClusteringChangeFeed`)

```python
# When creating a NEW story cluster
story = StoryCluster(
    id=story_id,
    category=article.category,
    title=article.title,
    status=StoryStatus.MONITORING,
    verification_level=1,
    first_seen=article.published_at,        # ← Set once, never changes
    last_updated=datetime.now(timezone.utc), # ← Will be updated on changes
    source_articles=[article.id],
    # ...
)
```

### **Story Update** (`StoryClusteringChangeFeed`)

```python
# When ADDING SOURCES to existing story
updates = {
    'source_articles': source_articles,
    'verification_level': verification_level,
    'status': status,
    'last_updated': datetime.now(timezone.utc).isoformat(),  # ← UPDATE timestamp
    'update_count': story.get('update_count', 0) + 1
}
# NOTE: first_seen is NOT in updates - remains unchanged!

await cosmos_client.update_story_cluster(story['id'], story['category'], updates)
```

### **Summary Generation** (`SummarizationChangeFeed`)

```python
# When generating AI summary
await cosmos_client.update_story_cluster(
    story_data['id'],
    story_data['category'],
    {'summary': summary}
)
# NOTE: Do NOT update last_updated - that should only change when sources are added!
# Updating last_updated here makes old stories appear as "Just now"
```

**Why this matters:**
- Summaries are generated hours after story creation
- If we updated `last_updated`, old stories would appear fresh
- Would break the feed sorting and "Just now" timestamps

---

## 📊 Critical Use Cases

### **1. Feed Sorting - "When News Broke"**

**Question:** Should feed sort by `first_seen` or `last_updated`?

**Answer:** **`first_seen`** (with status boost)

**Why:**
- Users want to see when news **broke**, not when it was last updated
- A story from 2 hours ago shouldn't jump to top just because a new source was added
- BREAKING stories get priority boost, but within that, sort by `first_seen`

**Implementation:**
```python
# In cosmos_service.py (API)
def story_sort_key(story):
    primary_time = story.get('first_seen', '')  # ← Sort by breaking news time
    
    # Status weight (BREAKING gets priority)
    status_weights = {
        'BREAKING': 1000,
        'DEVELOPING': 500,
        'VERIFIED': 100,
        'MONITORING': 10
    }
    status = story.get('status', 'VERIFIED')
    status_weight = status_weights.get(status, 50)
    
    return (primary_time, status_weight, source_count)
```

---

### **2. Breaking News Detection - "Is Story Active?"**

**Question:** How do we know if a story is actively developing?

**Answer:** Compare `last_updated` to now

**Why:**
- A 2-hour-old story (`first_seen`) can still be BREAKING if it just gained a source
- Need to detect **momentum** (new sources arriving) vs **stale** (no updates)

**Implementation:**
```python
# In story_clustering_changefeed
last_updated_str = story.get('last_updated', story['first_seen'])
last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
time_since_update = now - last_updated

# Story is actively developing if gaining sources AND recently updated
if is_gaining_sources and time_since_update < timedelta(minutes=30):
    status = StoryStatus.BREAKING
```

**Example - Gaza Hostages:**
```
Day 1 - 08:00: Story created (first_seen = 08:00)
Day 1 - 10:00: 3 sources (BREAKING)
Day 1 - 12:00: No new updates, transitions to VERIFIED

Day 2 - 14:00: NEW development - hostages released!
Day 2 - 14:05: Gains 2 new sources (last_updated = 14:05)
Day 2 - 14:07: Monitor runs, sees recent update → Back to BREAKING!

Without last_updated tracking, we couldn't detect this!
```

---

### **3. Status Transitions - "When to Move to VERIFIED?"**

**Question:** When should BREAKING stories become VERIFIED?

**Answer:** After **90 minutes without updates** (`last_updated`)

**Why:**
- Not based on age (`first_seen`) - story can be old but still developing
- Based on **activity** - if no new sources for 90 min, story is stable

**Implementation:**
```python
# In BreakingNewsMonitor
for story in breaking_stories:
    last_updated_str = story.get('last_updated', story['first_seen'])
    last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
    time_since_update = now - last_updated
    
    # Transition if NO NEW UPDATES for 90 minutes
    if time_since_update >= timedelta(minutes=90):
        await cosmos_client.update_story_cluster(
            story['id'],
            story['category'],
            {
                'status': StoryStatus.VERIFIED.value,
                'last_updated': now.isoformat()  # ← Mark transition time
            }
        )
```

---

### **4. iOS "UPDATED" Badge**

**Question:** When should iOS show the "UPDATED" badge?

**Answer:** When `last_updated` is significantly after `first_seen`

**Implementation (iOS Swift):**
```swift
var isRecentlyUpdated: Bool {
    guard let lastUpdated = lastUpdated else { return false }
    let timeSincePublished = lastUpdated.timeIntervalSince(publishedAt)
    // Consider it "updated" if last update was at least 30 minutes after publication
    return timeSincePublished >= 1800 // 30 minutes
}
```

**Example:**
```
Story published (first_seen):   06:00:00
New source added (last_updated): 06:05:00
Difference: 5 minutes → No badge

Story published (first_seen):   06:00:00
New source added (last_updated): 06:45:00
Difference: 45 minutes → "UPDATED" badge shows!
```

---

### **5. iOS "Just now" vs "5m ago"**

**Question:** Which timestamp for "time ago" display?

**Answer:** Depends on update status

**Implementation (iOS Swift):**
```swift
var timeAgo: String {
    // Determine which timestamp to use
    let referenceDate: Date
    if isRecentlyUpdated, let lastUpdated = lastUpdated {
        // Use lastUpdated for stories with UPDATED badge
        referenceDate = lastUpdated
    } else {
        // Use publishedAt (first_seen) for all other stories
        referenceDate = publishedAt
    }
    
    let components = calendar.dateComponents([.minute, .hour, .day], from: referenceDate, to: now)
    
    if let minute = components.minute, minute > 0 {
        return minute == 1 ? "1m ago" : "\(minute)m ago"
    } else {
        return "Just now"
    }
}
```

**Why this matters:**
- Prevents old stories from showing "Just now" after updates
- Shows accurate time for breaking news
- Shows update time for developing stories with "UPDATED" badge

---

## 🐛 Common Bugs & Fixes

### **Bug #1: Old Stories Showing "Just now"**

**Problem:**
```python
# WRONG: Updating last_updated when generating summary
await cosmos_client.update_story_cluster(
    story_id,
    category,
    {
        'summary': summary,
        'last_updated': datetime.now(timezone.utc).isoformat()  # ❌ DON'T DO THIS
    }
)
```

**Result:**
- Story from 3 hours ago
- Summary generated now
- `last_updated` set to now
- iOS shows "Just now" for 3-hour-old story ❌

**Fix:**
```python
# CORRECT: Don't update last_updated when generating summary
await cosmos_client.update_story_cluster(
    story_id,
    category,
    {'summary': summary}  # ← Only update summary, not timestamp
)
```

---

### **Bug #2: Stories Never Transitioning from BREAKING**

**Problem:**
```python
# WRONG: Using first_seen for transition logic
time_since_first = now - first_seen
if time_since_first >= timedelta(minutes=90):
    status = StoryStatus.VERIFIED  # ❌ Wrong!
```

**Result:**
- Gaza hostage story created yesterday
- NEW developments happening now
- Transitions to VERIFIED because it's old ❌
- Should stay BREAKING because actively updating ✅

**Fix:**
```python
# CORRECT: Use last_updated for transition logic
time_since_update = now - last_updated
if time_since_update >= timedelta(minutes=90):
    status = StoryStatus.VERIFIED  # ✅ Correct!
```

---

### **Bug #3: Feed Sorted by Update Time**

**Problem:**
```python
# WRONG: Sorting by last_updated
stories.sort(key=lambda s: s['last_updated'], reverse=True)
```

**Result:**
- Old story gets new source at 14:00
- Jumps to top of feed
- Pushes actual breaking news down ❌

**Fix:**
```python
# CORRECT: Sort by first_seen (with status weight)
stories.sort(key=lambda s: (s['status_weight'], s['first_seen']), reverse=True)
```

---

## 📋 Timestamp Rules

### **✅ DO:**

1. **Set `first_seen` once** - When story is created
2. **Update `last_updated`** - When sources are added
3. **Update `last_updated`** - When status explicitly changes (via monitor)
4. **Use `first_seen`** - For feed sorting (when news broke)
5. **Use `last_updated`** - For detecting active development
6. **Use `last_updated`** - For BREAKING → VERIFIED transitions
7. **Compare both** - For iOS "UPDATED" badge logic

### **❌ DON'T:**

1. **DON'T update `first_seen`** - Ever, after creation
2. **DON'T update `last_updated`** - When generating summaries
3. **DON'T update `last_updated`** - When generating headlines
4. **DON'T update `last_updated`** - For any background processing
5. **DON'T sort by `last_updated`** - Use `first_seen` instead
6. **DON'T use `first_seen`** - For status transitions

---

## 🔍 Debugging Timestamps

### **Check Current Timestamps:**

```bash
cd Azure/scripts

# See story timestamps
./query-logs.sh custom "traces | where timestamp > ago(30m) | where message contains 'Story Cluster' | project timestamp, message | take 20"

# Look for patterns like:
# Story Cluster: updated - story_xxx [BREAKING] | {..., "first_seen": "2025-10-13T06:00:00Z", ...}
```

### **Verify Timestamp Updates:**

```bash
# Check if last_updated is being set on source additions
./query-logs.sh custom "traces | where timestamp > ago(30m) | where message contains 'Updated story cluster' | project timestamp, message"

# Should see frequent updates when articles are clustering
```

### **Monitor for Timestamp Bugs:**

```bash
# Check if summaries are incorrectly updating last_updated
./query-logs.sh custom "traces | where timestamp > ago(1h) | where message contains 'summary' and message contains 'last_updated' | project timestamp, message"

# Should see ZERO results - summaries shouldn't update last_updated!
```

---

## 💡 Why Two Timestamps Matter

### **Single Timestamp Problems:**

If we only had ONE timestamp:

❌ **Can't distinguish new stories from updated stories**
- All stories look the same age
- No way to show "UPDATED" badges
- No way to detect story momentum

❌ **Can't properly sort feed**
- Sort by creation: Updated stories buried
- Sort by update: Old stories jump to top

❌ **Can't detect active development**
- Old story getting new sources looks stale
- Can't keep it as BREAKING

❌ **Can't show accurate "time ago"**
- "Just now" for 3-hour-old story after summary
- Confuses users about news recency

### **Two Timestamp Benefits:**

✅ **Clear story lifecycle**
- `first_seen`: When it happened
- `last_updated`: When we learned more

✅ **Proper feed sorting**
- Sort by breaking news time (`first_seen`)
- Boost actively developing stories (`last_updated`)

✅ **Accurate status management**
- Promote based on recency (`first_seen`)
- Transition based on activity (`last_updated`)

✅ **Better UX**
- Show when news broke
- Show when story evolved
- Clear "UPDATED" indicators

---

## 🎯 Summary

### **The Two Timestamps:**

| Timestamp | Purpose | Changes? | Used For |
|-----------|---------|----------|----------|
| **`first_seen`** | When news broke | **NEVER** | Feed sorting, story age, initial BREAKING promotion |
| **`last_updated`** | When story changed | **YES** (on source add/status change) | Active development detection, status transitions, "UPDATED" badges |

### **Golden Rule:**

> **`first_seen` = When it happened**  
> **`last_updated` = When we learned more**

---

**Both timestamps are critical to making Newsreel's breaking news system work correctly!**


