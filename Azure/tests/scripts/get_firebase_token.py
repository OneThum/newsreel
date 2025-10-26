#!/usr/bin/env python3
"""
Firebase JWT Token Generator for API Testing

This script obtains a Firebase JWT token for authenticating with the Newsreel API.
It uses the same Firebase credentials as the iOS app.

Usage:
    python3 get_firebase_token.py

Requirements:
    pip install firebase-admin

Environment Variables:
    GOOGLE_APPLICATION_CREDENTIALS: Path to Firebase service account JSON file
"""

import os
import sys
import json
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, auth

# Firebase project configuration from GoogleService-Info.plist
FIREBASE_PROJECT_ID = "newsreel-865a5"
FIREBASE_API_KEY = "AIzaSyBK923FfBgdy3qt1wsrmal8c2eRk6f56Wg"

def get_firebase_token(use_test_account: bool = True):
    """
    Get a Firebase JWT token for API authentication
    
    Args:
        use_test_account: If True, creates a test user account for testing
        
    Returns:
        JWT token string
    """
    try:
        # Check if Firebase Admin is initialized
        if not firebase_admin._apps:
            # Initialize with project ID
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'projectId': FIREBASE_PROJECT_ID
            })
            print(f"✅ Firebase Admin initialized for project: {FIREBASE_PROJECT_ID}")
        
        if use_test_account:
            # Create or get test account
            test_email = "test@newsreel.test"
            test_password = "TestPassword123!"
            
            try:
                # Try to get existing user
                user = auth.get_user_by_email(test_email)
                print(f"✅ Found existing test user: {test_email}")
            except auth.UserNotFoundError:
                # Create new test user
                user = auth.create_user(
                    email=test_email,
                    password=test_password,
                    email_verified=True
                )
                print(f"✅ Created test user: {test_email}")
            
            # Get custom token (server-side)
            custom_token = auth.create_custom_token(user.uid)
            print(f"✅ Custom token created for user: {user.uid}")
            return custom_token
        
        else:
            # For production use, you'd need to authenticate with email/password
            # and exchange for ID token (requires REST API calls)
            print("⚠️  Production authentication requires Firebase REST API")
            return None
            
    except Exception as e:
        print(f"❌ Error getting Firebase token: {e}")
        return None


def save_token_to_file(token: str, filename: str = "firebase_token.txt"):
    """Save token to file for use in tests"""
    try:
        with open(filename, 'w') as f:
            f.write(token)
        print(f"✅ Token saved to {filename}")
    except Exception as e:
        print(f"❌ Error saving token: {e}")


def main():
    """Main entry point"""
    print("=" * 60)
    print("Firebase JWT Token Generator")
    print("=" * 60)
    print()
    
    # Note: This is a simplified approach
    # For actual testing, you'll need to:
    # 1. Use Firebase REST API to sign in with email/password
    # 2. Exchange credentials for ID token
    # 3. Use that ID token for API authentication
    
    print("ℹ️  This script requires Firebase Admin SDK setup")
    print("ℹ️  For system tests, consider using Firebase REST API directly")
    print()
    
    print("Alternative: Use the iOS app to get a token, then:")
    print("  export NEWSREEL_JWT_TOKEN='<token_from_ios_app>'")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
