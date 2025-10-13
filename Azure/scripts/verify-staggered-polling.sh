#!/bin/bash

# Verify Staggered Polling Fix
# Run this 5-10 minutes after deployment to verify continuous polling

echo "🔍 Verifying Staggered Polling Fix"
echo "===================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "📊 Test 1: Checking for Silence Gaps"
echo "Expected: 0 (or very few) 'No feeds need polling' messages"
echo ""

SILENCE_COUNT=$(./query-logs.sh custom "traces | where timestamp > ago(10m) | where message contains 'No feeds need polling' | count" 2>/dev/null | jq -r '.tables[0].rows[0][0]' 2>/dev/null || echo "0")

if [ "$SILENCE_COUNT" = "0" ] || [ "$SILENCE_COUNT" = "null" ]; then
    echo -e "${GREEN}✅ PASS: No silence gaps detected${NC}"
    echo "   Result: $SILENCE_COUNT 'No feeds need polling' messages"
else
    echo -e "${RED}❌ FAIL: Silence gaps still present${NC}"
    echo "   Result: $SILENCE_COUNT 'No feeds need polling' messages (should be 0)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📊 Test 2: Checking Polling Frequency"
echo "Expected: ~60 polling events in 10 minutes (1 per 10 seconds)"
echo ""

POLLING_COUNT=$(./query-logs.sh custom "traces | where timestamp > ago(10m) | where message contains 'feeds this cycle' | count" 2>/dev/null | jq -r '.tables[0].rows[0][0]' 2>/dev/null || echo "0")

if [ "$POLLING_COUNT" -ge 50 ]; then
    echo -e "${GREEN}✅ PASS: Polling frequency good${NC}"
    echo "   Result: $POLLING_COUNT polling events in 10 min"
elif [ "$POLLING_COUNT" -ge 30 ]; then
    echo -e "${YELLOW}⚠️  PARTIAL: Polling slower than expected${NC}"
    echo "   Result: $POLLING_COUNT polling events in 10 min (expected ~60)"
else
    echo -e "${RED}❌ FAIL: Polling too slow${NC}"
    echo "   Result: $POLLING_COUNT polling events in 10 min (expected ~60)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📊 Test 3: Checking Feeds Per Cycle"
echo "Expected: ~5 feeds per cycle (not 12+)"
echo ""

echo "Recent polling events:"
./query-logs.sh custom "traces | where timestamp > ago(5m) | where message contains 'Polling' and message contains 'feeds this cycle' | project timestamp, message | order by timestamp desc | take 5" 2>/dev/null | jq -r '.tables[0].rows[] | "\(.[0]): \(.[1])"' 2>/dev/null | while read -r line; do
    echo "   $line"
    
    # Extract number of feeds
    if [[ $line =~ Polling\ ([0-9]+)\ feeds ]]; then
        FEEDS_COUNT="${BASH_REMATCH[1]}"
        if [ "$FEEDS_COUNT" -le 6 ]; then
            echo -e "      ${GREEN}✅ Good: $FEEDS_COUNT feeds (target: 5)${NC}"
        elif [ "$FEEDS_COUNT" -le 10 ]; then
            echo -e "      ${YELLOW}⚠️  OK: $FEEDS_COUNT feeds (target: 5)${NC}"
        else
            echo -e "      ${RED}❌ Too many: $FEEDS_COUNT feeds (target: 5)${NC}"
        fi
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📊 Test 4: Checking Article Flow"
echo "Expected: Steady stream, not bursts"
echo ""

echo "Articles per minute (last 10 minutes):"
./query-logs.sh custom "traces | where timestamp > ago(10m) | where message contains 'new articles out of' | extend minute = bin(timestamp, 1m) | summarize count() by minute | order by minute desc" 2>/dev/null | jq -r '.tables[0].rows[] | "\(.[0]): \(.[1]) article ingestion events"' 2>/dev/null | head -10

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📊 Test 5: Overall Health Check"
echo ""

./analyze-system-health.sh 10m 2>/dev/null | jq '{
    staggered_polling: .analysis.staggered_polling,
    feed_diversity: .analysis.feed_diversity,
    sources: .analysis.sources
}' 2>/dev/null

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "✅ Verification Complete!"
echo ""
echo "Expected after fix:"
echo "  • Silence gaps: 0"
echo "  • Polling frequency: 50-60 per 10 min"
echo "  • Feeds per cycle: 5"
echo "  • Articles: Steady flow across all minutes"
echo ""
echo "If all tests pass, the staggered polling fix is working! 🎉"

