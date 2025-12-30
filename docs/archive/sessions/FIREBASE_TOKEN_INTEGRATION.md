# Firebase JWT Token Integration - Complete Guide

## Summary

You now have a complete Firebase JWT token generation system for testing the Newsreel API. This includes:

1. **Command-line tool** - `get_firebase_token.py`
2. **Python module** - `firebase_auth_helper.py`  
3. **Pytest fixtures** - Updated `conftest.py`
4. **Documentation** - Quick start and detailed guides

---

## Why This Matters

The Newsreel API requires Firebase JWT tokens for authenticated requests. Previously:
- ❌ You had to manually create test users
- ❌ You had to copy tokens from the iOS app
- ❌ Tokens would expire and break tests
- ❌ No easy way to manage test authentication

Now:
- ✅ Tokens are generated automatically
- ✅ Tests can request tokens on demand
- ✅ Tokens are cached for performance
- ✅ Multiple fallback sources for flexibility

---

## Quick Usage Examples

### CLI Tool

```bash
# Generate and display token
python3 Azure/tests/scripts/get_firebase_token.py

# Save to file (reusable)
python3 Azure/tests/scripts/get_firebase_token.py --save

# Get just the token (for exporting)
export NEWSREEL_JWT_TOKEN=$(python3 Azure/tests/scripts/get_firebase_token.py --get-token)

# Use custom account
python3 Azure/tests/scripts/get_firebase_token.py \
  --email test@example.com \
  --password MyPassword123 \
  --save
```

### In pytest fixtures

```python
# Auto-get token with caching
def test_api(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get("https://api.newsreel.app/api/stories", headers=headers)
    assert response.status_code == 200

# Pre-authenticated client
def test_stories(api_client_authenticated):
    response = api_client_authenticated.get("/api/stories/feed")
    assert response.status_code == 200
```

### In Python code

```python
from scripts.firebase_auth_helper import FirebaseAuthHelper

helper = FirebaseAuthHelper()
token = helper.get_token()
headers = helper.get_auth_header()

# Force refresh if needed
new_token = helper.get_token(force_refresh=True)
```

---

## Token Priority Chain

When you request a token, the system tries (in order):

1. **Cached token** (if valid) - Fastest
2. **Environment variable** - `NEWSREEL_JWT_TOKEN`
3. **Local file** - `firebase_token.txt`
4. **Firebase API** - Generates new, saves to file

This means:
- First run: Creates test user in Firebase, gets token, saves to file
- Subsequent runs: Reuse file (instant)
- Tests: Can use `@pytest.fixture` or direct calls
- CI/CD: Can provide token via environment variable

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Your Test Code                        │
├─────────────────────────────────────────────────────────┤
│  Fixtures:          │  Direct Usage:                   │
│  - auth_token       │  - FirebaseAuthHelper()          │
│  - auth_headers     │  - get_firebase_jwt_token()      │
│  - api_client_      │  - get_token_with_env_fallback() │
│    authenticated    │                                  │
└──────────────┬──────────────────────────────────────────┘
               │
        ┌──────▼────────────────────────────┐
        │  firebase_auth_helper.py           │
        │  - Class: FirebaseAuthHelper       │
        │  - Caching & fallback logic        │
        └──────┬──────────────────────────────┘
               │
        ┌──────▼──────────────────────────┐
        │  get_firebase_token.py           │
        │  - Firebase REST API calls       │
        │  - User creation/signin          │
        │  - File I/O                      │
        └──────┬──────────────────────────┘
               │
        ┌──────▼─────────────────────────────┐
        │  Token Sources (Priority Order)    │
        │  1. Memory cache                   │
        │  2. NEWSREEL_JWT_TOKEN env var     │
        │  3. firebase_token.txt file        │
        │  4. Firebase identitytoolkit API   │
        └──────────────────────────────────┘
```

---

## File Locations

```
Azure/tests/
├── scripts/
│   ├── get_firebase_token.py          ← Main generator (150 lines)
│   ├── firebase_auth_helper.py         ← Test helper module (160 lines)
│   ├── FIREBASE_TOKEN_QUICKSTART.md    ← This quick start
│   └── README.md                       ← Full documentation
├── conftest.py                         ← Updated with fixtures
└── [your test files]
```

---

## Requirements

Only needs:
```bash
pip install requests  # (Usually already installed with pytest)
```

No service account credentials needed! Uses standard Firebase REST API.

---

## Security Considerations

✅ **Safe to use:**
- No credentials stored in code
- Test account only (created in Firebase)
- Token file can be in `.gitignore`
- API key is Firebase Web API (public key OK)

⚠️ **Best practices:**
- Don't commit `firebase_token.txt`
- Regenerate tokens periodically
- Use environment variable in CI/CD
- Don't share tokens outside your team

---

## Common Patterns

### Pattern 1: Authenticated API Test
```python
def test_get_user_profile(api_client_authenticated):
    response = api_client_authenticated.get("/api/user/preferences")
    assert response.status_code == 200
    assert "preferences" in response.json()
```

### Pattern 2: Multiple Requests
```python
def test_story_workflow(api_client_authenticated):
    # Get stories
    stories = api_client_authenticated.get("/api/stories/feed").json()
    assert len(stories) > 0
    
    # Get specific story
    story_id = stories[0]["id"]
    story = api_client_authenticated.get(f"/api/stories/{story_id}").json()
    assert story["id"] == story_id
```

### Pattern 3: Custom Test Account
```python
@pytest.fixture
def custom_auth_token():
    helper = FirebaseAuthHelper()
    return helper.get_token(
        email="testuser@example.com",
        password="CustomPassword123"
    )

def test_with_custom_user(custom_auth_token):
    headers = {"Authorization": f"Bearer {custom_auth_token}"}
    # ... use headers
```

### Pattern 4: Forced Refresh
```python
def test_token_refresh(firebase_auth_helper):
    token1 = firebase_auth_helper.get_token()
    token2 = firebase_auth_helper.get_token(force_refresh=True)
    
    # Different tokens
    assert token1 != token2
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "Failed to sign in" | Test user doesn't exist | Run `get_firebase_token.py --save` |
| "Firebase API error: 400" | Invalid API key | Check FIREBASE_API_KEY is set |
| "Token not available" | No file or env var | Generate with `--save` flag |
| Token expired | Old cached token | Use `force_refresh=True` |
| Import error | Path issue | Run from `Azure/tests/` directory |

---

## Next Steps

1. **First time setup:**
   ```bash
   cd Azure/tests
   python3 scripts/get_firebase_token.py --save
   ```

2. **Run a test:**
   ```bash
   pytest tests/integration/test_api.py -v
   ```

3. **Check it works:**
   ```bash
   python3 -c "from scripts.firebase_auth_helper import get_token; print(get_token()[:50])"
   ```

---

## Integration Points

This system integrates with:

- ✅ **pytest** - Via fixtures in `conftest.py`
- ✅ **requests** - HTTP client with auth headers
- ✅ **Firebase** - REST API for token generation
- ✅ **Azure API** - Authenticated requests with JWT
- ✅ **CI/CD** - Environment variable support
- ✅ **Local testing** - File-based caching

---

## Support

For questions or issues:

1. Check `FIREBASE_TOKEN_QUICKSTART.md` for common scenarios
2. Review examples in `Azure/tests/scripts/README.md`
3. Check script help: `python3 get_firebase_token.py --help`
4. Examine `firebase_auth_helper.py` for API details

