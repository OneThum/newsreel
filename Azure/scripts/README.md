# Newsreel Log Analysis CLI Tools

**CLI-accessible logging for agent-automated system reviews** 🤖

## 🎯 Purpose

These scripts enable:
1. **Manual log review** by developers
2. **Automated log analysis** by AI agents
3. **System health monitoring** without Azure Portal

All queries use **Azure CLI** and **Application Insights** (already included in your subscription, no extra cost).

---

## 📋 Prerequisites

```bash
# 1. Azure CLI installed
az --version

# 2. Logged in to Azure
az login

# 3. Correct subscription selected
az account set --subscription "Newsreel Subscription"

# 4. jq installed (for JSON formatting)
brew install jq  # macOS
```

---

## 🔧 Available Tools

### 1. `query-logs.sh` - Query Specific Metrics

**Basic Usage:**
```bash
./query-logs.sh [query-type] [time-range]
```

**Query Types:**

| Type | Purpose | Target Metric |
|------|---------|---------------|
| `source-diversity` | Track feed source variety | > 10 unique sources per 20 stories |
| `categorization` | Category accuracy & confidence | > 70% average confidence |
| `rss-fetch` | RSS feed performance | < 2s average fetch time |
| `clustering` | Story clustering stats | > 60% match rate |
| `performance` | Operation speed | < 500ms p95 |
| `summary-generation` | AI summary metrics | < 2s average |
| `errors` | Recent errors | 0 errors |
| `feed-quality` | Overall feed quality | "Excellent" rating |

**Examples:**
```bash
# Check source diversity (last hour)
./query-logs.sh source-diversity 1h | jq

# Check errors (last 30 minutes)
./query-logs.sh errors 30m | jq '.tables[0].rows'

# Performance over 24 hours
./query-logs.sh performance 24h | jq

# Custom query
./query-logs.sh custom "traces | where message contains 'BBC' | take 10"
```

---

### 2. `analyze-system-health.sh` - Automated Health Check

**For AI agents and automated monitoring.**

**Usage:**
```bash
./analyze-system-health.sh [time-range]
```

**Output:**
Structured JSON with:
- Health scores for each subsystem
- Specific recommendations
- Prioritized next actions
- Monitoring commands

**Example:**
```bash
# Quick health check (last hour)
./analyze-system-health.sh 1h | jq

# Full 24-hour analysis
./analyze-system-health.sh 24h | jq

# Extract specific metrics
./analyze-system-health.sh 1h | jq '.analysis.source_diversity'

# Get next actions
./analyze-system-health.sh 1h | jq '.next_actions'
```

**Sample Output:**
```json
{
  "timestamp": "2025-10-13T20:30:00Z",
  "time_range": "1h",
  "analysis": {
    "source_diversity": {
      "unique_sources": 4,
      "total_stories": 20,
      "diversity_score": 0.20,
      "status": "poor",
      "recommendation": "⚠️  CRITICAL: Source diversity is poor. Implement Phase 2 immediately."
    },
    "categorization": {
      "avg_confidence": 0.65,
      "status": "fair",
      "recommendation": "Consider Phase 4 (Improved Categorization)."
    },
    "performance": {
      "p95_duration_ms": 450,
      "status": "excellent",
      "recommendation": "Performance is excellent (p95 < 1s)."
    },
    "errors": {
      "count": 2,
      "status": "acceptable",
      "recommendation": "Few errors detected. Monitor for patterns."
    },
    "feed_quality": {
      "rating": "Fair",
      "recommendation": "⚠️  Feed quality is fair. Implement Phase 2 and Phase 4."
    }
  },
  "next_actions": [
    {
      "priority": 1,
      "phase": 2,
      "action": "Implement Feed Diversity Algorithm",
      "file": "Azure/api/app/services/feed_service.py"
    }
  ]
}
```

---

## 🤖 Agent-Automated Workflow

**For AI agents to autonomously monitor and improve the system:**

### Step 1: Run Health Check
```bash
HEALTH=$(./analyze-system-health.sh 1h)
```

### Step 2: Extract Recommendations
```bash
echo "$HEALTH" | jq '.next_actions[] | select(.priority == 1)'
```

### Step 3: Take Action
```bash
# If source diversity is poor, agent can:
# 1. Read PRODUCT_IMPROVEMENT_ROADMAP.md
# 2. Implement Phase 2 (Feed Diversity Algorithm)
# 3. Deploy changes
# 4. Verify improvement with next health check
```

### Step 4: Verify Changes
```bash
# Wait 1 hour, then re-check
./analyze-system-health.sh 1h | jq '.analysis.source_diversity.status'
# Expected: "good" or "excellent"
```

---

## 📊 Key Metrics to Monitor

### 1. Source Diversity (CRITICAL)
```bash
./query-logs.sh source-diversity 1h | jq -r '.tables[0].rows[0] | "Sources: \(.[1])/\(.[2]) = \(.[1] / .[2] * 100)%"'
```

**Target:** > 60% (12+ unique sources per 20 stories)  
**Alert:** < 40% (Phase 2 needed)

### 2. Categorization Confidence
```bash
./query-logs.sh categorization 24h | jq -r '.tables[0].rows[] | "\(.[0]): \(.[2] * 100)% confidence"'
```

**Target:** > 70% average confidence  
**Alert:** < 50% (Phase 4 needed)

### 3. Error Rate
```bash
./query-logs.sh errors 1h | jq '.tables[0].rows | length'
```

**Target:** 0 errors  
**Alert:** > 10 errors/hour

### 4. Performance
```bash
./query-logs.sh performance 1h | jq -r '.tables[0].rows[] | "\(.[0]): p95=\(.[4])ms"'
```

**Target:** p95 < 500ms  
**Alert:** p95 > 2000ms

---

## 🚨 Common Issues & Solutions

### Issue: "No data available"
**Cause:** Logging not yet deployed  
**Solution:**
```bash
cd "/Users/davemac/Library/CloudStorage/OneDrive-OneThumSoftware/One Thum Software/Newsreel/Azure/functions"
func azure functionapp publish newsreel-func-51689
```

### Issue: Low source diversity
**Cause:** No diversity algorithm  
**Solution:** Implement Phase 2 from `PRODUCT_IMPROVEMENT_ROADMAP.md`

### Issue: Low categorization confidence
**Cause:** Keyword-only categorization  
**Solution:** Implement Phase 4 from `PRODUCT_IMPROVEMENT_ROADMAP.md`

### Issue: High API call rate
**Cause:** 30s polling without changes  
**Solution:** Implement Phase 3 (Smart Polling) from roadmap

---

## 💰 Cost Impact

**Application Insights (Already Included):**
- Free tier: 5GB/month
- Structured logging: ~50MB/month
- **Cost: $0** (well within free tier)

**CLI Queries:**
- Free (part of Azure CLI)
- No additional charges

---

## 🔄 Deployment Workflow

### 1. Deploy Backend Logging
```bash
cd "/Users/davemac/Library/CloudStorage/OneDrive-OneThumSoftware/One Thum Software/Newsreel/Azure/functions"
func azure functionapp publish newsreel-func-51689
```

### 2. Wait 5 Minutes
(Let RSS ingestion run and generate logs)

### 3. Run First Health Check
```bash
cd "/Users/davemac/Library/CloudStorage/OneDrive-OneThumSoftware/One Thum Software/Newsreel/Azure/scripts"
./analyze-system-health.sh 1h | jq
```

### 4. Review Recommendations
```bash
./analyze-system-health.sh 1h | jq '.next_actions'
```

### 5. Implement Fixes
Follow recommendations from health check

### 6. Verify Improvements
```bash
# Check specific metric improved
./query-logs.sh source-diversity 1h | jq
```

---

## 📈 Success Metrics (After Phase 2)

**Before Phase 2:**
```bash
$ ./query-logs.sh source-diversity 1h | jq -r '.tables[0].rows[0]'
["2025-10-13T20:00:00Z", 4, 20, {...}]
# 4 sources / 20 stories = 20% diversity ❌
```

**After Phase 2:**
```bash
$ ./query-logs.sh source-diversity 1h | jq -r '.tables[0].rows[0]'
["2025-10-13T21:00:00Z", 14, 20, {...}]
# 14 sources / 20 stories = 70% diversity ✅
```

---

## 🎓 Advanced Usage

### Continuous Monitoring (Cron Job)
```bash
# Add to crontab for hourly health checks
0 * * * * cd /path/to/scripts && ./analyze-system-health.sh 1h > /tmp/newsreel-health.json
```

### Alert on Issues
```bash
#!/bin/bash
HEALTH=$(./analyze-system-health.sh 1h)
CRITICAL=$(echo "$HEALTH" | jq '.next_actions[] | select(.priority == 1)')

if [ -n "$CRITICAL" ]; then
    echo "ALERT: Critical issues detected"
    echo "$CRITICAL" | jq
    # Send notification (Slack, email, etc.)
fi
```

### Export for Analysis
```bash
# Export to CSV for spreadsheet analysis
./query-logs.sh source-diversity 24h | jq -r '.tables[0].rows[] | @csv' > diversity-report.csv
```

---

## 🆘 Support

**View logs in Azure Portal:**
```
https://portal.azure.com/#@{tenant}/resource/subscriptions/{subscription}/resourceGroups/newsreel-rg/providers/microsoft.insights/components/{app-insights}/logs
```

**Test queries locally:**
```bash
# Dry run (doesn't execute query)
echo "traces | where timestamp > ago(1h) | take 10"
```

**Debug script issues:**
```bash
# Enable verbose output
set -x
./query-logs.sh source-diversity 1h
set +x
```

---

**Questions? See `PRODUCT_IMPROVEMENT_ROADMAP.md` for implementation details.**
