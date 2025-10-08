# Terraform Infrastructure as Code

Infrastructure automation for Newsreel Azure backend using Terraform.

## What Gets Created

- **Resource Group**: `newsreel-prod-rg`
- **Cosmos DB**: Serverless account with 4 containers
- **Storage Account**: For Azure Functions state
- **Function App**: Python 3.11 consumption plan
- **Container Registry**: For Docker images
- **Container Apps Environment**: Hosting for Story API
- **Application Insights**: Monitoring and logging
- **Key Vault**: Secrets management
- **Notification Hub**: Push notifications (optional)

## Prerequisites

1. Azure CLI installed and authenticated
2. Terraform 1.5+ installed
3. Appropriate Azure subscription access

## Setup

1. **Create `terraform.tfvars`**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. **Edit values**:
   ```hcl
   subscription_id = "d4abcc64-9e59-4094-8d89-10b5d36b6d4c"
   anthropic_api_key = "sk-ant-..."
   twitter_bearer_token = "AAAA..."
   firebase_credentials = "{...}"
   ```

3. **Initialize Terraform**:
   ```bash
   terraform init
   ```

4. **Review plan**:
   ```bash
   terraform plan
   ```

5. **Apply configuration**:
   ```bash
   terraform apply
   ```

## Estimated Costs

| Resource | Monthly Cost |
|----------|--------------|
| Cosmos DB (Serverless) | $5-10 |
| Functions (Consumption) | $10-15 |
| Container Apps | $30-40 |
| Storage | $2-5 |
| Container Registry | $5 |
| Application Insights | $5-10 |
| Key Vault | $0-1 |
| **Total** | **$57-86/month** |

## State Management

Terraform state is stored in Azure Storage:
- Storage Account: `newsreelterraform`
- Container: `tfstate`
- Key: `terraform.tfstate`

## Outputs

After applying, Terraform outputs:
- Cosmos DB endpoint and connection string
- Function App name and URL
- Container App URL
- Application Insights instrumentation key

## Commands

```bash
# Format configuration
terraform fmt

# Validate configuration
terraform validate

# Plan changes
terraform plan

# Apply changes
terraform apply

# Show current state
terraform show

# List resources
terraform state list

# Destroy everything (⚠️ dangerous)
terraform destroy
```

## Status

**Ready**: Structure created  
**Pending**: Implementation (Phase 1)  
**Note**: Requires Azure subscription access to deploy

