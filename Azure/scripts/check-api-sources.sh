#!/bin/bash
#
# Quick script to check API response for duplicate sources
#

API_URL="https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/api/stories/feed?limit=20"

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "🔍 CHECKING API FOR DUPLICATE SOURCES"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# Fetch stories
echo "📡 Fetching stories from API..."
response=$(curl -s "$API_URL")

if [ $? -ne 0 ]; then
    echo "❌ Failed to fetch from API"
    exit 1
fi

# Get first story with multiple sources
story_id=$(echo "$response" | jq -r '.[0].id')
story_title=$(echo "$response" | jq -r '.[0].title')
source_count=$(echo "$response" | jq -r '.[0].source_count')
sources_array_length=$(echo "$response" | jq -r '.[0].sources | length')

echo "✅ Got response"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📰 FIRST STORY IN FEED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Title: $story_title"
echo "ID: $story_id"
echo "source_count field: $source_count"
echo "sources array length: $sources_array_length"
echo ""

if [ "$sources_array_length" = "0" ] || [ "$sources_array_length" = "null" ]; then
    echo "❌ PROBLEM: API returned EMPTY sources array!"
    echo "   The source_count says $source_count but sources array is empty"
    echo ""
    echo "   This means the API is NOT including sources in the response."
    echo "   iOS app will have nothing to display in Multiple Perspectives section."
    echo ""
    exit 1
elif [ "$source_count" != "$sources_array_length" ]; then
    echo "⚠️  WARNING: Mismatch between source_count and sources array length"
    echo "   source_count: $source_count"
    echo "   sources length: $sources_array_length"
    echo ""
fi

# Get all source names
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 SOURCE ANALYSIS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Extract source names
source_names=$(echo "$response" | jq -r '.[0].sources[].source')
unique_count=$(echo "$source_names" | sort -u | wc -l | tr -d ' ')
total_count=$(echo "$source_names" | wc -l | tr -d ' ')

echo "Unique sources: $unique_count"
echo "Total sources: $total_count"
echo ""

if [ "$unique_count" != "$total_count" ]; then
    echo "❌ DUPLICATES DETECTED!"
    echo ""
    echo "Breakdown:"
    echo "$source_names" | sort | uniq -c | sort -rn | while read count name; do
        if [ "$count" -gt 1 ]; then
            echo "  🔴 $name: appears $count times"
        else
            echo "  🟢 $name: appears once"
        fi
    done
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔬 DETAILED INVESTIGATION"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Find a source that appears multiple times
    duplicate_source=$(echo "$source_names" | sort | uniq -c | sort -rn | head -1 | awk '{print $2}')
    
    echo "Examining: $duplicate_source"
    echo ""
    echo "$response" | jq -r --arg source "$duplicate_source" '
        .[0].sources[] | 
        select(.source == $source) | 
        "  ID: \(.id)\n  Title: \(.title)\n  URL: \(.article_url)\n"
    '
    
else
    echo "✅ ALL SOURCES UNIQUE - No duplicates!"
    echo ""
    echo "Sources:"
    echo "$source_names" | sort | sed 's/^/  • /'
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$sources_array_length" = "0" ]; then
    echo "❌ CRITICAL: API not returning sources array"
    echo "   Problem: Backend API bug"
    echo "   Fix needed: Check stories.py map_story_to_response()"
elif [ "$unique_count" != "$total_count" ]; then
    echo "❌ PROBLEM: API returning duplicate sources"
    echo "   Problem: Backend deduplication not working"
    echo "   Fix needed: Check API deduplication logic in stories.py"
else
    echo "✅ API WORKING CORRECTLY"
    echo "   All sources unique, no duplicates"
fi

echo ""

