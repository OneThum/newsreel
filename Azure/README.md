# Newsreel Azure Backend

This directory contains all Azure backend infrastructure and services for Newsreel.

## Structure

```
Azure/
├── functions/          # Azure Functions (Python 3.11)
│   ├── rss_ingestion/     # RSS feed polling (every 5 min)
│   ├── story_clustering/  # Article clustering (change feed trigger)
│   ├── summarization/     # AI summarization (event-driven)
│   └── requirements.txt   # Python dependencies
│
├── api/                # FastAPI Story API (Container Apps)
│   ├── app/
│   │   ├── main.py        # FastAPI application
│   │   ├── routers/       # API routes
│   │   ├── models/        # Data models
│   │   └── services/      # Business logic
│   ├── Dockerfile         # Container image
│   └── requirements.txt   # Python dependencies
│
├── infrastructure/     # Terraform IaC
│   ├── main.tf           # Main Terraform config
│   ├── variables.tf      # Variable definitions
│   ├── outputs.tf        # Output values
│   └── terraform.tfvars  # Variable values (not committed)
│
└── scripts/           # Deployment scripts
    ├── deploy-functions.sh
    ├── deploy-api.sh
    └── setup-cosmos.sh
```

## Services

### Azure Functions (Consumption Plan)

**RSS Ingestion** (Timer: Every 5 minutes)
- Polls 100 RSS feeds in parallel
- HTTP 304 conditional requests for efficiency
- Stores raw articles in Cosmos DB

**Story Clustering** (Cosmos Change Feed)
- Groups related articles using fingerprinting
- Detects breaking news velocity
- Triggers summarization when 2+ sources available

**Summarization** (Event-driven)
- Calls Claude API for multi-source synthesis
- Implements prompt caching for cost optimization
- Tracks version history

**Breaking News Monitor** (Timer: Every 2 minutes)
- Monitors Twitter for breaking news signals
- Triggers immediate RSS verification
- Queues push notifications

### Story API (Azure Container Apps)

**FastAPI REST API** with endpoints:
- `GET /api/stories/feed` - Personalized feed
- `GET /api/stories/{id}` - Story detail
- `GET /api/stories/{id}/sources` - Source articles
- `POST /api/stories/{id}/interact` - Record interactions
- `GET /api/user/profile` - User profile
- `PUT /api/user/preferences` - Update preferences
- `GET /health` - Health check

**Features**:
- Firebase JWT authentication
- Cosmos DB integration
- In-memory caching (5-min TTL)
- Auto-scaling (0-3 instances)

## Database (Cosmos DB Serverless)

**Containers**:
- `raw_articles` - Partition: /published_date, TTL: 30 days
- `story_clusters` - Partition: /category, TTL: 90 days
- `user_profiles` - Partition: /id, No TTL
- `user_interactions` - Partition: /user_id, TTL: 180 days

## Deployment

### Prerequisites
- Azure CLI installed and authenticated
- Terraform installed
- Python 3.11+
- Docker (for Container Apps)

### Quick Start

1. **Set up Terraform backend**:
   ```bash
   cd infrastructure
   ./setup-backend.sh
   ```

2. **Configure variables**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

3. **Deploy infrastructure**:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

4. **Deploy functions**:
   ```bash
   cd ../scripts
   ./deploy-functions.sh
   ```

5. **Deploy API**:
   ```bash
   ./deploy-api.sh
   ```

For detailed instructions, see [Azure Setup Guide](../docs/Azure_Setup_Guide.md)

## Monitoring

- **Application Insights**: Centralized logging and monitoring
- **Cost Alerts**: Budget alerts at $250/month (85% of target)
- **Health Checks**: API health endpoint for uptime monitoring

## Cost Management

**Target**: $96/month Azure services (within $150 budget)

| Service | Monthly Cost |
|---------|--------------|
| Cosmos DB (Serverless) | $5-10 |
| Azure Functions | $10-15 |
| Container Apps | $30-40 |
| Storage | $2-5 |
| Application Insights | $5-10 |

See [Cost Management Guide](../docs/Cost_Management.md) for tracking and optimization.

## Development

**Local Testing**:
- Functions: `cd functions && func start`
- API: `cd api && uvicorn app.main:app --reload`

**Environment Variables**:
- See `.env.example` files in each directory
- Never commit secrets to git

## Status

**Current**: Structure created, ready for implementation  
**Next**: Deploy once Azure subscription access is granted  
**Blocked**: Need access to Newsreel Subscription (d4abcc64-9e59-4094-8d89-10b5d36b6d4c)

