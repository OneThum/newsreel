#!/bin/bash

# Quick Story Status Check
# Gets current status of specific story

STORY_ID="${1:-story_20251012_084423_58f041ad44cd}"

echo "🔍 Checking Story: $STORY_ID"
echo "================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check latest status from logs
echo "Latest activity (last 10 minutes):"
./query-logs.sh custom "traces | where timestamp > ago(10m) | where message contains '$STORY_ID' | project timestamp, message | order by timestamp desc | take 10" 2>&1 | \
python3 << 'PYTHON_SCRIPT'
import sys, json, re
from datetime import datetime

try:
    data = json.load(sys.stdin)
    rows = data['tables'][0]['rows']
    
    if not rows:
        print("  ⚠️  No recent activity found for this story")
        sys.exit(0)
    
    latest_status = None
    latest_sources = None
    latest_action = None
    
    for row in rows:
        ts = row[0]
        msg = row[1]
        
        # Parse timestamp
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        time_ago = (datetime.utcnow().replace(tzinfo=dt.tzinfo) - dt).total_seconds() / 60
        
        # Extract status
        status_match = re.search(r'\[([A-Z]+)\]', msg)
        if status_match and not latest_status:
            latest_status = status_match.group(1)
        
        # Extract source count
        sources_match = re.search(r'"source_count":\s*(\d+)', msg)
        if sources_match and not latest_sources:
            latest_sources = sources_match.group(1)
        
        # Extract action
        if 'Story Cluster:' in msg:
            action_match = re.search(r'Story Cluster: (\w+)', msg)
            if action_match and not latest_action:
                latest_action = action_match.group(1)
        
        # Print activity
        time_str = f"{int(time_ago)}m ago" if time_ago < 60 else f"{int(time_ago/60)}h ago"
        
        if 'promoted to BREAKING' in msg:
            print(f"  🔥 {time_str}: PROMOTED TO BREAKING")
        elif 'Status transition' in msg:
            print(f"  🔄 {time_str}: Status transition")
        elif 'Added' in msg:
            source_match = re.search(r'Added (\w+) to story.*\(now (\d+)', msg)
            if source_match:
                print(f"  📰 {time_str}: Added {source_match.group(1)} → {source_match.group(2)} sources")
        elif 'Story Cluster:' in msg:
            if latest_status:
                print(f"  📊 {time_str}: {latest_action} - [{latest_status}] - {latest_sources} sources")
    
    print("\n" + "="*50)
    print(f"Current Status: {latest_status if latest_status else 'Unknown'}")
    print(f"Source Count: {latest_sources if latest_sources else 'Unknown'}")
    print(f"Last Activity: {int(time_ago)}m ago")
    
    # Recommendations
    print("\n" + "="*50)
    if latest_status == 'VERIFIED' and latest_sources and int(latest_sources) >= 3:
        print("⚠️  ISSUE: Story has 3+ sources but status is VERIFIED")
        print("   Expected: BREAKING (if updated recently)")
        print("   Action: Check if 'actively developing' logic triggered")
    elif latest_status == 'BREAKING':
        print("✅ SUCCESS: Story is marked as BREAKING")
    else:
        print(f"ℹ️  Status: {latest_status}, Sources: {latest_sources}")

except json.JSONDecodeError:
    print("  ⚠️  No data received from query")
except Exception as e:
    print(f"  ❌ Error: {e}")
    import traceback
    traceback.print_exc()
PYTHON_SCRIPT

