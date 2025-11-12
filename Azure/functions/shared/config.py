"""Configuration management for Azure Functions"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


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
    STORY_FINGERPRINT_SIMILARITY_THRESHOLD: float = 0.50  # 50% similarity required for clustering (reduced from 0.60 to allow more new stories)

    # Clustering Overhaul Feature Flags
    CLUSTERING_USE_SIMHASH: bool = os.getenv('CLUSTERING_USE_SIMHASH', 'false') == 'true'
    CLUSTERING_USE_TIME_WINDOW: bool = os.getenv('CLUSTERING_USE_TIME_WINDOW', 'false') == 'true'
    CLUSTERING_USE_ADAPTIVE_THRESHOLD: bool = os.getenv('CLUSTERING_USE_ADAPTIVE', 'false') == 'true'
    CLUSTERING_USE_EMBEDDINGS: bool = os.getenv('CLUSTERING_USE_EMBEDDINGS', 'false') == 'true'
    CLUSTERING_USE_EVENT_SIGNATURES: bool = os.getenv('CLUSTERING_USE_EVENT_SIGNATURES', 'false') == 'true'

    # SimHash Configuration
    SIMHASH_SHINGLE_SIZE: int = 3  # Number of words per shingle
    SIMHASH_BITS: int = 64  # Fingerprint size
    SIMHASH_HAMMING_THRESHOLD: int = 3  # Max hamming distance for near-duplicate detection
    SIMHASH_HASH_TTL_DAYS: int = 7  # How long to keep hashes for comparison

    # Phase 2: Semantic Embeddings Configuration
    EMBEDDINGS_MODEL: str = os.getenv('EMBEDDINGS_MODEL', 'intfloat/multilingual-e5-large')
    EMBEDDINGS_DIMENSION: int = 1024  # Dimension for multilingual-e5-large (Phase 3.6)
    EMBEDDINGS_BATCH_SIZE: int = 16  # Reduced batch size for larger model memory requirements
    EMBEDDINGS_SERVICE_URL: str = os.getenv('EMBEDDINGS_SERVICE_URL', '')  # ACI endpoint
    EMBEDDINGS_TIMEOUT_SECONDS: int = 60  # Increased timeout for larger model processing

    # FAISS Vector Index Configuration
    VECTOR_INDEX_TYPE: str = os.getenv('VECTOR_INDEX_TYPE', 'auto')  # 'flat', 'ivf', 'hnsw', 'auto'
    VECTOR_INDEX_PATH: str = os.getenv('VECTOR_INDEX_PATH', '/tmp/vector_index')  # Storage path
    VECTOR_INDEX_REBUILD_THRESHOLD: int = 10000  # Rebuild index when it grows too large

    # Phase 3: Event Signatures Configuration
    EVENT_SIGNATURES_ENABLED: bool = CLUSTERING_USE_EVENT_SIGNATURES
    EVENT_SIGNATURE_SIMILARITY_THRESHOLD: float = 0.6  # Similarity threshold for event signature matching
    EVENT_SIGNATURE_CONFIDENCE_THRESHOLD: float = 0.3  # Minimum confidence for signature extraction

    # Phase 3: Cluster Maintenance Configuration
    CLUSTER_MAINTENANCE_ENABLED: bool = True
    CLUSTER_MAINTENANCE_INTERVAL_HOURS: int = 6  # Run maintenance every 6 hours
    CLUSTER_MAINTENANCE_MAX_CLUSTERS: int = 1000  # Max clusters to process per run
    CLUSTER_MAINTENANCE_MERGE_THRESHOLD: float = 0.8  # Similarity threshold for merging
    CLUSTER_MAINTENANCE_SPLIT_THRESHOLD: float = 0.7  # Diversity threshold for splitting
    CLUSTER_DECAY_SINGLE_ARTICLE_DAYS: int = 14  # Days before decaying single-article clusters
    CLUSTER_DECAY_INACTIVE_DAYS: int = 30  # Days before decaying inactive clusters

    # Phase 3: Geographic Features Configuration
    GEOGRAPHIC_FEATURES_ENABLED: bool = os.getenv('CLUSTERING_USE_GEOGRAPHIC', 'false') == 'true'
    GEOGRAPHIC_SIMILARITY_THRESHOLD: float = 0.5  # Similarity threshold for geographic matching
    GEOGRAPHIC_MAX_DISTANCE_KM: float = 500.0  # Maximum distance to consider locations similar
    GEOGRAPHIC_SIMILARITY_WEIGHT: float = 0.15  # Weight in overall clustering score

    # Phase 3: Wikidata Linking Configuration
    WIKIDATA_LINKING_ENABLED: bool = os.getenv('WIKIDATA_LINKING_ENABLED', 'true').lower() == 'true'
    WIKIDATA_API_TIMEOUT_SECONDS: int = 10
    WIKIDATA_MAX_CANDIDATES: int = 5
    WIKIDATA_CACHE_SIZE: int = 1000

    # Phase 3: Scoring Optimization Configuration
    SCORING_OPTIMIZATION_ENABLED: bool = os.getenv('SCORING_OPTIMIZATION_ENABLED', 'true').lower() == 'true'
    SCORING_MODEL_PATH: str = os.path.join(os.getcwd(), 'models', 'similarity_model.pkl')
    SCORING_SIMILARITY_THRESHOLD: float = 0.7  # Threshold for considering articles similar
    SCORING_TRAINING_DATA_PATH: str = os.path.join(os.getcwd(), 'data', 'training_pairs.json')
    
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
    def validate(cls, require_cosmos: bool = True) -> bool:
        """Validate required configuration"""
        required = []

        if require_cosmos:
            required.extend([
                ("COSMOS_CONNECTION_STRING", cls.COSMOS_CONNECTION_STRING),
                ("COSMOS_DATABASE_NAME", cls.COSMOS_DATABASE_NAME),
            ])

        missing = [name for name, value in required if not value]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

        return True


# Skip validation in test environments
try:
    config = Config()
    config.validate(require_cosmos=False)  # Skip Cosmos validation for testing
except Exception as e:
    logger.warning(f"Config validation failed (expected in test environments): {e}")
    config = Config()

