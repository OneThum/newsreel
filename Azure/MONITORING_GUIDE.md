# Azure Backend Monitoring Guide

**Date**: October 8, 2025  
**Purpose**: Monitor Newsreel Azure backend health, performance, and costs

---

## 🎯 Daily Monitoring Routine (5 minutes)

### 1. Check API Health
```bash
curl https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/health
```

**Expected**: `{"status":"healthy","cosmos_db":"connected"}`  
**If Unhealthy**: Check Container App logs

### 2. Verify RSS Ingestion
```bash
# Check last 50 lines of Function logs
az functionapp log tail \
  --name newsreel-func-51689 \
  --resource-group Newsreel-RG \
  | grep -E "RSS ingestion|articles"
```

**Expected**: "RSS ingestion complete: X new articles"  
**If No Activity**: RSS feeds may be down or slow

### 3. Check Cosmos DB Data
- Open Azure Portal → Cosmos DB → newsreel-db-1759951135
- Data Explorer → newsreel-db → raw_articles
- Should see growing number of articles

### 4. Monitor Costs
```bash
# Open Cost Management dashboard
open "https://portal.azure.com/#blade/Microsoft_Azure_CostManagement/Menu/costanalysis"
```

**Target**: <$3/day ($90/month)  
**Alert**: >$5/day

---

## 📊 Key Metrics Dashboard

### Application Insights Quick Queries

**Access**: https://portal.azure.com → Application Insights → newsreel-insights → Logs

#### API Request Rate
```kusto
requests
| where timestamp > ago(1h)
| summarize count() by bin(timestamp, 5m)
| render timechart
```

#### API Response Time
```kusto
requests
| where timestamp > ago(1h)
| summarize 
    avg_duration = avg(duration),
    p50 = percentile(duration, 50),
    p95 = percentile(duration, 95),
    p99 = percentile(duration, 99)
| project avg_duration, p50, p95, p99
```

**Target**: P50 < 200ms, P95 < 500ms

#### Error Rate
```kusto
requests
| where timestamp > ago(24h)
| summarize 
    total = count(),
    errors = countif(success == false)
| extend error_rate = (errors * 100.0) / total
| project total, errors, error_rate
```

**Target**: <1% error rate

#### Function Execution Count
```kusto
requests
| where timestamp > ago(1h)
| where cloud_RoleName contains "newsreel-func"
| summarize count() by name
| order by count_ desc
```

**Expected**: 
- RSS Ingestion: ~12/hour (every 5 min)
- Clustering: Varies with article count
- Summarization: Varies with story updates

#### Cosmos DB RU Consumption
```kusto
dependencies
| where type == "Azure DocumentDB"
| where timestamp > ago(1h)
| extend ru = toreal(customDimensions.requestCharge)
| summarize total_ru = sum(ru), avg_ru = avg(ru), count = count()
| extend ru_per_second = total_ru / 3600
```

**Target**: <100 RU/s average

---

## 🔍 Detailed Monitoring

### RSS Ingestion Health

**What to Watch:**
- Execution frequency: Should run every 5 minutes
- Success rate: >90% of feeds should fetch successfully
- Article count: Should see 50-200 new articles per run
- Execution time: <60 seconds

**Log Patterns:**
```
✅ Good: "RSS ingestion complete: 47 new articles out of 156 total"
✅ Good: "Fetched 9 of 10 feeds successfully"
⚠️  Warning: "Timeout fetching feed: ESPN"
❌ Bad: "RSS ingestion failed: Cannot connect to Cosmos DB"
```

**Query Logs:**
```bash
az monitor app-insights query \
  --app newsreel-insights \
  --analytics-query "traces 
    | where message contains 'RSS ingestion'
    | where timestamp > ago(1h)
    | order by timestamp desc
    | take 20"
```

### Story Clustering Health

**What to Watch:**
- Processing speed: 1-3 seconds per article
- Match rate: >70% of articles should match existing stories
- New story rate: ~20-30% of articles create new stories

**Log Patterns:**
```
✅ Good: "Article reuters_20251008_123456 clustered into story story_..."
✅ Good: "Updated story cluster story_xyz: now 3 sources, status=BREAKING"
⚠️  Warning: "Could not fetch articles for story"
```

### AI Summarization Health

**What to Watch:**
- Trigger rate: Should trigger when stories reach 2+ sources
- Generation time: 3-5 seconds per summary
- Cost per summary: $0.004-0.006
- Cache hit rate: >60% after initial summaries

**Log Patterns:**
```
✅ Good: "Generated summary v1: 142 words, 3240ms, $0.0048"
✅ Good: "Story story_xyz has new sources, regenerating summary"
⚠️  Warning: "Not enough sources for summarization: 1"
❌ Bad: "Error generating summary: API key invalid"
```

### Breaking News Monitor Health

**What to Watch:**
- Execution frequency: Every 2 minutes
- Detection accuracy: Only 3+ source stories should be marked breaking
- Notification rate: Should be low (1-5 per day typically)

**Log Patterns:**
```
✅ Good: "Found 2 breaking stories to notify"
✅ Good: "Marked notification as sent for story story_xyz"
ℹ️  Info: "No breaking stories requiring notifications"
```

---

## 🚨 Alerts to Configure

### Critical Alerts (Set up in Azure Portal)

1. **API Down**
   - Metric: Failed requests > 10 in 5 minutes
   - Action: Email + SMS

2. **High Error Rate**
   - Metric: Error rate > 5%
   - Action: Email

3. **Cosmos DB Throttling**
   - Metric: 429 responses > 100 in 5 minutes
   - Action: Email

4. **High Costs**
   - Metric: Daily spending > $5
   - Action: Email

5. **Function Failures**
   - Metric: Function failures > 10 in 5 minutes
   - Action: Email

### Configure via Azure Portal

1. Go to Application Insights → newsreel-insights
2. Click "Alerts" in left menu
3. Click "+ New alert rule"
4. Configure condition, action group (email), and action

---

## 📈 Performance Monitoring

### Container App Scaling

**Check if scaling to zero:**
```bash
az containerapp revision list \
  --name newsreel-api \
  --resource-group Newsreel-RG \
  --query "[].{name:name, replicas:properties.replicas, active:properties.active}" \
  -o table
```

**Expected**: 0 replicas when idle, 1-3 when active

### Function Cold Starts

**Query cold start times:**
```kusto
requests
| where timestamp > ago(1h)
| where cloud_RoleName contains "newsreel-func"
| where customDimensions.Category == "Host.Startup"
| summarize avg(duration), max(duration)
```

**Expected**: <3 seconds average

### Cosmos DB Performance

**Check latency:**
```bash
az monitor metrics list \
  --resource newsreel-db-1759951135 \
  --resource-group Newsreel-RG \
  --resource-type "Microsoft.DocumentDB/databaseAccounts" \
  --metric "ServerSideLatency" \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ) \
  --interval PT5M
```

**Expected**: <50ms average

---

## 💰 Cost Monitoring

### Daily Cost Check

```bash
# Month-to-date spending
az consumption usage list \
  --start-date $(date +%Y-%m-01) \
  --end-date $(date +%Y-%m-%d) 2>/dev/null | \
  jq -r '.[] | select(.instanceId | contains("Newsreel-RG")) | .pretaxCost' | \
  awk '{sum+=$1} END {print "MTD Cost: $" sum}'
```

### Cost by Service

**Via Azure Portal:**
1. Cost Management + Billing
2. Cost Analysis
3. Filter by: Resource Group = "Newsreel-RG"
4. Group by: Service Name

**Expected Monthly Breakdown:**
- Cosmos DB: $30-35
- Container Apps: $25-30
- Functions: $5
- Container Registry: $5
- Storage: $0.50
- App Insights: $10

### Anthropic API Costs

**Track in Application Insights:**
```kusto
traces
| where message contains "Generated summary"
| extend cost = extract("\\$([0-9.]+)", 1, message)
| summarize total_cost = sum(todouble(cost)), count = count()
| extend avg_cost = total_cost / count
```

**Expected**: $0.004-0.006 per summary, ~10-20K summaries/month = $50-80

---

## 🔧 Performance Tuning

### If API is Slow (>500ms P95)

**Check bottlenecks:**
```bash
# View slow requests
az monitor app-insights query \
  --app newsreel-insights \
  --analytics-query "requests 
    | where timestamp > ago(1h)
    | where duration > 500
    | summarize count() by operation_Name
    | order by count_ desc"
```

**Solutions:**
1. Increase cache TTL
2. Add database indexes
3. Optimize queries
4. Increase Container App CPU/memory

### If Cosmos DB is Expensive

**Check RU consumption by operation:**
```bash
# Most expensive queries
az monitor app-insights query \
  --app newsreel-insights \
  --analytics-query "dependencies
    | where type == 'Azure DocumentDB'
    | where timestamp > ago(24h)
    | extend ru = toreal(customDimensions.requestCharge)
    | summarize total_ru = sum(ru), count = count() by operation_Name
    | extend avg_ru = total_ru / count
    | order by total_ru desc
    | take 10"
```

**Solutions:**
1. Use point reads instead of queries (1 RU vs 3+ RUs)
2. Add caching layer
3. Optimize query filters
4. Use partition keys in queries

### If Functions Timeout

**Check execution times:**
```kusto
requests
| where cloud_RoleName contains "newsreel-func"
| where timestamp > ago(1h)
| summarize avg(duration), max(duration), count() by operation_Name
| order by avg_duration desc
```

**Solutions:**
1. Reduce batch size
2. Optimize article processing
3. Add timeout handling
4. Split large operations

---

## 📱 Mobile App Monitoring

### Track iOS App Usage

**User signups:**
```kusto
traces
| where message contains "Created new user profile"
| where timestamp > ago(24h)
| summarize count()
```

**Active users:**
```kusto
requests
| where url contains "/api/stories/feed"
| where timestamp > ago(24h)
| summarize dcount(user_Id)
```

**Popular categories:**
```kusto
requests
| where url contains "/api/stories/feed"
| where url contains "category="
| extend category = extract("category=([^&]+)", 1, url)
| summarize count() by category
| order by count_ desc
```

---

## 🚨 Incident Response

### API Down

1. **Check health endpoint**
   ```bash
   curl https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/health
   ```

2. **View recent errors**
   ```bash
   az containerapp logs show --name newsreel-api --resource-group Newsreel-RG --tail 100
   ```

3. **Restart if needed**
   ```bash
   az containerapp revision restart \
     --name newsreel-api \
     --resource-group Newsreel-RG \
     --revision-name $(az containerapp revision list \
       --name newsreel-api \
       --resource-group Newsreel-RG \
       --query "[0].name" -o tsv)
   ```

### Functions Not Running

1. **Check status**
   ```bash
   az functionapp show \
     --name newsreel-func-51689 \
     --resource-group Newsreel-RG \
     --query "{state:state, healthCheckStatus:hostNameSslStates[0].sslState}"
   ```

2. **View logs**
   ```bash
   az functionapp log tail --name newsreel-func-51689 --resource-group Newsreel-RG
   ```

3. **Restart**
   ```bash
   az functionapp restart --name newsreel-func-51689 --resource-group Newsreel-RG
   ```

### High Costs

1. **Identify top consumer**
   ```bash
   # Portal → Cost Management → Cost Analysis
   # Group by: Service
   # Filter: Newsreel-RG
   ```

2. **Check Cosmos DB RUs**
   ```bash
   az cosmosdb show \
     --name newsreel-db-1759951135 \
     --resource-group Newsreel-RG
   ```

3. **Scale down if needed**
   ```bash
   # Reduce Container App max replicas
   az containerapp update \
     --name newsreel-api \
     --resource-group Newsreel-RG \
     --max-replicas 2
   ```

---

## 📊 Weekly Review Checklist

- [ ] Review Application Insights dashboard
- [ ] Check error logs and fix issues
- [ ] Review cost trends
- [ ] Check Cosmos DB storage growth
- [ ] Verify all functions executing successfully
- [ ] Review API response times
- [ ] Check for security issues
- [ ] Update RSS feed list if needed

---

## 🎓 Advanced Monitoring

### Custom Metrics

**Track summarization costs:**
```kusto
traces
| where message contains "Generated summary"
| extend 
    cost = extract("\\$([0-9.]+)", 1, message),
    cached = extract("cached_tokens: ([0-9]+)", 1, message)
| summarize 
    total_cost = sum(todouble(cost)),
    total_summaries = count(),
    avg_cached = avg(todouble(cached))
| extend avg_cost = total_cost / total_summaries
```

**Track user engagement:**
```kusto
requests
| where url contains "/api/stories"
| where url contains "interact"
| extend interaction_type = extract("interaction_type\":\"([^\"]+)\"", 1, url)
| summarize count() by interaction_type
| render piechart
```

### Performance Baselines

| Metric | Baseline | Alert Threshold |
|--------|----------|-----------------|
| API P95 latency | <500ms | >1000ms |
| Function execution time | <30s | >60s |
| Error rate | <1% | >5% |
| Cosmos DB RU/s | <50 | >200 |
| Daily cost | $2-3 | >$5 |

---

## 🔔 Alert Configuration

### Critical Alerts (Immediate)

1. **API Health Check Fails**
   - Every 5 minutes, if health endpoint returns non-200
   - Action: SMS + Email

2. **Cosmos DB Unavailable**
   - If connection failures > 10 in 5 minutes
   - Action: SMS + Email

3. **Function Complete Failure**
   - If all executions fail for 15 minutes
   - Action: Email

### Warning Alerts (Review Daily)

1. **High API Latency**
   - P95 > 1 second for 15 minutes
   - Action: Email

2. **Elevated Error Rate**
   - >3% errors for 15 minutes
   - Action: Email

3. **High RU Consumption**
   - >200 RU/s for 30 minutes
   - Action: Email

4. **Daily Cost Exceeds $5**
   - Once per day
   - Action: Email

---

## 📝 Monitoring Best Practices

1. **Check daily** (5 min routine above)
2. **Review weekly** (Application Insights dashboard)
3. **Analyze monthly** (Costs, trends, optimizations)
4. **Set up alerts** (Proactive monitoring)
5. **Document issues** (Build knowledge base)
6. **Optimize continuously** (Improve performance)

---

## 🎯 Success Indicators

### Technical Health
- ✅ API uptime > 99.5%
- ✅ P95 latency < 500ms
- ✅ Error rate < 1%
- ✅ RSS ingestion success > 90%
- ✅ Functions executing on schedule

### User Satisfaction
- ✅ Feed loads in < 2 seconds
- ✅ Stories update every 5 minutes
- ✅ Breaking news detected within 10 minutes
- ✅ Summaries are accurate and concise

### Cost Efficiency
- ✅ Daily cost < $3
- ✅ Monthly Azure cost < $100
- ✅ Total monthly cost < $250
- ✅ Cost per user < $1/month (at scale)

---

**Monitor regularly to ensure smooth operation!** 📊✅

