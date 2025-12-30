"""Configuration management for Azure Functions"""
import os
from typing import Optional


class Config:
    """Application configuration"""
    
    # Azure Cosmos DB
    COSMOS_CONNECTION_STRING: str = os.getenv("COSMOS_CONNECTION_STRING", "")
    COSMOS_DATABASE_NAME: str = os.getenv("COSMOS_DATABASE_NAME", "newsreel-db")
    
    # Containers
    CONTAINER_RAW_ARTICLES: str = "raw_articles"
    CONTAINER_STORY_CLUSTERS: str = "story_clusters"
    CONTAINER_USER_PROFILES: str = "user_profiles"
    CONTAINER_USER_INTERACTIONS: str = "user_interactions"
    CONTAINER_MODERATION_QUEUE: str = "moderation_queue"
    CONTAINER_BATCH_TRACKING: str = "batch_tracking"
    
    # Azure Storage
    STORAGE_CONNECTION_STRING: str = os.getenv("STORAGE_CONNECTION_STRING", "")
    QUEUE_NAME_SUMMARIZATION: str = "summarization-queue"
    
    # Anthropic API
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")  # Claude 3.5 Haiku (fastest, cheapest)
    ANTHROPIC_MAX_TOKENS: int = 500
    
    # OpenAI API (for semantic embeddings)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"  # Best price/performance
    
    # Twitter/X API
    TWITTER_BEARER_TOKEN: str = os.getenv("TWITTER_BEARER_TOKEN", "")
    
    # Firebase
    FIREBASE_CREDENTIALS: str = os.getenv("FIREBASE_CREDENTIALS", "")
    FCM_SERVER_KEY: str = os.getenv("FCM_SERVER_KEY", "")
    
    # RSS Configuration
    RSS_USE_ALL_FEEDS: bool = os.getenv("RSS_USE_ALL_FEEDS", "false").lower() == "true"
    RSS_POLL_INTERVAL_MINUTES: int = 5
    RSS_USER_AGENT: str = "Newsreel/1.0 (+https://newsreel.app)"
    RSS_TIMEOUT_SECONDS: int = 30
    RSS_MAX_CONCURRENT: int = 25  # Increased from 20 to handle 100 feeds
    
    # Story Clustering
    MIN_SOURCES_FOR_DEVELOPING: int = 2
    MIN_SOURCES_FOR_BREAKING: int = 3
    BREAKING_NEWS_WINDOW_MINUTES: int = 30
    
    # Semantic Clustering (2025 - OpenAI embeddings)
    SEMANTIC_CLUSTER_THRESHOLD: float = 0.82  # Cosine similarity threshold for same story
    SEMANTIC_MAYBE_THRESHOLD: float = 0.75  # Threshold for entity validation check
    
    # DEPRECATED: Legacy keyword-based threshold (kept for reference)
    STORY_FINGERPRINT_SIMILARITY_THRESHOLD: float = 0.70  # Not used with semantic clustering
    
    # Summarization
    MIN_SOURCES_FOR_SUMMARY: int = 1  # Generate summaries for ALL stories (changed from 2)
    MAX_SUMMARIES_PER_DAY: int = 3000  # Budget control: ~$5-7/day with Claude Haiku 4.5
    SUMMARIZATION_BACKFILL_ENABLED: bool = os.getenv("SUMMARIZATION_BACKFILL_ENABLED", "false").lower() == "true"  # Disabled by default to save costs
    
    # Batch Processing (50% cost reduction for backfill)
    BATCH_PROCESSING_ENABLED: bool = os.getenv("BATCH_PROCESSING_ENABLED", "true").lower() == "true"  # Enabled by default for cost savings
    BATCH_MAX_SIZE: int = 500  # Max requests per batch (API limit is 100,000)
    BATCH_BACKFILL_HOURS: int = 48  # Only backfill stories from last N hours
    BATCH_POLL_INTERVAL_MINUTES: int = 30  # How often to submit new batches and check results
    
    # Rate Limiting
    FREE_TIER_DAILY_LIMIT: int = 20
    PREMIUM_TIER_DAILY_LIMIT: int = 1000
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        required = [
            ("COSMOS_CONNECTION_STRING", cls.COSMOS_CONNECTION_STRING),
            ("COSMOS_DATABASE_NAME", cls.COSMOS_DATABASE_NAME),
        ]
        
        missing = [name for name, value in required if not value]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True


config = Config()

