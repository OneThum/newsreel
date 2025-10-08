# Story API - FastAPI Backend

FastAPI REST API deployed to Azure Container Apps for serving stories to iOS app.

## Features

- **Firebase JWT Authentication**: Validates iOS app user tokens
- **Cosmos DB Integration**: Direct queries to story and user data
- **Personalized Recommendations**: ML-based story ranking
- **Caching**: In-memory cache with 5-minute TTL
- **Auto-scaling**: 0-3 instances based on load
- **Health Checks**: Kubernetes-style liveness/readiness probes

## API Endpoints

### Stories
- `GET /api/stories/feed` - Personalized story feed
- `GET /api/stories/{id}` - Story detail
- `GET /api/stories/{id}/sources` - Source articles
- `GET /api/stories/breaking` - Breaking news
- `POST /api/stories/{id}/interact` - Record user interaction

### User
- `GET /api/user/profile` - Current user profile
- `PUT /api/user/preferences` - Update preferences
- `POST /api/user/device-token` - Register push notification token

### System
- `GET /health` - Health check endpoint
- `GET /metrics` - Prometheus metrics (internal)

## Local Development

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload --port 8000
```

Visit: http://localhost:8000/docs for Swagger UI

## Docker

```bash
# Build image
docker build -t story-api:latest .

# Run container
docker run -p 8000:8000 \
  -e COSMOS_CONNECTION_STRING="..." \
  -e FIREBASE_CREDENTIALS="..." \
  story-api:latest
```

## Deployment

```bash
cd ../scripts
./deploy-api.sh
```

## Structure

```
api/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── routers/
│   │   ├── stories.py       # Story endpoints
│   │   ├── users.py         # User endpoints
│   │   └── health.py        # Health checks
│   ├── services/
│   │   ├── cosmos_service.py
│   │   ├── auth_service.py
│   │   └── recommendation_service.py
│   ├── models/
│   │   ├── story.py
│   │   ├── user.py
│   │   └── interaction.py
│   └── middleware/
│       ├── auth.py
│       └── cors.py
├── Dockerfile
├── requirements.txt
└── .dockerignore
```

## Environment Variables

```bash
COSMOS_CONNECTION_STRING=<connection_string>
COSMOS_DATABASE_NAME=newsapp-db
FIREBASE_CREDENTIALS=<service_account_json>
ENVIRONMENT=production
LOG_LEVEL=info
```

## Performance

- **Target Latency**: <200ms (P50), <500ms (P95)
- **Caching Strategy**: 5-minute TTL on feed queries
- **Rate Limiting**: 100 requests/minute per user (free), 1000/min (premium)

## Monitoring

- **Application Insights**: Request tracing, dependency tracking
- **Metrics**: Prometheus-compatible `/metrics` endpoint
- **Alerts**: Configured for high latency, errors, and high CPU

## Status

**Ready**: Structure created  
**Pending**: Implementation (Phase 1)  
**Estimated Time**: 6-8 hours to implement full API

