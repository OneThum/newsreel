# Badge Logging & Monitoring System ✅

## Overview
Comprehensive logging system implemented to monitor status badge accuracy and track the badging process from backend to frontend display.

## Backend Logging (Azure Functions)

### 1. **Story Cluster Creation/Update** (`function_app.py`)

Every story cluster event now logs the status:

```python
logger.log_story_cluster(
    story_id=story_id,
    action="created",  # or "updated"
    source_count=1,
    status="MONITORING",  # or DEVELOPING, VERIFIED, BREAKING
    category=category,
    fingerprint=fingerprint,
    title=title
)
```

**Log Format:**
```
Story Cluster: created - story_20251013_023252_abc123 [MONITORING]
{
  "event_type": "story_cluster",
  "story_id": "story_20251013_023252_abc123",
  "action": "created",
  "source_count": 1,
  "status": "MONITORING",
  "category": "technology",
  "fingerprint": "abc123",
  "title": "Breaking news story..."
}
```

### 2. **Status Transitions Logged**

The backend logs status changes as stories accumulate sources:

- **1 source** → `MONITORING` (gray badge)
- **2 sources** → `DEVELOPING` (orange badge)
- **3+ sources (within 30min)** → `BREAKING` (red badge)
- **3+ sources (after 30min)** → `VERIFIED` (no badge unless updated)

### 3. **Query Logs**

```bash
# View all story cluster events with status
az monitor app-insights query \
  --app newsreel-insights \
  --resource-group newsreel-rg \
  --analytics-query "traces | where customDimensions.event_type == 'story_cluster' | project timestamp, customDimensions | order by timestamp desc"
```

## iOS App Logging

### 1. **Status Distribution** (`MainAppView.swift`)

When stories are loaded, the app logs the distribution of statuses:

```swift
log.log("📊 Status distribution: MONITORING: 5, DEVELOPING: 3, BREAKING: 1", category: .ui, level: .info)
```

**Example Output:**
```
[19:45:12] [UI] ℹ️ INFO - ✅ Stories loaded successfully: 20 new stories, 20 total
[19:45:12] [UI] ℹ️ INFO - 📊 Status distribution: MONITORING: 12, DEVELOPING: 5, VERIFIED: 2, BREAKING: 1
[19:45:12] [UI] ℹ️ INFO - 🔄 Recently updated stories: 2
```

### 2. **Badge Display Tracking** (`StoryCard.swift`)

Every time a badge is displayed in the UI, it's logged:

```swift
log.log("🏷️ Badge displayed: DEVELOPING for story 'Breaking news about...' (sources: 2)", 
       category: .ui, level: .debug)
```

**Example Output:**
```
[19:45:13] [UI] 🔍 DEBUG - 🏷️ Badge displayed: MONITORING for story 'New tech breakthrough announced by Apple...' (sources: 1)
[19:45:13] [UI] 🔍 DEBUG - 🏷️ Badge displayed: DEVELOPING for story 'Market volatility continues as investors...' (sources: 2)
[19:45:13] [UI] 🔍 DEBUG - 🏷️ Badge displayed: BREAKING for story 'Breaking: Major earthquake strikes region...' (sources: 3)
[19:45:13] [UI] 🔍 DEBUG - 🏷️ Badge displayed: UPDATED for story 'Climate summit reaches agreement...' (sources: 5)
```

### 3. **Updated Stories Tracking**

Stories that show the "UPDATED" badge are logged separately:

```swift
log.log("🔄 Recently updated stories: 2", category: .ui, level: .info)
```

## Monitoring & Accuracy Verification

### Manual Verification

**Check if backend is assigning correct statuses:**
```bash
# Get recent story cluster events
az monitor app-insights query \
  --app newsreel-insights \
  --resource-group newsreel-rg \
  --analytics-query "traces 
    | where timestamp > ago(1h) 
    | extend cd = parse_json(message)
    | where cd.event_type == 'story_cluster' 
    | project timestamp, story_id=cd.story_id, action=cd.action, sources=cd.source_count, status=cd.status, title=cd.title
    | order by timestamp desc" \
  --output table
```

**Expected output:**
```
Timestamp               StoryId                             Action   Sources  Status       Title
--------------------   ---------------------------------   -------  -------  -----------  ---------------------------
2025-10-13T02:45:12Z   story_20251013_024512_abc123      created  1        MONITORING   Breaking: Tech company...
2025-10-13T02:46:30Z   story_20251013_024512_abc123      updated  2        DEVELOPING   Breaking: Tech company...
2025-10-13T02:48:15Z   story_20251013_024512_abc123      updated  3        BREAKING     Breaking: Tech company...
```

### Programmatic Monitoring

**1. Status Distribution Analysis**
```bash
# Check status distribution from backend logs
az monitor app-insights query \
  --app newsreel-insights \
  --resource-group newsreel-rg \
  --analytics-query "traces 
    | where timestamp > ago(24h) 
    | extend cd = parse_json(message)
    | where cd.event_type == 'story_cluster' 
    | summarize count() by tostring(cd.status)
    | order by count_ desc" \
  --output table
```

**2. Status Transition Tracking**
```bash
# Track stories that changed status
az monitor app-insights query \
  --app newsreel-insights \
  --resource-group newsreel-rg \
  --analytics-query "traces 
    | where timestamp > ago(6h) 
    | extend cd = parse_json(message)
    | where cd.event_type == 'story_cluster' and cd.action == 'updated'
    | project timestamp, story_id=cd.story_id, sources=cd.source_count, status=cd.status
    | order by story_id, timestamp asc" \
  --output table
```

**3. Badge Accuracy Verification**

Compare backend status assignments with iOS display:

```bash
# Backend: Check what statuses were assigned
az monitor app-insights query \
  --app newsreel-insights \
  --resource-group newsreel-rg \
  --analytics-query "traces | where customDimensions.event_type == 'story_cluster' | summarize count() by tostring(customDimensions.status)"

# iOS: Check what badges were displayed (from device logs)
# View in Xcode Console or iOS device logs
# Look for "📊 Status distribution" entries
```

### Accuracy Validation Rules

**✅ Correct Badge Assignments:**
- **MONITORING**: `source_count == 1` → Gray badge should display
- **DEVELOPING**: `source_count == 2` → Orange badge should display  
- **BREAKING**: `source_count >= 3` AND `time_since_first < 30min` → Red badge should display
- **VERIFIED**: `source_count >= 3` AND `time_since_first >= 30min` → No badge (unless updated)
- **UPDATED**: `last_updated - published_at >= 30min` → Blue badge should display

**❌ Badge Issues to Watch For:**
- Stories with 2 sources showing MONITORING (should be DEVELOPING)
- Stories with 3+ sources within 30min not showing BREAKING
- Stories with 3+ sources after 30min showing any badge (unless updated)
- "UPDATED" badge showing on recently published stories

## Automated Monitoring Script

Create a cron job or scheduled task to run this validation:

```bash
#!/bin/bash
# validate-badges.sh

echo "=== Badge Status Validation ==="
echo "Checking last 1 hour of activity..."

# Get status distribution from backend
BACKEND_DIST=$(az monitor app-insights query \
  --app newsreel-insights \
  --resource-group newsreel-rg \
  --analytics-query "traces 
    | where timestamp > ago(1h) 
    | extend cd = parse_json(message)
    | where cd.event_type == 'story_cluster' 
    | summarize count() by tostring(cd.status)" \
  --output json | jq -r '.tables[0].rows[] | @tsv')

echo "Backend Status Distribution:"
echo "$BACKEND_DIST"

# Check for potential misassignments
echo ""
echo "Checking for potential issues..."

# Look for stories that should have transitioned but didn't
STALE_MONITORING=$(az monitor app-insights query \
  --app newsreel-insights \
  --resource-group newsreel-rg \
  --analytics-query "traces 
    | where timestamp > ago(1h) 
    | extend cd = parse_json(message)
    | where cd.event_type == 'story_cluster' 
    | where cd.status == 'MONITORING' and cd.source_count > 1
    | count" \
  --output json | jq -r '.tables[0].rows[0][0]')

if [ "$STALE_MONITORING" -gt 0 ]; then
    echo "⚠️ WARNING: Found $STALE_MONITORING stories stuck in MONITORING with 2+ sources"
else
    echo "✅ No stories stuck in MONITORING status"
fi
```

## Benefits

1. **End-to-End Visibility**: Track status from assignment to display
2. **Accuracy Verification**: Compare backend logic with frontend display
3. **Performance Monitoring**: Track status transitions over time
4. **Debugging**: Quickly identify badge display issues
5. **Product Analytics**: Understand status distribution in feed

## Example Investigation Flow

**User reports: "Why is this story showing MONITORING when it has 3 sources?"**

1. **Check Backend Logs**:
   ```bash
   az monitor app-insights query --analytics-query "traces | where customDimensions.story_id == 'story_123' | project timestamp, customDimensions"
   ```
   
2. **Verify Source Count**:
   - Check `source_count` in logs
   - Verify it matches actual sources in Cosmos DB
   
3. **Check Status Logic**:
   - Was it created recently? (BREAKING window)
   - Did it age out? (VERIFIED, no badge)
   
4. **Check iOS Display**:
   - Search device logs for "🏷️ Badge displayed" for that story
   - Verify status matches backend assignment

## Deployment Status

- ✅ Backend logging enhanced with status field
- ✅ iOS app logging added for status distribution
- ✅ iOS app logging added for badge display
- ✅ Azure Functions redeployed
- ✅ iOS app built successfully
- ✅ All logs accessible via Application Insights
- ✅ CLI queries documented for agent automation

## Next Steps

- Monitor logs for 24 hours to establish baseline
- Create automated validation script (above)
- Set up alerts for badge misassignments
- Build dashboard for status distribution trends

The badge system is now fully observable and can be programmatically monitored! 🎉

