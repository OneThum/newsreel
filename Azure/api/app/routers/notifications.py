"""
Device Token Management Router
Handles registration/unregistration of FCM tokens for push notifications
"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..middleware.auth import get_current_user
from ..services.cosmos_service import cosmos_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/device-token",
    tags=["notifications"],
    dependencies=[Depends(get_current_user)]
)


class DeviceTokenRequest(BaseModel):
    """Device token registration request"""
    fcm_token: str
    platform: str = "ios"
    app_version: str = "1.0"


class DeviceTokenResponse(BaseModel):
    """Device token registration response"""
    success: bool
    message: str


@router.post("/register", response_model=DeviceTokenResponse)
async def register_device_token(
    request: DeviceTokenRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Register a device token for push notifications
    
    - Stores FCM token in Cosmos DB linked to user
    - Enables push notifications for breaking news
    """
    logger.info(f"📱 Registering device token for user: {user_id}")
    logger.debug(f"   Token: {request.fcm_token[:20]}...")
    logger.debug(f"   Platform: {request.platform}")
    logger.debug(f"   App version: {request.app_version}")
    
    try:
        # Get user container
        container = cosmos_service.get_container("user_preferences")
        
        # Query for existing user preferences
        query = "SELECT * FROM c WHERE c.user_id = @user_id"
        parameters = [{"name": "@user_id", "value": user_id}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if items:
            # Update existing document
            user_prefs = items[0]
            user_prefs["fcm_token"] = request.fcm_token
            user_prefs["platform"] = request.platform
            user_prefs["app_version"] = request.app_version
            user_prefs["token_registered_at"] = datetime.utcnow().isoformat()
            user_prefs["notifications_enabled"] = True
            
            container.replace_item(
                item=user_prefs["id"],
                body=user_prefs
            )
            
            logger.info(f"✅ Updated FCM token for user: {user_id}")
        else:
            # Create new document
            user_prefs = {
                "id": f"prefs_{user_id}",
                "user_id": user_id,
                "fcm_token": request.fcm_token,
                "platform": request.platform,
                "app_version": request.app_version,
                "token_registered_at": datetime.utcnow().isoformat(),
                "notifications_enabled": True,
                "notification_preferences": {
                    "breaking_news": True,
                    "developing_stories": True,
                    "daily_digest": False
                }
            }
            
            container.create_item(body=user_prefs)
            logger.info(f"✅ Created new FCM token for user: {user_id}")
        
        return DeviceTokenResponse(
            success=True,
            message="Device token registered successfully"
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to register device token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register device token"
        )


@router.post("/unregister", response_model=DeviceTokenResponse)
async def unregister_device_token(
    request: DeviceTokenRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Unregister a device token (e.g., on logout)
    
    - Removes FCM token from Cosmos DB
    - Disables push notifications
    """
    logger.info(f"📱 Unregistering device token for user: {user_id}")
    
    try:
        # Get user container
        container = cosmos_service.get_container("user_preferences")
        
        # Query for existing user preferences
        query = "SELECT * FROM c WHERE c.user_id = @user_id"
        parameters = [{"name": "@user_id", "value": user_id}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if items:
            # Update existing document to remove token
            user_prefs = items[0]
            user_prefs["fcm_token"] = None
            user_prefs["notifications_enabled"] = False
            user_prefs["token_unregistered_at"] = datetime.utcnow().isoformat()
            
            container.replace_item(
                item=user_prefs["id"],
                body=user_prefs
            )
            
            logger.info(f"✅ Removed FCM token for user: {user_id}")
        else:
            logger.warning(f"⚠️  No preferences found for user: {user_id}")
        
        return DeviceTokenResponse(
            success=True,
            message="Device token unregistered successfully"
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to unregister device token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unregister device token"
        )


@router.get("/status")
async def get_notification_status(user_id: str = Depends(get_current_user)):
    """
    Get notification status for the current user
    
    Returns whether notifications are enabled and token info
    """
    try:
        container = cosmos_service.get_container("user_preferences")
        
        query = "SELECT * FROM c WHERE c.user_id = @user_id"
        parameters = [{"name": "@user_id", "value": user_id}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if items:
            user_prefs = items[0]
            return {
                "notifications_enabled": user_prefs.get("notifications_enabled", False),
                "has_token": user_prefs.get("fcm_token") is not None,
                "platform": user_prefs.get("platform"),
                "preferences": user_prefs.get("notification_preferences", {})
            }
        else:
            return {
                "notifications_enabled": False,
                "has_token": False,
                "platform": None,
                "preferences": {}
            }
            
    except Exception as e:
        logger.error(f"❌ Failed to get notification status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification status"
        )

