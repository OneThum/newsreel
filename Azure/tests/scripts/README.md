# Database Cleanup Scripts

**⚠️ DESTRUCTIVE OPERATIONS - READ CAREFULLY**

---

## Overview

These scripts permanently delete articles from Cosmos DB. Use them with extreme caution!

---

## Scripts

### 1. `cleanup_old_articles.py`

**Purpose**: Delete old articles, keep recent ones  
**Keeps**: Articles ingested in the last hour  
**Deletes**: Everything older than 1 hour  
**Use Case**: Maintain a small test dataset, reduce database size

**Usage**:
```bash
cd Azure/tests
python3 scripts/cleanup_old_articles.py
```

**Safety**:
- ✅ Keeps recent data (last hour)
- ⚠️  Requires confirmation before deletion
- 📊 Shows count before deletion

**Example Output**:
```
⏰ Cutoff time: 2025-10-26 00:15:00 UTC
   (Keeping articles ingested after this time)

Found 145,000 articles to delete (older than 1 hour)
Found 1,479 recent articles to keep (last hour)

Delete 145,000 old articles? (y/N):
```

---

### 2. `cleanup_all_articles.py`

**Purpose**: DELETE ALL ARTICLES from database  
**Keeps**: NOTHING  
**Deletes**: EVERYTHING  
**Use Case**: Complete system reset, start fresh

**Usage**:
```bash
cd Azure/tests
python3 scripts/cleanup_all_articles.py
```

**Safety**:
- ⚠️  **EXTREME CAUTION**
- 🔒 **THREE confirmations required**:
  1. Type "DELETE ALL ARTICLES"
  2. Type "YES I AM SURE"
  3. Type "CONFIRM DELETE"
- ⚠️  **CANNOT BE UNDONE**

**Confirmations Required**:
```
⚠️  WARNING: DESTRUCTIVE OPERATION ⚠️

This script will DELETE ALL ARTICLES from Cosmos DB!
This operation is PERMANENT and CANNOT BE UNDONE!

Type 'DELETE ALL ARTICLES' to continue: DELETE ALL ARTICLES

⚠️  Are you absolutely sure?
Type 'YES I AM SURE' to proceed: YES I AM SURE

⚠️  FINAL WARNING
Type 'CONFIRM DELETE' to proceed: CONFIRM DELETE
```

---

## From Health Report Dashboard

Both scripts can be triggered from the health report:

```
file:///Users/.../Newsreel/Azure/tests/reports/health_report.html
```

**Buttons**:
1. **🧹 Delete Old Articles** (orange) - Runs `cleanup_old_articles.py`
2. **⚠️ DELETE ALL ARTICLES** (red) - Runs `cleanup_all_articles.py`

**How it works**:
1. Click button
2. Read warning in popup
3. Click OK to copy command
4. Paste in terminal
5. Follow prompts carefully

---

## Safety Features

### Multiple Confirmations
- Scripts require explicit typed confirmations
- Cannot accidentally delete by hitting Enter
- Must type exact phrases

### Progress Tracking
```
🗑️  Deleting articles...
  Deleted 100/145,000 articles (0.1%)
  Deleted 200/145,000 articles (0.1%)
  ...
```

### Summary Report
```
================================================================================
DELETION COMPLETE
================================================================================
✓ Successfully deleted: 145,000 articles
⚠️  Failed to delete: 0 articles

Timestamp: 2025-10-26 01:20:00 UTC
```

---

## When to Use

### `cleanup_old_articles.py` ✅
**Good for**:
- Testing with fresh data
- Reducing database costs
- Maintaining a small test dataset
- Keeping last hour of data for debugging

**Example scenarios**:
- "I want to test RSS ingestion with a clean slate but keep recent articles"
- "Database is too large, trim it down to recent data"
- "Need to free up space but not lose everything"

### `cleanup_all_articles.py` ⚠️
**Good for**:
- Complete system reset
- Starting from scratch
- Clearing test data entirely
- Troubleshooting database corruption

**Example scenarios**:
- "I want to completely reset the system"
- "Need to clear all test data before going live"
- "Database has corrupt data, need fresh start"

### When NOT to use ❌
**DON'T USE IN PRODUCTION** unless you know exactly what you're doing!

These scripts are designed for **testing/development** environments.

---

## Troubleshooting

### "No articles to delete"
- Database is already empty
- Check connection string in `.env`

### "Failed to delete X articles"
- Network issues
- Permission issues
- First 5 errors are shown

### "Connection failed"
- Check `COSMOS_CONNECTION_STRING` in `.env`
- Verify Cosmos DB is accessible
- Check network connection

---

## Recovery

### If you deleted by accident:
1. **Stop immediately** (Ctrl+C)
2. Articles deleted so far are **gone forever**
3. Remaining articles are **still in database**
4. Check what's left:
   ```bash
   cd Azure/tests
   python3 diagnostics/check_rss_ingestion.py
   ```

### No backup/restore:
⚠️  These scripts **do not create backups**  
⚠️  Deletion is **permanent and immediate**  
⚠️  No "undo" or "restore" functionality

**Prevention is the only solution** - read prompts carefully!

---

## Best Practices

### Before Running
1. ✅ Read all warnings
2. ✅ Verify you're in correct environment
3. ✅ Check `.env` points to correct database
4. ✅ Consider if you really need to delete
5. ✅ Announce to team if shared database

### During Running
1. ✅ Read each prompt carefully
2. ✅ Type confirmations exactly as shown
3. ✅ Don't run if uncertain
4. ✅ Watch progress output
5. ✅ Can abort with Ctrl+C

### After Running
1. ✅ Verify results in summary
2. ✅ Check health report dashboard
3. ✅ Run diagnostics to verify state
4. ✅ Restart RSS ingestion if needed

---

## Technical Details

### What Gets Deleted

**Articles Container** (`raw_articles`):
- ✅ All raw article documents
- ✅ All ingestion metadata
- ✅ All processing flags

**Stories Container** (`story_clusters`):
- ❌ NOT deleted (kept intact)
- Stories remain but may have broken source links

### Deletion Method
- Uses Cosmos DB `delete_item()` API
- Requires both `id` and `partition_key`
- Processes one article at a time
- No batch deletion (safer)

### Performance
- **Speed**: ~100-500 articles/second
- **145,000 articles**: ~5-10 minutes
- **Progress updates**: Every 100 articles

---

## Support

**Problems?**
- Check `Azure/tests/diagnostics/system_health_report.py`
- Review Cosmos DB logs in Azure Portal
- Contact: dave@onethum.com

**Documentation**:
- Main README: `Azure/tests/README.md`
- Health Report Features: `Azure/tests/HEALTH_REPORT_FEATURES.md`

---

**Last Updated**: October 26, 2025  
**Status**: ✅ Production Ready (for dev/test environments)

## Firebase JWT Token Generation

### Overview

The Newsreel API requires Firebase JWT tokens for authentication. These scripts help you generate and manage tokens for testing.

### Quick Start

#### 1. Get a Token from Command Line

```bash
# Generate and print token
python3 scripts/get_firebase_token.py

# Export to environment variable
export NEWSREEL_JWT_TOKEN=$(python3 scripts/get_firebase_token.py --get-token)

# Save to file for future use
python3 scripts/get_firebase_token.py --save

# Use custom credentials
python3 scripts/get_firebase_token.py --email user@example.com --password MyPassword123
```

#### 2. Use in Test Fixtures

Add to your `conftest.py`:

```python
import pytest
from scripts.firebase_auth_helper import FirebaseAuthHelper

# Create auth helper
auth_helper = FirebaseAuthHelper(verbose=True)

@pytest.fixture
def auth_token():
    """Get Firebase JWT token for tests"""
    token = auth_helper.get_token()
    if not token:
        pytest.skip("Firebase token not available")
    return token

@pytest.fixture
def auth_headers(auth_token):
    """Get Authorization headers for API requests"""
    return {"Authorization": f"Bearer {auth_token}"}

@pytest.fixture
def api_client_authenticated(auth_headers):
    """HTTP client with Firebase auth"""
    import requests
    client = requests.Session()
    client.headers.update(auth_headers)
    return client
```

#### 3. Use in Test Code

```python
def test_authenticated_endpoint(api_client_authenticated):
    response = api_client_authenticated.get("/api/stories/feed")
    assert response.status_code == 200

def test_with_auth_token(auth_token):
    import requests
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(
        "https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io/api/stories/feed",
        headers=headers,
        timeout=10
    )
    assert response.status_code == 200
```

### Token Sources (Priority Order)

The token helper tries multiple sources in this order:

1. **Cached token** - Fast, reused from previous call
2. **Environment variable** - `NEWSREEL_JWT_TOKEN`
3. **Local file** - `firebase_token.txt`
4. **Firebase API** - Generate new token (creates user if needed)

### Environment Variables

You can customize behavior with environment variables:

```bash
# Use different Firebase project
export FIREBASE_PROJECT_ID="my-project-id"
export FIREBASE_API_KEY="my-api-key"

# Use different test account
export FIREBASE_TEST_EMAIL="my-test-user@example.com"
export FIREBASE_TEST_PASSWORD="MyPassword123"

# Reuse existing token
export NEWSREEL_JWT_TOKEN="eyJhbGciOiJSUzI1NiIs..."
```

### API Reference

#### `get_firebase_token.py`

**Functions:**

- `get_firebase_jwt_token(email, password, create_if_missing=True)` - Get JWT token
- `create_test_user(email, password)` - Create new Firebase user
- `login_user(email, password)` - Sign in existing user
- `save_token_to_file(token, filename)` - Save token to file
- `load_token_from_file(filename)` - Load token from file
- `get_token_with_env_fallback(email, password)` - Get token with all fallbacks

#### `firebase_auth_helper.py`

**Class: `FirebaseAuthHelper`**

```python
helper = FirebaseAuthHelper(verbose=True)

# Get token with caching
token = helper.get_token()

# Force refresh
token = helper.get_token(force_refresh=True)

# Get as header dict
headers = helper.get_auth_header()

# Validate token exists
is_valid = helper.validate_token_exists()

# Clear cache
helper.clear_cache()

# Direct access
token_from_env = helper.get_token_from_env()
token_from_file = helper.get_token_from_file("custom_file.txt")
helper.save_token(token, "custom_file.txt")
```

**Convenience functions:**

```python
from scripts.firebase_auth_helper import get_token, get_auth_headers

token = get_token()
headers = get_auth_headers()
```

### Common Scenarios

#### Scenario 1: First-time test setup

```bash
# Generate and save token
python3 scripts/get_firebase_token.py --save

# Now all tests can use it
pytest tests/integration/
```

#### Scenario 2: CI/CD Pipeline

```bash
# In your CI pipeline, generate token once
TOKEN=$(python3 scripts/get_firebase_token.py --get-token)
export NEWSREEL_JWT_TOKEN=$TOKEN

# Run all tests
pytest tests/
```

#### Scenario 3: Local development with test account

```bash
# Create a persistent test account
python3 scripts/get_firebase_token.py \
  --email testdev@newsreel.local \
  --password DevPassword123 \
  --save

# Reuse in all tests
export NEWSREEL_JWT_TOKEN=$(cat firebase_token.txt)
```

#### Scenario 4: Running tests without setup

If `firebase_token.txt` doesn't exist and no environment variable is set, the token will be generated on first use and saved automatically.

```python
# First test run generates and caches token
def test_api(auth_token):
    # Token auto-generated if needed
    assert auth_token is not None
```

### Troubleshooting

#### Issue: "Failed to sign in" error

**Solution**: The test account doesn't exist. Run:

```bash
python3 scripts/get_firebase_token.py --save
```

This will create the test account automatically.

#### Issue: "Firebase API error: 400"

**Solution**: Your Firebase API key may be invalid. Check:

```bash
# Verify API key is set
echo $FIREBASE_API_KEY

# Or verify in the script
grep FIREBASE_API_KEY scripts/get_firebase_token.py
```

#### Issue: Token is expired

**Solution**: Regenerate with force refresh:

```python
token = auth_helper.get_token(force_refresh=True)
```

Or from command line:

```bash
rm firebase_token.txt
python3 scripts/get_firebase_token.py --save
```

### Security Notes

- **Never commit tokens** - `firebase_token.txt` should be in `.gitignore`
- **Test account only** - The default test account is for testing only
- **Rotate tokens** - Regenerate tokens periodically
- **Environment variable** - Only set `NEWSREEL_JWT_TOKEN` for CI/CD, not locally

