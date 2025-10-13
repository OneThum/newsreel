#!/bin/bash
# Configure API Keys and Secrets for Newsreel Azure Backend
# Run this after deployment to add required API keys

set -e

RESOURCE_GROUP="Newsreel-RG"
FUNCTION_APP="newsreel-func-51689"
CONTAINER_APP="newsreel-api"

echo "🔐 Newsreel Azure - Secret Configuration"
echo "=========================================="
echo ""

# Check if required tools are installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install it first."
    exit 1
fi

# Check if logged in
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure. Please run: az login"
    exit 1
fi

echo "✅ Azure CLI ready"
echo ""

# Function to prompt for secret
prompt_for_secret() {
    local secret_name=$1
    local description=$2
    local optional=$3
    
    echo "📝 $secret_name"
    echo "   $description"
    
    if [ "$optional" = "true" ]; then
        echo "   (Optional - press Enter to skip)"
    fi
    
    read -p "   Enter value: " secret_value
    
    if [ -z "$secret_value" ]; then
        if [ "$optional" = "true" ]; then
            echo "   ⏭️  Skipped"
            echo ""
            return 1
        else
            echo "   ❌ This is required!"
            return 1
        fi
    fi
    
    echo "$secret_value"
    echo ""
    return 0
}

# Anthropic API Key
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  Anthropic API Key (Required for AI Summarization)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Get your key from: https://console.anthropic.com/"
echo ""

if ANTHROPIC_KEY=$(prompt_for_secret "ANTHROPIC_API_KEY" "Claude Sonnet 4 API key (starts with sk-ant-)" "false"); then
    echo "Adding to Function App..."
    az functionapp config appsettings set \
        --name $FUNCTION_APP \
        --resource-group $RESOURCE_GROUP \
        --settings "ANTHROPIC_API_KEY=$ANTHROPIC_KEY" \
        --output none
    echo "✅ Anthropic API key configured"
else
    echo "⚠️  Skipping Anthropic key (AI summarization won't work)"
fi
echo ""

# Firebase Credentials
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Firebase Service Account (Required for Authentication)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Get credentials from:"
echo "  1. https://console.firebase.google.com/project/newsreel-865a5"
echo "  2. Settings ⚙️  → Service Accounts"
echo "  3. Generate New Private Key"
echo "  4. Save the JSON file"
echo ""
echo "Enter the path to the downloaded JSON file:"
read -p "   File path: " firebase_file

if [ -f "$firebase_file" ]; then
    echo "Reading Firebase credentials..."
    FIREBASE_CREDS=$(cat "$firebase_file" | jq -c .)
    
    echo "Adding to Function App..."
    az functionapp config appsettings set \
        --name $FUNCTION_APP \
        --resource-group $RESOURCE_GROUP \
        --settings "FIREBASE_CREDENTIALS=$FIREBASE_CREDS" \
        --output none
    
    echo "Adding to Container App..."
    az containerapp update \
        --name $CONTAINER_APP \
        --resource-group $RESOURCE_GROUP \
        --set-env-vars "FIREBASE_CREDENTIALS=$FIREBASE_CREDS" "FIREBASE_PROJECT_ID=newsreel-865a5" \
        --output none
    
    echo "✅ Firebase credentials configured"
else
    echo "⚠️  File not found. Skipping Firebase configuration."
    echo "   Authentication won't work until this is configured!"
fi
echo ""

# Twitter Bearer Token (Optional)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  Twitter Bearer Token (Optional - Phase 2)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Get token from: https://developer.twitter.com/"
echo "Cost: $100/month for Basic tier"
echo ""

if TWITTER_TOKEN=$(prompt_for_secret "TWITTER_BEARER_TOKEN" "Twitter API Bearer Token" "true"); then
    echo "Adding to Function App..."
    az functionapp config appsettings set \
        --name $FUNCTION_APP \
        --resource-group $RESOURCE_GROUP \
        --settings "TWITTER_BEARER_TOKEN=$TWITTER_TOKEN" \
        --output none
    echo "✅ Twitter token configured"
else
    echo "ℹ️  Breaking news monitor will work without Twitter (RSS-based detection only)"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Configuration Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  1. Wait for RSS ingestion (runs every 5 minutes)"
echo "  2. Monitor logs: az functionapp log tail --name $FUNCTION_APP --resource-group $RESOURCE_GROUP"
echo "  3. Check Cosmos DB for articles after 5-10 minutes"
echo "  4. Test API from iOS app"
echo ""
echo "Monitor deployment:"
echo "  API Health: curl https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/health"
echo "  API Docs: https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/docs"
echo ""
echo "🚀 Your backend is ready!"

