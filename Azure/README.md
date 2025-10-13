# Newsreel Azure Backend

**Status**: ✅ **DEPLOYED & RUNNING**  
**Date**: October 8, 2025  
**API Endpoint**: `https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io`

---

## 📚 Documentation Index

All documentation for the Azure backend deployment:

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **[DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)** | Complete deployment details | Review what was deployed |
| **[NEXT_STEPS.md](NEXT_STEPS.md)** | Configuration & testing guide | Add API keys, test system |
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | Quick reference card | Daily operations |
| **[iOS_AZURE_INTEGRATION.md](../iOS_AZURE_INTEGRATION.md)** | iOS integration guide | Connect iOS app |
| **[IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)** | Implementation documentation | Understand the code |

---

## 🚀 Quick Start

### 1. Verify Deployment
```bash
# Test API health
curl https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/health

# Expected: {"status":"healthy","cosmos_db":"connected"}
```

### 2. Add Required API Keys
```bash
# Add Anthropic API key (for AI summarization)
az functionapp config appsettings set \
  --name newsreel-func-51689 \
  --resource-group Newsreel-RG \
  --settings "ANTHROPIC_API_KEY=<your-key>"

# Add Firebase credentials (see NEXT_STEPS.md for details)
```

### 3. Monitor First RSS Ingestion
```bash
# Watch function logs (RSS ingestion runs every 5 minutes)
az functionapp log tail \
  --name newsreel-func-51689 \
  --resource-group Newsreel-RG
```

### 4. Connect iOS App
Update `APIService.swift`:
```swift
private let baseURL = "https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io"
```

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  iOS App (SwiftUI)                   │
│              Firebase JWT Authentication              │
└───────────────────────┬─────────────────────────────┘
                        │ HTTPS
                        ▼
┌─────────────────────────────────────────────────────┐
│         Azure Container App (FastAPI API)            │
│    newsreel-api.thankfulpebble-0dde6120...io        │
│    - Auth middleware                                 │
│    - Rate limiting                                   │
│    - Personalization engine                          │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│        Azure Cosmos DB (Serverless NoSQL)            │
│    newsreel-db-1759951135                           │
│    - raw_articles (RSS feeds)                        │
│    - story_clusters (aggregated stories)             │
│    - user_profiles                                   │
│    - user_interactions                               │
└─────────────────────────────────────────────────────┘
                        ▲
                        │
┌─────────────────────────────────────────────────────┐
│         Azure Functions (Python 3.11)                │
│    newsreel-func-51689                              │
│                                                      │
│    1. RSS Ingestion (Timer: every 5 min)            │
│       → Fetches 10 RSS feeds in parallel            │
│       → Stores articles in Cosmos DB                 │
│                                                      │
│    2. Story Clustering (Change Feed)                 │
│       → Groups related articles                      │
│       → Detects breaking news (3+ sources)           │
│                                                      │
│    3. Summarization (Change Feed)                    │
│       → Claude Sonnet 4 API                          │
│       → Multi-source synthesis                       │
│                                                      │
│    4. Breaking News Monitor (Timer: every 2 min)     │
│       → Queues push notifications                    │
└─────────────────────────────────────────────────────┘
```

---

## 📦 Deployed Resources

| Resource | Name | Type | Status |
|----------|------|------|--------|
| Cosmos DB | newsreel-db-1759951135 | Serverless | ✅ |
| Storage | newsreelstorage51494 | Standard_LRS | ✅ |
| Function App | newsreel-func-51689 | Consumption | ✅ |
| Container Registry | newsreelacr | Basic | ✅ |
| Container App | newsreel-api | FastAPI | ✅ |
| App Insights | newsreel-insights | Monitoring | ✅ |

**Total Monthly Cost**: $77-87 (well under $150 budget) ✅

---

## 📂 Directory Structure

```
Azure/
├── functions/              # Azure Functions (Python 3.11)
│   ├── rss_ingestion/      # Timer: every 5 min
│   ├── story_clustering/   # Change feed trigger
│   ├── summarization/      # Change feed trigger
│   ├── breaking_news_monitor/ # Timer: every 2 min
│   ├── shared/             # Shared utilities
│   │   ├── models.py       # Pydantic models
│   │   ├── cosmos_client.py # DB wrapper
│   │   ├── config.py       # Configuration
│   │   ├── utils.py        # Helper functions
│   │   └── rss_feeds.py    # Feed configuration
│   ├── host.json
│   ├── requirements.txt
│   └── local.settings.json.example
│
├── api/                    # FastAPI REST API
│   ├── app/
│   │   ├── main.py         # FastAPI app
│   │   ├── config.py       # Settings
│   │   ├── models/         # Request/response models
│   │   ├── services/       # Business logic
│   │   │   ├── cosmos_service.py
│   │   │   ├── auth_service.py
│   │   │   └── recommendation_service.py
│   │   ├── middleware/     # Auth, CORS
│   │   └── routers/        # API endpoints
│   │       ├── stories.py
│   │       ├── users.py
│   │       └── health.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .dockerignore
│
├── infrastructure/         # Terraform (not used, deployed via CLI)
├── scripts/                # Deployment scripts
│
├── DEPLOYMENT_SUMMARY.md   # ✅ Complete deployment details
├── NEXT_STEPS.md          # ⏭️ Configuration guide
├── QUICK_REFERENCE.md     # 📋 Quick reference
├── IMPLEMENTATION_COMPLETE.md # 📝 Implementation docs
└── README.md              # 👈 You are here
```

---

## 🔧 Development Workflow

### Update Functions Code
```bash
cd functions

# Make your changes
# Test locally (optional):
func start

# Deploy to Azure:
func azure functionapp publish newsreel-func-51689
```

### Update API Code
```bash
cd api

# Make your changes
# Test locally (optional):
uvicorn app.main:app --reload

# Deploy to Azure:
az acr build --registry newsreelacr --image newsreel-api:latest .
# Container App will auto-update
```

### View Logs
```bash
# API logs (real-time)
az containerapp logs show --name newsreel-api --resource-group Newsreel-RG --follow

# Function logs (real-time)
az functionapp log tail --name newsreel-func-51689 --resource-group Newsreel-RG

# Application Insights (historical)
# https://portal.azure.com → newsreel-insights
```

---

## 📊 Monitoring

### Health Checks

**API Health**:
```bash
curl https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-10-08T...",
  "cosmos_db": "connected"
}
```

### Key Metrics to Monitor

1. **Cosmos DB Request Units (RU/s)**
   - Target: <100 RU/s average
   - Alert: >200 RU/s sustained

2. **Container App CPU/Memory**
   - Should scale to 0 when idle
   - Monitor for memory leaks

3. **Function Execution Count**
   - RSS Ingestion: ~288/day (every 5 min)
   - Clustering: Varies with articles
   - Summarization: Varies with stories

4. **API Response Time**
   - Target: <200ms P50, <500ms P95
   - Alert: >1s P95

5. **Error Rate**
   - Target: <1% errors
   - Alert: >5% errors

### Application Insights Queries

```kusto
// Function execution times
requests
| where timestamp > ago(1h)
| summarize avg(duration), max(duration), count() by name
| order by avg_duration desc

// API errors
exceptions
| where timestamp > ago(1h)
| summarize count() by type, outerMessage

// Cosmos DB RU consumption
dependencies
| where type == "Azure DocumentDB"
| where timestamp > ago(1h)
| extend ru = toreal(customDimensions.requestCharge)
| summarize sum(ru) by bin(timestamp, 5m)
```

---

## 💰 Cost Management

### Current Configuration

| Service | SKU | Scaling | Est. Cost |
|---------|-----|---------|-----------|
| Cosmos DB | Serverless | Auto | $30-35/mo |
| Container App | 0.5 vCPU, 1GB | 0-3 replicas | $25-30/mo |
| Function App | Consumption | Auto | $5/mo |
| Storage | Standard_LRS | Fixed | $0.50/mo |
| Container Registry | Basic | Fixed | $5/mo |
| App Insights | Pay-as-go | Auto | $10/mo |

**Total**: $77-87/month ✅

### Cost Optimization Tips

1. **Cosmos DB**: 
   - Use serverless (only pay for what you use)
   - Set TTL on containers to auto-delete old data
   - Optimize queries (use partition keys)

2. **Container Apps**:
   - Scales to zero when idle (no cost)
   - Monitor for memory leaks that prevent scaling to zero

3. **Functions**:
   - Consumption plan is most cost-effective
   - Optimize execution time

4. **Logs**:
   - Application Insights has free tier (5GB/month)
   - Set retention to 30 days

---

## 🧪 Testing

### Test Checklist

- [ ] **API Health**: `curl .../health` returns healthy
- [ ] **Cosmos DB**: Connected and accessible
- [ ] **Functions**: Deployed and visible in portal
- [ ] **RSS Ingestion**: Runs every 5 minutes
- [ ] **Articles**: Appearing in `raw_articles` container
- [ ] **Stories**: Appearing in `story_clusters` container
- [ ] **Authentication**: Firebase JWT validation works
- [ ] **iOS Integration**: App can fetch stories
- [ ] **Rate Limiting**: Free tier limit enforced
- [ ] **Monitoring**: Application Insights receiving data

### Test Commands

```bash
# 1. Health check
curl https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/health

# 2. API documentation
open https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/docs

# 3. Check Functions are running
az functionapp list --resource-group Newsreel-RG --query "[].{name:name, state:state}" -o table

# 4. Check Container App status
az containerapp show --name newsreel-api --resource-group Newsreel-RG --query "properties.runningStatus"

# 5. View recent logs
az containerapp logs show --name newsreel-api --resource-group Newsreel-RG --tail 50
```

---

## 🚨 Troubleshooting

### Common Issues

**Problem**: API returns 500 error  
**Solution**: Check Container App logs for error details

**Problem**: No articles appearing in Cosmos DB  
**Solution**: Check Function logs, verify RSS feeds are accessible

**Problem**: Authentication fails  
**Solution**: Verify Firebase credentials are set in environment variables

**Problem**: High costs  
**Solution**: Check Cosmos DB RU consumption, ensure Container App scales to zero

**Problem**: Functions not triggering  
**Solution**: Check timer schedule, verify Cosmos DB change feed is active

### Debug Commands

```bash
# View API logs in real-time
az containerapp logs show --name newsreel-api --resource-group Newsreel-RG --follow

# View Function logs in real-time  
az functionapp log tail --name newsreel-func-51689 --resource-group Newsreel-RG

# Check Function status
az functionapp show --name newsreel-func-51689 --resource-group Newsreel-RG --query "{name:name, state:state, httpsOnly:httpsOnly}"

# Query Cosmos DB
az cosmosdb sql database show --account-name newsreel-db-1759951135 --resource-group Newsreel-RG --name newsreel-db

# Check Container App revisions
az containerapp revision list --name newsreel-api --resource-group Newsreel-RG -o table
```

---

## 📞 Support & Resources

### Azure Portal Links

- [Resource Group](https://portal.azure.com/#@onethum.com/resource/subscriptions/d4abcc64-9e59-4094-8d89-10b5d36b6d4c/resourceGroups/Newsreel-RG/overview)
- [Cosmos DB](https://portal.azure.com/#@onethum.com/resource/subscriptions/d4abcc64-9e59-4094-8d89-10b5d36b6d4c/resourceGroups/Newsreel-RG/providers/Microsoft.DocumentDB/databaseAccounts/newsreel-db-1759951135/overview)
- [Function App](https://portal.azure.com/#@onethum.com/resource/subscriptions/d4abcc64-9e59-4094-8d89-10b5d36b6d4c/resourceGroups/Newsreel-RG/providers/Microsoft.Web/sites/newsreel-func-51689/appServices)
- [Container App](https://portal.azure.com/#@onethum.com/resource/subscriptions/d4abcc64-9e59-4094-8d89-10b5d36b6d4c/resourceGroups/Newsreel-RG/providers/Microsoft.App/containerApps/newsreel-api/overview)
- [Application Insights](https://portal.azure.com/#@onethum.com/resource/subscriptions/d4abcc64-9e59-4094-8d89-10b5d36b6d4c/resourceGroups/Newsreel-RG/providers/microsoft.insights/components/newsreel-insights/overview)
- [Cost Management](https://portal.azure.com/#blade/Microsoft_Azure_CostManagement/Menu/overview)

### Documentation

- **Azure Functions**: https://docs.microsoft.com/azure/azure-functions/
- **Container Apps**: https://docs.microsoft.com/azure/container-apps/
- **Cosmos DB**: https://docs.microsoft.com/azure/cosmos-db/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Firebase Auth**: https://firebase.google.com/docs/auth

### Project Documentation

- GitHub Repo: https://github.com/OneThum/newsreel.git
- Product Spec: `/docs/Product_Specification.md`
- Development Roadmap: `/docs/Development_Roadmap.md`

---

## ✅ What's Done

- ✅ All Azure resources deployed
- ✅ Cosmos DB with 6 containers
- ✅ 4 Azure Functions deployed and configured
- ✅ FastAPI REST API deployed
- ✅ Auto-scaling configured (0-3 replicas)
- ✅ HTTPS endpoints secured
- ✅ Monitoring with Application Insights
- ✅ Cost within budget ($77-87/month)
- ✅ Health checks passing
- ✅ Ready for iOS integration

## ⏭️ What's Next

1. Add Anthropic API key → Enable AI summarization
2. Add Firebase credentials → Enable authentication
3. Wait for RSS ingestion → Articles populate Cosmos DB
4. Test from iOS app → Verify end-to-end flow
5. Monitor costs → Stay within budget
6. Expand RSS feeds → Phase 2 (10 → 100 feeds)

---

**Backend Deployed & Ready!** 🚀  
**Now connect your iOS app and start building!** 📱

See [NEXT_STEPS.md](NEXT_STEPS.md) for detailed configuration instructions.
