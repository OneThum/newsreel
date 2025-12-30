#!/bin/bash

# Setup Automated Daily iOS Quality Tests
# This script configures cron jobs to run the iOS data quality test daily

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔧 SETTING UP AUTOMATED DAILY iOS QUALITY TESTS"
echo "================================================"
echo ""

# Check if cron is available
if ! command -v crontab &> /dev/null; then
    echo "❌ Cron is not available on this system"
    echo "   This script requires a Unix-like system with cron"
    echo ""
    echo "💡 Alternative: Set up the test to run via:"
    echo "   - Azure DevOps Pipeline"
    echo "   - GitHub Actions"
    echo "   - Azure Functions Timer Trigger"
    echo "   - AWS Lambda scheduled event"
    exit 1
fi

echo "✅ Cron is available"

# Check if the test script exists and is executable
TEST_SCRIPT="$SCRIPT_DIR/daily-ios-quality-test.sh"
if [ ! -x "$TEST_SCRIPT" ]; then
    echo "❌ Test script not found or not executable: $TEST_SCRIPT"
    exit 1
fi

echo "✅ Test script is available: $TEST_SCRIPT"

# Create a cron job entry
# Run at 9:00 AM UTC daily
CRON_JOB="0 9 * * * $TEST_SCRIPT"

echo ""
echo "📅 CREATING CRON JOB"
echo "===================="
echo "Schedule: Daily at 9:00 AM UTC"
echo "Command: $CRON_JOB"
echo ""

# Check if the cron job already exists
EXISTING_CRON=$(crontab -l 2>/dev/null | grep -F "$TEST_SCRIPT" || true)
if [ -n "$EXISTING_CRON" ]; then
    echo "⚠️  Cron job already exists:"
    echo "   $EXISTING_CRON"
    echo ""
    read -p "Update existing cron job? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "ℹ️  Keeping existing cron job"
        exit 0
    fi
fi

# Add or update the cron job
if crontab -l 2>/dev/null | grep -F "$TEST_SCRIPT" > /dev/null; then
    # Update existing
    crontab -l | sed "/$TEST_SCRIPT/d" | { cat; echo "$CRON_JOB"; } | crontab -
    echo "✅ Updated existing cron job"
else
    # Add new
    crontab -l 2>/dev/null | { cat; echo "$CRON_JOB"; } | crontab -
    echo "✅ Added new cron job"
fi

echo ""
echo "🎉 AUTOMATION SETUP COMPLETE!"
echo "=============================="
echo ""
echo "📊 Daily iOS Quality Test will run:"
echo "   - Every day at 9:00 AM UTC"
echo "   - Results logged to: $PROJECT_ROOT/tests/daily_ios_quality_test_YYYYMMDD.log"
echo "   - JUnit XML: $PROJECT_ROOT/tests/daily_ios_quality_test_YYYYMMDD.xml"
echo ""
echo "🔍 To check cron status:"
echo "   crontab -l"
echo ""
echo "🛑 To remove the cron job:"
echo "   crontab -l | grep -v daily-ios-quality-test.sh | crontab -"
echo ""

# Test the cron job setup by running it once
echo "🧪 TESTING THE SETUP (running test now)..."
echo ""

"$TEST_SCRIPT"

echo ""
echo "✅ Setup verification complete!"
echo "📈 Your iOS data quality is now monitored daily!"




