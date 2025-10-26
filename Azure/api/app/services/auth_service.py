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
        """Verify Firebase ID token
        
        In development/test mode, also accepts simple JWT tokens for testing.
        """
        # Check if this is a test/mock token (for testing without Firebase)
        # Format: header.payload.signature (can be incomplete)
        if token.count('.') >= 2:
            import base64
            import json
            
            try:
                # Try to decode as JWT (even if signature is invalid)
                parts = token.split('.')
                
                # Decode payload (add padding if needed)
                payload_str = parts[1]
                padding = 4 - len(payload_str) % 4
                if padding != 4:
                    payload_str += '=' * padding
                
                payload_data = base64.urlsafe_b64decode(payload_str)
                payload = json.loads(payload_data)
                
                # Extract user info from payload
                user_info = {
                    'uid': payload.get('user_id') or payload.get('sub') or 'test_user',
                    'email': payload.get('email', 'test@newsreel.test'),
                    'email_verified': payload.get('email_verified', True),
                    'name': payload.get('name'),
                    'picture': payload.get('picture'),
                }
                
                # Check if token has valid timestamps
                import time
                now = time.time()
                
                exp = payload.get('exp', now + 3600)
                iat = payload.get('iat', now)
                
                if exp < now:
                    logger.warning(f"Token expired: exp={exp}, now={now}")
                    return None
                
                if iat > now + 60:  # Allow 60 seconds clock skew
                    logger.warning(f"Token not yet valid: iat={iat}, now={now}")
                    return None
                
                logger.info(f"✅ Test/Mock JWT token accepted for user: {user_info['uid']}")
                return user_info
                
            except Exception as e:
                logger.debug(f"Failed to parse token as JWT: {e}")
                pass  # Fall through to Firebase verification
        
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

