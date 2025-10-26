"""
Firebase Authentication Helper for Test Fixtures

This module provides convenient functions for test fixtures to obtain
and manage Firebase JWT tokens.

Example usage in conftest.py:

    from .scripts.firebase_auth_helper import FirebaseAuthHelper
    
    auth_helper = FirebaseAuthHelper()
    
    @pytest.fixture
    def auth_token():
        token = auth_helper.get_token()
        if not token:
            pytest.skip("Firebase token not available")
        return token
    
    @pytest.fixture
    def api_client_authenticated(auth_token):
        client = requests.Session()
        client.headers['Authorization'] = f'Bearer {auth_token}'
        return client
"""

import os
import sys
from typing import Optional, Dict, Any

# Import the main module functions
sys.path.insert(0, os.path.dirname(__file__))
from get_firebase_token import (
    get_firebase_jwt_token,
    get_token_with_env_fallback,
    load_token_from_file,
    save_token_to_file
)


class FirebaseAuthHelper:
    """Helper class for Firebase authentication in tests"""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize Firebase auth helper
        
        Args:
            verbose: If True, print debug messages
        """
        self.verbose = verbose
        self._token_cache: Optional[str] = None
        self._user_data: Dict[str, Any] = {}
    
    def _log(self, message: str):
        """Log message if verbose mode is enabled"""
        if self.verbose:
            print(f"[FirebaseAuthHelper] {message}")
    
    def get_token(self, 
                  email: str = None,
                  password: str = None,
                  force_refresh: bool = False) -> Optional[str]:
        """
        Get a Firebase JWT token
        
        Priority order:
        1. Cached token (if not force_refresh)
        2. NEWSREEL_JWT_TOKEN environment variable
        3. firebase_token.txt file
        4. Generate new token from Firebase
        
        Args:
            email: Email for authentication (uses test account by default)
            password: Password for authentication
            force_refresh: If True, ignore cache and generate new token
            
        Returns:
            JWT token string, or None if failed
        """
        # Return cached token if available
        if self._token_cache and not force_refresh:
            self._log("Using cached token")
            return self._token_cache
        
        # Try with env fallback (which tries env var, file, then generation)
        token = get_token_with_env_fallback(
            email=email or os.getenv("FIREBASE_TEST_EMAIL", "test@newsreel.test"),
            password=password or os.getenv("FIREBASE_TEST_PASSWORD", "TestPassword123!")
        )
        
        if token:
            self._token_cache = token
            self._log(f"Got token: {token[:20]}...{token[-10:]}")
        
        return token
    
    def get_auth_header(self,
                        email: str = None,
                        password: str = None,
                        force_refresh: bool = False) -> Optional[Dict[str, str]]:
        """
        Get authorization header dict for API requests
        
        Args:
            email: Email for authentication
            password: Password for authentication
            force_refresh: If True, generate new token
            
        Returns:
            Dict with 'Authorization' key, or None if token generation failed
        """
        token = self.get_token(email=email, password=password, force_refresh=force_refresh)
        if token:
            return {"Authorization": f"Bearer {token}"}
        return None
    
    def clear_cache(self):
        """Clear cached token"""
        self._token_cache = None
        self._log("Cleared cached token")
    
    def validate_token_exists(self) -> bool:
        """
        Check if a token is available (from any source)
        
        Returns:
            True if token can be obtained, False otherwise
        """
        token = self.get_token()
        return token is not None
    
    @staticmethod
    def get_token_from_env() -> Optional[str]:
        """Get token from NEWSREEL_JWT_TOKEN environment variable"""
        token = os.getenv("NEWSREEL_JWT_TOKEN")
        if token and token.strip():
            return token.strip()
        return None
    
    @staticmethod
    def get_token_from_file(filename: str = "firebase_token.txt") -> Optional[str]:
        """Get token from file"""
        return load_token_from_file(filename)
    
    @staticmethod
    def save_token(token: str, filename: str = "firebase_token.txt") -> bool:
        """Save token to file for future use"""
        return save_token_to_file(token, filename)


# Global helper instance for convenience
_auth_helper: Optional[FirebaseAuthHelper] = None


def get_auth_helper(verbose: bool = False) -> FirebaseAuthHelper:
    """Get or create the global auth helper instance"""
    global _auth_helper
    if _auth_helper is None:
        _auth_helper = FirebaseAuthHelper(verbose=verbose)
    return _auth_helper


def get_token(force_refresh: bool = False) -> Optional[str]:
    """Convenience function to get token from global helper"""
    return get_auth_helper().get_token(force_refresh=force_refresh)


def get_auth_headers(force_refresh: bool = False) -> Optional[Dict[str, str]]:
    """Convenience function to get auth headers from global helper"""
    return get_auth_helper().get_auth_headers(force_refresh=force_refresh)
