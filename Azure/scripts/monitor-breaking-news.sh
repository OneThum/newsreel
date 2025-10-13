#!/bin/bash

# Real-Time Breaking News Monitor
# Tracks the Gaza hostage release story and verifies breaking news detection

echo "🔥 LIVE BREAKING NEWS MONITOR - Gaza Hostage Release"
echo "====================================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

STORY_ID="story_20251012_084423_58f041ad44cd"

echo -e "${BLUE}Target Story ID: ${STORY_ID}${NC}"
echo ""

# Function to check story status
check_story_status() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${YELLOW}$(date -u +'%Y-%m-%d %H:%M:%S UTC')${NC}"
    echo ""
    
    # 1. Check story status in logs
    echo -e "${BLUE}1️⃣ Story Status from Logs:${NC}"
    ./query-logs.sh custom "traces | where timestamp > ago(5m) | where message contains '$STORY_ID' | project timestamp, message | order by timestamp desc | take 5" 2>&1 | \
        python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    rows = data['tables'][0]['rows']
    if rows:
        for row in rows:
            ts = row[0].split('.')[0].replace('T', ' ').replace('Z', '')
            msg = row[1]
            
            # Extract key info
            if 'Story Cluster:' in msg:
                if '[BREAKING]' in msg:
                    print(f'   ✅ {ts}: BREAKING status')
                elif '[VERIFIED]' in msg:
                    print(f'   ⚠️  {ts}: VERIFIED status')
                elif '[DEVELOPING]' in msg:
                    print(f'   📊 {ts}: DEVELOPING status')
                    
                # Extract source count
                if 'source_count' in msg:
                    import re
                    match = re.search(r'\"source_count\":\s*(\d+)', msg)
                    if match:
                        print(f'      Sources: {match.group(1)}')
            elif 'promoted to BREAKING' in msg:
                print(f'   🔥 {ts}: PROMOTED TO BREAKING!')
            elif 'Added' in msg and 'sources' in msg:
                import re
                match = re.search(r'Added (\w+) to story.*\(now (\d+)', msg)
                if match:
                    print(f'   📰 {ts}: Added {match.group(1)} source (now {match.group(2)} total)')
    else:
        print('   No recent activity')
except Exception as e:
    print(f'   Error: {e}')
" 2>/dev/null || echo "   ⚠️  Query failed"
    
    echo ""
    
    # 2. Check recent clustering activity
    echo -e "${BLUE}2️⃣ Recent Clustering Activity (Gaza/Hostage):${NC}"
    ./query-logs.sh custom "traces | where timestamp > ago(10m) | where message contains 'israel' or message contains 'hostage' or message contains 'gaza' or message contains 'ceasefire' | where message contains 'Added' or message contains 'Story Cluster:' or message contains 'promoted' | project timestamp, message | order by timestamp desc | take 10" 2>&1 | \
        python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    rows = data['tables'][0]['rows']
    if rows:
        for row in rows[:10]:
            ts = row[0].split('.')[0].replace('T', ' ').replace('Z', '')
            msg = row[1][:120]
            print(f'   {ts}: {msg}')
    else:
        print('   No recent Gaza/hostage activity')
except:
    print('   ⚠️  Query failed')
" 2>/dev/null || echo "   ⚠️  Query failed"
    
    echo ""
    
    # 3. Check breaking news monitor
    echo -e "${BLUE}3️⃣ Breaking News Monitor Activity:${NC}"
    ./query-logs.sh custom "traces | where timestamp > ago(10m) | where message contains 'BreakingNewsMonitor' or message contains 'Status transition' or message contains 'BREAKING stories' | project timestamp, message | order by timestamp desc | take 5" 2>&1 | \
        python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    rows = data['tables'][0]['rows']
    if rows:
        for row in rows:
            ts = row[0].split('.')[0].replace('T', ' ').replace('Z', '')
            msg = row[1]
            if 'Status transition' in msg:
                print(f'   🔄 {ts}: {msg[:100]}')
            elif 'BREAKING stories' in msg:
                print(f'   📊 {ts}: {msg[:100]}')
            else:
                print(f'   ℹ️  {ts}: {msg[:80]}')
    else:
        print('   No recent monitor activity')
except:
    print('   ⚠️  Query failed')
" 2>/dev/null || echo "   ⚠️  Query failed"
    
    echo ""
}

# Main monitoring loop
echo -e "${GREEN}Starting live monitoring... (Press Ctrl+C to stop)${NC}"
echo ""

INTERVAL=30  # Check every 30 seconds

while true; do
    check_story_status
    
    echo ""
    echo -e "${YELLOW}Next check in ${INTERVAL} seconds...${NC}"
    echo ""
    
    sleep $INTERVAL
done

