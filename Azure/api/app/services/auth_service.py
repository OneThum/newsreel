"""Authentication Service"""
import logging
from typing import Optional, Dict, Any
import json

try:
    import firebase_admin
    from firebase_admin import credentials, auth
except ImportError:
    firebase_admin = None
    auth = None

from ..config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Firebase authentication service"""
    
    def __init__(self):
        self.app = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        if not firebase_admin:
            logger.warning("Firebase Admin SDK not installed")
            return
        
        try:
            if settings.firebase_credentials:
                # Parse credentials from environment variable
                cred_dict = json.loads(settings.firebase_credentials)
                cred = credentials.Certificate(cred_dict)
                self.app = firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized")
            else:
                logger.warning("Firebase credentials not configured")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify Firebase ID token"""
        if not auth:
            logger.error("Firebase auth not available")
            return None
        
        try:
            # Verify the token with Firebase
            decoded_token = auth.verify_id_token(token)
            
            # Extract user info
            user_info = {
                'uid': decoded_token.get('uid'),
                'email': decoded_token.get('email'),
                'email_verified': decoded_token.get('email_verified', False),
                'name': decoded_token.get('name'),
                'picture': decoded_token.get('picture'),
            }
            
            return user_info
            
        except auth.InvalidIdTokenError:
            logger.warning("Invalid Firebase token")
            return None
        except auth.ExpiredIdTokenError:
            logger.warning("Expired Firebase token")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None
    
    async def get_user(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user by UID"""
        if not auth:
            return None
        
        try:
            user_record = auth.get_user(uid)
            return {
                'uid': user_record.uid,
                'email': user_record.email,
                'email_verified': user_record.email_verified,
                'display_name': user_record.display_name,
                'photo_url': user_record.photo_url,
                'disabled': user_record.disabled,
            }
        except Exception as e:
            logger.error(f"Error getting user {uid}: {e}")
            return None


# Global instance
auth_service = AuthService()

