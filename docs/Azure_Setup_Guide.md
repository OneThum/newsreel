# Azure Setup Guide for Newsreel

This guide walks through setting up the Azure infrastructure for Newsreel.

---

## ⚠️ CRITICAL: Budget and Resource Guidelines

**BEFORE creating ANY new resource, read this:**

### Budget Constraints (HARD LIMITS)
- **Azure Maximum**: $150/month - CANNOT BE EXCEEDED
- **Total Project Maximum**: $300/month - CANNOT BE EXCEEDED

### Resource Reuse Policy
**ALWAYS check for existing resources before creating new ones.**

All resources MUST be within the **Newsreel Subscription**:
- Subscription ID: `d4abcc64-9e59-4094-8d89-10b5d36b6d4c`
- Directory: One Thum Software (onethum.com)

---

## Prerequisites

- Azure subscription (Newsreel Subscription)
- Azure CLI installed (`brew install azure-cli` on macOS)
- Terraform installed (`brew install terraform`)
- Python 3.11+ installed
- Git configured

---

## Step 0: Check for Existing Resources (DO THIS FIRST!)

**Before proceeding with any setup, check what already exists:**

```bash
# Login to Azure first
az login

# Set subscription
az account set --subscription "d4abcc64-9e59-4094-8d89-10b5d36b6d4c"

# List ALL existing resources
az resource list --output table

# List resource groups
az group list --output table

# Check for specific services
az cosmosdb list --output table
az functionapp list --output table
az storage account list --output table
az containerapp list --output table
az webapp list --output table

# Check current month's costs
az consumption usage list \
  --start-date $(date -d "$(date +%Y-%m-01)" +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --output table
```

**If you find existing resources**:
1. Evaluate if they can be repurposed for Newsreel
2. Check their current costs
3. Document why you need a new resource if creating one
4. Get approval before creating new resources

---

## Step 1: Azure CLI Login

```bash
# Login to Azure
az login

# Set your subscription (if you have multiple)
az account list --output table
az account set --subscription "d4abcc64-9e59-4094-8d89-10b5d36b6d4c"

# Verify
az account show
```

---

## Step 2: Create Service Principal for Terraform

```bash
# Create service principal
az ad sp create-for-rbac \
  --name "newsreel-terraform-sp" \
  --role Contributor \
  --scopes /subscriptions/d4abcc64-9e59-4094-8d89-10b5d36b6d4c

# Save the output - you'll need:
# - appId (client_id)
# - password (client_secret)
# - tenant
```

Store these credentials securely. You'll use them for Terraform authentication.

---

## Step 3: Create Terraform Backend Storage

Terraform needs a place to store state.

```bash
# Create resource group for Terraform
az group create \
  --name newsreel-terraform-rg \
  --location westus2

# Create storage account
az storage account create \
  --name newsreelterraform \
  --resource-group newsreel-terraform-rg \
  --location westus2 \
  --sku Standard_LRS

# Get storage account key
ACCOUNT_KEY=$(az storage account keys list \
  --resource-group newsreel-terraform-rg \
  --account-name newsreelterraform \
  --query '[0].value' -o tsv)

# Create blob container for state
az storage container create \
  --name tfstate \
  --account-name newsreelterraform \
  --account-key $ACCOUNT_KEY
```

---

## Step 4: Configure Terraform Variables

Create `Azure/infrastructure/terraform.tfvars`:

```hcl
# Do NOT commit this file - it's in .gitignore

environment = "prod"
location    = "westus2"

# Get this from Anthropic (https://console.anthropic.com/)
anthropic_api_key = "sk-ant-..."

# Get this from Twitter Developer Portal
twitter_bearer_token = "AAAA..."

# Get this from Firebase Console (service account JSON as string)
firebase_credentials = "{\"type\":\"service_account\",...}"
```

---

## Step 5: Initialize Terraform

```bash
cd Azure/infrastructure

# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Plan deployment (see what will be created)
terraform plan

# If everything looks good, apply
terraform apply
```

This will create:
- Resource Group
- Cosmos DB (serverless)
- Storage Account
- Function App
- Container Registry
- Container Apps Environment
- Application Insights
- Notification Hub

**Expected time**: 10-15 minutes

---

## Step 6: Verify Deployment

```bash
# List all resources
az resource list \
  --resource-group newsreel-prod-rg \
  --output table

# Get Cosmos DB endpoint
az cosmosdb show \
  --name newsreel-prod-cosmos \
  --resource-group newsreel-prod-rg \
  --query documentEndpoint

# Get Function App URL
az functionapp show \
  --name newsreel-prod-func \
  --resource-group newsreel-prod-rg \
  --query defaultHostName
```

---

## Step 7: Set Up Cosmos DB Containers

The Terraform script creates the database and containers, but you can verify:

```bash
# Get connection string
COSMOS_CONN=$(az cosmosdb keys list \
  --name newsreel-prod-cosmos \
  --resource-group newsreel-prod-rg \
  --type connection-strings \
  --query 'connectionStrings[0].connectionString' -o tsv)

echo $COSMOS_CONN
```

Containers created:
- `raw_articles` (partition key: `/published_date`)
- `story_clusters` (partition key: `/category`)
- `user_profiles` (partition key: `/id`)
- `user_interactions` (partition key: `/user_id`)

---

## Step 8: Deploy Azure Functions

```bash
cd Azure/functions

# Install dependencies
pip install -r requirements.txt --target .python_packages/lib/site-packages

# Deploy
func azure functionapp publish newsreel-prod-func
```

Or use the deployment script:

```bash
cd Azure
./scripts/deploy-functions.sh
```

---

## Step 9: Deploy Container Apps

```bash
cd Azure

# Build and push Story API
./scripts/deploy-containers.sh
```

This will:
1. Build Docker image
2. Push to Azure Container Registry
3. Deploy to Container Apps
4. Scale to zero when idle

---

## Step 10: Configure Secrets in Key Vault

```bash
# Create Key Vault
az keyvault create \
  --name newsreel-prod-kv \
  --resource-group newsreel-prod-rg \
  --location westus2

# Add secrets
az keyvault secret set \
  --vault-name newsreel-prod-kv \
  --name "AnthropicApiKey" \
  --value "sk-ant-..."

az keyvault secret set \
  --vault-name newsreel-prod-kv \
  --name "TwitterBearerToken" \
  --value "AAAA..."

az keyvault secret set \
  --vault-name newsreel-prod-kv \
  --name "FirebaseCredentials" \
  --file path/to/firebase-adminsdk.json
```

---

## Step 11: Set Up Monitoring

### Application Insights

Already created by Terraform. Get the instrumentation key:

```bash
az monitor app-insights component show \
  --app newsreel-prod-insights \
  --resource-group newsreel-prod-rg \
  --query instrumentationKey
```

### Cost Alerts

```bash
# Create budget alert at $250/month (85% of $300 target)
az consumption budget create \
  --budget-name newsreel-monthly-budget \
  --amount 300 \
  --time-grain Monthly \
  --start-date $(date +%Y-%m-01) \
  --end-date 2026-12-31 \
  --resource-group newsreel-prod-rg
```

---

## Step 12: Test the Deployment

### Test Health Endpoint

```bash
# Get Container App URL
STORY_API_URL=$(az containerapp show \
  --name story-api \
  --resource-group newsreel-prod-rg \
  --query 'properties.configuration.ingress.fqdn' -o tsv)

# Test health endpoint
curl https://$STORY_API_URL/health
```

Expected response:
```json
{
  "status": "healthy",
  "checks": {
    "api": "healthy",
    "cosmos_db": "healthy",
    "cache": "healthy"
  }
}
```

### Test RSS Ingestion

```bash
# Manually trigger RSS ingestion function
az functionapp function invoke \
  --name newsreel-prod-func \
  --resource-group newsreel-prod-rg \
  --function-name rss_ingestion_timer
```

Check Application Insights logs to see if articles were fetched.

---

## Cost Monitoring

### View Current Costs

```bash
# Current month costs
az consumption usage list \
  --start-date $(date -d "$(date +%Y-%m-01)" +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d)

# Or use Azure Portal
# Cost Management + Billing → Cost Analysis
```

### Expected Monthly Costs

| Service | Cost |
|---------|------|
| Cosmos DB | $5-10 |
| Functions | $10-15 |
| Container Apps | $30-40 |
| Storage | $2-5 |
| Insights | $5-10 |
| **Total (Azure only)** | **~$50-80** |

Plus:
- Anthropic Claude: $80
- Twitter API: $100

**Total: ~$230-280/month**

---

## Troubleshooting

### Terraform Fails

```bash
# Check detailed error
terraform apply -debug

# Force recreate a resource
terraform taint azurerm_cosmosdb_account.main
terraform apply
```

### Function App Not Starting

```bash
# Check logs
az functionapp log tail \
  --name newsreel-prod-func \
  --resource-group newsreel-prod-rg

# Restart function app
az functionapp restart \
  --name newsreel-prod-func \
  --resource-group newsreel-prod-rg
```

### Container App Not Responding

```bash
# Check logs
az containerapp logs show \
  --name story-api \
  --resource-group newsreel-prod-rg \
  --follow

# Check revision status
az containerapp revision list \
  --name story-api \
  --resource-group newsreel-prod-rg \
  --output table
```

### Cosmos DB Throttling

```bash
# Check RU consumption
az cosmosdb sql database throughput show \
  --account-name newsreel-prod-cosmos \
  --name newsapp-db \
  --resource-group newsreel-prod-rg
```

If you're getting throttled frequently:
1. Optimize queries
2. Add caching
3. Consider provisioned throughput (temporary)

---

## Cleanup (Destroy Everything)

**⚠️ Warning**: This will delete all resources and data.

```bash
cd Azure/infrastructure

# Destroy everything
terraform destroy

# Or delete resource group
az group delete \
  --name newsreel-prod-rg \
  --yes --no-wait
```

---

## Next Steps

1. ✅ Azure infrastructure deployed
2. → Set up Firebase project (see Firebase_Setup_Guide.md)
3. → Configure RSS feeds (see RSS_Configuration.md)
4. → Begin iOS app development
5. → Set up CI/CD pipeline

---

## Useful Commands Reference

```bash
# Azure CLI
az login
az account list
az account set --subscription "..."
az group list
az resource list --resource-group newsreel-prod-rg

# Terraform
terraform init
terraform plan
terraform apply
terraform destroy
terraform state list
terraform output

# Function Apps
func start                    # Run locally
func azure functionapp publish
func azure functionapp logstream

# Docker (for Container Apps)
docker build -t story-api .
docker run -p 8000:8000 story-api
docker tag story-api newsreelprodacr.azurecr.io/story-api:latest
docker push newsreelprodacr.azurecr.io/story-api:latest
```

---

## Support Resources

- **Azure Docs**: https://docs.microsoft.com/azure/
- **Terraform Azure Provider**: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs
- **Azure Functions Python**: https://docs.microsoft.com/azure/azure-functions/functions-reference-python
- **Cosmos DB**: https://docs.microsoft.com/azure/cosmos-db/

---

**Document Owner**: DevOps Team  
**Last Updated**: October 8, 2025  
**Next Review**: After initial deployment

