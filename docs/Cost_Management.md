# Cost Management Guide for Newsreel

**Last Updated**: October 8, 2025

---

## Budget Constraints

### Hard Limits (MUST NOT EXCEED)

- **Azure Services**: Maximum $150/month
- **Total Project**: Maximum $300/month

These are hard limits that cannot be exceeded under any circumstances.

---

## Current Budget Allocation

### Azure Services ($96/month projected)

| Service | Monthly Cost | Justification | Notes |
|---------|--------------|---------------|-------|
| **Azure Cosmos DB** | $31 | Serverless, 10GB storage + 100M RUs | Core database |
| **Azure Container Apps** | $40 | 0.25 vCPU, scale to zero | Story API |
| **Azure Functions** | $15 | Consumption plan, ~1M executions | RSS ingestion, clustering, summarization |
| **Azure Storage** | $5 | Blob + Queue storage | Function storage |
| **Application Insights** | $5 | 5GB log ingestion (limited) | Monitoring |
| **Azure Subtotal** | **$96** | | **$54 under Azure budget ✅** |

### External Services ($180/month projected)

| Service | Monthly Cost | Justification | Notes |
|---------|--------------|---------------|-------|
| **Anthropic Claude API** | $80 | ~10k summaries/month with prompt caching | AI summarization |
| **Twitter/X API** | $100 | Basic tier for filtered stream | Breaking news detection |
| **Firebase Auth** | $0 | Free tier (under 50k MAU) | User authentication |
| **RevenueCat** | $0 | Free tier (up to $2.5k MRR) | Subscription management |
| **External Subtotal** | **$180** | | |

**RevenueCat Pricing Note:**
- Free tier: Up to $2,500 Monthly Recurring Revenue (MRR)
- At $4.99/user/month, supports ~500 paying subscribers before charges apply
- After free tier: 1% of tracked revenue (e.g., $25/month for $2,500 MRR)
- Includes: Receipt validation, webhooks, subscriber analytics, cross-platform support

### Total Project: $276/month

**Buffer remaining**: $24 (8% under budget)

---

## Azure Subscription Details

- **Subscription Name**: Newsreel Subscription
- **Subscription ID**: `d4abcc64-9e59-4094-8d89-10b5d36b6d4c`
- **Directory**: One Thum Software (onethum.com)
- **Access**: Via Azure CLI
- **Region**: West US 2 (primary)

---

## Cost Monitoring Strategy

### 1. Check for Existing Resources FIRST

**CRITICAL**: Before creating any new Azure resource, ALWAYS check if one already exists that can be repurposed.

```bash
# List all resources in subscription
az resource list --subscription d4abcc64-9e59-4094-8d89-10b5d36b6d4c --output table

# List resource groups
az group list --subscription d4abcc64-9e59-4094-8d89-10b5d36b6d4c --output table

# Check specific resource types
az cosmosdb list --output table
az functionapp list --output table
az storage account list --output table
az containerapp list --output table
```

**Process**:
1. Search for existing resources first
2. Evaluate if existing resource can be reused
3. Only create new if absolutely necessary
4. Document reason for new resource creation

### 2. Daily Cost Monitoring

```bash
# View current month costs
az consumption usage list \
  --subscription d4abcc64-9e59-4094-8d89-10b5d36b6d4c \
  --start-date $(date -d "$(date +%Y-%m-01)" +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --output table

# View by resource group
az consumption usage list \
  --subscription d4abcc64-9e59-4094-8d89-10b5d36b6d4c \
  --resource-group newsreel-prod-rg \
  --output table
```

### 3. Budget Alerts

Set up alerts at multiple thresholds:

```bash
# Alert at $120 (80% of Azure budget)
az consumption budget create \
  --budget-name newsreel-azure-warning \
  --amount 150 \
  --time-grain Monthly \
  --start-date $(date +%Y-%m-01) \
  --end-date 2026-12-31 \
  --resource-group newsreel-prod-rg \
  --notifications \
    threshold=80 \
    contactEmails="[your-email@onethum.com]" \
    contactRoles="[Owner,Contributor]"

# Alert at $135 (90% of Azure budget)
az consumption budget create \
  --budget-name newsreel-azure-critical \
  --amount 150 \
  --time-grain Monthly \
  --start-date $(date +%Y-%m-01) \
  --end-date 2026-12-31 \
  --resource-group newsreel-prod-rg \
  --notifications \
    threshold=90 \
    contactEmails="[your-email@onethum.com]" \
    contactRoles="[Owner,Contributor]"
```

### 4. Real-Time Cost Tracking

**Application Insights Query** (for Claude API costs):

```kusto
traces
| where customDimensions.cost_usd > 0
| summarize 
    total_cost = sum(todouble(customDimensions.cost_usd)),
    request_count = count()
    by bin(timestamp, 1h)
| order by timestamp desc
```

---

## Cost Optimization Strategies

### Current Optimizations

✅ **Cosmos DB Serverless**
- Pay only for RUs consumed
- No idle costs
- Auto-scales from zero

✅ **Container Apps Scale-to-Zero**
- No cost when idle
- Scales up on demand
- Maximum 3 instances

✅ **Functions Consumption Plan**
- Pay per execution
- Free tier: 1M executions/month
- Auto-scales

✅ **Claude API Prompt Caching**
- 90% cost reduction on cached content
- System prompt cached
- Saves ~$50/month

✅ **HTTP 304 Caching for RSS**
- Reduces bandwidth
- Fewer requests
- Lower storage costs

### If Budget Pressure Increases

#### Option 1: Reduce Application Insights ($5 savings)
```bash
# Limit daily cap to 1GB
az monitor app-insights component update \
  --app newsreel-prod-insights \
  --resource-group newsreel-prod-rg \
  --cap 1
```

#### Option 2: Optimize Cosmos DB Queries
- Add more specific indexes
- Reduce query frequency
- Implement aggressive caching
- **Potential savings**: $10-15/month

#### Option 3: Reduce Function Execution Frequency
- RSS polling: 5min → 10min
- Breaking news monitoring: 2min → 5min
- **Potential savings**: $5-10/month

#### Option 4: Use Twitter API More Efficiently
- Filter more aggressively
- Reduce monitored accounts
- Consider downgrade if possible
- **Potential savings**: Could save $100/month

#### Option 5: Optimize Claude API Usage
- Summarize only stories with 3+ sources
- Increase cache hit rate
- Reduce summary length slightly
- **Potential savings**: $10-20/month

---

## Cost Alert Thresholds

| Threshold | Action | Responsible |
|-----------|--------|-------------|
| **$120/month (Azure)** | Review and optimize | Development Team |
| **$135/month (Azure)** | Immediate action required | Tech Lead |
| **$150/month (Azure)** | HARD STOP - investigate immediately | CTO |
| **$240/month (Total)** | Review all services | Development Team |
| **$270/month (Total)** | Immediate action required | Tech Lead |
| **$300/month (Total)** | HARD STOP - investigate immediately | CTO |

---

## Resource Tagging Strategy

Tag all Azure resources for cost tracking:

```bash
# Tag resource with project and environment
az resource tag \
  --ids /subscriptions/d4abcc64-9e59-4094-8d89-10b5d36b6d4c/resourceGroups/newsreel-prod-rg/providers/Microsoft.DocumentDB/databaseAccounts/newsreel-prod-cosmos \
  --tags project=newsreel environment=production cost-center=backend
```

**Standard Tags**:
- `project`: newsreel
- `environment`: production/staging/dev
- `cost-center`: backend/frontend/infrastructure
- `owner`: team-name
- `critical`: true/false

---

## Monthly Cost Review Checklist

- [ ] Review Azure cost by service
- [ ] Review Claude API token usage
- [ ] Check for unused resources
- [ ] Verify scale-to-zero is working
- [ ] Review Application Insights log volume
- [ ] Check Cosmos DB RU consumption patterns
- [ ] Verify Function execution counts
- [ ] Review Container Apps scaling metrics
- [ ] Check for cost anomalies
- [ ] Update projections for next month

---

## Emergency Cost Reduction Plan

If costs exceed budget:

### Immediate Actions (0-24 hours)

1. **Stop non-essential functions**
```bash
# Disable breaking news monitor temporarily
az functionapp config appsettings set \
  --name newsreel-prod-func \
  --resource-group newsreel-prod-rg \
  --settings FUNCTION_ENABLED_breaking_news_monitor=false
```

2. **Scale down Container Apps**
```bash
# Reduce max replicas to 1
az containerapp update \
  --name story-api \
  --resource-group newsreel-prod-rg \
  --max-replicas 1
```

3. **Reduce Application Insights**
```bash
# Set daily cap to 0.5GB
az monitor app-insights component update \
  --app newsreel-prod-insights \
  --resource-group newsreel-prod-rg \
  --cap 0.5
```

### Short-term Actions (1-7 days)

1. Reduce RSS polling frequency
2. Optimize Cosmos DB queries
3. Implement more aggressive caching
4. Review and remove unused resources
5. Negotiate Twitter API alternatives

### Long-term Actions (1-4 weeks)

1. Consider regional optimization
2. Implement reserved capacity for stable workloads
3. Explore alternative AI providers
4. Build custom breaking news detection
5. Optimize database schema

---

## Cost Reporting

### Weekly Report Template

**Week of**: [Date]

**Azure Costs**:
- Current: $XX.XX
- Projected Monthly: $XX.XX
- Budget: $150.00
- Status: ✅ Under budget / ⚠️ Near limit / ❌ Over budget

**External Costs**:
- Claude API: $XX.XX
- Twitter API: $XX.XX
- Total: $XX.XX

**Total Project**:
- Current: $XX.XX
- Projected: $XX.XX
- Budget: $300.00
- Buffer: $XX.XX

**Action Items**:
- [ ] Action 1
- [ ] Action 2

---

## Contact for Cost Issues

- **Primary**: Development Lead
- **Secondary**: DevOps Engineer
- **Escalation**: CTO
- **Azure Support**: https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade

---

**Document Owner**: DevOps Team  
**Review Cadence**: Weekly  
**Next Review**: After first month of operation

