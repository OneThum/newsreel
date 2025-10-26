#!/usr/bin/env python3
"""
Azure Application Insights Log Analyzer

Analyzes Azure logs to identify issues and patterns.
"""
import os
import sys
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from colorama import Fore, init

init(autoreset=True)

load_dotenv()

print(f"\n{Fore.CYAN}{'='*80}")
print(f"{Fore.CYAN}AZURE APPLICATION INSIGHTS LOG ANALYZER")
print(f"{Fore.CYAN}{'='*80}\n")

# Check if Azure credentials are configured
app_insights_id = os.getenv('AZURE_APP_INSIGHTS_ID')
subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')

if not app_insights_id or not subscription_id:
    print(f"{Fore.YELLOW}⚠  Azure Application Insights not configured")
    print(f"\nTo enable log analysis, add to .env:")
    print(f"  AZURE_SUBSCRIPTION_ID=your_subscription_id")
    print(f"  AZURE_APP_INSIGHTS_ID=your_app_insights_id")
    print(f"\nFor now, here are the log queries you can run manually in Azure Portal:\n")
else:
    print(f"{Fore.GREEN}✓ Azure Application Insights configured\n")
    print(f"Note: Automated log querying requires Azure SDK setup.")
    print(f"For now, run these queries manually in Azure Portal:\n")

# Common log queries
print(f"{Fore.YELLOW}{'='*80}")
print(f"COMMON LOG QUERIES")
print(f"{'='*80}\n")

queries = {
    "RSS Ingestion Frequency": """
traces
| where message contains "RSS ingestion complete"
| where timestamp > ago(1h)
| summarize count() by bin(timestamp, 1m)
| render timechart
    """,
    
    "RSS Ingestion Errors": """
traces
| where severityLevel >= 3  // Error or Critical
| where message contains "RSS"
| where timestamp > ago(24h)
| project timestamp, severityLevel, message
| order by timestamp desc
| take 100
    """,
    
    "Clustering Matches vs New Stories": """
traces
| where message contains "CLUSTERING"
| where timestamp > ago(1h)
| summarize 
    matches = countif(message contains "MATCH"),
    new = countif(message contains "new story"),
    total = count()
| extend match_rate = matches * 100.0 / (matches + new)
    """,
    
    "Clustering Similarity Scores": """
traces
| where message contains "similarity"
| where timestamp > ago(1h)
| extend similarity = extract("similarity ([0-9.]+)", 1, message)
| where isnotempty(similarity)
| summarize 
    avg_similarity = avg(todouble(similarity)),
    max_similarity = max(todouble(similarity)),
    min_similarity = min(todouble(similarity)),
    count()
    """,
    
    "Duplicate Source Prevention": """
traces
| where message contains "DUPLICATE SOURCE"
| where timestamp > ago(24h)
| project timestamp, message
| order by timestamp desc
    """,
    
    "Summarization Costs (24h)": """
traces
| where message contains "Generated summary"
| where timestamp > ago(24h)
| extend cost = extract("\\$([0-9.]+)", 1, message)
| where isnotempty(cost)
| summarize 
    total_cost = sum(todouble(cost)),
    avg_cost = avg(todouble(cost)),
    summary_count = count()
    """,
    
    "Summarization Generation Times": """
traces
| where message contains "Generated summary"
| where timestamp > ago(24h)
| extend gen_time = extract("([0-9]+)ms", 1, message)
| where isnotempty(gen_time)
| summarize 
    avg_time = avg(todouble(gen_time)),
    p50 = percentile(todouble(gen_time), 50),
    p95 = percentile(todouble(gen_time), 95),
    p99 = percentile(todouble(gen_time), 99)
    """,
    
    "AI Refusals": """
traces
| where message contains "Claude refused" or message contains "fallback summary"
| where timestamp > ago(24h)
| project timestamp, message
| order by timestamp desc
    """,
    
    "Breaking News Status Transitions": """
traces
| where message contains "Status transition" or message contains "BREAKING"
| where timestamp > ago(24h)
| project timestamp, message
| order by timestamp desc
    """,
    
    "Function Execution Times": """
requests
| where timestamp > ago(1h)
| summarize 
    count = count(),
    avg_duration = avg(duration),
    p95_duration = percentile(duration, 95)
    by name
| order by avg_duration desc
    """,
    
    "Error Summary (Last 24h)": """
traces
| where severityLevel >= 3
| where timestamp > ago(24h)
| summarize count() by severityLevel, operation_Name
| order by count_ desc
    """,
    
    "Most Common Errors": """
exceptions
| where timestamp > ago(24h)
| summarize count() by type, outerMessage
| order by count_ desc
| take 20
    """,
    
    "API Response Times": """
requests
| where timestamp > ago(1h)
| where name startswith "GET" or name startswith "POST"
| summarize 
    count = count(),
    avg_duration = avg(duration),
    p50 = percentile(duration, 50),
    p95 = percentile(duration, 95),
    p99 = percentile(duration, 99)
    by name
| order by count desc
    """,
}

for query_name, query in queries.items():
    print(f"{Fore.GREEN}━━━ {query_name} ━━━")
    print(query.strip())
    print()

print(f"\n{Fore.CYAN}{'='*80}")
print(f"HOW TO RUN THESE QUERIES")
print(f"{'='*80}\n")

print("1. Go to Azure Portal: https://portal.azure.com")
print("2. Navigate to: Application Insights > Logs")
print("3. Copy and paste any query above")
print("4. Adjust time range as needed")
print("5. Click 'Run' to execute")
print()

print(f"\n{Fore.CYAN}{'='*80}")
print(f"COMMON PATTERNS TO LOOK FOR")
print(f"{'='*80}\n")

print(f"{Fore.YELLOW}RSS Ingestion Issues:")
print("  - Gaps in ingestion frequency chart")
print("  - High error rates for specific sources")
print("  - Declining article counts over time")
print()

print(f"{Fore.YELLOW}Clustering Issues:")
print("  - Very low match rates (<10%)")
print("  - Many similarity scores below threshold (0.70)")
print("  - Frequent duplicate source warnings")
print()

print(f"{Fore.YELLOW}Summarization Issues:")
print("  - High AI refusal rate")
print("  - Generation times >5000ms")
print("  - Daily costs exceeding budget")
print()

print(f"{Fore.YELLOW}Performance Issues:")
print("  - API response times >1000ms")
print("  - Function execution times >30s")
print("  - High exception rates")
print()

print(f"\n{Fore.GREEN}For automated log analysis, install Azure SDK:")
print("  pip install azure-monitor-query azure-identity")
print()

