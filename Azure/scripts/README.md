# Deployment Scripts

Automation scripts for deploying Newsreel Azure backend services.

## Scripts

### `deploy-functions.sh`
Deploys Azure Functions to the Function App.

```bash
./deploy-functions.sh
```

**What it does**:
1. Installs Python dependencies to `.python_packages/`
2. Packages function code
3. Deploys to Azure Functions
4. Verifies deployment

**Prerequisites**:
- Azure CLI authenticated
- Function App already created (via Terraform)
- Python 3.11 installed

### `deploy-api.sh`
Builds and deploys the FastAPI Story API to Azure Container Apps.

```bash
./deploy-api.sh
```

**What it does**:
1. Builds Docker image
2. Pushes to Azure Container Registry
3. Deploys to Container Apps
4. Verifies deployment

**Prerequisites**:
- Azure CLI authenticated
- Docker installed and running
- Container Apps environment created (via Terraform)

### `setup-cosmos.sh`
Initializes Cosmos DB with sample data (optional).

```bash
./setup-cosmos.sh
```

**What it does**:
1. Creates database and containers (if not exist)
2. Configures indexing policies
3. Optionally loads sample data for testing

**Prerequisites**:
- Azure CLI authenticated
- Cosmos DB account created (via Terraform)

### `check-deployment.sh`
Verifies all services are running correctly.

```bash
./check-deployment.sh
```

**What it does**:
1. Checks Function App status
2. Tests Container App health endpoint
3. Verifies Cosmos DB connectivity
4. Reports any issues

## Usage

**Full deployment workflow**:

```bash
# 1. Deploy infrastructure (first time only)
cd ../infrastructure
terraform apply

# 2. Deploy functions
cd ../scripts
./deploy-functions.sh

# 3. Deploy API
./deploy-api.sh

# 4. Verify everything works
./check-deployment.sh
```

**Updating after code changes**:

```bash
# Update functions only
./deploy-functions.sh

# Update API only
./deploy-api.sh
```

## Environment Variables

Scripts read from:
1. Terraform outputs (via `terraform output -json`)
2. Azure CLI (current subscription)
3. Environment variables (if set)

## Troubleshooting

**Function deployment fails**:
```bash
# Check Function App logs
az functionapp log tail --name newsreel-prod-func --resource-group newsreel-prod-rg
```

**Container App deployment fails**:
```bash
# Check Container App logs
az containerapp logs show --name story-api --resource-group newsreel-prod-rg --follow
```

**Docker build fails**:
```bash
# Build with verbose output
docker build -t story-api:latest --progress=plain ../api
```

## Status

**Ready**: Script structure created  
**Pending**: Implementation (Phase 1)  
**Note**: Scripts will be implemented as services are built

