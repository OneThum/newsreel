"""Users API Router"""
import logging
from typing import Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status

from ..models.requests import PreferencesUpdateRequest, DeviceTokenRequest
from ..models.responses import UserProfileResponse, ErrorResponse
from ..services.cosmos_service import cosmos_service
from ..middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["users"])


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get current user profile
    
    Returns the authenticated user's profile including preferences,
    subscription status, and interaction statistics.
    """
    
    return UserProfileResponse(
        id=user['id'],
        email=user.get('email', ''),
        subscription_tier=user.get('subscription', {}).get('tier', 'free'),
        created_at=datetime.fromisoformat(
            user.get('created_at', '').replace('Z', '+00:00')
        ),
        last_active=datetime.fromisoformat(
            user.get('last_active', '').replace('Z', '+00:00')
        ),
        preferences=user.get('preferences', {}),
        interaction_stats=user.get('interaction_stats', {}),
        rate_limiting=user.get('rate_limiting', {})
    )


@router.put("/preferences")
async def update_preferences(
    preferences: PreferencesUpdateRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update user preferences
    
    Updates user preferences for content curation, notifications, and reading settings.
    """
    
    # Initialize Cosmos DB connection
    cosmos_service.connect()
    
    # Get current preferences
    current_prefs = user.get('preferences', {})
    
    # Update only provided fields
    updates = {}
    
    if preferences.categories is not None:
        current_prefs['categories'] = preferences.categories
        updates['preferences'] = current_prefs
    
    if preferences.sources_boost is not None:
        current_prefs['sources_boost'] = preferences.sources_boost
        updates['preferences'] = current_prefs
    
    if preferences.sources_mute is not None:
        current_prefs['sources_mute'] = preferences.sources_mute
        updates['preferences'] = current_prefs
    
    if preferences.notification_settings is not None:
        current_prefs['notification_settings'] = {
            **current_prefs.get('notification_settings', {}),
            **preferences.notification_settings
        }
        updates['preferences'] = current_prefs
    
    if preferences.reading_preferences is not None:
        current_prefs['reading_preferences'] = {
            **current_prefs.get('reading_preferences', {}),
            **preferences.reading_preferences
        }
        updates['preferences'] = current_prefs
    
    if updates:
        await cosmos_service.update_user_profile(user['id'], updates)
        logger.info(f"Updated preferences for user {user['id']}")
    
    return {"status": "success", "message": "Preferences updated"}


@router.post("/device-token")
async def register_device_token(
    device_token: DeviceTokenRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Register device token for push notifications
    
    Registers or updates the user's device token for receiving push notifications.
    """
    
    # Initialize Cosmos DB connection
    cosmos_service.connect()
    
    # Get current device tokens
    device_tokens = user.get('device_tokens', [])
    
    # Check if token already exists
    token_exists = False
    for dt in device_tokens:
        if dt.get('token') == device_token.token:
            # Update last_used
            dt['last_used'] = datetime.now(timezone.utc).isoformat()
            token_exists = True
            break
    
    # Add new token if not exists
    if not token_exists:
        device_tokens.append({
            'token': device_token.token,
            'platform': device_token.platform,
            'added_at': datetime.now(timezone.utc).isoformat(),
            'last_used': datetime.now(timezone.utc).isoformat()
        })
    
    # Update user profile
    await cosmos_service.update_user_profile(user['id'], {
        'device_tokens': device_tokens
    })
    
    logger.info(f"Registered device token for user {user['id']}")
    
    return {"status": "success", "message": "Device token registered"}


@router.delete("/device-token/{token}")
async def unregister_device_token(
    token: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Unregister device token
    
    Removes a device token from the user's profile.
    """
    
    # Initialize Cosmos DB connection
    cosmos_service.connect()
    
    # Get current device tokens
    device_tokens = user.get('device_tokens', [])
    
    # Remove token
    device_tokens = [dt for dt in device_tokens if dt.get('token') != token]
    
    # Update user profile
    await cosmos_service.update_user_profile(user['id'], {
        'device_tokens': device_tokens
    })
    
    logger.info(f"Unregistered device token for user {user['id']}")
    
    return {"status": "success", "message": "Device token unregistered"}

