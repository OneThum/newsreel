# Firebase JWT Token - Quick Start

## What is This?

You now have tools to generate **Firebase JWT tokens** for testing the Newsreel API.

The API requires authentication with these tokens. Instead of setting them up manually, these scripts automate the process.

---

## One-Minute Setup

### 1. Generate and Save Token

```bash
cd /Users/davemac/Library/CloudStorage/OneDrive-OneThumSoftware/One\ Thum\ Software/Newsreel/Azure/tests
python3 scripts/get_firebase_token.py --save
```

✅ **Done!** Token is now saved to `firebase_token.txt`

### 2. Use in Your Tests

#### Option A: Command line export
```bash
export NEWSREEL_JWT_TOKEN=$(cat firebase_token.txt)
pytest tests/integration/
```

#### Option B: Use fixture in pytest
```python
def test_api(auth_token):
    # auth_token automatically available
    assert auth_token is not None
```

#### Option C: Use authenticated client fixture
```python
def test_stories(api_client_authenticated):
    # Pre-authenticated requests.Session() available
    response = api_client_authenticated.get("/api/stories/feed")
    assert response.status_code == 200
```

---

## How It Works

### File-Based
- `firebase_token.txt` - Your saved token (reused automatically)

### Scriptable
```bash
# Just get the token string
TOKEN=$(python3 scripts/get_firebase_token.py --get-token)
echo $TOKEN
```

### Programmatic
```python
from scripts.firebase_auth_helper import FirebaseAuthHelper

helper = FirebaseAuthHelper()
token = helper.get_token()
headers = helper.get_auth_header()
```

---

## What Gets Created

**Test User Account:**
- Email: `test@newsreel.test`
- Password: `TestPassword123!`
- Created in Firebase Console automatically

**Token File:**
- Location: `firebase_token.txt`
- Format: Raw JWT token
- Add to `.gitignore` (already done)

---

## For Different Scenarios

### CI/CD Pipeline
```bash
# Generate fresh token for this run
TOKEN=$(python3 scripts/get_firebase_token.py --get-token)
export NEWSREEL_JWT_TOKEN=$TOKEN
pytest tests/
```

### Custom Test Account
```bash
python3 scripts/get_firebase_token.py \
  --email myaccount@test.com \
  --password MyPassword123 \
  --save
```

### Force Refresh Token
```python
token = helper.get_token(force_refresh=True)
```

---

## Troubleshooting

### "Failed to sign in" error
The test account doesn't exist yet. Just run:
```bash
python3 scripts/get_firebase_token.py --save
```

### "Firebase API error: 400"
Your Firebase API key might be wrong. Check:
```bash
python3 scripts/get_firebase_token.py
# Look for error details
```

### Token expired
Regenerate:
```bash
rm firebase_token.txt
python3 scripts/get_firebase_token.py --save
```

---

## Files Created

1. **`get_firebase_token.py`** - Main token generation script
   - CLI tool
   - Firebase REST API integration
   - User management

2. **`firebase_auth_helper.py`** - Python module for tests
   - Class: `FirebaseAuthHelper`
   - Functions: `get_token()`, `get_auth_headers()`
   - Caching & fallback logic

3. **Updated `conftest.py`** - New pytest fixtures
   - `auth_token` - Get JWT token
   - `auth_headers` - Get auth headers
   - `api_client_authenticated` - Pre-authenticated HTTP client
   - `firebase_auth_helper` - Auth helper instance

---

## That's It!

You can now:
- ✅ Generate tokens for testing
- ✅ Use them in pytest fixtures
- ✅ Authenticate API requests
- ✅ Run integration tests with real Firebase authentication

Happy testing! 🚀
