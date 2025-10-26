#!/usr/bin/env python3
"""
Helper script to save test results in format expected by health dashboard

Run after pytest to convert results to dashboard format
"""
import json
import sys
import os
from datetime import datetime, timezone

# Default pytest JSON report structure
def convert_pytest_json_to_dashboard_format(pytest_json_file, output_file):
    """Convert pytest-json-report output to dashboard format"""
    try:
        with open(pytest_json_file, 'r') as f:
            pytest_data = json.load(f)
        
        # Extract key metrics
        summary = pytest_data.get('summary', {})
        
        dashboard_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total': summary.get('total', 0),
            'passed': summary.get('passed', 0),
            'failed': summary.get('failed', 0),
            'skipped': summary.get('skipped', 0),
            'error': summary.get('error', 0),
            'duration': pytest_data.get('duration', 0),
            'exitcode': pytest_data.get('exitcode', 0)
        }
        
        # Save in dashboard format
        with open(output_file, 'w') as f:
            json.dump(dashboard_data, f, indent=2)
        
        print(f"✓ Test results saved to: {output_file}")
        print(f"  Total: {dashboard_data['total']}")
        print(f"  Passed: {dashboard_data['passed']}")
        print(f"  Failed: {dashboard_data['failed']}")
        print(f"  Duration: {dashboard_data['duration']:.2f}s")
        
        return True
        
    except FileNotFoundError:
        print(f"✗ File not found: {pytest_json_file}")
        print(f"  Make sure to run pytest with: --json-report --json-report-file={pytest_json_file}")
        return False
    except Exception as e:
        print(f"✗ Error converting results: {e}")
        return False


if __name__ == "__main__":
    # Default paths
    test_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pytest_json = os.path.join(test_dir, 'reports', '.report.json')
    dashboard_json = os.path.join(test_dir, 'reports', 'test_results.json')
    
    if len(sys.argv) > 1:
        pytest_json = sys.argv[1]
    if len(sys.argv) > 2:
        dashboard_json = sys.argv[2]
    
    success = convert_pytest_json_to_dashboard_format(pytest_json, dashboard_json)
    sys.exit(0 if success else 1)

