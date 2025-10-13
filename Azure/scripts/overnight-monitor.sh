#!/bin/bash
#
# Overnight Monitoring Script
# Runs continuously and checks Azure logs every 5 minutes
# Logs findings to overnight_monitoring_log.txt
#

LOG_FILE="overnight_monitoring_log.txt"
CHECK_INTERVAL=300  # 5 minutes

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "🌙 OVERNIGHT MONITORING STARTED"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "Start time: $(date)"
echo "Log file: $LOG_FILE"
echo "Check interval: ${CHECK_INTERVAL}s (5 minutes)"
echo ""
echo "Press Ctrl+C to stop"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# Initialize log file
echo "=== Overnight Monitoring Started: $(date) ===" > "$LOG_FILE"
echo "" >> "$LOG_FILE"

check_count=0

# Function to perform one check cycle
run_check() {
    check_count=$((check_count + 1))
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔍 CHECK #$check_count - $timestamp"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Log to file
    echo "" >> "$LOG_FILE"
    echo "=== Check #$check_count - $timestamp ===" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    
    # Check 1: Look for duplicate source warnings
    echo "📊 Checking for duplicate source warnings (last 10 minutes)..."
    duplicate_count=$(az monitor app-insights query \
        --app newsreel-insights \
        --resource-group newsreel-rg \
        --analytics-query "traces | where timestamp > ago(10m) | where message contains 'DUPLICATE SOURCES' | count" \
        --output tsv 2>/dev/null | tail -1)
    
    if [ -n "$duplicate_count" ] && [ "$duplicate_count" -gt 0 ]; then
        echo "⚠️  Found $duplicate_count duplicate source warnings!"
        echo "⚠️  DUPLICATE WARNINGS: $duplicate_count" >> "$LOG_FILE"
        
        # Get details
        echo "" >> "$LOG_FILE"
        echo "Recent duplicate warnings:" >> "$LOG_FILE"
        az monitor app-insights query \
            --app newsreel-insights \
            --resource-group newsreel-rg \
            --analytics-query "traces | where timestamp > ago(10m) | where message contains 'DUPLICATE SOURCES' | project timestamp, message | take 5" \
            --output table >> "$LOG_FILE" 2>&1
    else
        echo "✅ No duplicate warnings (good!)"
        echo "✅ No duplicate warnings" >> "$LOG_FILE"
    fi
    
    echo "" >> "$LOG_FILE"
    
    # Check 2: Story clustering activity
    echo "📰 Checking story clustering activity (last 10 minutes)..."
    activity=$(az monitor app-insights query \
        --app newsreel-insights \
        --resource-group newsreel-rg \
        --analytics-query "traces | where timestamp > ago(10m) | where message contains 'Added' and message contains 'article to story' | count" \
        --output tsv 2>/dev/null | tail -1)
    
    if [ -n "$activity" ] && [ "$activity" -gt 0" ]; then
        echo "📊 $activity articles added to stories"
        echo "📊 Articles added: $activity" >> "$LOG_FILE"
        
        # Get sample
        echo "" >> "$LOG_FILE"
        echo "Sample activity:" >> "$LOG_FILE"
        az monitor app-insights query \
            --app newsreel-insights \
            --resource-group newsreel-rg \
            --analytics-query "traces | where timestamp > ago(10m) | where message contains 'unique sources' | project timestamp, message | take 3" \
            --output table >> "$LOG_FILE" 2>&1
    else
        echo "ℹ️  No clustering activity in last 10 minutes"
        echo "ℹ️  No clustering activity" >> "$LOG_FILE"
    fi
    
    echo "" >> "$LOG_FILE"
    
    # Check 3: Function app health
    echo "🏥 Checking Azure Functions health..."
    function_state=$(az functionapp show \
        --name newsreel-func-51689 \
        --resource-group newsreel-rg \
        --query "state" \
        --output tsv 2>/dev/null)
    
    if [ "$function_state" == "Running" ]; then
        echo "✅ Azure Functions: Running"
        echo "✅ Functions: Running" >> "$LOG_FILE"
    else
        echo "⚠️  Azure Functions: $function_state"
        echo "⚠️  Functions: $function_state" >> "$LOG_FILE"
    fi
    
    echo "" >> "$LOG_FILE"
    
    # Summary
    echo ""
    echo "Check complete. Next check in 5 minutes..."
    echo "Log saved to: $LOG_FILE"
}

# Trap Ctrl+C to exit gracefully
trap 'echo ""; echo "═══════════════════════════════════════════════════════════════════════════════"; echo "🌙 MONITORING STOPPED"; echo "═══════════════════════════════════════════════════════════════════════════════"; echo ""; echo "Total checks performed: $check_count"; echo "Log file: $LOG_FILE"; echo ""; exit 0' INT

# Main monitoring loop
while true; do
    run_check
    sleep $CHECK_INTERVAL
done

