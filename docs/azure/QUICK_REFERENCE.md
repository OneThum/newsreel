# Newsreel Azure - Quick Reference Card

**Last Updated**: October 8, 2025

---

## 🌐 Essential URLs

| Service | URL |
|---------|-----|
| **API Endpoint** | `https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io` |
| **API Health** | `https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/health` |
| **API Docs (Swagger)** | `https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/docs` |
| **Function App** | `https://newsreel-func-51689.azurewebsites.net` |
| **Azure Portal** | `https://portal.azure.com` |

---

## 📦 Resource Names

| Type | Name |
|------|------|
| **Resource Group** | `Newsreel-RG` |
| **Subscription** | `OneThum-Apps-Subscription` |
| **Subscription ID** | `d4abcc64-9e59-4094-8d89-10b5d36b6d4c` |
| **Region** | `Central US` |
| **Cosmos DB** | `newsreel-db-1759951135` |
| **Database** | `newsreel-db` |
| **Storage** | `newsreelstorage51494` |
| **Function App** | `newsreel-func-51689` |
| **Container Registry** | `newsreelacr` |
| **Container App** | `newsreel-api` |
| **App Insights** | `newsreel-insights` |

---

## 🔑 Environment Variables

### Function App: newsreel-func-51689

```bash
COSMOS_CONNECTION_STRING=AccountEndpoint=https://newsreel-db-1759951135.documents.azure.com:443/;AccountKey=***
COSMOS_DATABASE_NAME=newsreel-db
STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=newsreelstorage51494;***
LOG_LEVEL=INFO
ANTHROPIC_API_KEY=<TODO: Add your key>
FIREBASE_CREDENTIALS=<TODO: Add service account JSON>
TWITTER_BEARER_TOKEN=<Optional>
```

### Container App: newsreel-api

```bash
COSMOS_CONNECTION_STRING=<Same as Functions>
COSMOS_DATABASE_NAME=newsreel-db
FIREBASE_CREDENTIALS=<TODO: Add service account JSON>
FIREBASE_PROJECT_ID=newsreel-865a5
ENVIRONMENT=production
```

---

## ⚡ Quick Commands

### View API Logs
```bash
az containerapp logs show --name newsreel-api --resource-group Newsreel-RG --follow
```

### View Function Logs
```bash
az functionapp log tail --name newsreel-func-51689 --resource-group Newsreel-RG
```

### Check API Health
```bash
curl https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/health
```

### List All Resources
```bash
az resource list --resource-group Newsreel-RG -o table
```

### Redeploy Functions
```bash
cd "/Users/davemac/Library/CloudStorage/OneDrive-OneThumSoftware/One Thum Software/Newsreel/Azure/functions"
func azure functionapp publish newsreel-func-51689
```

### Rebuild & Deploy API
```bash
cd "/Users/davemac/Library/CloudStorage/OneDrive-OneThumSoftware/One Thum Software/Newsreel/Azure/api"
az acr build --registry newsreelacr --image newsreel-api:latest .
```

### Add Environment Variable to Functions
```bash
az functionapp config appsettings set \
  --name newsreel-func-51689 \
  --resource-group Newsreel-RG \
  --settings "KEY_NAME=value"
```

### Add Environment Variable to Container App
```bash
az containerapp update \
  --name newsreel-api \
  --resource-group Newsreel-RG \
  --set-env-vars "KEY_NAME=value"
```

---

## 📊 Cosmos DB Containers

| Container | Partition Key | TTL | Purpose |
|-----------|---------------|-----|---------|
| `raw_articles` | `/published_date` | 30 days | RSS articles |
| `story_clusters` | `/category` | 90 days | Aggregated stories |
| `user_profiles` | `/id` | None | User data |
| `user_interactions` | `/user_id` | 180 days | Tracking |
| `leases` | `/id` | None | Change feed |
| `leases-summarization` | `/id` | None | Change feed |

---

## 🔄 Azure Functions

| Function | Trigger | Schedule |
|----------|---------|----------|
| RSS Ingestion | Timer | Every 5 min |
| Story Clustering | Change Feed | On new articles |
| Summarization | Change Feed | On story updates |
| Breaking News | Timer | Every 2 min |

---

## 📡 API Endpoints

### Public (No Auth)
- `GET /health` - Health check
- `GET /` - Root info
- `GET /docs` - Swagger UI

### Authenticated (Firebase JWT)
- `GET /api/stories/feed` - Personalized feed
- `GET /api/stories/breaking` - Breaking news
- `GET /api/stories/{id}` - Story detail
- `GET /api/stories/{id}/sources` - Source articles
- `POST /api/stories/{id}/interact` - Record interaction
- `GET /api/user/profile` - User profile
- `PUT /api/user/preferences` - Update preferences
- `POST /api/user/device-token` - Register device
- `DELETE /api/user/device-token/{token}` - Unregister device

---

## 💰 Monthly Costs (Estimated)

| Service | Cost |
|---------|------|
| Cosmos DB | $30-35 |
| Container Apps | $25-30 |
| Function App | $5 |
| Storage | $0.50 |
| Container Registry | $5 |
| App Insights | $10 |
| **Azure Total** | **$77-87** |
| Anthropic API | $50-80 (when configured) |
| Twitter API | $100 (optional) |

---

## 🧪 Testing

### Test Health
```bash
curl https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/health
# Expected: {"status":"healthy","cosmos_db":"connected"}
```

### Test with Firebase Token
```bash
TOKEN="<firebase-jwt>"
curl -H "Authorization: Bearer $TOKEN" \
  https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/api/user/profile
```

### Check Cosmos DB
```bash
# Azure Portal → Cosmos DB → newsreel-db-1759951135 → Data Explorer
# Check raw_articles container for articles
```

---

## 🚨 Troubleshooting

### API returns 500
```bash
az containerapp logs show --name newsreel-api --resource-group Newsreel-RG --follow
```

### Functions not running
```bash
az functionapp log tail --name newsreel-func-51689 --resource-group Newsreel-RG
```

### Check costs
```bash
# Azure Portal → Cost Management
open "https://portal.azure.com/#blade/Microsoft_Azure_CostManagement/Menu/overview"
```

---

## 📱 iOS Integration

Update `APIService.swift`:
```swift
private let baseURL = "https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io"
```

Test connection:
```swift
let url = URL(string: "\(baseURL)/health")!
let (data, _) = try await URLSession.shared.data(from: url)
// Should succeed
```

---

## ✅ Pre-Launch Checklist

- [ ] Add Anthropic API key to Functions
- [ ] Add Firebase credentials to Functions
- [ ] Add Firebase credentials to Container App
- [ ] Wait for RSS ingestion
- [ ] Verify articles in Cosmos DB
- [ ] Verify stories being clustered
- [ ] Test API from iOS app
- [ ] Set up budget alerts
- [ ] Monitor logs for errors

---

## 📞 Quick Links

| Resource | Link |
|----------|------|
| **Resource Group** | [Open](https://portal.azure.com/#@onethum.com/resource/subscriptions/d4abcc64-9e59-4094-8d89-10b5d36b6d4c/resourceGroups/Newsreel-RG/overview) |
| **Cosmos DB** | [Open](https://portal.azure.com/#@onethum.com/resource/subscriptions/d4abcc64-9e59-4094-8d89-10b5d36b6d4c/resourceGroups/Newsreel-RG/providers/Microsoft.DocumentDB/databaseAccounts/newsreel-db-1759951135/overview) |
| **Function App** | [Open](https://portal.azure.com/#@onethum.com/resource/subscriptions/d4abcc64-9e59-4094-8d89-10b5d36b6d4c/resourceGroups/Newsreel-RG/providers/Microsoft.Web/sites/newsreel-func-51689/appServices) |
| **Container App** | [Open](https://portal.azure.com/#@onethum.com/resource/subscriptions/d4abcc64-9e59-4094-8d89-10b5d36b6d4c/resourceGroups/Newsreel-RG/providers/Microsoft.App/containerApps/newsreel-api/overview) |
| **Application Insights** | [Open](https://portal.azure.com/#@onethum.com/resource/subscriptions/d4abcc64-9e59-4094-8d89-10b5d36b6d4c/resourceGroups/Newsreel-RG/providers/microsoft.insights/components/newsreel-insights/overview) |
| **Cost Management** | [Open](https://portal.azure.com/#blade/Microsoft_Azure_CostManagement/Menu/overview) |

---

**Keep this handy!** Quick reference for daily operations. 📋

