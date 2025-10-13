#!/bin/bash
#
# Newsreel Automated System Health Analysis
# Comprehensive monitoring for summarization, clustering, updates, and sources
#
# Usage: ./analyze-system-health.sh [time-range]
# Output: Structured JSON with health scores and actionable recommendations
#

set -euo pipefail

# Configuration
TIME_RANGE="${1:-1h}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_INSIGHTS_ID=$(az resource show \
    --resource-group "newsreel-rg" \
    --name "newsreel-insights" \
    --resource-type "Microsoft.Insights/components" \
    --query "properties.AppId" -o tsv 2>/dev/null)

# Helper function to query logs
query_logs() {
    local query="$1"
    az monitor app-insights query \
        --app "$APP_INSIGHTS_ID" \
        --analytics-query "$query" \
        --output json 2>/dev/null || echo '{"tables":[{"rows":[]}]}'
}

echo "{"
echo "  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
echo "  \"time_range\": \"$TIME_RANGE\","
echo "  \"analysis\": {"

# ============================================================================
# 1. SUMMARIZATION QUALITY
# ============================================================================

echo "    \"summarization\": {"

SUMMARY_QUERY="
traces
| where timestamp > ago($TIME_RANGE)
| where message contains 'Summary Generated'
| extend jsonPart = split(message, ' | ')[1]
| extend data = parse_json(tostring(jsonPart))
| summarize 
    total_summaries = count(),
    avg_duration_ms = avg(toint(data.duration_ms)),
    avg_word_count = avg(toint(data.word_count)),
    avg_sources = avg(toint(data.source_count))
| project total_summaries, avg_duration_ms, avg_word_count, avg_sources
"

summary_result=$(query_logs "$SUMMARY_QUERY")
total_summaries=$(echo "$summary_result" | jq -r '.tables[0].rows[0][0] // 0' 2>/dev/null || echo "0")
avg_duration=$(echo "$summary_result" | jq -r '.tables[0].rows[0][1] // 0' 2>/dev/null || echo "0")
avg_words=$(echo "$summary_result" | jq -r '.tables[0].rows[0][2] // 0' 2>/dev/null || echo "0")
avg_sources=$(echo "$summary_result" | jq -r '.tables[0].rows[0][3] // 0' 2>/dev/null || echo "0")

echo "      \"total_generated\": $total_summaries,"
echo "      \"avg_duration_ms\": $(printf "%.0f" "$avg_duration"),"
echo "      \"avg_word_count\": $(printf "%.0f" "$avg_words"),"
echo "      \"avg_sources_per_summary\": $(printf "%.1f" "$avg_sources"),"

if [ "$total_summaries" -eq 0 ]; then
    echo "      \"status\": \"no_data\","
    echo "      \"recommendation\": \"No summaries generated. Check if summarization function is running.\""
elif (( $(echo "$avg_duration < 3000" | bc -l 2>/dev/null || echo "1") )); then
    echo "      \"status\": \"excellent\","
    echo "      \"recommendation\": \"Summary generation is fast (<3s). Quality looks good.\""
else
    echo "      \"status\": \"slow\","
    echo "      \"recommendation\": \"⚠️  Summaries taking >3s. Consider caching or prompt optimization.\""
fi

echo "    },"

# ============================================================================
# 2. STORY CLUSTERING QUALITY
# ============================================================================

echo "    \"clustering\": {"

CLUSTERING_QUERY="
traces
| where timestamp > ago($TIME_RANGE)
| where message contains 'Story Cluster'
| extend jsonPart = split(message, ' | ')[1]
| extend data = parse_json(tostring(jsonPart))
| summarize 
    stories_created = countif(data.action == 'created'),
    stories_updated = countif(data.action == 'updated'),
    avg_sources = avg(toint(data.source_count)),
    multi_source_stories = countif(toint(data.source_count) > 1)
| project stories_created, stories_updated, avg_sources, multi_source_stories
"

clustering_result=$(query_logs "$CLUSTERING_QUERY")
stories_created=$(echo "$clustering_result" | jq -r '.tables[0].rows[0][0] // 0' 2>/dev/null || echo "0")
stories_updated=$(echo "$clustering_result" | jq -r '.tables[0].rows[0][1] // 0' 2>/dev/null || echo "0")
avg_sources_per_story=$(echo "$clustering_result" | jq -r '.tables[0].rows[0][2] // 0' 2>/dev/null || echo "0")
multi_source_count=$(echo "$clustering_result" | jq -r '.tables[0].rows[0][3] // 0' 2>/dev/null || echo "0")

echo "      \"stories_created\": $stories_created,"
echo "      \"stories_updated\": $stories_updated,"
echo "      \"avg_sources_per_story\": $(printf "%.1f" "$avg_sources_per_story"),"
echo "      \"multi_source_stories\": $multi_source_count,"

if [ "$stories_created" -eq 0 ]; then
    echo "      \"status\": \"no_data\","
    echo "      \"recommendation\": \"No clustering activity. Check if RSS ingestion is working.\""
elif (( $(echo "$avg_sources_per_story > 2" | bc -l 2>/dev/null || echo "0") )); then
    echo "      \"status\": \"excellent\","
    echo "      \"recommendation\": \"Clustering is working well. Average >2 sources per story.\""
elif (( $(echo "$avg_sources_per_story > 1.5" | bc -l 2>/dev/null || echo "0") )); then
    echo "      \"status\": \"good\","
    echo "      \"recommendation\": \"Clustering is decent. Consider tuning fingerprint matching for better results.\""
else
    echo "      \"status\": \"poor\","
    echo "      \"recommendation\": \"⚠️  Most stories are single-source. Review clustering algorithm (fingerprint/fuzzy matching).\""
fi

echo "    },"

# ============================================================================
# 3. STORY UPDATE FREQUENCY
# ============================================================================

echo "    \"story_updates\": {"

UPDATE_QUERY="
traces
| where timestamp > ago($TIME_RANGE)
| where message contains 'Story Cluster' and message contains 'updated'
| extend jsonPart = split(message, ' | ')[1]
| extend data = parse_json(tostring(jsonPart))
| summarize 
    total_updates = count(),
    stories_with_multiple_updates = dcount(tostring(data.story_id))
| project total_updates, stories_with_multiple_updates
"

update_result=$(query_logs "$UPDATE_QUERY")
total_updates=$(echo "$update_result" | jq -r '.tables[0].rows[0][0] // 0' 2>/dev/null || echo "0")
unique_stories_updated=$(echo "$update_result" | jq -r '.tables[0].rows[0][1] // 0' 2>/dev/null || echo "0")

updates_per_hour=$(echo "$total_updates" | awk '{print $1}')

echo "      \"total_updates\": $total_updates,"
echo "      \"unique_stories_updated\": $unique_stories_updated,"
echo "      \"updates_per_hour\": $updates_per_hour,"

if [ "$total_updates" -eq 0 ]; then
    echo "      \"status\": \"stale\","
    echo "      \"recommendation\": \"No story updates. Stories aren't being enriched with new sources.\""
elif [ "$total_updates" -gt 20 ]; then
    echo "      \"status\": \"excellent\","
    echo "      \"recommendation\": \"Stories are being actively updated with new information. Great!\""
else
    echo "      \"status\": \"moderate\","
    echo "      \"recommendation\": \"Some updates happening. Consider improving clustering to catch more related articles.\""
fi

echo "    },"

# ============================================================================
# 4. SOURCE HEALTH & DIVERSITY
# ============================================================================

echo "    \"sources\": {"

SOURCE_QUERY="
traces
| where timestamp > ago($TIME_RANGE)
| where message contains 'RSS Fetch'
| extend jsonPart = split(message, ' | ')[1]
| extend data = parse_json(tostring(jsonPart))
| summarize 
    total_fetches = count(),
    successful = countif(data.success == true),
    total_articles = sum(toint(data.article_count)),
    unique_sources = dcount(tostring(data.source))
| project total_fetches, successful, total_articles, unique_sources
"

source_result=$(query_logs "$SOURCE_QUERY")
total_fetches=$(echo "$source_result" | jq -r '.tables[0].rows[0][0] // 0' 2>/dev/null || echo "0")
successful_fetches=$(echo "$source_result" | jq -r '.tables[0].rows[0][1] // 0' 2>/dev/null || echo "0")
total_articles=$(echo "$source_result" | jq -r '.tables[0].rows[0][2] // 0' 2>/dev/null || echo "0")
unique_sources=$(echo "$source_result" | jq -r '.tables[0].rows[0][3] // 0' 2>/dev/null || echo "0")

if [ "$total_fetches" -gt 0 ]; then
    success_rate=$(echo "scale=2; ($successful_fetches * 100) / $total_fetches" | bc 2>/dev/null || echo "0")
else
    success_rate="0"
fi

echo "      \"unique_sources_active\": $unique_sources,"
echo "      \"total_fetch_attempts\": $total_fetches,"
echo "      \"successful_fetches\": $successful_fetches,"
echo "      \"success_rate_percent\": $(printf "%.1f" "$success_rate"),"
echo "      \"total_articles_fetched\": $total_articles,"

if [ "$unique_sources" -eq 0 ]; then
    echo "      \"status\": \"offline\","
    echo "      \"recommendation\": \"🚨 CRITICAL: No sources are active. Check RSS ingestion function.\""
elif [ "$unique_sources" -lt 10 ]; then
    echo "      \"status\": \"poor\","
    echo "      \"recommendation\": \"⚠️  Only $unique_sources sources active. Review feed configuration and add more sources.\""
elif [ "$unique_sources" -lt 50 ]; then
    echo "      \"status\": \"moderate\","
    echo "      \"recommendation\": \"$unique_sources sources active (moderate). Consider adding more for better diversity.\""
else
    echo "      \"status\": \"excellent\","
    echo "      \"recommendation\": \"$unique_sources sources active. Great diversity!\""
fi

echo "    },"

# ============================================================================
# 5. FEED DIVERSITY (NEW ARTICLES DISTRIBUTION)
# ============================================================================

echo "    \"feed_diversity\": {"

DIVERSITY_QUERY="
traces
| where timestamp > ago($TIME_RANGE)
| where message contains 'Feed Diversity'
| extend jsonPart = split(message, ' | ')[1]
| extend data = parse_json(tostring(jsonPart))
| where toint(data.total_stories) > 0
| summarize 
    avg_unique_sources = avg(toint(data.unique_sources)),
    avg_total_stories = avg(toint(data.total_stories))
| project avg_unique_sources, avg_total_stories
"

diversity_result=$(query_logs "$DIVERSITY_QUERY")
avg_unique=$(echo "$diversity_result" | jq -r '.tables[0].rows[0][0] // 0' 2>/dev/null || echo "0")
avg_total=$(echo "$diversity_result" | jq -r '.tables[0].rows[0][1] // 0' 2>/dev/null || echo "0")

if (( $(echo "$avg_total > 0" | bc -l 2>/dev/null || echo "0") )); then
    diversity_score=$(echo "scale=2; $avg_unique / $avg_total" | bc 2>/dev/null || echo "0")
else
    diversity_score="0"
fi

echo "      \"avg_sources_per_batch\": $(printf "%.1f" "$avg_unique"),"
echo "      \"avg_stories_per_batch\": $(printf "%.1f" "$avg_total"),"
echo "      \"diversity_score\": $(printf "%.2f" "$diversity_score"),"

if (( $(echo "$diversity_score > 0.6" | bc -l 2>/dev/null || echo "0") )); then
    echo "      \"status\": \"excellent\","
    echo "      \"recommendation\": \"Feed diversity is excellent (>60%). Stories from many sources.\""
elif (( $(echo "$diversity_score > 0.4" | bc -l 2>/dev/null || echo "0") )); then
    echo "      \"status\": \"good\","
    echo "      \"recommendation\": \"Feed diversity is good. Consider staggering RSS polls for even better distribution.\""
elif (( $(echo "$diversity_score > 0" | bc -l 2>/dev/null || echo "0") )); then
    echo "      \"status\": \"poor\","
    echo "      \"recommendation\": \"⚠️  Feed dominated by few sources (<40% diversity). Implement staggered polling.\""
else
    echo "      \"status\": \"no_data\","
    echo "      \"recommendation\": \"No diversity data. Check if staggered polling is working.\""
fi

echo "    },"

# ============================================================================
# 6. STAGGERED POLLING VERIFICATION
# ============================================================================

echo "    \"staggered_polling\": {"

POLLING_QUERY="
traces
| where timestamp > ago(10m)
| where message contains 'staggered polling'
| summarize 
    poll_cycles = count(),
    last_poll = max(timestamp)
| project poll_cycles, last_poll
"

polling_result=$(query_logs "$POLLING_QUERY")
poll_cycles=$(echo "$polling_result" | jq -r '.tables[0].rows[0][0] // 0' 2>/dev/null || echo "0")
last_poll=$(echo "$polling_result" | jq -r '.tables[0].rows[0][1] // "never"' 2>/dev/null || echo "never")

echo "      \"poll_cycles_last_10min\": $poll_cycles,"
echo "      \"last_poll_time\": \"$last_poll\","

if [ "$poll_cycles" -eq 0 ]; then
    echo "      \"status\": \"offline\","
    echo "      \"recommendation\": \"🚨 Staggered polling not detected. Check if RSS function is running.\""
elif [ "$poll_cycles" -lt 30 ]; then
    echo "      \"status\": \"slow\","
    echo "      \"recommendation\": \"⚠️  Only $poll_cycles cycles in 10 min (expected ~60 for 10-sec polling). Check function schedule.\""
else
    echo "      \"status\": \"active\","
    echo "      \"recommendation\": \"Staggered polling is active and healthy ($poll_cycles cycles in 10 min).\""
fi

echo "    }"

# ============================================================================
# OVERALL HEALTH & RECOMMENDATIONS
# ============================================================================

echo "  },"
echo "  \"next_actions\": ["

# Generate prioritized recommendations
actions_added=0

# Priority 1: Critical issues
if [ "$unique_sources" -eq 0 ]; then
    if [ $actions_added -gt 0 ]; then echo "    ,"; fi
    echo "    {\"priority\": 1, \"area\": \"sources\", \"action\": \"Fix RSS ingestion - no sources active\", \"command\": \"./query-logs.sh errors 1h\"}"
    actions_added=$((actions_added + 1))
fi

# Priority 2: Summarization quality
if [ "$total_summaries" -eq 0 ] && [ "$stories_created" -gt 0 ]; then
    if [ $actions_added -gt 0 ]; then echo "    ,"; fi
    echo "    {\"priority\": 2, \"area\": \"summarization\", \"action\": \"Summaries not being generated. Check summarization function and Anthropic API key.\", \"doc\": \"docs/Azure_Setup_Guide.md\"}"
    actions_added=$((actions_added + 1))
fi

# Priority 3: Clustering improvement
if (( $(echo "$avg_sources_per_story < 1.5" | bc -l 2>/dev/null || echo "0") )) && [ "$stories_created" -gt 5 ]; then
    if [ $actions_added -gt 0 ]; then echo "    ,"; fi
    echo "    {\"priority\": 3, \"area\": \"clustering\", \"action\": \"Improve clustering algorithm. Avg sources/story is only $avg_sources_per_story.\", \"file\": \"Azure/functions/shared/utils.py\", \"function\": \"generate_story_fingerprint\"}"
    actions_added=$((actions_added + 1))
fi

# Priority 4: Add more sources
if [ "$unique_sources" -lt 50 ] && [ "$unique_sources" -gt 0 ]; then
    if [ $actions_added -gt 0 ]; then echo "    ,"; fi
    echo "    {\"priority\": 4, \"area\": \"sources\", \"action\": \"Add more RSS sources. Currently only $unique_sources active.\", \"file\": \"Azure/functions/shared/rss_feeds.py\"}"
    actions_added=$((actions_added + 1))
fi

# Priority 5: Story updates
if [ "$total_updates" -lt 10 ] && [ "$stories_created" -gt 10 ]; then
    if [ $actions_added -gt 0 ]; then echo "    ,"; fi
    echo "    {\"priority\": 5, \"area\": \"updates\", \"action\": \"Stories not being updated with new info. Only $total_updates updates detected.\", \"recommendation\": \"Review clustering thresholds to catch more related articles.\"}"
    actions_added=$((actions_added + 1))
fi

# Default: All good
if [ $actions_added -eq 0 ]; then
    echo "    {\"priority\": 0, \"action\": \"System healthy. All metrics look good.\", \"next_check\": \"1h\"}"
fi

echo "  ],"
echo "  \"monitoring_commands\": {"
echo "    \"view_summaries\": \"./query-logs.sh performance 1h | jq\","
echo "    \"view_clustering\": \"az monitor app-insights query --app '$APP_INSIGHTS_ID' --analytics-query 'traces | where timestamp > ago(1h) | where message contains \\\"Story Cluster\\\"'\","
echo "    \"view_sources\": \"./query-logs.sh source-diversity 1h | jq\","
echo "    \"view_errors\": \"./query-logs.sh errors 1h | jq\""
echo "  }"
echo "}"
