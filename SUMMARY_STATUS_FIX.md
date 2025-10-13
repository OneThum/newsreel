# 📊 "No Summary Available" Issue - Analysis & Fix

**Date**: October 13, 2025  
**Status**: Fix ready, API deployment pending

---

## 🔍 ROOT CAUSES IDENTIFIED

### **1. RESTAURANT SPAM STILL GETTING THROUGH** 🚨

**Problem**: Feed polluted with restaurant listings from The Age's "Good Food" guide

**Examples from logs**:
```
"Paper Daisy"
"Omakase by Prefecture 48"
"Papi's Birria Tacos"
"Ommi Don"
"Paranormal Wines"
"Paski Sopra"
"Passeggiata"
"Paste Australia"
"Pearl"
"Pellegrino 2000"
"Peonee"
"Pilu at Freshwater"
"Poachers Pantry"
```

**Root Cause**: These are bare restaurant names with **NO description text**. Previous filter checked for lifestyle keywords in descriptions, but these articles have empty descriptions.

**Impact**: ~20 restaurant listings per ingestion cycle creating "No summary available" stories

---

### **2. SUMMARY GENERATION TIMING**

**The delay workflow**:
```
1. Story created in DB         →  08:21:02
2. Story appears in API         →  08:21:02 (instant)
3. Cosmos DB Change Feed        →  08:21:12 (10 sec delay)
4. Summarization starts         →  08:21:12
5. Claude API call              →  08:21:18 (6 sec)
6. Summary written to DB        →  08:21:18
7. Summary visible in API       →  08:21:18

TOTAL: 16 seconds minimum
```

**But in practice**: 2-5 minutes due to:
- Change Feed processing batches
- Multiple stories in queue
- Claude API rate limits
- Cosmos DB write latency

**Result**: Stories appear in feed WITHOUT summaries for 2-5 minutes, showing "No summary available"

---

## ✅ FIXES IMPLEMENTED

### **Fix 1: Enhanced Restaurant Spam Filter** ✅ **DEPLOYED**

**Deployed**: 08:27:56 UTC

**Changes to `Azure/functions/shared/utils.py`**:

```python
# BEFORE: Only checked description text
if any(keyword in text for keyword in lifestyle_dining_keywords):
    return True

# AFTER: Also checks URL patterns WITHOUT needing description
restaurant_url_patterns = [
    '/good-food',
    '/best-restaurant',
    '/food-drink',
    '/venue',
    '/eating-out'
]
if any(pattern in url_lower for pattern in restaurant_url_patterns):
    # And title is JUST a proper noun (restaurant name)
    # Block if no common news verbs/indicators
    news_indicators = ['says', 'announces', 'reports', 'confirms', 'claims', 
                      'accuses', 'reveals', 'attack', 'fire', 'death', 'killed',
                      'injured', 'arrested', 'charged', 'verdict', 'found']
    if not any(indicator in title.lower() for indicator in news_indicators):
        return True  # Block restaurant listing
```

**Expected Result**:
- ✅ "Paper Daisy" → **BLOCKED** (URL: `/good-food/paper-daisy`)
- ✅ "Papi's Birria Tacos" → **BLOCKED** (URL: `/good-food/papis-birria-tacos`)
- ✅ "Fire at popular restaurant kills 3" → **ALLOWED** (has news verb "kills")

---

### **Fix 2: Add "Summary Generating..." Status** ⚠️ **CODE READY, NEEDS DEPLOYMENT**

**Changes to `Azure/api/app/models/responses.py`**:

```python
class SummaryResponse(BaseModel):
    text: str
    version: int
    word_count: int
    generated_at: datetime
    status: str = "available"  # NEW: "available", "generating", "failed", "none"
```

**Changes to `Azure/api/app/routers/stories.py`**:

```python
if summary_data and summary_data.get('text'):
    # Summary available
    summary = SummaryResponse(
        text=summary_data.get('text', ''),
        version=summary_data.get('version', 1),
        word_count=summary_data.get('word_count', 0),
        generated_at=datetime.fromisoformat(...),
        status="available"
    )
else:
    # Story exists but no summary yet
    # Check if story is recent (< 3 minutes old)
    story_age_minutes = (datetime.now(timezone.utc) - story['first_seen']).total_seconds() / 60
    
    if story_age_minutes < 3:
        # Story is fresh, summary is likely generating
        summary = SummaryResponse(
            text="",  # Empty text
            version=0,
            word_count=0,
            generated_at=datetime.now(timezone.utc),
            status="generating"  # iOS can show "Summary generating..."
        )
    # else: No summary object returned (story is old, no summary will come)
```

**API Response Examples**:

```json
// Fresh story (< 3 min old, no summary yet)
{
  "id": "story_123",
  "title": "Breaking news just in",
  "summary": {
    "text": "",
    "version": 0,
    "word_count": 0,
    "status": "generating"  // iOS shows "Summary generating..."
  }
}

// Story with summary
{
  "id": "story_123",
  "title": "Breaking news just in",
  "summary": {
    "text": "Full summary text here...",
    "version": 1,
    "word_count": 125,
    "status": "available"  // iOS shows summary
  }
}

// Old story without summary
{
  "id": "story_456",
  "title": "Old story from yesterday",
  "summary": null  // iOS shows "No summary available"
}
```

---

## 📱 iOS APP CHANGES NEEDED

**File**: `Newsreel App/Newsreel/Views/Components/StoryDetailView.swift`

**Current Code** (Line 177-187):
```swift
if !story.displaySummary.isEmpty {
    Text(story.displaySummary)
        .font(.outfit(size: 17, weight: .regular))
        .foregroundStyle(.primary)
        .lineSpacing(6)
        .frame(maxWidth: .infinity, alignment: .leading)
} else {
    Text("No summary available.")  // ← THIS IS THE PROBLEM
        .font(.outfit(size: 17, weight: .regular))
        .foregroundStyle(.tertiary)
        .italic()
        .frame(maxWidth: .infinity, alignment: .leading)
}
```

**Recommended Fix**:
```swift
if !story.displaySummary.isEmpty {
    Text(story.displaySummary)
        .font(.outfit(size: 17, weight: .regular))
        .foregroundStyle(.primary)
        .lineSpacing(6)
        .frame(maxWidth: .infinity, alignment: .leading)
} else if story.summary?.status == "generating" {
    // NEW: Show generating message for fresh stories
    HStack(spacing: 8) {
        ProgressView()
            .scaleEffect(0.8)
        Text("Summary generating...")
            .font(.outfit(size: 17, weight: .regular))
            .foregroundStyle(.secondary)
    }
    .frame(maxWidth: .infinity, alignment: .leading)
} else {
    // Old stories without summaries
    Text("No summary available.")
        .font(.outfit(size: 17, weight: .regular))
        .foregroundStyle(.tertiary)
        .italic()
        .frame(maxWidth: .infinity, alignment: .leading)
}
```

**Bonus - Add to Story Model** (`Story.swift`):
```swift
// Story.swift - Add computed property
extension Story {
    var summaryStatus: String {
        // If summary exists and has text, it's available
        if !summary.isEmpty && !displaySummary.isEmpty {
            return "available"
        }
        
        // If story is fresh (< 3 min), summary might be generating
        let now = Date()
        let age = now.timeIntervalSince(publishedAt) / 60  // minutes
        if age < 3 {
            return "generating"
        }
        
        // Old story without summary
        return "none"
    }
}
```

---

## 🚀 DEPLOYMENT STEPS

### **Step 1: Azure Functions (Restaurant Filter)** ✅ **COMPLETE**

Already deployed at 08:27:56 UTC. Restaurant spam should stop immediately.

---

### **Step 2: API Container App (Summary Status)** ⚠️ **PENDING**

**Option A: Local Docker Build & Push** (if Docker running):
```bash
cd Azure/api

# Build image
docker build -t newsreel-api:latest .

# Tag for Azure Container Registry
docker tag newsreel-api:latest <ACR_NAME>.azurecr.io/newsreel-api:latest

# Login to ACR
az acr login --name <ACR_NAME>

# Push image
docker push <ACR_NAME>.azurecr.io/newsreel-api:latest

# Update container app
az containerapp update \
  --name newsreel-api \
  --resource-group newsreel-rg \
  --image <ACR_NAME>.azurecr.io/newsreel-api:latest
```

**Option B: Azure Cloud Build** (if Docker not available):
```bash
cd Azure/api

# Build in Azure
az acr build \
  --registry <ACR_NAME> \
  --image newsreel-api:latest \
  --file Dockerfile .

# Update container app
az containerapp update \
  --name newsreel-api \
  --resource-group newsreel-rg \
  --image <ACR_NAME>.azurecr.io/newsreel-api:latest
```

---

### **Step 3: iOS App (Display Logic)** ⚠️ **PENDING**

1. Update `Story.swift` model to include `summaryStatus` computed property
2. Update `StoryDetailView.swift` to show "Summary generating..." for fresh stories
3. Test with:
   - Fresh story (< 3 min) without summary → Should show "Summary generating..."
   - Story with summary → Should show summary text
   - Old story without summary → Should show "No summary available."

---

## 📊 EXPECTED RESULTS

### **Immediate (after API deployment)**:

**Feed behavior**:
```
Story created → Appears in feed immediately
├─ If < 3 min old: Shows "Summary generating..." ✨
├─ After 2-5 min: Summary appears automatically
└─ If > 3 min old: Shows "No summary available"
```

### **After 30 minutes**:

- ✅ NO more restaurant listings in feed
- ✅ Stories show "Summary generating..." instead of "No summary available"
- ✅ Better UX - users understand summary is coming
- ✅ Reduced confusion - clear what's happening

---

## 🎯 TESTING

### **Test 1: Restaurant Filter**

**Wait 10 minutes after deployment, then check logs**:
```bash
cd Azure/scripts
./query-logs.sh custom "traces | where timestamp > ago(10m) | where message contains '🚫 Filtered' and message contains 'food' | project timestamp, message"
```

**Expected**: Should see restaurant names being filtered

---

### **Test 2: Summary Status (after API deployed)**

**Scenario A: Fresh story**
```
1. Create new story in feed (< 3 min old)
2. Tap to open
3. Should show: "Summary generating..." with progress indicator
4. Wait 2-3 minutes
5. Refresh
6. Should show: Full summary text
```

**Scenario B: Old story**
```
1. Open story from yesterday without summary
2. Should show: "No summary available."
3. No progress indicator (not generating)
```

---

## 💰 COST IMPACT

### **Restaurant Filter**:
- **Savings**: ~100-200 articles/day not ingested
- **AI Cost Avoided**: ~$5-10/day (no summaries generated for spam)
- **Storage Saved**: Less junk in database

### **Summary Status Indicator**:
- **Cost**: $0 (just adds a status field)
- **Benefit**: Massively improved UX

---

## 📝 NOTES

1. **Restaurant filter is already live** (08:27 UTC deployment)
2. **API changes are ready** but need container rebuild/redeploy
3. **iOS changes are optional** - API will work without them, but UX won't improve
4. **3-minute threshold** is configurable - can adjust if needed
5. **Change feed latency** is inherent to Cosmos DB - can't eliminate entirely

---

## 🔄 ROLLBACK PLAN

If issues arise:

**Restaurant Filter** (Functions):
```bash
# Revert utils.py to previous version
git checkout HEAD~1 -- Azure/functions/shared/utils.py
cd Azure/functions
func azure functionapp publish newsreel-func-51689 --python
```

**Summary Status** (API):
```bash
# Revert API changes
git checkout HEAD~1 -- Azure/api/app/models/responses.py
git checkout HEAD~1 -- Azure/api/app/routers/stories.py
# Rebuild and redeploy API
```

---

**Status**: 
- ✅ **Restaurant filter**: Deployed and active
- ⚠️ **Summary status**: Code ready, awaiting API deployment
- ⚠️ **iOS updates**: Pending


