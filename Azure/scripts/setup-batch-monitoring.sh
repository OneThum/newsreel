#!/bin/bash
# Setup Monitoring and Alerts for Batch Processing
# This script configures Application Insights queries and alert rules

set -e

echo "🔍 Setting up Batch Processing Monitoring"
echo "=========================================="

# Configuration
RESOURCE_GROUP="Newsreel-RG"
FUNCTION_APP="newsreel-func-51689"

# Get Application Insights resource
echo "Finding Application Insights resource..."
APP_INSIGHTS=$(az monitor app-insights component list \
  --resource-group "$RESOURCE_GROUP" \
  --query '[0].{name:name, id:id}' \
  -o json)

INSIGHTS_NAME=$(echo "$APP_INSIGHTS" | jq -r '.name')
INSIGHTS_ID=$(echo "$APP_INSIGHTS" | jq -r '.id')

echo "✅ Found Application Insights: $INSIGHTS_NAME"

# Get Function App resource ID
FUNCTION_APP_ID=$(az functionapp show \
  --name "$FUNCTION_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --query 'id' -o tsv)

echo ""
echo "📊 Creating Custom Application Insights Queries"
echo "-----------------------------------------------"

# Note: Azure CLI doesn't support creating saved queries directly
# These queries can be saved manually in the Application Insights portal

cat << 'EOF' > /tmp/batch_monitoring_queries.txt
=== Application Insights Queries for Batch Processing ===

1. BATCH SUBMISSION RATE (last 24 hours)
traces
| where timestamp > ago(24h)
| where message contains "Batch submitted"
| summarize BatchesSubmitted=count() by bin(timestamp, 1h)
| render timechart 

2. BATCH SUCCESS RATE (last 7 days)
traces
| where timestamp > ago(7d)
| where message contains "Completed batch"
| parse message with * "succeeded, " ErrorCount:int " errored"
| parse message with * ": " SuccessCount:int " succeeded"
| extend TotalRequests = SuccessCount + ErrorCount
| extend SuccessRate = todouble(SuccessCount) / todouble(TotalRequests) * 100
| summarize AvgSuccessRate=avg(SuccessRate) by bin(timestamp, 6h)
| render timechart 

3. STORIES IN QUEUE TREND
traces
| where timestamp > ago(24h)
| where message contains "stories needing summaries"
| parse message with * "Found " StoryCount:int " stories"
| summarize StoriesInQueue=max(StoryCount) by bin(timestamp, 30m)
| render timechart 

4. BATCH PROCESSING ERRORS
traces
| where timestamp > ago(24h)
| where (message contains "Error" or message contains "Failed") 
  and (message contains "batch" or message contains "Batch")
| project timestamp, severityLevel, message
| order by timestamp desc

5. BATCH COST TRACKING
traces
| where timestamp > ago(7d)
| where message contains "Batch summary for"
| parse message with * "$" Cost:double
| summarize TotalCost=sum(Cost), AvgCost=avg(Cost) by bin(timestamp, 1d)
| render barchart 

6. BATCH SIZE DISTRIBUTION
traces  
| where timestamp > ago(7d)
| where message contains "Submitting batch with"
| parse message with * "with " BatchSize:int " requests"
| summarize Count=count() by BatchSize
| render columnchart 

7. BATCH PROCESSING TIME
traces
| where timestamp > ago(7d)
| where message contains "Batch " and message contains "processing status"
| parse message with "Batch " BatchId:string ":"
| summarize StartTime=min(timestamp), EndTime=max(timestamp) by BatchId
| extend ProcessingTimeMinutes = datetime_diff('minute', EndTime, StartTime)
| where ProcessingTimeMinutes > 0
| summarize AvgProcessingTime=avg(ProcessingTimeMinutes), 
           MaxProcessingTime=max(ProcessingTimeMinutes) 
| render table 

EOF

cat /tmp/batch_monitoring_queries.txt
echo ""
echo "✅ Query templates saved to /tmp/batch_monitoring_queries.txt"
echo "   Copy these to Application Insights → Logs → Save"

echo ""
echo "🔔 Creating Alert Rules"
echo "----------------------"

# Alert 1: High Batch Failure Rate
echo "Creating alert: High Batch Failure Rate..."
az monitor scheduled-query create \
  --name "BatchProcessing-HighFailureRate" \
  --resource-group "$RESOURCE_GROUP" \
  --scopes "$INSIGHTS_ID" \
  --condition "count 'Placeholder' > 0" \
  --description "Alert when batch processing failure rate exceeds 10%" \
  --disabled true \
  --evaluation-frequency 30m \
  --window-size 30m \
  --severity 2 \
  --query "traces | where message contains 'Completed batch' | parse message with * ': ' SuccessCount:int ' succeeded, ' ErrorCount:int ' errored' | extend TotalRequests = SuccessCount + ErrorCount | extend FailureRate = todouble(ErrorCount) / todouble(TotalRequests) * 100 | where FailureRate > 10" \
  2>/dev/null || echo "⚠️  Note: Alert creation requires manual setup in Azure Portal"

# Alert 2: Batch Processing Stopped
echo "Creating alert: No Batches Submitted..."
az monitor scheduled-query create \
  --name "BatchProcessing-NoSubmissions" \
  --resource-group "$RESOURCE_GROUP" \
  --scopes "$INSIGHTS_ID" \
  --condition "count 'Placeholder' == 0" \
  --description "Alert when no batches have been submitted in 2 hours" \
  --disabled true \
  --evaluation-frequency 1h \
  --window-size 2h \
  --severity 3 \
  --query "traces | where message contains 'Batch submitted'" \
  2>/dev/null || echo "⚠️  Note: Alert creation requires manual setup in Azure Portal"

# Alert 3: High Cost
echo "Creating alert: High Daily Cost..."
az monitor scheduled-query create \
  --name "BatchProcessing-HighCost" \
  --resource-group "$RESOURCE_GROUP" \
  --scopes "$INSIGHTS_ID" \
  --condition "count 'Placeholder' > 0" \
  --description "Alert when daily batch processing cost exceeds $5" \
  --disabled true \
  --evaluation-frequency 6h \
  --window-size 24h \
  --severity 2 \
  --query "traces | where message contains 'Batch summary for' | parse message with * '$' Cost:double | summarize TotalCost=sum(Cost) | where TotalCost > 5.0" \
  2>/dev/null || echo "⚠️  Note: Alert creation requires manual setup in Azure Portal"

echo ""
echo "📈 Setting up Dashboard"
echo "----------------------"

echo "Dashboard configuration can be created manually in Azure Portal:"
echo "1. Go to Azure Portal → Dashboards"
echo "2. Create new dashboard: 'Batch Processing Monitoring'"
echo "3. Add tiles for:"
echo "   - Batch submission rate (line chart)"
echo "   - Success rate (gauge, target: >95%)"
echo "   - Stories in queue (number)"
echo "   - Daily cost (number)"
echo "   - Recent errors (table)"
echo ""

echo "✅ Monitoring Setup Complete!"
echo "============================="
echo ""
echo "📋 Manual Setup Required in Azure Portal:"
echo ""
echo "1. Application Insights Queries:"
echo "   - Navigate to: $INSIGHTS_NAME → Logs"
echo "   - Copy queries from /tmp/batch_monitoring_queries.txt"
echo "   - Save each as a query for quick access"
echo ""
echo "2. Alert Rules (if automated creation failed):"
echo "   - Navigate to: $INSIGHTS_NAME → Alerts → Create alert rule"
echo "   - Configure based on the attempts above"
echo "   - Add action group for email/SMS notifications"
echo ""
echo "3. Dashboard:"
echo "   - Navigate to: Azure Portal → Dashboard"
echo "   - Pin query results and metrics"
echo ""
echo "4. Recommended Alerts to Create:"
echo "   ✓ Batch failure rate > 10% (severity: warning)"
echo "   ✓ No batches submitted in 2 hours (severity: info)"
echo "   ✓ Daily cost > $5 (severity: warning)"
echo "   ✓ Queue size > 200 stories (severity: info)"
echo "   ✓ Batch processing time > 90 minutes (severity: warning)"
echo ""
echo "📚 Documentation: docs/BATCH_PROCESSING.md"
echo ""

