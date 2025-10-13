#!/usr/bin/env python3
"""
Automated Monitoring System for Newsreel Backend

This script continuously monitors:
1. Azure Functions logs for duplicate source warnings
2. API responses for source diversity
3. Story clustering behavior
4. Duplicate detection and reporting

Runs autonomously and logs findings for iterative debugging.

Usage:
    python automated-monitor.py --duration 3600  # Run for 1 hour
    python automated-monitor.py --continuous     # Run forever
"""

import os
import sys
import time
import json
import requests
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import subprocess

# Configuration
API_BASE_URL = "https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io"
CHECK_INTERVAL = 60  # Check every 60 seconds
LOG_FILE = "monitoring_results.jsonl"

# ANSI colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'


class NewsreelMonitor:
    """Automated monitoring system for Newsreel"""
    
    def __init__(self):
        self.findings = []
        self.story_history = {}  # Track stories over time
        self.duplicate_count = 0
        self.checked_stories = 0
        
    def log_finding(self, level, category, message, details=None):
        """Log a finding with timestamp"""
        finding = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'category': category,
            'message': message,
            'details': details or {}
        }
        self.findings.append(finding)
        
        # Also write to file
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(finding) + '\n')
        
        # Print to console
        color = {
            'INFO': BLUE,
            'WARNING': YELLOW,
            'ERROR': RED,
            'SUCCESS': GREEN
        }.get(level, '')
        
        print(f"{color}[{level}] {category}: {message}{RESET}")
        if details:
            print(f"  Details: {json.dumps(details, indent=2)}")
    
    def check_azure_logs(self):
        """Check Azure Application Insights for duplicate warnings"""
        try:
            # Query for duplicate source warnings in last 5 minutes
            query = """
            traces
            | where timestamp > ago(5m)
            | where message contains "DUPLICATE SOURCES"
            | project timestamp, message
            | order by timestamp desc
            | take 20
            """
            
            # Use Azure CLI to query
            result = subprocess.run([
                'az', 'monitor', 'app-insights', 'query',
                '--app', 'newsreel-insights',
                '--resource-group', 'newsreel-rg',
                '--analytics-query', query
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                warnings = data.get('tables', [{}])[0].get('rows', [])
                
                if warnings:
                    self.log_finding(
                        'WARNING',
                        'Azure Logs',
                        f"Found {len(warnings)} duplicate source warnings in last 5 minutes",
                        {'warnings': warnings[:5]}  # Show first 5
                    )
                    return len(warnings)
                else:
                    self.log_finding(
                        'INFO',
                        'Azure Logs',
                        "No duplicate warnings in last 5 minutes"
                    )
                    return 0
            else:
                self.log_finding(
                    'ERROR',
                    'Azure Logs',
                    f"Failed to query logs: {result.stderr}"
                )
                return None
                
        except Exception as e:
            self.log_finding(
                'ERROR',
                'Azure Logs',
                f"Error checking Azure logs: {e}"
            )
            return None
    
    def check_api_feed(self):
        """Check API feed for duplicate sources"""
        try:
            # Note: This endpoint requires auth, so it will fail
            # But we can still use it to test connectivity
            response = requests.get(
                f"{API_BASE_URL}/api/stories/feed?limit=20",
                timeout=10
            )
            
            if response.status_code == 403:
                self.log_finding(
                    'INFO',
                    'API Check',
                    "API requires authentication (expected)"
                )
                return None
            
            if response.status_code == 200:
                stories = response.json()
                return self.analyze_stories(stories)
            else:
                self.log_finding(
                    'WARNING',
                    'API Check',
                    f"Unexpected status code: {response.status_code}"
                )
                return None
                
        except Exception as e:
            self.log_finding(
                'ERROR',
                'API Check',
                f"Error checking API: {e}"
            )
            return None
    
    def analyze_stories(self, stories):
        """Analyze stories for source diversity"""
        issues = []
        
        for story in stories:
            self.checked_stories += 1
            story_id = story.get('id', 'unknown')
            source_count = story.get('source_count', 0)
            sources = story.get('sources', [])
            
            # Track this story
            if story_id not in self.story_history:
                self.story_history[story_id] = {
                    'first_seen': datetime.utcnow().isoformat(),
                    'title': story.get('title', 'Unknown'),
                    'source_counts': []
                }
            
            self.story_history[story_id]['source_counts'].append({
                'timestamp': datetime.utcnow().isoformat(),
                'count': source_count,
                'sources_array_length': len(sources)
            })
            
            # Check for issues
            if len(sources) == 0 and source_count > 0:
                issue = {
                    'type': 'empty_sources_array',
                    'story_id': story_id,
                    'title': story.get('title', '')[:80],
                    'source_count': source_count,
                    'sources_length': 0
                }
                issues.append(issue)
                self.log_finding(
                    'ERROR',
                    'Source Array Empty',
                    f"Story {story_id} claims {source_count} sources but array is empty",
                    issue
                )
            
            elif len(sources) > 0:
                # Check for duplicates
                source_names = [s.get('source', 'unknown') for s in sources]
                source_counts_dict = Counter(source_names)
                duplicates = {k: v for k, v in source_counts_dict.items() if v > 1}
                
                if duplicates:
                    self.duplicate_count += 1
                    issue = {
                        'type': 'duplicate_sources',
                        'story_id': story_id,
                        'title': story.get('title', '')[:80],
                        'total_sources': len(sources),
                        'unique_sources': len(source_counts_dict),
                        'duplicates': dict(duplicates)
                    }
                    issues.append(issue)
                    self.log_finding(
                        'WARNING',
                        'Duplicate Sources',
                        f"Story {story_id} has {len(sources) - len(source_counts_dict)} duplicate entries",
                        issue
                    )
        
        return issues
    
    def check_function_health(self):
        """Check if Azure Functions are running"""
        try:
            result = subprocess.run([
                'az', 'functionapp', 'show',
                '--name', 'newsreel-functions',
                '--resource-group', 'newsreel-rg',
                '--query', 'state',
                '-o', 'tsv'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                state = result.stdout.strip()
                if state == 'Running':
                    self.log_finding(
                        'SUCCESS',
                        'Function Health',
                        "Azure Functions are running"
                    )
                    return True
                else:
                    self.log_finding(
                        'ERROR',
                        'Function Health',
                        f"Azure Functions state: {state}"
                    )
                    return False
            else:
                self.log_finding(
                    'ERROR',
                    'Function Health',
                    f"Failed to check function health: {result.stderr}"
                )
                return None
                
        except Exception as e:
            self.log_finding(
                'ERROR',
                'Function Health',
                f"Error checking function health: {e}"
            )
            return None
    
    def generate_report(self):
        """Generate a summary report"""
        print(f"\n{BOLD}{CYAN}{'='*80}{RESET}")
        print(f"{BOLD}{CYAN}MONITORING SUMMARY{RESET}")
        print(f"{BOLD}{CYAN}{'='*80}{RESET}\n")
        
        print(f"Checked stories: {self.checked_stories}")
        print(f"Duplicate issues found: {self.duplicate_count}")
        print(f"Total findings: {len(self.findings)}")
        print()
        
        # Count by level
        by_level = Counter(f['level'] for f in self.findings)
        print(f"Findings by level:")
        for level, count in sorted(by_level.items()):
            color = {
                'INFO': BLUE,
                'WARNING': YELLOW,
                'ERROR': RED,
                'SUCCESS': GREEN
            }.get(level, '')
            print(f"  {color}{level}: {count}{RESET}")
        print()
        
        # Recent issues
        recent_issues = [f for f in self.findings if f['level'] in ['WARNING', 'ERROR']][-10:]
        if recent_issues:
            print(f"{BOLD}Recent issues:{RESET}")
            for issue in recent_issues:
                print(f"  [{issue['timestamp']}] {issue['category']}: {issue['message']}")
            print()
        
        # Story tracking
        if self.story_history:
            print(f"{BOLD}Tracked stories: {len(self.story_history)}{RESET}")
            # Show stories with changing source counts
            changing = {k: v for k, v in self.story_history.items() 
                       if len(v['source_counts']) > 1}
            if changing:
                print(f"  Stories with changing source counts: {len(changing)}")
                for story_id, data in list(changing.items())[:5]:
                    counts = [c['count'] for c in data['source_counts']]
                    print(f"    {story_id}: {counts[0]}→{counts[-1]} sources")
            print()
        
        # Save detailed report
        report_file = f"monitoring_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'summary': {
                    'checked_stories': self.checked_stories,
                    'duplicate_count': self.duplicate_count,
                    'total_findings': len(self.findings),
                    'by_level': dict(by_level)
                },
                'findings': self.findings,
                'story_history': self.story_history
            }, f, indent=2)
        
        print(f"Detailed report saved to: {report_file}")
        print()
    
    def run_check_cycle(self):
        """Run one complete check cycle"""
        print(f"\n{BOLD}[{datetime.utcnow().isoformat()}] Running check cycle...{RESET}")
        
        # Check function health
        self.check_function_health()
        
        # Check Azure logs for warnings
        self.check_azure_logs()
        
        # Try to check API (will fail due to auth, but that's okay)
        self.check_api_feed()
        
        print(f"{BOLD}Check cycle complete{RESET}")
    
    def run(self, duration=None, continuous=False):
        """Run monitoring for specified duration or continuously"""
        start_time = time.time()
        
        print(f"{BOLD}{GREEN}{'='*80}{RESET}")
        print(f"{BOLD}{GREEN}NEWSREEL AUTOMATED MONITOR STARTED{RESET}")
        print(f"{BOLD}{GREEN}{'='*80}{RESET}\n")
        
        if continuous:
            print(f"Running continuously (Ctrl+C to stop)...")
        elif duration:
            print(f"Running for {duration} seconds...")
        
        print(f"Check interval: {CHECK_INTERVAL} seconds")
        print(f"Logging to: {LOG_FILE}")
        print()
        
        try:
            while True:
                self.run_check_cycle()
                
                # Check if we should stop
                if duration and (time.time() - start_time) >= duration:
                    break
                
                # Wait for next check
                print(f"Next check in {CHECK_INTERVAL} seconds...")
                time.sleep(CHECK_INTERVAL)
                
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Monitoring stopped by user{RESET}")
        
        finally:
            self.generate_report()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated monitoring for Newsreel')
    parser.add_argument('--duration', type=int, help='Run for N seconds')
    parser.add_argument('--continuous', action='store_true', help='Run continuously')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds')
    
    args = parser.parse_args()
    
    global CHECK_INTERVAL
    CHECK_INTERVAL = args.interval
    
    monitor = NewsreelMonitor()
    
    if args.continuous:
        monitor.run(continuous=True)
    elif args.duration:
        monitor.run(duration=args.duration)
    else:
        # Default: run for 10 minutes
        monitor.run(duration=600)


if __name__ == "__main__":
    main()

