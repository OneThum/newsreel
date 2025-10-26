# Health Report Interactive Features

**Last Updated**: October 26, 2025  
**Status**: ✅ Complete

---

## New Features Added

The `health_report.html` now includes:

### 1. ✅ Auto-Refresh (Every 30 seconds)
- Page automatically reloads every 30 seconds
- Shows live indicator: "🔄 Auto-refreshes every 30s"
- Keep the page open to monitor system in real-time

### 2. ✅ Interactive Test Buttons
Four clickable buttons to run tests:

1. **🔍 Run Diagnostics** - Execute all diagnostic scripts
2. **⚙️ Run Unit Tests** - Run unit test suite
3. **🔗 Run Integration Tests** - Run integration test suite
4. **🚀 Run All Tests** - Run complete test suite

### 3. ✅ One-Click Command Copy
- Click any button → popup with command
- Click "OK" → command copied to clipboard
- Paste in terminal and run!

### 4. ✅ Test Results Display
- Shows last test run results (if available)
- Displays: passed/failed count, pass rate, duration
- Visual indicators: ✅ (all passed) or ❌ (some failed)
- Instructions shown when no results available

---

## How It Works

### Button Click Flow

```
User clicks "Run Unit Tests"
  ↓
Popup shows: "Copy this command to clipboard?"
  cd Azure/tests && pytest unit/ -v --json-report --json-report-file=reports/test_results.json
  ↓
User clicks "OK"
  ↓
Command copied to clipboard
  ↓
User pastes in terminal and runs
  ↓
Results saved to reports/test_results.json
  ↓
Next report refresh shows test results!
```

### Commands Generated

Each button generates a specific command:

**🔍 Run Diagnostics**:
```bash
cd Azure/tests && ./run_all_diagnostics.sh
```

**⚙️ Run Unit Tests**:
```bash
cd Azure/tests && pytest unit/ -v --json-report --json-report-file=reports/test_results.json
```

**🔗 Run Integration Tests**:
```bash
cd Azure/tests && pytest integration/ -v --json-report --json-report-file=reports/test_results.json
```

**🚀 Run All Tests**:
```bash
cd Azure/tests && pytest -v --json-report --json-report-file=reports/test_results.json
```

---

## Test Results Display

### When Tests Haven't Run

Shows:
```
ℹ️ No test results available
Run tests using the buttons above to see results here.

# Quick start:
cd Azure/tests
pytest unit/ -v --json-report --json-report-file=reports/test_results.json
```

### When Tests Have Run

Shows:
```
✅ Last Test Run: 2025-10-26 01:30:45 UTC
56/56 tests passed (100.0%)
Duration: 2.34s
```

Or if tests failed:
```
❌ Last Test Run: 2025-10-26 01:30:45 UTC
54/56 tests passed (96.4%) | 2 failed
Duration: 2.34s
```

---

## Setup for Full Integration

To enable test results to appear in the report, install the pytest JSON plugin:

```bash
cd Azure/tests
pip install pytest-json-report
```

Then run tests with the `--json-report` flag (the buttons do this automatically).

---

## Usage Examples

### Monitor System + Run Tests

**Terminal 1** - Auto-generate reports every 30s:
```bash
cd Azure/tests
while true; do 
  python3 diagnostics/system_health_report.py
  sleep 30
done
```

**Browser** - Open health report:
```
file:///Users/davemac/Library/CloudStorage/OneDrive-OneThumSoftware/One%20Thum%20Software/Newsreel/Azure/tests/reports/health_report.html
```

**Terminal 2** - Run tests:
1. Click any button in browser
2. Copy command from popup  
3. Paste and run in terminal
4. Wait 30 seconds for report to refresh with results

---

## Visual Design

### Test Section Layout

```
┌─────────────────────────────────────────────────┐
│ 🧪 Test Suite                                   │
│ Run tests to verify system functionality        │
│                                                  │
│ [🔍 Run Diagnostics] [⚙️ Run Unit Tests]       │
│ [🔗 Run Integration Tests] [🚀 Run All Tests]  │
│                                                  │
│ ┌─────────────────────────────────────────────┐ │
│ │ ✅ Last Test Run: 2025-10-26 01:30:45 UTC  │ │
│ │ 56/56 tests passed (100.0%)                 │ │
│ │ Duration: 2.34s                             │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### Button Styling

- **Primary** (blue): Diagnostics
- **Success** (green): Unit & Integration tests
- **Secondary** (gray): All tests
- **Hover effects**: Darker shade on mouseover
- **Responsive**: Wraps on smaller screens

---

## Technical Details

### HTML Elements Added

1. **CSS Classes**:
   - `.test-section` - Container for test UI
   - `.button-group` - Flex layout for buttons
   - `.btn`, `.btn-primary`, `.btn-success`, `.btn-secondary` - Button styles
   - `.test-results` - Results display box
   - `.test-passed`, `.test-failed` - Color coding
   - `.code-block` - Terminal-style code display

2. **JavaScript Functions**:
   - `copyCommand(command)` - Copy to clipboard
   - `showInstructions(type)` - Show command popup

3. **Meta Tags**:
   - `<meta http-equiv="refresh" content="30">` - Auto-refresh

### Data Collection

The `collect_test_results()` method:
1. Checks for `reports/test_results.json`
2. Parses JSON if found
3. Stores in `self.report_data['tests']`
4. HTML template reads this data
5. Displays formatted results

---

## Future Enhancements (Optional)

Potential improvements:

1. **Live Test Execution** (requires server):
   - Run tests via WebSocket
   - Stream output to browser
   - No terminal needed

2. **Test History**:
   - Show last 5-10 test runs
   - Trend charts (pass rate over time)

3. **Per-Test Details**:
   - Expand to show individual test results
   - Click test name to see output

4. **Integration with CI/CD**:
   - Show GitHub Actions status
   - Link to workflow runs

---

## Files Modified

1. **`diagnostics/system_health_report.py`**:
   - Added `collect_test_results()` method
   - Added `_generate_test_results_section()` method
   - Added test section to HTML template
   - Added CSS for buttons and test results
   - Added JavaScript for clipboard copy

---

## Browser Compatibility

✅ **Tested on**:
- Chrome/Edge (Chromium)
- Safari
- Firefox

**Features**:
- ✅ Auto-refresh: All browsers
- ✅ Buttons: All browsers
- ✅ Clipboard API: Modern browsers (Chrome 66+, Safari 13.1+, Firefox 63+)

**Fallback**: If clipboard copy fails, alert shows error message.

---

## Summary

**Your health report now has**:

✅ **Auto-refresh every 30 seconds** - Real-time monitoring  
✅ **4 interactive test buttons** - Easy test execution  
✅ **One-click command copy** - No typing needed  
✅ **Test results display** - See last run status  
✅ **Visual indicators** - Green=pass, Red=fail  
✅ **Instructions** - Help text when needed

**Open the report and try it out!**

```
file:///Users/davemac/Library/CloudStorage/OneDrive-OneThumSoftware/One%20Thum%20Software/Newsreel/Azure/tests/reports/health_report.html
```

---

**Status**: ✅ Production Ready  
**Version**: 2.0 (Interactive)

