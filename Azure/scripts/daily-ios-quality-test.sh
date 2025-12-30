#!/bin/bash

# Daily iOS Client Data Quality Test Runner
# This script runs the comprehensive iOS data quality test daily
# and logs results for monitoring system health

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🧪 DAILY iOS CLIENT DATA QUALITY TEST"
echo "====================================="
echo "Timestamp: $(date)"
echo "Project: $PROJECT_ROOT"
echo ""

cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Python virtual environment activated"
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✅ Python virtual environment activated"
else
    echo "⚠️  No virtual environment found, using system Python"
fi

# Check if we're in the tests directory
if [ ! -d "tests" ]; then
    echo "❌ Tests directory not found!"
    exit 1
fi

cd tests

# Run the iOS quality test
echo ""
echo "🚀 Running iOS Client Data Quality Test..."
echo ""

# Set PYTHONPATH to include the functions directory
export PYTHONPATH="$PROJECT_ROOT/functions:$PYTHONPATH"

# Run the test with detailed output
pytest ai/test_ios_client_data_quality.py::test_ios_client_data_quality \
    -v \
    --tb=short \
    --log-cli-level=INFO \
    --junitxml=daily_ios_quality_test_$(date +%Y%m%d).xml \
    2>&1 | tee daily_ios_quality_test_$(date +%Y%m%d).log

TEST_EXIT_CODE=$?

echo ""
echo "📊 TEST RESULTS SUMMARY"
echo "======================="

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ TEST PASSED - iOS data quality is good!"
    echo "📈 System is healthy and providing quality data to iOS clients"

    # Extract key metrics from the log
    if [ -f "daily_ios_quality_test_$(date +%Y%m%d).log" ]; then
        echo ""
        echo "📋 KEY METRICS:"
        grep -E "(Overall Score|Structural validation|Source diversity|Clustering quality|Summaries)" "daily_ios_quality_test_$(date +%Y%m%d).log" | head -10
    fi

else
    echo "❌ TEST FAILED - iOS data quality issues detected!"
    echo "🔥 System needs attention - check the detailed log above"
    echo ""
    echo "🚨 ALERT: iOS users may be experiencing poor data quality"
    echo "   - Check summarization pipeline"
    echo "   - Review source diversity"
    echo "   - Validate data structure integrity"
fi

echo ""
echo "📁 Logs saved to:"
echo "   - daily_ios_quality_test_$(date +%Y%m%d).log"
echo "   - daily_ios_quality_test_$(date +%Y%m%d).xml (JUnit format)"

echo ""
echo "🎯 Next scheduled run: Tomorrow at $(date -v+1d +%Y-%m-%d) 09:00 UTC"
echo ""

exit $TEST_EXIT_CODE




