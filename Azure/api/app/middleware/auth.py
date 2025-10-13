"""Authentication Middleware"""
import logging
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..services.auth_service import auth_service
from ..services.cosmos_service import cosmos_service
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user
    Validates Firebase JWT token and returns user info
    """
    
    token = credentials.credentials
    
    # Verify token with Firebase
    user_info = await auth_service.verify_token(token)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get or create user profile in Cosmos DB
    user_id = user_info['uid']
    user_profile = await cosmos_service.get_user_profile(user_id)
    
    if not user_profile:
        # Create new user profile
        user_profile = {
            'id': user_id,
            'firebase_uid': user_id,
            'email': user_info.get('email', ''),
            'created_at': datetime.now(timezone.utc).isoformat(),
            'last_active': datetime.now(timezone.utc).isoformat(),
            'subscription': {
                'tier': 'free',
                'started_at': datetime.now(timezone.utc).isoformat()
            },
            'preferences': {
                'categories': [],
                'sources_boost': [],
                'sources_mute': [],
                'notification_settings': {
                    'breaking_news': True,
                    'threshold': 'major'
                },
                'reading_preferences': {
                    'summary_length': 'standard',
                    'font_size': 'medium',
                    'theme': 'auto'
                }
            },
            'interaction_stats': {
                'total_stories_viewed': 0,
                'total_stories_liked': 0,
                'total_stories_saved': 0,
                'total_stories_shared': 0
            },
            'personalization_profile': {
                'category_scores': {},
                'topic_scores': {},
                'recency_preference': 0.75,
                'diversity_preference': 0.60
            },
            'rate_limiting': {
                'daily_story_count': 0,
                'last_reset': datetime.now(timezone.utc).isoformat(),
                'exceeded_limit': False
            },
            'device_tokens': []
        }
        
        user_profile = await cosmos_service.create_user_profile(user_profile)
        logger.info(f"Created new user profile: {user_id}")
    else:
        # Update last active
        await cosmos_service.update_user_profile(user_id, {
            'last_active': datetime.now(timezone.utc).isoformat()
        })
    
    return user_profile


async def get_optional_user(
    request: Request
) -> Optional[Dict[str, Any]]:
    """
    Optional authentication - returns user if authenticated, None otherwise
    """
    
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.replace('Bearer ', '')
    
    try:
        user_info = await auth_service.verify_token(token)
        if user_info:
            user_id = user_info['uid']
            user_profile = await cosmos_service.get_user_profile(user_id)
            return user_profile
    except Exception as e:
        logger.warning(f"Optional auth failed: {e}")
    
    return None


async def auth_middleware(request: Request, call_next):
    """
    Middleware to add authentication context to request
    """
    # This is a simple pass-through middleware
    # Actual authentication is handled by the get_current_user dependency
    response = await call_next(request)
    return response


def check_rate_limit(user: Dict[str, Any], tier_specific: bool = True) -> Dict[str, Any]:
    """
    Check if user has exceeded rate limit
    Returns rate limit info instead of raising exception
    """
    
    rate_limiting = user.get('rate_limiting', {})
    subscription = user.get('subscription', {})
    
    daily_count = rate_limiting.get('daily_story_count', 0)
    last_reset = rate_limiting.get('last_reset', '')
    
    # Check if we need to reset daily count
    if last_reset:
        try:
            last_reset_dt = datetime.fromisoformat(last_reset.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            
            if (now - last_reset_dt).days >= 1:
                # Reset count
                daily_count = 0
        except Exception:
            pass
    
    # Check limit based on tier
    tier = subscription.get('tier', 'free')
    
    if tier == 'free':
        limit = 20
    else:  # paid
        limit = 1000
    
    limit_reached = daily_count >= limit
    remaining = max(0, limit - daily_count)
    
    return {
        'limit_reached': limit_reached,
        'daily_count': daily_count,
        'daily_limit': limit,
        'remaining': remaining,
        'tier': tier
    }

