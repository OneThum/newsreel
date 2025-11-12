"""Data models for Newsreel"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class StoryStatus(str, Enum):
    """Story verification status"""
    MONITORING = "MONITORING"  # 1 source
    DEVELOPING = "DEVELOPING"  # 2 sources
    BREAKING = "BREAKING"      # 3+ sources, within 30 min
    VERIFIED = "VERIFIED"      # 3+ sources, after 30 min


class SubscriptionTier(str, Enum):
    """User subscription tiers"""
    FREE = "free"
    PAID = "paid"


class InteractionType(str, Enum):
    """User interaction types"""
    VIEW = "view"
    LIKE = "like"
    SAVE = "save"
    SHARE = "share"
    SOURCE_CLICK = "source_click"
    CARD_FLIP = "card_flip"


class Entity(BaseModel):
    """Named entity extracted from article"""
    text: str
    type: str  # PERSON, LOCATION, ORGANIZATION, EVENT, etc.
    confidence: Optional[float] = None
    linked_name: Optional[str] = None  # Phase 1: Basic entity linking via string matching


class Coordinates(BaseModel):
    """Geographic coordinates"""
    lat: float
    lng: float


class Location(BaseModel):
    """Story location information"""
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    coordinates: Optional[Coordinates] = None


class RawArticle(BaseModel):
    """Raw article from RSS feed"""
    id: str
    source: str
    source_url: str
    source_tier: int = 1
    article_url: str
    title: str
    description: Optional[str] = None
    published_at: datetime  # Original publication date from RSS feed
    fetched_at: datetime  # When we first saw this article (immutable)
    updated_at: datetime  # When we last updated this record (for upserts)
    published_date: str  # YYYY-MM-DD format for partitioning
    content: Optional[str] = None
    author: Optional[str] = None
    entities: List[Entity] = Field(default_factory=list)
    category: str = "general"
    tags: List[str] = Field(default_factory=list)
    language: str = "en"
    story_fingerprint: str
    embedding: Optional[List[float]] = None
    processed: bool = False
    processing_attempts: int = 0

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class SummaryVersion(BaseModel):
    """AI-generated summary metadata"""
    version: int
    text: str
    generated_at: datetime
    model: str
    word_count: int
    generation_time_ms: int
    prompt_tokens: int
    completion_tokens: int
    cached_tokens: int = 0
    cost_usd: float
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class VersionHistory(BaseModel):
    """Historical version of a story"""
    version: int
    timestamp: datetime
    summary: str
    source_count: int
    status: StoryStatus
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class StoryCluster(BaseModel):
    """Aggregated story from multiple sources"""
    id: str
    event_fingerprint: str
    title: str
    category: str
    tags: List[str] = Field(default_factory=list)
    status: StoryStatus
    verification_level: int  # Number of sources
    first_seen: datetime
    last_updated: datetime
    published_at: Optional[datetime] = None  # Publication date for iOS app (set to first_seen)
    source_articles: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Optional[SummaryVersion] = None
    version_history: List[VersionHistory] = Field(default_factory=list)
    location: Optional[Location] = None
    importance_score: int = 50
    confidence_score: int = 50
    update_count: int = 0
    view_count: int = 0
    like_count: int = 0
    save_count: int = 0
    share_count: int = 0
    breaking_news: bool = False
    breaking_detected_at: Optional[datetime] = None
    push_notification_sent: bool = False
    push_notification_sent_at: Optional[datetime] = None
    needs_human_review: bool = False
    human_reviewed: bool = False
    corrections: List[Dict[str, Any]] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    @property
    def article_count(self) -> int:
        """Number of articles in this story cluster"""
        return len(self.source_articles)


class NotificationSettings(BaseModel):
    """User notification preferences"""
    breaking_news: bool = True
    threshold: str = "major"  # minor, moderate, major
    quiet_hours: Optional[Dict[str, Any]] = None
    geographic_focus: List[str] = Field(default_factory=list)


class ReadingPreferences(BaseModel):
    """User reading preferences"""
    summary_length: str = "standard"  # brief, standard, detailed
    font_size: str = "medium"
    theme: str = "auto"  # light, dark, auto


class Preferences(BaseModel):
    """User preferences"""
    categories: List[str] = Field(default_factory=list)
    sources_boost: List[str] = Field(default_factory=list)
    sources_mute: List[str] = Field(default_factory=list)
    notification_settings: NotificationSettings = Field(default_factory=NotificationSettings)
    reading_preferences: ReadingPreferences = Field(default_factory=ReadingPreferences)


class Subscription(BaseModel):
    """User subscription details"""
    tier: SubscriptionTier = SubscriptionTier.FREE
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    auto_renew: bool = False
    platform: Optional[str] = None
    original_transaction_id: Optional[str] = None
    receipt_validated_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class RateLimiting(BaseModel):
    """Rate limiting information"""
    daily_story_count: int = 0
    last_reset: datetime = Field(default_factory=datetime.utcnow)
    exceeded_limit: bool = False
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class DeviceToken(BaseModel):
    """Push notification device token"""
    token: str
    platform: str = "ios"
    added_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class UserProfile(BaseModel):
    """User profile and preferences"""
    id: str  # Firebase UID
    firebase_uid: str
    email: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    subscription: Subscription = Field(default_factory=Subscription)
    preferences: Preferences = Field(default_factory=Preferences)
    location: Optional[Location] = None
    interaction_stats: Dict[str, Any] = Field(default_factory=dict)
    personalization_profile: Dict[str, Any] = Field(default_factory=dict)
    rate_limiting: RateLimiting = Field(default_factory=RateLimiting)
    device_tokens: List[DeviceToken] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class UserInteraction(BaseModel):
    """User interaction with a story"""
    id: str
    user_id: str
    story_id: str
    interaction_type: InteractionType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str
    dwell_time_seconds: int = 0
    card_flipped: bool = False
    sources_clicked: List[str] = Field(default_factory=list)
    device_info: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class RSSFeedConfig(BaseModel):
    """RSS feed configuration"""
    id: str
    name: str
    url: str
    source_id: str  # Short identifier (e.g., "reuters")
    category: str
    tier: int = 1  # 1 = premium, 2 = standard, 3 = supplementary
    language: str = "en"
    country: Optional[str] = None
    enabled: bool = True
    last_fetched: Optional[datetime] = None
    last_etag: Optional[str] = None
    last_modified: Optional[str] = None
    error_count: int = 0
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )

