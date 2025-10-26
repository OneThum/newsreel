# Test Setup Instructions

To see test results in the health dashboard, you need to install the pytest JSON report plugin.

---

## Quick Setup

```bash
cd ~/Library/CloudStorage/OneDrive-OneThumSoftware/One\ Thum\ Software/Newsreel/Azure/tests

# Install the JSON report plugin
pip install pytest-json-report

# Or install all test dependencies
pip install -r requirements.txt
```

---

## Verify Installation

```bash
pytest --version
pytest --help | grep json-report
```

You should see `--json-report` in the output.

---

## Run Tests and See Results in Dashboard

### Option 1: Use Dashboard Buttons (Recommended)

1. Open health report:
   ```
   file:///Users/davemac/Library/CloudStorage/OneDrive-OneThumSoftware/One%20Thum%20Software/Newsreel/Azure/tests/reports/health_report.html
   ```

2. Click any test button (Unit Tests, Integration Tests, etc.)

3. Paste command in terminal and run

4. Refresh dashboard (auto-refreshes every 30s)

5. See results in "🧪 Test Suite" section!

### Option 2: Run Manually

```bash
cd ~/Library/CloudStorage/OneDrive-OneThumSoftware/One\ Thum\ Software/Newsreel/Azure/tests

# Run tests with JSON report
pytest unit/ -v --json-report --json-report-file=reports/.report.json

# Convert to dashboard format
python3 scripts/save_test_results.py

# Regenerate dashboard
python3 diagnostics/system_health_report.py

# Open dashboard
open reports/health_report.html
```

---

## What You'll See

After running tests, the dashboard will show:

```
✅ Last Test Run: 2025-10-26 02:45:30 UTC
56/56 tests passed (100.0%)
Duration: 2.34s
```

Or if tests failed:

```
❌ Last Test Run: 2025-10-26 02:45:30 UTC
54/56 tests passed (96.4%) | 2 failed
Duration: 2.34s
```

---

## Troubleshooting

### "No test results available"

**Cause**: Tests haven't been run yet, or JSON file not created

**Solution**:
1. Install plugin: `pip install pytest-json-report`
2. Run tests using dashboard button or manual command
3. Wait 30 seconds for dashboard to refresh

### "pytest: error: unrecognized arguments: --json-report"

**Cause**: pytest-json-report plugin not installed

**Solution**:
```bash
pip install pytest-json-report
```

### Tests run but dashboard still shows "No results"

**Cause**: JSON file not in correct location

**Solution**:
```bash
# Check if file exists
ls -la reports/test_results.json

# If missing, run conversion script
python3 scripts/save_test_results.py
```

### Dashboard shows old results

**Cause**: Dashboard needs refresh

**Solution**:
- Wait 30 seconds (auto-refresh)
- Or manually refresh browser (Cmd+R)
- Or regenerate report: `python3 diagnostics/system_health_report.py`

---

## File Locations

**Pytest raw output**: `reports/.report.json` (hidden file)  
**Dashboard format**: `reports/test_results.json` (what dashboard reads)  
**Conversion script**: `scripts/save_test_results.py`

---

## Example Workflow

```bash
# 1. Install dependencies (once)
pip install pytest-json-report

# 2. Run tests (click dashboard button or run manually)
cd ~/Library/CloudStorage/OneDrive-OneThumSoftware/One\ Thum\ Software/Newsreel/Azure/tests
pytest integration/ -v --json-report --json-report-file=reports/.report.json
python3 scripts/save_test_results.py

# 3. View results
# Dashboard auto-refreshes every 30s, or open:
open reports/health_report.html
```

---

## Continuous Monitoring Setup

**Terminal 1** - Keep dashboard updating:
```bash
cd ~/Library/CloudStorage/OneDrive-OneThumSoftware/One\ Thum\ Software/Newsreel/Azure/tests
while true; do 
  python3 diagnostics/system_health_report.py
  sleep 30
done
```

**Browser** - Keep open, auto-refreshes:
```
file:///Users/davemac/Library/CloudStorage/OneDrive-OneThumSoftware/One%20Thum%20Software/Newsreel/Azure/tests/reports/health_report.html
```

**Terminal 2** - Run tests as needed:
```bash
# Click any test button in dashboard, paste here
```

**Result**: Live monitoring with test results updating automatically! 🎉

---

**Last Updated**: October 26, 2025

