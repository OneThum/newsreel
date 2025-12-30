"""
Embedding Service API - Phase 2 Clustering Overhaul

FastAPI service for generating semantic embeddings using SentenceTransformers.
Deployed as Azure Container Instance for handling the large multilingual-e5-large model.

Endpoints:
- POST /embed: Generate embeddings for articles
- GET /health: Health check
- GET /model-info: Model information
"""
import logging
import time
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import numpy as np
from embeddings import ArticleEmbedder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Newsreel Embedding Service",
    description="Semantic embeddings for news article clustering",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global embedder instance
embedder: Optional[ArticleEmbedder] = None


class ArticleRequest(BaseModel):
    """Request model for single article embedding"""
    title: str = Field(..., description="Article title")
    description: Optional[str] = Field("", description="Article description or content")
    entities: Optional[List[Dict[str, Any]]] = Field(None, description="Extracted named entities")


class BatchArticleRequest(BaseModel):
    """Request model for batch article embedding"""
    articles: List[ArticleRequest] = Field(..., description="List of articles to embed")
    batch_size: Optional[int] = Field(32, description="Processing batch size")


class EmbeddingResponse(BaseModel):
    """Response model for embeddings"""
    embedding: List[float] = Field(..., description="Embedding vector")
    dimension: int = Field(..., description="Embedding dimension")
    model: str = Field(..., description="Model used")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class BatchEmbeddingResponse(BaseModel):
    """Response model for batch embeddings"""
    embeddings: List[List[float]] = Field(..., description="List of embedding vectors")
    dimension: int = Field(..., description="Embedding dimension")
    model: str = Field(..., description="Model used")
    count: int = Field(..., description="Number of articles processed")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    model_name: Optional[str] = Field(None, description="Model name if loaded")


@app.on_event("startup")
async def startup_event():
    """Initialize the embedding model on startup"""
    global embedder
    try:
        logger.info("Initializing embedding model...")
        start_time = time.time()

        embedder = ArticleEmbedder()

        load_time = time.time() - start_time
        logger.info(".2f")

    except Exception as e:
        logger.error(f"Failed to initialize embedding model: {e}")
        embedder = None
        raise


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if embedder else "unhealthy",
        model_loaded=embedder is not None,
        model_name=embedder.model_name if embedder else None
    )


@app.get("/model-info")
async def model_info():
    """Get information about the loaded model"""
    if not embedder:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return {
        "model_name": embedder.model_name,
        "embedding_dimension": embedder.embedding_dim,
        "status": "ready"
    }


@app.post("/embed", response_model=EmbeddingResponse)
async def embed_article(request: ArticleRequest):
    """Generate embedding for a single article"""
    if not embedder:
        raise HTTPException(status_code=503, detail="Embedding model not available")

    try:
        start_time = time.time()

        # Generate embedding
        embedding = embedder.embed_article(
            title=request.title,
            description=request.description or "",
            entities=request.entities
        )

        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        return EmbeddingResponse(
            embedding=embedding.tolist(),
            dimension=len(embedding),
            model=embedder.model_name,
            processing_time_ms=processing_time
        )

    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@app.post("/embed/batch", response_model=BatchEmbeddingResponse)
async def embed_articles_batch(request: BatchArticleRequest):
    """Generate embeddings for multiple articles"""
    if not embedder:
        raise HTTPException(status_code=503, detail="Embedding model not available")

    if not request.articles:
        raise HTTPException(status_code=400, detail="No articles provided")

    try:
        start_time = time.time()

        # Convert request to dict format expected by batch_embed
        articles_dict = [
            {
                "title": article.title,
                "description": article.description or "",
                "entities": article.entities
            }
            for article in request.articles
        ]

        # Generate batch embeddings
        embeddings = embedder.batch_embed(
            articles=articles_dict,
            batch_size=request.batch_size
        )

        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        return BatchEmbeddingResponse(
            embeddings=embeddings.tolist(),
            dimension=embedder.embedding_dim,
            model=embedder.model_name,
            count=len(request.articles),
            processing_time_ms=processing_time
        )

    except Exception as e:
        logger.error(f"Batch embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch embedding generation failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Newsreel Embedding Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "GET /health - Health check",
            "GET /model-info - Model information",
            "POST /embed - Single article embedding",
            "POST /embed/batch - Batch article embeddings"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
