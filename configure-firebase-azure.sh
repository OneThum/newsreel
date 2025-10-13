#!/bin/bash

# Configure Firebase Credentials on Azure Container App
# This enables JWT token validation for all users (including anonymous)

echo "🔐 Configuring Firebase Credentials on Azure..."

# Check if service account file is provided
if [ -z "$1" ]; then
    echo "❌ Error: Please provide path to Firebase service account JSON file"
    echo ""
    echo "Usage: ./configure-firebase-azure.sh /path/to/firebase-service-account.json"
    echo ""
    echo "To get the file:"
    echo "1. Go to https://console.firebase.google.com"
    echo "2. Select your project"
    echo "3. Settings → Service accounts"
    echo "4. Generate new private key"
    exit 1
fi

FIREBASE_JSON_PATH="$1"

# Verify file exists
if [ ! -f "$FIREBASE_JSON_PATH" ]; then
    echo "❌ Error: File not found: $FIREBASE_JSON_PATH"
    exit 1
fi

echo "📄 Using Firebase credentials from: $FIREBASE_JSON_PATH"

# Read the JSON file (it's already a JSON string)
FIREBASE_CREDS=$(cat "$FIREBASE_JSON_PATH")

echo "✅ Firebase credentials loaded"
echo ""
echo "🚀 Updating Azure Container App..."

# Update Container App with Firebase credentials
az containerapp update \
  --name newsreel-api \
  --resource-group Newsreel-RG \
  --set-env-vars "FIREBASE_CREDENTIALS=$FIREBASE_CREDS" \
  --output table

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Firebase credentials configured on Azure"
    echo ""
    echo "🎯 What this enables:"
    echo "   ✅ Anonymous users can authenticate"
    echo "   ✅ Apple Sign-In users can authenticate"
    echo "   ✅ All users get personalized feeds"
    echo "   ✅ Interaction tracking works (like, save, view)"
    echo "   ✅ User profiles created automatically"
    echo ""
    echo "🔄 Container App is restarting (takes ~30 seconds)..."
    echo ""
    echo "✅ After restart, your iOS app will work fully!"
    echo ""
    echo "Test it:"
    echo "1. Wait 30 seconds for Azure to restart"
    echo "2. In Xcode: Cmd+R to run app"
    echo "3. Watch console - should see:"
    echo "   ✅ API Response: 200 (not 401)"
    echo "   ✅ Feed loaded successfully"
    echo "   ✅ Interactions recorded"
else
    echo ""
    echo "❌ Failed to update Container App"
    echo "Check Azure CLI is logged in: az login"
    exit 1
fi

