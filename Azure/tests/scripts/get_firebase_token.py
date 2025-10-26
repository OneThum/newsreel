#!/usr/bin/env python3
"""
Firebase JWT Token Generator for API Testing

This script obtains a Firebase JWT token for authenticating with the Newsreel API.
It uses the Firebase REST API to authenticate, which matches what the iOS app does.

Usage:
    # Get token and export to environment
    export NEWSREEL_JWT_TOKEN=$(python3 get_firebase_token.py --get-token)
    
    # Use in tests
    from get_firebase_token import get_firebase_jwt_token
    token = get_firebase_jwt_token()

Requirements:
    pip install requests

Environment Variables:
    FIREBASE_API_KEY: Firebase Web API key (from Google console)
    FIREBASE_PROJECT_ID: Firebase project ID
"""

import os
import sys
import json
import requests
from datetime import datetime
from typing import Optional, Dict, Any

# Firebase project configuration
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "newsreel-865a5")
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "AIzaSyBK923FfBgdy3qt1wsrmal8c2eRk6f56Wg")

# Test account credentials
TEST_EMAIL = os.getenv("FIREBASE_TEST_EMAIL", "test@newsreel.test")
TEST_PASSWORD = os.getenv("FIREBASE_TEST_PASSWORD", "TestPassword123!")

# Firebase REST API endpoints
FIREBASE_SIGNUP_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp"
FIREBASE_LOGIN_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"


def create_test_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Create a Firebase test user via REST API
    
    Args:
        email: User email
        password: User password
        
    Returns:
        User info dict with uid, or None if failed
    """
    try:
        response = requests.post(
            f"{FIREBASE_SIGNUP_URL}?key={FIREBASE_API_KEY}",
            json={"email": email, "password": password, "returnSecureToken": True},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Created test user: {email} (UID: {data.get('localId', 'unknown')})")
            return data
        elif response.status_code == 400:
            error = response.json().get("error", {}).get("message", "Unknown error")
            if "EMAIL_EXISTS" in error or "email already exists" in error.lower():
                print(f"ℹ️  Test user already exists: {email}")
                # Try to sign in
                return login_user(email, password)
            else:
                print(f"❌ Failed to create user: {error}")
                return None
        else:
            print(f"❌ Firebase API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return None


def login_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Sign in a Firebase user via REST API
    
    Args:
        email: User email
        password: User password
        
    Returns:
        User info dict with idToken and localId, or None if failed
    """
    try:
        response = requests.post(
            f"{FIREBASE_LOGIN_URL}?key={FIREBASE_API_KEY}",
            json={"email": email, "password": password, "returnSecureToken": True},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Signed in: {email} (UID: {data.get('localId', 'unknown')})")
            return data
        else:
            error = response.json().get("error", {}).get("message", "Unknown error")
            print(f"❌ Failed to sign in: {error}")
            return None
            
    except Exception as e:
        print(f"❌ Error signing in: {e}")
        return None


def get_firebase_jwt_token(
    email: str = TEST_EMAIL,
    password: str = TEST_PASSWORD,
    create_if_missing: bool = True
) -> Optional[str]:
    """
    Get a Firebase JWT token for API authentication
    
    This function:
    1. Attempts to sign in with provided credentials
    2. If user doesn't exist and create_if_missing=True, creates the user
    3. Returns the JWT ID token for use with the Newsreel API
    
    Args:
        email: User email (default: test account)
        password: User password (default: test account)
        create_if_missing: If True, creates user if they don't exist
        
    Returns:
        JWT ID token string, or None if failed
    """
    print(f"\n{'=' * 60}")
    print(f"Firebase JWT Token Generator")
    print(f"{'=' * 60}\n")
    
    # Try to sign in first
    user_data = login_user(email, password)
    
    # If sign in failed and we should create user, do that
    if not user_data and create_if_missing:
        print(f"ℹ️  Creating test user...")
        user_data = create_test_user(email, password)
        
        # If creation succeeded, try signing in again
        if user_data:
            user_data = login_user(email, password)
    
    if user_data and "idToken" in user_data:
        token = user_data["idToken"]
        print(f"\n✅ Got Firebase JWT token")
        print(f"   User ID: {user_data.get('localId', 'unknown')}")
        print(f"   Token preview: {token[:20]}...{token[-10:]}")
        print(f"   Token length: {len(token)} characters\n")
        return token
    else:
        print(f"❌ Failed to obtain Firebase JWT token\n")
        return None


def save_token_to_file(token: str, filename: str = "firebase_token.txt") -> bool:
    """
    Save token to file for use in tests
    
    Args:
        token: JWT token
        filename: File to save to
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filename, 'w') as f:
            f.write(token)
        print(f"✅ Token saved to {filename}")
        return True
    except Exception as e:
        print(f"❌ Error saving token: {e}")
        return False


def load_token_from_file(filename: str = "firebase_token.txt") -> Optional[str]:
    """
    Load token from file
    
    Args:
        filename: File to load from
        
    Returns:
        Token string, or None if file doesn't exist or is empty
    """
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                token = f.read().strip()
                if token:
                    print(f"✅ Loaded token from {filename}")
                    return token
    except Exception as e:
        print(f"⚠️  Could not load token from file: {e}")
    return None


def get_token_with_env_fallback(
    email: str = TEST_EMAIL,
    password: str = TEST_PASSWORD
) -> Optional[str]:
    """
    Get token with multiple fallback options:
    1. Environment variable NEWSREEL_JWT_TOKEN
    2. Local firebase_token.txt file
    3. Generate new token from Firebase
    
    Args:
        email: User email for generation
        password: User password for generation
        
    Returns:
        JWT token string, or None if all methods fail
    """
    # Check environment variable first
    if "NEWSREEL_JWT_TOKEN" in os.environ:
        token = os.environ["NEWSREEL_JWT_TOKEN"].strip()
        if token:
            print(f"✅ Using token from NEWSREEL_JWT_TOKEN environment variable")
            return token
    
    # Check local file
    token = load_token_from_file("firebase_token.txt")
    if token:
        return token
    
    # Generate new token
    print(f"ℹ️  Generating new Firebase token...")
    token = get_firebase_jwt_token(email, password)
    
    if token:
        # Save for future use
        save_token_to_file(token)
    
    return token


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Firebase JWT Token Generator")
    parser.add_argument(
        "--get-token",
        action="store_true",
        help="Print just the token (for export)"
    )
    parser.add_argument(
        "--email",
        default=TEST_EMAIL,
        help=f"User email (default: {TEST_EMAIL})"
    )
    parser.add_argument(
        "--password",
        default=TEST_PASSWORD,
        help="User password"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save token to firebase_token.txt"
    )
    
    args = parser.parse_args()
    
    token = get_firebase_jwt_token(args.email, args.password)
    
    if not token:
        return 1
    
    if args.get_token:
        # Print just the token for use in export
        print(token, end='')
    
    if args.save:
        save_token_to_file(token)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
