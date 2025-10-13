"""API Response Models"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class SourceArticle(BaseModel):
    """Source article reference"""
    id: str
    source: str
    title: str
    article_url: str
    published_at: datetime


class SummaryResponse(BaseModel):
    """Summary information"""
    text: str
    version: int
    word_count: int
    generated_at: datetime


class StoryResponse(BaseModel):
    """Story response model"""
    id: str
    title: str
    category: str
    tags: List[str] = Field(default_factory=list)
    status: str
    verification_level: int
    summary: Optional[SummaryResponse] = None
    source_count: int
    first_seen: datetime
    last_updated: datetime
    importance_score: int
    breaking_news: bool
    user_liked: bool = False
    user_saved: bool = False


class StoryDetailResponse(StoryResponse):
    """Detailed story response with sources"""
    sources: List[SourceArticle] = Field(default_factory=list)


class FeedResponse(BaseModel):
    """Feed response model"""
    stories: List[StoryResponse]
    total: int
    has_more: bool
    next_offset: Optional[int] = None


class UserProfileResponse(BaseModel):
    """User profile response"""
    id: str
    email: str
    subscription_tier: str
    created_at: datetime
    last_active: datetime
    preferences: Dict[str, Any]
    interaction_stats: Dict[str, Any]
    rate_limiting: Dict[str, Any]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime
    cosmos_db: str = "unknown"


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None

