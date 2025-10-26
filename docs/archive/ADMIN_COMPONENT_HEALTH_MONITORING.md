# Admin Component Health Monitoring System

**Date**: October 18, 2025  
**Status**: ✅ Implemented and Deployed

## Overview

Added comprehensive component health monitoring to the Admin Dashboard, allowing real-time visibility into the status of each backend component. This helps quickly identify when systems are down or degraded.

## Components Monitored

### 1. **RSS Ingestion** 🔄
- **What it does**: Fetches articles from 121 RSS feeds every 10 seconds
- **Healthy**: Articles fetched within last 2 minutes
- **Degraded**: 2-15 minutes since last fetch
- **Down**: >15 minutes since last fetch
- **Critical**: ✅ Yes - without this, no new content

### 2. **Story Clustering** 🔗
- **What it does**: Groups related articles into stories
- **Healthy**: Stories updated within last 5 minutes
- **Degraded**: 5-30 minutes since last update
- **Down**: >30 minutes since last update
- **Critical**: ✅ Yes - without this, articles don't become stories

### 3. **AI Summarization (Live)** ✨
- **What it does**: Generates summaries via Cosmos DB change feed
- **Healthy**: Summaries generated within last 30 minutes
- **Degraded**: 30 minutes - 2 hours since last summary
- **Down**: >2 hours since last summary
- **Critical**: ⚠️ High Priority - impacts user experience significantly

### 4. **AI Summarization (Backfill)** 🔁
- **What it does**: Catches stories that didn't get summaries
- **Healthy**: All recent stories (48h) have summaries
- **Degraded**: <10 stories missing summaries
- **Down**: ≥10 stories missing summaries
- **Critical**: ⚠️ Medium Priority - secondary system

### 5. **Breaking News Monitor** 🔔
- **What it does**: Manages breaking news transitions and notifications
- **Healthy**: Always (passive monitoring)
- **Degraded**: N/A
- **Down**: Only if database query fails
- **Critical**: ⚠️ Low Priority - nice to have

## Implementation

### Backend (Python/FastAPI)

#### New Models (`Azure/api/app/routers/admin.py`)

```python
class ComponentHealth(BaseModel):
    """Individual component health status"""
    status: str  # "healthy", "degraded", "down"
    message: str
    last_checked: datetime
    response_time_ms: int | None = None

class SystemHealth(BaseModel):
    overall_status: str
    api_health: str
    functions_health: str
    database_health: str
    
    # Detailed component statuses
    rss_ingestion: ComponentHealth | None = None
    story_clustering: ComponentHealth | None = None
    summarization_changefeed: ComponentHealth | None = None
    summarization_backfill: ComponentHealth | None = None
    breaking_news_monitor: ComponentHealth | None = None
```

#### Health Checks Logic

Each component is checked by querying Cosmos DB for recent activity:

**RSS Ingestion**:
```python
# Check if new articles are being ingested
most_recent_article = query("SELECT TOP 1 c.fetched_at FROM c ORDER BY c.fetched_at DESC")
minutes_since_fetch = (now - last_fetch_time).total_seconds() / 60

if minutes_since_fetch < 2:
    status = "healthy"
elif minutes_since_fetch < 15:
    status = "degraded"
else:
    status = "down"
```

**Story Clustering**:
```python
# Check if stories are being updated
recent_story_update = query("SELECT TOP 1 c.last_updated FROM c ORDER BY c.last_updated DESC")
minutes_since_update = (now - last_update_time).total_seconds() / 60

if minutes_since_update < 5:
    status = "healthy"
elif minutes_since_update < 30:
    status = "degraded"
else:
    status = "down"
```

**Summarization Change Feed**:
```python
# Check if summaries are being generated
recent_summary = query("SELECT TOP 1 c.summary.generated_at FROM c WHERE IS_DEFINED(c.summary) ORDER BY c.summary.generated_at DESC")
minutes_since_summary = (now - last_summary_time).total_seconds() / 60

if minutes_since_summary < 30:
    status = "healthy"
elif minutes_since_summary < 120:
    status = "degraded"
else:
    status = "down"
```

### iOS App (Swift/SwiftUI)

#### Updated Models (`Newsreel App/Newsreel/Models/AdminModels.swift`)

```swift
struct ComponentHealth: Codable {
    let status: String  // "healthy", "degraded", "down"
    let message: String
    let lastChecked: Date
    let responseTimeMs: Int?
}

struct SystemHealth: Codable {
    let overallStatus: String
    let apiHealth: String
    let functionsHealth: String
    let databaseHealth: String
    
    // Detailed component statuses
    let rssIngestion: ComponentHealth?
    let storyClustering: ComponentHealth?
    let summarizationChangefeed: ComponentHealth?
    let summarizationBackfill: ComponentHealth?
    let breakingNewsMonitor: ComponentHealth?
}
```

#### New UI Component (`AdminDashboardView.swift`)

```swift
struct ComponentStatusRow: View {
    let label: String
    let icon: String
    let health: ComponentHealth
    
    var statusColor: Color {
        switch health.status {
        case "healthy": return .green
        case "degraded": return .orange
        case "down": return .red
        default: return .gray
        }
    }
    
    var statusIcon: String {
        switch health.status {
        case "healthy": return "checkmark.circle.fill"
        case "degraded": return "exclamationmark.triangle.fill"
        case "down": return "xmark.circle.fill"
        default: return "questionmark.circle.fill"
        }
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                Text(label)
                Spacer()
                HStack(spacing: 4) {
                    Image(systemName: statusIcon)
                        .foregroundStyle(statusColor)
                    Text(health.status.capitalized)
                        .foregroundStyle(statusColor)
                }
            }
            
            Text(health.message)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }
}
```

#### Admin Dashboard Section

```swift
private func componentStatusSection(metrics: AdminMetrics) -> some View {
    DashboardCard(
        title: "Component Health",
        icon: "checkmark.seal.fill",
        color: overallComponentColor(metrics: metrics)
    ) {
        VStack(spacing: 12) {
            if let rssHealth = metrics.systemHealth.rssIngestion {
                ComponentStatusRow(
                    label: "RSS Ingestion",
                    icon: "antenna.radiowaves.left.and.right",
                    health: rssHealth
                )
            }
            
            // ... (other components)
        }
    }
}
```

## Visual Design

### Status Colors
- 🟢 **Green (Healthy)**: Component operating normally
- 🟠 **Orange (Degraded)**: Component running but slow or outdated
- 🔴 **Red (Down)**: Component not functioning

### Status Icons
- ✅ **Checkmark Circle**: Healthy
- ⚠️ **Triangle Warning**: Degraded
- ❌ **X Circle**: Down

### Card Color Logic
The "Component Health" card's color reflects the worst status:
- Red if **any** component is down
- Orange if **any** component is degraded (and none down)
- Green if **all** components are healthy

## API Endpoint

### `/api/admin/metrics` (Enhanced)

**Method**: `GET`  
**Auth**: Admin only (`david@mclauchlan.com`, `dave@onethum.com`)  
**Response**: Enhanced `AdminMetrics` with detailed component health

**Example Response**:
```json
{
  "timestamp": "2025-10-18T19:30:00Z",
  "system_health": {
    "overall_status": "healthy",
    "api_health": "healthy",
    "functions_health": "healthy",
    "database_health": "healthy",
    "rss_ingestion": {
      "status": "healthy",
      "message": "Active - Last fetch 1 min ago",
      "last_checked": "2025-10-18T19:30:00Z",
      "response_time_ms": null
    },
    "story_clustering": {
      "status": "healthy",
      "message": "Active - Last update 2 min ago",
      "last_checked": "2025-10-18T19:30:00Z"
    },
    "summarization_changefeed": {
      "status": "down",
      "message": "Stopped - Last summary 127.3 hours ago",
      "last_checked": "2025-10-18T19:30:00Z"
    },
    "summarization_backfill": {
      "status": "down",
      "message": "43 stories missing summaries",
      "last_checked": "2025-10-18T19:30:00Z"
    },
    "breaking_news_monitor": {
      "status": "healthy",
      "message": "Monitoring 5 breaking stories",
      "last_checked": "2025-10-18T19:30:00Z"
    }
  }
}
```

## Use Cases

### Scenario 1: Summarization Stopped (Today's Issue)
**Before**:
- Users report "No summaries" in app
- Need to manually check database
- Hard to know when it stopped

**After**:
- Admin dashboard shows: "🔴 AI Summarization (Live): Down - Stopped - Last summary 127.3 hours ago"
- Immediately visible that summarization stopped on Oct 13
- Can see backfill status separately

### Scenario 2: RSS Ingestion Slow
**Before**:
- Feed feels stale
- No visibility into ingestion

**After**:
- Admin dashboard shows: "🟠 RSS Ingestion: Degraded - Slow - Last fetch 8 min ago"
- Know system is running but slower than normal

### Scenario 3: All Systems Operational
**Before**:
- Uncertainty if everything is working

**After**:
- Admin dashboard shows green card: "✅ Component Health"
- All components show "Healthy" with recent timestamps
- Confidence the system is running properly

## Monitoring Best Practices

### Regular Checks
- **Daily**: Quick glance at admin dashboard
- **After deployments**: Verify all components recover
- **On user reports**: First place to check for issues

### Alert Thresholds
- **Critical** (Red): Requires immediate action
  - RSS Ingestion down
  - Story Clustering down
  - Summarization down >2 hours
  
- **Warning** (Orange): Monitor closely
  - Any component degraded
  - Multiple components yellow
  
- **Healthy** (Green): No action needed

### Response Procedures

**If RSS Ingestion is Down**:
1. Check Azure Functions app status
2. Review function logs for errors
3. Verify `RSS_USE_ALL_FEEDS` setting
4. Restart function app if needed

**If Story Clustering is Down**:
1. Check Cosmos DB change feed leases
2. Review function logs for errors
3. Consider resetting lease container
4. Verify source articles are being created

**If Summarization is Down**:
1. Check `ANTHROPIC_API_KEY` is configured
2. Review function logs for API errors
3. Reset `leases-summarization` container
4. Enable backfill function if needed

## Future Enhancements

### Potential Additions
1. **Response Time Tracking**: Measure query performance
2. **Historical Trends**: Show component uptime over time
3. **Push Notifications**: Alert admin when components go down
4. **Auto-Recovery**: Automatic lease resets on detection
5. **Cost Tracking**: Show API costs per component
6. **Performance Metrics**: Throughput, latency, error rates

### Additional Components to Monitor
1. **Firebase Auth**: Token validation health
2. **Azure Cosmos DB**: RU consumption, throttling
3. **Image Processing**: If added in future
4. **Cache Layer**: If Redis/CDN is added

## Deployment

### API Deployment
```bash
cd Azure/api
az acr build --registry newsreelacr --image newsreel-api:latest .
```

### iOS App
- Updated models and UI are part of next App Store build
- Admin dashboard automatically picks up new health data

## Testing

### Manual Testing
1. Open admin dashboard in iOS app
2. Verify "Component Health" card appears
3. Check each component shows status and message
4. Verify colors match status (green/orange/red)
5. Pull to refresh to update data

### Simulating Failures
1. **Simulate RSS Down**: Stop function app, check after 15 min
2. **Simulate Clustering Down**: Remove change feed trigger, check after 30 min
3. **Simulate Summarization Down**: Remove API key, check after 2 hours

## Documentation

### Files Modified
- **Backend**: `Azure/api/app/routers/admin.py` (+200 lines)
- **iOS Models**: `Newsreel App/Newsreel/Models/AdminModels.swift` (+40 lines)
- **iOS UI**: `Newsreel App/Newsreel/Views/Admin/AdminDashboardView.swift` (+100 lines)

### New Features
- ✅ Detailed component health checks
- ✅ Visual status indicators (green/orange/red)
- ✅ Descriptive status messages
- ✅ Last checked timestamps
- ✅ Overall component health color coding

## Impact

### Benefits
- **Faster Diagnosis**: See component status at a glance
- **Proactive Monitoring**: Catch issues before users report them
- **Better Transparency**: Clear visibility into system state
- **Reduced Downtime**: Quick identification and response

### User Experience
- Admin can quickly verify system health
- No need to manually query database
- Clear, actionable status messages
- Color-coded for quick scanning

---

**Status**: ✅ Complete and Deployed  
**Impact**: High - Critical for system monitoring  
**Next Steps**: Monitor dashboard for any component failures

