# Newsreel Embedding Service

FastAPI service for generating semantic embeddings using SentenceTransformers. Deployed as Azure Container Instance for the Newsreel clustering overhaul (Phase 2).

## Overview

This service provides semantic embeddings for news articles using the `intfloat/multilingual-e5-large` model, which supports multiple languages and provides high-quality semantic similarity for improved news story clustering.

## Features

- **Multilingual Support**: Handles news in multiple languages
- **Batch Processing**: Efficient batch embedding for multiple articles
- **REST API**: FastAPI-based HTTP API
- **Health Checks**: Built-in health monitoring
- **Entity Enhancement**: Optional entity-aware embedding (Phase 3)

## API Endpoints

### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_name": "intfloat/multilingual-e5-large"
}
```

### GET `/model-info`
Get information about the loaded model.

**Response:**
```json
{
  "model_name": "intfloat/multilingual-e5-large",
  "embedding_dimension": 1024,
  "status": "ready"
}
```

### POST `/embed`
Generate embedding for a single article.

**Request:**
```json
{
  "title": "Breaking: Major earthquake hits California coast",
  "description": "A magnitude 7.2 earthquake struck off the California coast...",
  "entities": [
    {"text": "California", "type": "LOCATION"},
    {"text": "earthquake", "type": "EVENT"}
  ]
}
```

**Response:**
```json
{
  "embedding": [0.123, 0.456, ...],
  "dimension": 1024,
  "model": "intfloat/multilingual-e5-large",
  "processing_time_ms": 45.2
}
```

### POST `/embed/batch`
Generate embeddings for multiple articles.

**Request:**
```json
{
  "articles": [
    {
      "title": "Article 1 title",
      "description": "Article 1 content...",
      "entities": []
    },
    {
      "title": "Article 2 title",
      "description": "Article 2 content...",
      "entities": []
    }
  ],
  "batch_size": 32
}
```

**Response:**
```json
{
  "embeddings": [[0.123, ...], [0.456, ...]],
  "dimension": 1024,
  "model": "intfloat/multilingual-e5-large",
  "count": 2,
  "processing_time_ms": 67.8
}
```

## Deployment

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the service:
```bash
python app.py
```

3. Test the API:
```bash
curl http://localhost:8080/health
```

### Azure Container Instances Deployment

Use the provided deployment script:

```bash
# Set your configuration
export RESOURCE_GROUP="newsreel-rg"
export ACI_NAME="newsreel-embeddings"
export LOCATION="eastus"
export DNS_NAME_LABEL="newsreel-embeddings"

# If using Azure Container Registry:
export ACR_LOGIN_SERVER="youracr.azurecr.io"

# Run deployment
chmod +x deploy.sh
./deploy.sh
```

The script will:
- Build the Docker image
- Push to ACR (if configured)
- Deploy to Azure Container Instances
- Provide the service URL

### Manual Deployment

1. Build the Docker image:
```bash
docker build -t newsreel/embeddings .
```

2. Deploy to ACI:
```bash
az container create \
  --resource-group newsreel-rg \
  --name newsreel-embeddings \
  --image newsreel/embeddings \
  --cpu 2 \
  --memory 4 \
  --ports 8080 \
  --dns-name-label newsreel-embeddings
```

## Configuration

### Environment Variables

- `MODEL_NAME`: SentenceTransformers model to use (default: `intfloat/multilingual-e5-large`)

### Resource Requirements

- **CPU**: 2 cores recommended
- **Memory**: 4GB minimum (model is ~2GB)
- **Storage**: Additional space for model cache

## Monitoring

### Health Checks

The service includes built-in health checks that verify:
- Service availability
- Model loading status
- Memory usage

### Logs

Monitor application logs:
```bash
az container logs --resource-group newsreel-rg --name newsreel-embeddings
```

### Performance Metrics

- Single article embedding: ~50-100ms
- Batch processing: ~10-50ms per article (depending on batch size)
- Cold start time: ~30-60 seconds (due to model loading)

## Integration

### Azure Functions Configuration

After deployment, configure your Azure Functions:

```bash
# Set the service URL
EMBEDDINGS_SERVICE_URL="http://your-aci-fqdn:8080"
```

### Usage in Code

```python
from embeddings_client import get_embeddings_client

async def embed_article(title, description):
    client = await get_embeddings_client()
    embedding = await client.embed_article(title, description)
    return embedding
```

## Troubleshooting

### Common Issues

1. **Model loading timeout**: Increase memory allocation or use GPU-enabled ACI
2. **High latency**: Check network connectivity between Functions and ACI
3. **Out of memory**: Increase ACI memory allocation

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Cost Optimization

- **ACI Costs**: ~$50-100/month for 2CPU/4GB configuration
- **Model Caching**: Model is cached in container for faster startups
- **Batch Processing**: Use batch endpoints for multiple articles

## Future Enhancements

- **GPU Support**: Deploy on GPU-enabled ACI for faster inference
- **Model Updates**: Support for newer SentenceTransformers models
- **Entity Enhancement**: Integrate with spaCy for better entity recognition
- **Caching**: Add Redis caching for frequently requested embeddings
