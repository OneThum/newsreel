"""API Configuration"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # App Info
    app_name: str = "Newsreel Story API"
    app_version: str = "1.0.0"
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # Azure Cosmos DB
    cosmos_connection_string: str = os.getenv("COSMOS_CONNECTION_STRING", "")
    cosmos_database_name: str = os.getenv("COSMOS_DATABASE_NAME", "newsreel-db")
    
    # Firebase
    firebase_credentials: str = os.getenv("FIREBASE_CREDENTIALS", "")
    firebase_project_id: str = os.getenv("FIREBASE_PROJECT_ID", "newsreel-865a5")
    
    # CORS
    cors_origins: list = [
        "http://localhost:3000",
        "https://newsreel.app",
        "*"  # Allow all for mobile app
    ]
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    free_tier_daily_limit: int = 20
    premium_tier_daily_limit: int = 1000
    
    # Caching
    cache_ttl_seconds: int = 300  # 5 minutes
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        case_sensitive = False


settings = Settings()

