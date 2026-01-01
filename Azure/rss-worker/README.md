# Newsreel RSS Worker

**Always-on Container App for bulletproof RSS feed ingestion**

## Overview

This replaces the flaky Azure Functions timer-based RSS ingestion with a reliable queue-based architecture.

### Before (Flaky)
```
Timer (10s) → Azure Function → Direct RSS Fetch → Cosmos DB
                    ↓
        Cold starts, timeouts, dropped feeds 😢
```

### After (Bulletproof)
```
Timer (10s) → Azure Function → Service Bus Queue → Container App Worker → Cosmos DB
                    ↓                                      ↓
        Lightweight, fast                    Always-on, retry logic,
        (just pushes URLs)                   circuit breaker 💪
```

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Azure Function │     │   Service Bus    │     │  Container App  │
│  (Timer 10s)    │────▶│     Queue        │────▶│    RSS Worker   │
│                 │     │  (rss-feeds)     │     │  (always-on)    │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
        ┌─────────────────────────────────────────────────┘
        │
        ▼
┌───────────────┐     ┌─────────────────┐
│   Cosmos DB   │     │   Dead Letter   │
│ (raw_articles)│     │     Queue       │
└───────────────┘     │ (failed msgs)   │
                      └─────────────────┘
```

## Features

| Feature | Old Architecture | New Architecture |
|---------|------------------|------------------|
| Cold starts | 5-30s delays | ✅ No cold starts |
| Connection pooling | No | ✅ Yes |
| Retry logic | Basic | ✅ Automatic (Service Bus) |
| Circuit breaker | No | ✅ Yes |
| Dead letter queue | No | ✅ Yes |
| Concurrent processing | Limited | ✅ 10+ feeds parallel |
| Monitoring | Logs only | ✅ Health endpoint + stats |

## Cost

| Configuration | Monthly Cost |
|---------------|--------------|
| Always-on (1 replica) | ~$85 |
| High availability (2 replicas) | ~$160 |
| Scale to zero (with cold starts) | ~$25 |

## Deployment

### Prerequisites

1. Azure CLI installed and logged in (`az login`)
2. Docker installed and running
3. Existing Newsreel infrastructure (Cosmos DB)

### Deploy

```bash
cd Azure/rss-worker
chmod +x deploy.sh
./deploy.sh
```

The script will:
1. Create Service Bus namespace and queue
2. Create Container Registry
3. Build and push Docker image
4. Create Container Apps environment
5. Deploy the worker container
6. Verify health endpoint

### Enable Queue-Based Ingestion

After deployment, enable the new architecture:

```bash
# Set environment variable on Azure Functions
az functionapp config appsettings set \
    --name newsreel-func-51689 \
    --resource-group Newsreel-RG \
    --settings \
        USE_QUEUE_BASED_RSS=true \
        SERVICE_BUS_CONNECTION_STRING="<from deploy output>"
```

## Monitoring

### Health Check

```bash
curl https://newsreel-rss-worker.<env>.centralus.azurecontainerapps.io/health
```

Response:
```json
{
  "status": "healthy",
  "uptime_seconds": 3600.5,
  "stats": {
    "feeds_processed": 450,
    "articles_stored": 1250,
    "errors": 3,
    "circuit_breaks": 12,
    "start_time": "2025-01-01T00:00:00Z"
  }
}
```

### Statistics

```bash
curl https://newsreel-rss-worker.<env>.centralus.azurecontainerapps.io/stats
```

### Logs

```bash
az containerapp logs show \
    --name newsreel-rss-worker \
    --resource-group Newsreel-RG \
    --follow
```

### Circuit Breaker Reset

If a feed is incorrectly marked as failing:

```bash
curl -X POST https://newsreel-rss-worker.<env>/circuit-breaker/reset/bbc_world
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_BUS_CONNECTION_STRING` | (required) | Service Bus connection string |
| `SERVICE_BUS_QUEUE_NAME` | `rss-feeds` | Queue name |
| `COSMOS_CONNECTION_STRING` | (required) | Cosmos DB connection string |
| `COSMOS_DATABASE_NAME` | `newsreel-db` | Database name |
| `OPENAI_API_KEY` | (optional) | For semantic embeddings |
| `MAX_CONCURRENT_FEEDS` | `10` | Parallel feed processing |
| `FEED_TIMEOUT_SECONDS` | `30` | HTTP timeout per feed |
| `CIRCUIT_BREAKER_THRESHOLD` | `3` | Failures before circuit opens |
| `CIRCUIT_BREAKER_TIMEOUT_MINUTES` | `30` | Time before retry |

## Local Development

```bash
# Copy environment file
cp local.env.example .env

# Edit with your values
vim .env

# Run locally
python worker.py
```

## Rollback

If issues occur, disable queue-based ingestion to revert to direct polling:

```bash
az functionapp config appsettings set \
    --name newsreel-func-51689 \
    --resource-group Newsreel-RG \
    --settings USE_QUEUE_BASED_RSS=false
```

The original `RSSIngestion` timer function will resume normal operation.

## Troubleshooting

### Worker not processing messages

1. Check Service Bus queue has messages:
   ```bash
   az servicebus queue show --name rss-feeds --namespace-name newsreel-servicebus -g Newsreel-RG --query messageCount
   ```

2. Check worker logs for errors:
   ```bash
   az containerapp logs show -n newsreel-rss-worker -g Newsreel-RG
   ```

3. Check circuit breaker status:
   ```bash
   curl https://<worker-url>/stats
   ```

### High error rate

1. Check which feeds are failing:
   ```bash
   curl https://<worker-url>/stats | jq '.circuit_breaker.open_feeds'
   ```

2. Reset circuit breaker for specific feed:
   ```bash
   curl -X POST https://<worker-url>/circuit-breaker/reset/<feed_id>
   ```

### Dead letter queue filling up

Messages in DLQ = feed consistently failing. Check:

1. Feed URL still valid
2. Feed not rate limiting us
3. Network issues

## Files

```
rss-worker/
├── Dockerfile           # Container image definition
├── requirements.txt     # Python dependencies
├── worker.py           # Main worker code
├── config.py           # Feed configuration
├── queue_producer.py   # Queue producer (for testing)
├── deploy.sh           # Deployment script
├── local.env.example   # Environment template
└── README.md           # This file
```

## Related Files

- `Azure/functions/function_app.py` - Queue producer timer function
- `Azure/functions/shared/queue_producer.py` - Queue producer module
- `Azure/functions/shared/config.py` - Feature flag configuration

---

**Last Updated**: January 2026  
**Status**: Production Ready

