#!/bin/bash
#
# Newsreel Log Query Script
# Query Application Insights logs via Azure CLI for automated analysis
#
# Usage: ./query-logs.sh [query-type] [time-range]
# Examples:
#   ./query-logs.sh source-diversity 1h
#   ./query-logs.sh categorization 24h
#   ./query-logs.sh performance 30m
#

set -euo pipefail

# Configuration
RESOURCE_GROUP="newsreel-rg"
APP_INSIGHTS_NAME="newsreel-insights"

APP_INSIGHTS_ID=$(az resource show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_INSIGHTS_NAME" \
    --resource-type "Microsoft.Insights/components" \
    --query "properties.AppId" -o tsv)

if [ -z "$APP_INSIGHTS_ID" ]; then
    echo "Error: Could not find Application Insights '$APP_INSIGHTS_NAME' in resource group $RESOURCE_GROUP"
    exit 1
fi

# Default time range: 1 hour
TIME_RANGE="${2:-1h}"

# Query function
query_logs() {
    local query="$1"
    az monitor app-insights query \
        --app "$APP_INSIGHTS_ID" \
        --analytics-query "$query" \
        --output json
}

# ============================================================================
# QUERY TEMPLATES
# ============================================================================

case "${1:-help}" in
    source-diversity)
        echo "📊 Querying Source Diversity Metrics (last $TIME_RANGE)..."
        query_logs "
traces
| where timestamp > ago($TIME_RANGE)
| where message contains 'Feed Diversity'
| extend jsonPart = split(message, ' | ')[1]
| extend diversityData = parse_json(tostring(jsonPart))
| project 
    timestamp,
    unique_sources = diversityData.unique_sources,
    total_stories = diversityData.total_stories,
    source_dist = diversityData.source_distribution
| order by timestamp desc
| take 20
"
        ;;
    
    categorization)
        echo "🏷️  Querying Categorization Accuracy (last $TIME_RANGE)..."
        query_logs "
traces
| where timestamp > ago($TIME_RANGE)
| where message contains 'Categorized'
| extend catData = parse_json(customDimensions)
| summarize 
    count(),
    avg(todouble(catData.score)) as avg_confidence
    by category = tostring(catData.category)
| order by count_ desc
"
        ;;
    
    rss-fetch)
        echo "📡 Querying RSS Fetch Performance (last $TIME_RANGE)..."
        query_logs "
traces
| where timestamp > ago($TIME_RANGE)
| where customDimensions.event_type == 'rss_fetch'
| extend rssData = parse_json(customDimensions)
| project 
    timestamp,
    source = rssData.source,
    article_count = toint(rssData.article_count),
    duration_ms = toint(rssData.duration_ms),
    success = rssData.success
| summarize 
    total_articles = sum(article_count),
    avg_duration = avg(duration_ms),
    success_rate = countif(success == true) * 100.0 / count()
    by source
| order by total_articles desc
"
        ;;
    
    clustering)
        echo "🔗 Querying Story Clustering Stats (last $TIME_RANGE)..."
        query_logs "
traces
| where timestamp > ago($TIME_RANGE)
| where customDimensions.event_type == 'story_cluster'
| extend clusterData = parse_json(customDimensions)
| summarize 
    created = countif(clusterData.action == 'created'),
    updated = countif(clusterData.action == 'updated'),
    avg_sources = avg(toint(clusterData.source_count))
    by category = tostring(clusterData.category)
| project category, created, updated, avg_sources
| order by created desc
"
        ;;
    
    performance)
        echo "⚡ Querying Performance Metrics (last $TIME_RANGE)..."
        query_logs "
traces
| where timestamp > ago($TIME_RANGE)
| where customDimensions.operation_name != ''
| extend perfData = parse_json(customDimensions)
| where perfData.status == 'success'
| summarize 
    count = count(),
    avg_duration = avg(toint(perfData.duration_ms)),
    p50_duration = percentile(toint(perfData.duration_ms), 50),
    p95_duration = percentile(toint(perfData.duration_ms), 95),
    p99_duration = percentile(toint(perfData.duration_ms), 99)
    by operation = tostring(perfData.operation_name)
| order by avg_duration desc
"
        ;;
    
    summary-generation)
        echo "✨ Querying AI Summary Generation (last $TIME_RANGE)..."
        query_logs "
traces
| where timestamp > ago($TIME_RANGE)
| where customDimensions.event_type == 'summary_generated'
| extend summaryData = parse_json(customDimensions)
| summarize 
    count = count(),
    avg_duration = avg(toint(summaryData.duration_ms)),
    avg_word_count = avg(toint(summaryData.word_count)),
    avg_sources = avg(toint(summaryData.source_count))
    by model = tostring(summaryData.model)
| project model, count, avg_duration_sec = avg_duration / 1000, avg_word_count, avg_sources
"
        ;;
    
    errors)
        echo "❌ Querying Recent Errors (last $TIME_RANGE)..."
        query_logs "
union traces, exceptions
| where timestamp > ago($TIME_RANGE)
| where severityLevel >= 3
| project 
    timestamp,
    message,
    type = itemType,
    details = tostring(customDimensions)
| order by timestamp desc
| take 50
"
        ;;
    
    feed-quality)
        echo "📰 Querying Feed Quality Metrics (last $TIME_RANGE)..."
        query_logs "
traces
| where timestamp > ago($TIME_RANGE)
| where message contains 'Feed Diversity'
| extend diversityData = parse_json(customDimensions)
| extend diversity_score = todouble(diversityData.unique_sources) / todouble(diversityData.total_stories)
| summarize 
    avg_diversity = avg(diversity_score),
    avg_unique_sources = avg(toint(diversityData.unique_sources)),
    avg_total_stories = avg(toint(diversityData.total_stories))
| extend 
    quality_rating = case(
        avg_diversity > 0.6, 'Excellent',
        avg_diversity > 0.4, 'Good',
        avg_diversity > 0.2, 'Fair',
        'Poor'
    )
| project avg_diversity, avg_unique_sources, avg_total_stories, quality_rating
"
        ;;
    
    custom)
        echo "🔍 Custom Query..."
        if [ -z "${2:-}" ]; then
            echo "Error: Please provide a custom query as second argument"
            exit 1
        fi
        query_logs "$2"
        ;;
    
    help|*)
        cat <<EOF
Newsreel Log Query Tool
========================

Usage: ./query-logs.sh [query-type] [time-range]

Query Types:
  source-diversity      - Track unique sources in feed (target: >10)
  categorization        - Categorization accuracy and confidence
  rss-fetch             - RSS feed fetch performance
  clustering            - Story clustering statistics
  performance           - Operation performance metrics
  summary-generation    - AI summary generation stats
  errors                - Recent errors and exceptions
  feed-quality          - Overall feed quality score
  custom "QUERY"        - Run custom KQL query

Time Ranges:
  30m    - Last 30 minutes
  1h     - Last hour (default)
  6h     - Last 6 hours
  24h    - Last 24 hours
  7d     - Last 7 days

Examples:
  ./query-logs.sh source-diversity 1h
  ./query-logs.sh categorization 24h
  ./query-logs.sh errors 30m
  ./query-logs.sh custom "traces | where message contains 'BBC' | take 10"

Output: JSON format (pipe to jq for formatting)
  ./query-logs.sh source-diversity | jq '.tables[0].rows'

EOF
        exit 0
        ;;
esac

echo "✅ Query complete"

