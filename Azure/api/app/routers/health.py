"""Health Check Router"""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter

from ..models.responses import HealthResponse
from ..config import settings
from ..services.cosmos_service import cosmos_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns the health status of the API and its dependencies.
    """
    
    cosmos_status = "unknown"
    
    try:
        # Test Cosmos DB connection
        cosmos_service.connect()
        cosmos_status = "connected"
    except Exception as e:
        logger.error(f"Cosmos DB health check failed: {e}")
        cosmos_status = "error"
    
    return HealthResponse(
        status="healthy" if cosmos_status == "connected" else "degraded",
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc),
        cosmos_db=cosmos_status
    )


@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }

