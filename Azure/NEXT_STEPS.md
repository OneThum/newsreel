# Newsreel Azure - Next Steps & Configuration

**Date**: October 8, 2025  
**Status**: Backend Deployed, Configuration Needed

---

## 🎯 Priority Actions

### ✅ IMMEDIATE (Do This Now)

#### 1. Add Anthropic API Key (Required for AI Summarization)

**Get API Key:**
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys
4. Create a new key

**Add to Azure Functions:**
```bash
# Replace <your-api-key> with actual key
az functionapp config appsettings set \
  --name newsreel-func-51689 \
  --resource-group Newsreel-RG \
  --settings "ANTHROPIC_API_KEY=<your-api-key>"
```

**Verify:**
```bash
az functionapp config appsettings list \
  --name newsreel-func-51689 \
  --resource-group Newsreel-RG \
  --query "[?name=='ANTHROPIC_API_KEY'].{name:name, value:'***REDACTED***'}" -o table
```

#### 2. Add Firebase Service Account Credentials

**Get Credentials:**
1. Go to Firebase Console: https://console.firebase.google.com/project/newsreel-865a5
2. Click Settings (⚙️) → Project Settings
3. Go to Service Accounts tab
4. Click "Generate New Private Key"
5. Download the JSON file

**Convert JSON to single-line string:**
```bash
# macOS/Linux
cat firebase-adminsdk.json | jq -c . > firebase-compact.json
```

**Add to Function App:**
```bash
# Copy the entire JSON content (as one line)
FIREBASE_CREDS='{"type":"service_account","project_id":"newsreel-865a5",...}'

az functionapp config appsettings set \
  --name newsreel-func-51689 \
  --resource-group Newsreel-RG \
  --settings "FIREBASE_CREDENTIALS=$FIREBASE_CREDS"
```

**Add to Container App (API):**
```bash
az containerapp update \
  --name newsreel-api \
  --resource-group Newsreel-RG \
  --set-env-vars "FIREBASE_CREDENTIALS=$FIREBASE_CREDS" \
                 "FIREBASE_PROJECT_ID=newsreel-865a5"
```

#### 3. Test RSS Ingestion

The RSS function runs every 5 minutes automatically. To test it immediately:

```bash
# View Function App logs to watch for RSS ingestion
az functionapp log tail \
  --name newsreel-func-51689 \
  --resource-group Newsreel-RG
```

Wait for the next 5-minute interval (e.g., :00, :05, :10, :15, etc.) and you should see:
```
RSS ingestion timer triggered
Loading 10 RSS feeds
Fetched X of 10 feeds successfully
RSS ingestion complete: X new articles out of Y total
```

**Manually trigger (if needed):**
```bash
# Get the function's master key
MASTER_KEY=$(az functionapp keys list \
  --name newsreel-func-51689 \
  --resource-group Newsreel-RG \
  --query "masterKey" -o tsv)

# Trigger the function (replace with actual URL from function list)
curl -X POST "https://newsreel-func-51689.azurewebsites.net/admin/functions/RSSIngestion" \
  -H "x-functions-key: $MASTER_KEY"
```

#### 4. Verify Data in Cosmos DB

After RSS ingestion runs:

```bash
# Option 1: Azure Portal
# 1. Go to https://portal.azure.com
# 2. Navigate to Cosmos DB → newsreel-db-1759951135
# 3. Open Data Explorer
# 4. Expand newsreel-db → raw_articles
# 5. Should see articles from RSS feeds

# Option 2: Azure CLI (query count)
az cosmosdb sql container show \
  --account-name newsreel-db-1759951135 \
  --resource-group Newsreel-RG \
  --database-name newsreel-db \
  --name raw_articles \
  --query "resource.id"
```

---

## 📱 iOS App Integration

### Update API Endpoint

Update your `APIService.swift` base URL:

```swift
// In APIService.swift
private let baseURL = "https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io"
```

### Test API from iOS

1. **Health Check (No Auth):**
```swift
// In your view model or service
let url = URL(string: "\(baseURL)/health")!
let (data, _) = try await URLSession.shared.data(from: url)
let health = try JSONDecoder().decode(HealthResponse.self, from: data)
print("API Status: \(health.status)")
```

2. **Test Authenticated Endpoint:**
```swift
// After user signs in with Firebase
guard let idToken = try await Auth.auth().currentUser?.getIDToken() else {
    return
}

var request = URLRequest(url: URL(string: "\(baseURL)/api/user/profile")!)
request.setValue("Bearer \(idToken)", forHTTPHeaderField: "Authorization")

let (data, response) = try await URLSession.shared.data(for: request)
// Should auto-create user profile and return it
```

3. **Test Story Feed:**
```swift
var request = URLRequest(url: URL(string: "\(baseURL)/api/stories/feed")!)
request.setValue("Bearer \(idToken)", forHTTPHeaderField: "Authorization")

let (data, _) = try await URLSession.shared.data(for: request)
let feed = try JSONDecoder().decode(FeedResponse.self, from: data)
print("Stories: \(feed.stories.count)")
```

---

## 🔍 Monitoring & Debugging

### View Function Logs (Real-time)

```bash
# All functions
az functionapp log tail \
  --name newsreel-func-51689 \
  --resource-group Newsreel-RG

# Specific time range
az monitor app-insights query \
  --app newsreel-insights \
  --analytics-query "traces | where timestamp > ago(1h) | order by timestamp desc | take 50"
```

### View API Logs (Real-time)

```bash
az containerapp logs show \
  --name newsreel-api \
  --resource-group Newsreel-RG \
  --follow
```

### Check Cosmos DB Metrics

```bash
# Request Units consumed (last hour)
az monitor metrics list \
  --resource newsreel-db-1759951135 \
  --resource-group Newsreel-RG \
  --resource-type "Microsoft.DocumentDB/databaseAccounts" \
  --metric "TotalRequestUnits" \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ) \
  --interval PT1M
```

### Application Insights Dashboard

```bash
# Open in browser
open "https://portal.azure.com/#@onethum.com/resource/subscriptions/d4abcc64-9e59-4094-8d89-10b5d36b6d4c/resourceGroups/Newsreel-RG/providers/microsoft.insights/components/newsreel-insights/overview"
```

---

## 💰 Cost Monitoring

### Set Up Budget Alert

```bash
# Create budget for $100/month with 80% alert
az consumption budget create \
  --budget-name newsreel-monthly-budget \
  --amount 100 \
  --category Cost \
  --time-grain Monthly \
  --start-date $(date +%Y-%m-01) \
  --end-date 2026-12-31 \
  --resource-group Newsreel-RG \
  --notifications "Actual_GreaterThan_80_Percent={\"enabled\":true,\"operator\":\"GreaterThan\",\"threshold\":80,\"contactEmails\":[\"dave@onethum.com\"]}"
```

### Check Current Costs

```bash
# Month-to-date costs
az consumption usage list \
  --start-date $(date +%Y-%m-01) \
  --end-date $(date +%Y-%m-%d) \
  --query "[?contains(instanceId, 'Newsreel-RG')].{service:meterCategory, cost:pretaxCost}" \
  --output table

# Or use Azure Portal
open "https://portal.azure.com/#blade/Microsoft_Azure_CostManagement/Menu/overview"
```

---

## 🧪 Testing the Full Pipeline

### Test End-to-End Flow

1. **RSS Ingestion** (every 5 min) → Creates articles in `raw_articles`
2. **Story Clustering** (change feed) → Groups articles into `story_clusters`
3. **Summarization** (change feed) → Generates AI summaries (needs Anthropic key)
4. **API Request** → Returns personalized feed to iOS app

**Watch the Flow:**

```bash
# Terminal 1: Watch Functions
az functionapp log tail --name newsreel-func-51689 --resource-group Newsreel-RG

# Terminal 2: Watch API
az containerapp logs show --name newsreel-api --resource-group Newsreel-RG --follow

# Terminal 3: Query Cosmos DB
# After 5 minutes, check article count
# Should see articles appearing in raw_articles
# Then story_clusters should populate
# Then summaries should be added (once Anthropic key is configured)
```

---

## 🚀 Optional: Add Twitter Monitoring (Phase 2)

**Get Twitter API Access:**
1. Go to https://developer.twitter.com/
2. Apply for API access (Basic tier: $100/month)
3. Get Bearer Token

**Add to Functions:**
```bash
az functionapp config appsettings set \
  --name newsreel-func-51689 \
  --resource-group Newsreel-RG \
  --settings "TWITTER_BEARER_TOKEN=<your-token>"
```

**Note**: Breaking news monitor will work without Twitter, but won't have real-time triggers. It will still detect breaking stories based on RSS source counts.

---

## 📊 Performance Tuning

### If API is Slow

**Increase Container App Resources:**
```bash
az containerapp update \
  --name newsreel-api \
  --resource-group Newsreel-RG \
  --cpu 1.0 \
  --memory 2.0Gi
```

### If Functions Timeout

**Increase Function Timeout:**
```bash
# Already set to 10 minutes in host.json
# If needed, can increase storage account performance tier
```

### If Cosmos DB Throttles

**Check RU consumption:**
```bash
# If consistently hitting limits, consider:
# 1. Adding caching layer in API
# 2. Optimizing queries
# 3. Using provisioned throughput for specific containers
```

---

## 🔄 Update Deployment

### Update Functions Code

```bash
cd "/Users/davemac/Library/CloudStorage/OneDrive-OneThumSoftware/One Thum Software/Newsreel/Azure/functions"

# Make code changes
# Then redeploy:
func azure functionapp publish newsreel-func-51689
```

### Update API Code

```bash
cd "/Users/davemac/Library/CloudStorage/OneDrive-OneThumSoftware/One Thum Software/Newsreel/Azure/api"

# Make code changes
# Then rebuild and deploy:
az acr build --registry newsreelacr --image newsreel-api:latest .

# Container App auto-updates, or force restart:
az containerapp revision restart \
  --name newsreel-api \
  --resource-group Newsreel-RG \
  --revision-name $(az containerapp revision list \
    --name newsreel-api \
    --resource-group Newsreel-RG \
    --query "[0].name" -o tsv)
```

---

## 🎓 Learning Resources

### Monitor Your Deployment
- **Application Insights**: https://portal.azure.com/#@onethum.com/resource/subscriptions/d4abcc64-9e59-4094-8d89-10b5d36b6d4c/resourceGroups/Newsreel-RG/providers/microsoft.insights/components/newsreel-insights
- **Cosmos DB**: https://portal.azure.com/#@onethum.com/resource/subscriptions/d4abcc64-9e59-4094-8d89-10b5d36b6d4c/resourceGroups/Newsreel-RG/providers/Microsoft.DocumentDB/databaseAccounts/newsreel-db-1759951135
- **Container App**: https://portal.azure.com/#@onethum.com/resource/subscriptions/d4abcc64-9e59-4094-8d89-10b5d36b6d4c/resourceGroups/Newsreel-RG/providers/Microsoft.App/containerApps/newsreel-api

### Documentation
- Azure Functions Python: https://docs.microsoft.com/azure/azure-functions/functions-reference-python
- Azure Container Apps: https://docs.microsoft.com/azure/container-apps/
- Cosmos DB: https://docs.microsoft.com/azure/cosmos-db/
- FastAPI: https://fastapi.tiangolo.com/

---

## ✅ Verification Checklist

Before connecting iOS app, verify:

- [ ] **Anthropic API key added to Functions**
  ```bash
  az functionapp config appsettings list --name newsreel-func-51689 --resource-group Newsreel-RG --query "[?name=='ANTHROPIC_API_KEY']"
  ```

- [ ] **Firebase credentials added to Functions and API**
  ```bash
  az functionapp config appsettings list --name newsreel-func-51689 --resource-group Newsreel-RG --query "[?name=='FIREBASE_CREDENTIALS']"
  ```

- [ ] **RSS ingestion running**
  ```bash
  # Check logs for "RSS ingestion complete"
  az functionapp log tail --name newsreel-func-51689 --resource-group Newsreel-RG
  ```

- [ ] **Articles in Cosmos DB**
  ```bash
  # Open Azure Portal → Cosmos DB → Data Explorer → raw_articles
  # Should see articles
  ```

- [ ] **Stories being clustered**
  ```bash
  # Check story_clusters container
  # Should see stories with multiple sources
  ```

- [ ] **API health check passing**
  ```bash
  curl https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/health
  # Should return: {"status":"healthy",...}
  ```

- [ ] **Cost monitoring enabled**
  ```bash
  az consumption budget list --resource-group Newsreel-RG
  ```

---

## 🐛 Common Issues & Solutions

### "Function not found" error
- **Cause**: Functions not deployed properly
- **Fix**: `func azure functionapp publish newsreel-func-51689`

### "Cannot connect to Cosmos DB"
- **Cause**: Connection string not set or incorrect
- **Fix**: Verify `COSMOS_CONNECTION_STRING` in app settings

### "Authentication failed" from iOS
- **Cause**: Firebase credentials not configured
- **Fix**: Add `FIREBASE_CREDENTIALS` to both Functions and API

### "No articles appearing"
- **Cause**: RSS feeds may be rate-limited or down
- **Fix**: Check logs, verify feeds are accessible, wait for next run

### High costs
- **Cause**: Too many RUs consumed, or container not scaling to zero
- **Fix**: Check metrics, optimize queries, verify auto-scale settings

---

## 📞 Support

If you encounter issues:

1. **Check logs first**: Function logs, Container App logs, Application Insights
2. **Verify configuration**: All environment variables set correctly
3. **Check Azure Service Health**: https://status.azure.com/
4. **Review documentation**: `/docs` folder and implementation guides

---

**Next Actions**: Add Anthropic & Firebase credentials, then test the full pipeline! 🚀

