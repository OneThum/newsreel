# Azure Functions for Newsreel

Python 3.11 serverless functions on Azure Functions Consumption plan.

## Functions

### 1. RSS Ingestion (Timer Trigger)
**Schedule**: Every 10 seconds (staggered polling)  
**File**: `function_app.py` (lines 516-620+)  
**Legacy**: `rss_ingestion/function_app.py` (deprecated)

Polls 5 RSS feeds per cycle for continuous news flow. Results in ~1 new article every 3 seconds on average instead of lumpy 5-minute batch updates.

**See**: `docs/RSS_INGESTION_CONFIG.md` for complete configuration and tuning options.

### 2. Story Clustering (Cosmos Change Feed)
**Trigger**: Cosmos DB change feed on `raw_articles`  
**File**: `story_clustering/function_app.py`

Groups related articles into story clusters.

### 3. Summarization (Queue Trigger)
**Trigger**: Azure Storage Queue  
**File**: `summarization/function_app.py`

Generates AI summaries using Claude API.

### 4. Breaking News Monitor (Timer Trigger)
**Schedule**: Every 2 minutes  
**File**: `breaking_news_monitor/function_app.py`

Monitors Twitter for breaking news signals.

## Local Development

```bash
# Install Azure Functions Core Tools
brew install azure-functions-core-tools@4

# Install dependencies
pip install -r requirements.txt

# Run locally
func start
```

## Deployment

```bash
cd ../scripts
./deploy-functions.sh
```

## Configuration

Environment variables are managed in Azure:
- `COSMOS_CONNECTION_STRING`
- `ANTHROPIC_API_KEY`
- `TWITTER_BEARER_TOKEN`
- `FIREBASE_CREDENTIALS`

## Structure

```
functions/
├── rss_ingestion/
│   ├── __init__.py
│   └── function_app.py
├── story_clustering/
│   ├── __init__.py
│   └── function_app.py
├── summarization/
│   ├── __init__.py
│   └── function_app.py
├── breaking_news_monitor/
│   ├── __init__.py
│   └── function_app.py
├── shared/              # Shared utilities
│   ├── __init__.py
│   ├── cosmos_client.py
│   └── models.py
├── host.json
├── local.settings.json.example
└── requirements.txt
```

## Status

**Ready**: Structure created  
**Pending**: Implementation (Phase 1)  
**Estimated Time**: 4-6 hours to implement all functions

