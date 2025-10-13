#!/bin/bash

# Push Notification Verification Script
# Checks if everything is configured correctly

set -e

echo "🔍 Newsreel Push Notification Verification"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

RESOURCE_GROUP="Newsreel-RG"
FUNCTION_APP="newsreel-func-51689"
COSMOS_ACCOUNT="newsreel-cosmos"
COSMOS_DB="newsreel-db"

# 1. Check Azure Function App FCM_SERVER_KEY
echo "1️⃣  Checking FCM_SERVER_KEY in Azure Function App..."
FCM_KEY=$(az functionapp config appsettings list \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --query "[?name=='FCM_SERVER_KEY'].value" -o tsv 2>/dev/null)

if [ -z "$FCM_KEY" ]; then
    echo -e "${RED}❌ FCM_SERVER_KEY not found${NC}"
    echo "   Run: az functionapp config appsettings set --name $FUNCTION_APP --resource-group $RESOURCE_GROUP --settings FCM_SERVER_KEY=\"your_key_here\""
else
    echo -e "${GREEN}✅ FCM_SERVER_KEY configured (${#FCM_KEY} characters)${NC}"
fi
echo ""

# 2. Check if API is running
echo "2️⃣  Checking if API is running..."
API_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/health || echo "000")

if [ "$API_HEALTH" = "200" ]; then
    echo -e "${GREEN}✅ API is running${NC}"
else
    echo -e "${RED}❌ API is not responding (HTTP $API_HEALTH)${NC}"
fi
echo ""

# 3. Check Cosmos DB connection
echo "3️⃣  Checking Cosmos DB connection..."
DB_EXISTS=$(az cosmosdb sql database show \
  --account-name $COSMOS_ACCOUNT \
  --name $COSMOS_DB \
  --resource-group $RESOURCE_GROUP \
  --query "id" -o tsv 2>/dev/null)

if [ -n "$DB_EXISTS" ]; then
    echo -e "${GREEN}✅ Cosmos DB connected${NC}"
else
    echo -e "${RED}❌ Cannot connect to Cosmos DB${NC}"
fi
echo ""

# 4. Check user_preferences container
echo "4️⃣  Checking user_preferences container..."
CONTAINER_EXISTS=$(az cosmosdb sql container show \
  --account-name $COSMOS_ACCOUNT \
  --database-name $COSMOS_DB \
  --name user_preferences \
  --resource-group $RESOURCE_GROUP \
  --query "id" -o tsv 2>/dev/null)

if [ -n "$CONTAINER_EXISTS" ]; then
    echo -e "${GREEN}✅ user_preferences container exists${NC}"
else
    echo -e "${YELLOW}⚠️  user_preferences container not found${NC}"
    echo "   Creating container..."
    az cosmosdb sql container create \
      --account-name $COSMOS_ACCOUNT \
      --database-name $COSMOS_DB \
      --name user_preferences \
      --partition-key-path "/user_id" \
      --resource-group $RESOURCE_GROUP \
      --throughput 400 > /dev/null 2>&1
    echo -e "${GREEN}✅ Container created${NC}"
fi
echo ""

# 5. Check for registered tokens
echo "5️⃣  Checking for registered device tokens..."
TOKEN_COUNT=$(az cosmosdb sql query \
  --account-name $COSMOS_ACCOUNT \
  --database-name $COSMOS_DB \
  --container-name user_preferences \
  --query-text "SELECT VALUE COUNT(1) FROM c WHERE c.fcm_token != null" \
  --resource-group $RESOURCE_GROUP 2>/dev/null | jq '.[0]' || echo "0")

if [ "$TOKEN_COUNT" = "0" ]; then
    echo -e "${YELLOW}⚠️  No device tokens registered yet${NC}"
    echo "   → Run the iOS app and grant notification permission"
else
    echo -e "${GREEN}✅ $TOKEN_COUNT device token(s) registered${NC}"
fi
echo ""

# 6. Check for BREAKING stories
echo "6️⃣  Checking for BREAKING stories..."
BREAKING_COUNT=$(az cosmosdb sql query \
  --account-name $COSMOS_ACCOUNT \
  --database-name $COSMOS_DB \
  --container-name story_clusters \
  --query-text "SELECT VALUE COUNT(1) FROM c WHERE c.status = 'BREAKING'" \
  --resource-group $RESOURCE_GROUP 2>/dev/null | jq '.[0]' || echo "0")

echo "   Found $BREAKING_COUNT BREAKING stories"
if [ "$BREAKING_COUNT" -gt "0" ]; then
    echo -e "${GREEN}✅ Breaking stories exist (will trigger notifications)${NC}"
else
    echo -e "${YELLOW}ℹ️  No breaking stories currently${NC}"
fi
echo ""

# 7. Check Xcode entitlements
echo "7️⃣  Checking Xcode entitlements..."
ENTITLEMENTS_FILE="Newsreel App/Newsreel/Newsreel.entitlements"
if [ -f "$ENTITLEMENTS_FILE" ]; then
    if grep -q "aps-environment" "$ENTITLEMENTS_FILE"; then
        ENV=$(grep -A1 "aps-environment" "$ENTITLEMENTS_FILE" | tail -1 | sed 's/.*<string>\(.*\)<\/string>.*/\1/')
        echo -e "${GREEN}✅ APNs environment: $ENV${NC}"
    else
        echo -e "${RED}❌ aps-environment not found in entitlements${NC}"
    fi
else
    echo -e "${RED}❌ Entitlements file not found${NC}"
fi
echo ""

# Summary
echo "=========================================="
echo "📊 Summary"
echo "=========================================="
echo ""

CHECKS_PASSED=0
CHECKS_TOTAL=7

[ -n "$FCM_KEY" ] && ((CHECKS_PASSED++))
[ "$API_HEALTH" = "200" ] && ((CHECKS_PASSED++))
[ -n "$DB_EXISTS" ] && ((CHECKS_PASSED++))
[ -n "$CONTAINER_EXISTS" ] && ((CHECKS_PASSED++))
[ "$TOKEN_COUNT" -gt "0" ] && ((CHECKS_PASSED++))
[ "$BREAKING_COUNT" -ge "0" ] && ((CHECKS_PASSED++))
[ -f "$ENTITLEMENTS_FILE" ] && ((CHECKS_PASSED++))

echo "$CHECKS_PASSED/$CHECKS_TOTAL checks passed"
echo ""

if [ "$CHECKS_PASSED" -eq "$CHECKS_TOTAL" ]; then
    echo -e "${GREEN}✅ All systems ready!${NC}"
    echo ""
    echo "🎯 Next steps:"
    echo "   1. Open Xcode and enable Push Notifications capability"
    echo "   2. Run the app (Cmd+R)"
    echo "   3. Login and grant notification permission"
    echo "   4. Check logs for token registration"
    echo "   5. Send test notification from Firebase Console"
elif [ "$CHECKS_PASSED" -ge $((CHECKS_TOTAL * 2 / 3)) ]; then
    echo -e "${YELLOW}⚠️  Most checks passed - minor issues to fix${NC}"
else
    echo -e "${RED}❌ Several issues need attention${NC}"
fi

echo ""
echo "📖 Full testing guide: docs/Push_Notification_Testing_Guide.md"

