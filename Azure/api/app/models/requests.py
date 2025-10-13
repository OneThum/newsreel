"""API Request Models"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class InteractionRequest(BaseModel):
    """Request to record user interaction"""
    interaction_type: str = Field(..., description="Type of interaction: view, like, save, share, source_click, card_flip")
    session_id: str = Field(..., description="Session ID")
    dwell_time_seconds: int = Field(default=0, description="Time spent viewing story")
    card_flipped: bool = Field(default=False, description="Whether user flipped card")
    sources_clicked: List[str] = Field(default_factory=list, description="List of source article IDs clicked")
    device_info: Optional[Dict[str, Any]] = Field(default=None, description="Device information")


class PreferencesUpdateRequest(BaseModel):
    """Request to update user preferences"""
    categories: Optional[List[str]] = Field(default=None, description="Preferred categories")
    sources_boost: Optional[List[str]] = Field(default=None, description="Sources to boost in feed")
    sources_mute: Optional[List[str]] = Field(default=None, description="Sources to mute")
    notification_settings: Optional[Dict[str, Any]] = Field(default=None, description="Notification preferences")
    reading_preferences: Optional[Dict[str, Any]] = Field(default=None, description="Reading preferences")


class DeviceTokenRequest(BaseModel):
    """Request to register device token"""
    token: str = Field(..., description="Push notification token")
    platform: str = Field(default="ios", description="Platform: ios or android")

