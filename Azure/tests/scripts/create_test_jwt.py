#!/usr/bin/env python3
"""
Create a test JWT token for API testing

This creates a test JWT token that mimics Firebase tokens for local testing.
Uses HS256 algorithm with a test secret key.
"""

import jwt
import json
from datetime import datetime, timedelta, timezone
import os

# Test secret - matches what we'd use for local testing
TEST_SECRET = os.getenv("JWT_SECRET_KEY", "test-secret-key-for-local-development-only")

def create_test_jwt():
    """Create a test JWT token"""
    
    # Create payload similar to Firebase
    now = datetime.now(timezone.utc)
    payload = {
        # Standard JWT claims
        "iss": "https://securetoken.google.com/newsreel-865a5",
        "aud": "newsreel-865a5",
        "auth_time": int(now.timestamp()),
        "user_id": "test_user_12345",
        "sub": "test_user_12345",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
        
        # Firebase custom claims
        "email": "test@newsreel.test",
        "email_verified": True,
        "firebase": {
            "identities": {
                "email": ["test@newsreel.test"]
            },
            "sign_in_provider": "anonymous"
        }
    }
    
    # Create JWT
    token = jwt.encode(
        payload,
        TEST_SECRET,
        algorithm="HS256"
    )
    
    return token

if __name__ == "__main__":
    token = create_test_jwt()
    print(token)
