#!/bin/bash
# Monitor First RSS Ingestion Run
# Watch the Newsreel backend come to life!

set -e

RESOURCE_GROUP="Newsreel-RG"
FUNCTION_APP="newsreel-func-51689"
COSMOS_ACCOUNT="newsreel-db-1759951135"
API_URL="https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io"

echo "📡 Newsreel Backend - First Run Monitor"
echo "========================================"
echo ""

# Check API health
echo "1️⃣  Checking API Health..."
HEALTH=$(curl -s "$API_URL/health")
if echo "$HEALTH" | grep -q "healthy"; then
    echo "   ✅ API is healthy and running"
    echo "   Response: $HEALTH"
else
    echo "   ❌ API health check failed"
    echo "   Response: $HEALTH"
    exit 1
fi
echo ""

# Check current time
CURRENT_MINUTE=$(date +%M)
NEXT_FIVE=$(( (($CURRENT_MINUTE / 5) + 1) * 5 ))
if [ $NEXT_FIVE -eq 60 ]; then
    NEXT_FIVE=0
fi

echo "2️⃣  RSS Ingestion Schedule"
echo "   Current time: $(date '+%H:%M:%S')"
echo "   RSS function runs every 5 minutes at: :00, :05, :10, :15, :20, etc."
echo "   Next scheduled run: $(date '+%H'):$(printf '%02d' $NEXT_FIVE):00"
echo ""

# Calculate wait time
CURRENT_SECONDS=$(date +%s)
NEXT_RUN_SECONDS=$(date -j -f "%Y-%m-%d %H:%M:%S" "$(date '+%Y-%m-%d %H'):$(printf '%02d' $NEXT_FIVE):00" +%s 2>/dev/null || echo 0)

if [ $NEXT_RUN_SECONDS -gt $CURRENT_SECONDS ]; then
    WAIT_TIME=$((NEXT_RUN_SECONDS - CURRENT_SECONDS))
    echo "   ⏰ Waiting ${WAIT_TIME} seconds for next run..."
else
    echo "   ⏰ Next run in a few minutes..."
fi
echo ""

# Check if Anthropic key is configured
echo "3️⃣  Checking Configuration..."
ANTHROPIC_SET=$(az functionapp config appsettings list \
    --name $FUNCTION_APP \
    --resource-group $RESOURCE_GROUP \
    --query "[?name=='ANTHROPIC_API_KEY'].value | [0]" -o tsv 2>/dev/null)

if [ -n "$ANTHROPIC_SET" ] && [ "$ANTHROPIC_SET" != "null" ]; then
    echo "   ✅ Anthropic API key configured"
else
    echo "   ⚠️  Anthropic API key NOT configured"
    echo "      AI summarization won't work until you add it"
    echo "      Run: ./configure-secrets.sh"
fi

FIREBASE_SET=$(az functionapp config appsettings list \
    --name $FUNCTION_APP \
    --resource-group $RESOURCE_GROUP \
    --query "[?name=='FIREBASE_CREDENTIALS'].value | [0]" -o tsv 2>/dev/null)

if [ -n "$FIREBASE_SET" ] && [ "$FIREBASE_SET" != "null" ]; then
    echo "   ✅ Firebase credentials configured"
else
    echo "   ⚠️  Firebase credentials NOT configured"
    echo "      Authentication won't work until you add them"
    echo "      Run: ./configure-secrets.sh"
fi
echo ""

# Monitor logs
echo "4️⃣  Monitoring Function Logs..."
echo "   Press Ctrl+C to stop"
echo "   Waiting for RSS ingestion to run..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "LIVE LOGS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Tail logs
az functionapp log tail \
    --name $FUNCTION_APP \
    --resource-group $RESOURCE_GROUP

# Note: The script will stay running until user presses Ctrl+C
# This allows them to see the RSS ingestion happen in real-time

