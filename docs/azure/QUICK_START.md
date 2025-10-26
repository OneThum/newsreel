# Quick Start Guide - Newsreel Azure Backend

This guide will help you quickly deploy and test the Newsreel Azure backend.

---

## Prerequisites Checklist

- [ ] Azure subscription with Contributor access
- [ ] Azure CLI installed and logged in
- [ ] Python 3.11 installed
- [ ] Docker installed (for API deployment)
- [ ] Azure Functions Core Tools v4
- [ ] Anthropic API key
- [ ] Firebase service account credentials

---

## 1. Deploy Infrastructure (5 minutes)

```bash
cd Azure/infrastructure

# Initialize Terraform
terraform init

# Review plan
terraform plan

# Deploy (approve when prompted)
terraform apply

# Note the outputs - you'll need these
```

**Outputs to save:**
- Cosmos DB connection string
- Storage account connection string
- Function App name
- Container Apps environment name

---

## 2. Configure Secrets (2 minutes)

### Create local.settings.json for Functions

```bash
cd ../functions
cp local.settings.json.example local.settings.json
```

Edit `local.settings.json` with your values:
```json
{
  "Values": {
    "COSMOS_CONNECTION_STRING": "<from terraform output>",
    "COSMOS_DATABASE_NAME": "newsreel-db",
    "STORAGE_CONNECTION_STRING": "<from terraform output>",
    "ANTHROPIC_API_KEY": "<your-key>",
    "FIREBASE_CREDENTIALS": "<firebase-service-account-json>",
    "LOG_LEVEL": "INFO"
  }
}
```

---

## 3. Deploy Azure Functions (5 minutes)

```bash
cd Azure/functions

# Install dependencies locally (for testing)
pip install -r requirements.txt

# Test locally (optional)
func start

# Deploy to Azure
func azure functionapp publish <your-function-app-name>
```

**Verify deployment:**
```bash
# Check functions are running
func azure functionapp list-functions <your-function-app-name>
```

---

## 4. Deploy Story API (5 minutes)

```bash
cd ../api

# Build Docker image
docker build -t newsreel-api:latest .

# Login to Azure Container Registry
az acr login --name <your-acr-name>

# Tag image
docker tag newsreel-api:latest <your-acr>.azurecr.io/newsreel-api:latest

# Push image
docker push <your-acr>.azurecr.io/newsreel-api:latest

# Deploy to Container Apps
az containerapp update \
  --name newsreel-api \
  --resource-group newsreel-prod-rg \
  --image <your-acr>.azurecr.io/newsreel-api:latest \
  --set-env-vars \
    COSMOS_CONNECTION_STRING=secretref:cosmos-connection \
    COSMOS_DATABASE_NAME=newsreel-db \
    FIREBASE_CREDENTIALS=secretref:firebase-creds \
    ENVIRONMENT=production
```

---

## 5. Test Deployment (3 minutes)

### Test API Health

```bash
# Get Container App URL
CONTAINER_APP_URL=$(az containerapp show \
  --name newsreel-api \
  --resource-group newsreel-prod-rg \
  --query "properties.configuration.ingress.fqdn" -o tsv)

# Test health endpoint
curl https://$CONTAINER_APP_URL/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-10-08T...",
  "cosmos_db": "connected"
}
```

### Test with Firebase Token

Get a Firebase ID token from your iOS app or Firebase Console, then:

```bash
# Test authenticated endpoint
curl https://$CONTAINER_APP_URL/api/user/profile \
  -H "Authorization: Bearer <your-firebase-token>"
```

### Check Functions are Running

```bash
# Check Function App logs
az functionapp log tail \
  --name <your-function-app-name> \
  --resource-group newsreel-prod-rg
```

Look for:
- "RSS ingestion timer triggered" (every 5 minutes)
- "Processing X documents from change feed" (when articles are added)

---

## 6. View Cosmos DB Data (2 minutes)

```bash
# Open Azure Portal
open https://portal.azure.com

# Navigate to: Cosmos DB → newsreel-db → Data Explorer
# You should see containers:
# - raw_articles (will populate after first RSS run)
# - story_clusters (will populate after clustering)
# - user_profiles (will populate after first API call)
```

---

## 7. Monitor Costs (1 minute)

```bash
# Open Cost Management
open "https://portal.azure.com/#blade/Microsoft_Azure_CostManagement/Menu/overview"

# Set up budget alert for $150/month:
az consumption budget create \
  --budget-name newsreel-budget \
  --amount 150 \
  --time-grain Monthly \
  --start-date $(date +%Y-%m-01) \
  --end-date 2026-12-31
```

---

## Troubleshooting

### Functions not deploying
```bash
# Check Function App status
az functionapp show \
  --name <function-app-name> \
  --resource-group newsreel-prod-rg \
  --query "state"

# View deployment logs
az functionapp log deployment show \
  --name <function-app-name> \
  --resource-group newsreel-prod-rg
```

### API not accessible
```bash
# Check Container App status
az containerapp show \
  --name newsreel-api \
  --resource-group newsreel-prod-rg \
  --query "properties.runningStatus"

# View logs
az containerapp logs show \
  --name newsreel-api \
  --resource-group newsreel-prod-rg
```

### Cosmos DB connection issues
```bash
# Test connection string
az cosmosdb show \
  --name <cosmos-account-name> \
  --resource-group newsreel-prod-rg \
  --query "documentEndpoint"

# List keys
az cosmosdb keys list \
  --name <cosmos-account-name> \
  --resource-group newsreel-prod-rg
```

---

## Next Steps

After successful deployment:

1. **Monitor Application Insights**
   - Portal → Application Insights → newsreel-insights
   - Check for errors, performance metrics

2. **Test iOS App Integration**
   - Update iOS app API endpoint to Container App URL
   - Test authentication flow
   - Test feed loading
   - Test story interactions

3. **Expand RSS Feeds** (Phase 2)
   - Update `shared/rss_feeds.py` with 90 more feeds
   - Redeploy functions

4. **Enable Twitter Monitoring** (Phase 2)
   - Get Twitter API credentials
   - Update environment variables
   - Implement Twitter streaming in breaking_news_monitor

5. **Optimize Personalization**
   - Monitor user interactions
   - Tune recommendation algorithm
   - A/B test different scoring strategies

---

## Configuration Files Reference

**Functions:**
- `functions/host.json` - Function runtime config
- `functions/requirements.txt` - Python dependencies
- `functions/local.settings.json` - Environment variables

**API:**
- `api/Dockerfile` - Container image definition
- `api/requirements.txt` - Python dependencies
- `api/app/config.py` - Application settings

**Shared:**
- `functions/shared/config.py` - Shared configuration
- `functions/shared/rss_feeds.py` - RSS feed list

---

## Support Resources

- **Azure Portal**: https://portal.azure.com
- **Application Insights**: Dashboard for logs/metrics
- **Cosmos DB Data Explorer**: View/query data
- **Container Apps Logs**: Real-time API logs
- **Function App Logs**: Real-time function logs

---

## Emergency Rollback

If something goes wrong:

```bash
# Stop Function App
az functionapp stop --name <function-app-name> --resource-group newsreel-prod-rg

# Stop Container App
az containerapp revision deactivate \
  --name newsreel-api \
  --resource-group newsreel-prod-rg \
  --revision <revision-name>

# Restore from backup (if needed)
# Cosmos DB has point-in-time restore for 30 days
```

---

**Total Deployment Time**: ~20 minutes  
**Estimated Monthly Cost**: $86.50 (well under $150 budget)

You're all set! 🚀

