"""
Newsreel Story API
FastAPI application for serving stories to iOS app
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .config import settings
from .middleware.cors import setup_cors
from .routers import stories_router, users_router, health_router, notifications_router, admin
from .routers import diagnostics, dashboard, simple_dashboard, status
from .services.cosmos_service import cosmos_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    
    # Initialize Cosmos DB connection
    try:
        cosmos_service.connect()
        logger.info("Connected to Cosmos DB")
    except Exception as e:
        logger.error(f"Failed to connect to Cosmos DB: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="REST API for Newsreel iOS app - AI-curated news aggregation",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup CORS
setup_cors(app)

# Include routers
app.include_router(health_router)
app.include_router(stories_router)
app.include_router(users_router)
app.include_router(notifications_router)
app.include_router(admin.router)
app.include_router(diagnostics.router)
app.include_router(dashboard.router)
app.include_router(simple_dashboard.router)
app.include_router(status.router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unexpected exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.environment == "development" else "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )

