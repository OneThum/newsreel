# CRITICAL POLICY: NO MOCK DATA IN TESTING OR DEBUGGING

## Executive Summary

**🚨 ABSOLUTE RULE: Mock data is never acceptable for finding real system problems.**

- ❌ Never use mock databases
- ❌ Never use fake API responses  
- ❌ Never test with fabricated data
- ✅ Always test against REAL deployed system
- ✅ Always use REAL data from live API
- ✅ Always use REAL Cosmos DB for integration/system tests

**Why:** Mock data hides the real problems. We proved this when 97% of tests passed while the system was completely broken.

---

## The Problem We're Solving

### Historical Mistake (What Happened)

We built comprehensive test suites with mock data:
- ✅ 54 unit tests passing
- ✅ 59 integration tests passing  
- ✅ 97% overall pass rate
- 🔴 **System completely non-functional**

**Why nobody noticed the broken system:**
- Mock tests couldn't see the problem
- Fake data doesn't reveal real issues
- We had high confidence in metrics that were meaningless

**The cost:**
- Wasted weeks of development
- False sense of security
- Real problems went undetected
- Users experience broken app

### The Lesson

**Real data from real systems is the ONLY reliable indicator of system health.**

---

## Policy: Real Data Only

### ✅ ALWAYS DO THIS

#### System Tests (Primary)
```python
# ✅ CORRECT: Test real deployed system with real data
def test_clustering_is_working(api_base_url, auth_headers):
    """Test clustering using REAL API and REAL data"""
    
    # Real API request
    response = requests.get(
        f"{api_base_url}/api/stories/feed?limit=20",
        headers=auth_headers  # Real JWT token
    )
    
    # Real data from real database
    stories = response.json()
    
    # Assert against real data
    multi_source = [s for s in stories if len(s.get('sources', [])) > 1]
    assert len(multi_source) > 0  # Real clustering validation
```

#### Integration Tests (Secondary - For Debugging Specific Issues)
```python
# ✅ ACCEPTABLE: Use real Cosmos DB when debugging specific pipeline
async def test_story_clustering_pipeline(cosmos_client_real):
    """Debug clustering with real database (not mock)"""
    
    # Use REAL Cosmos DB client connected to production
    stories = await cosmos_client_real.query_stories_by_fingerprint(fingerprint)
    
    # Real assertion with real data
    assert len(stories) > 0 or len(stories) == 0  # Shows actual DB state
```

#### Unit Tests (Tertiary - Logic Regression Prevention Only)
```python
# ✅ ACCEPTABLE: Mock only for core algorithm regression testing
def test_text_similarity_algorithm():
    """Test the text similarity algorithm logic"""
    
    # This is OK because:
    # 1. We're testing pure math, not system behavior
    # 2. Results are deterministic (same input = same output)
    # 3. We already know system is broken from system tests
    # 4. This only prevents breaking existing logic
    
    sim = calculate_text_similarity("President announces policy", "President unveils plan")
    assert sim > 0.5  # Math check only
```

---

### ❌ NEVER DO THIS

#### ❌ Mock Cosmos DB in Integration Tests
```python
# WRONG: Mock database hides real issues
@pytest.fixture
def mock_cosmos_client():
    mock = MagicMock()
    mock.query_stories_by_fingerprint.return_value = [{"id": "fake"}]  # FAKE DATA
    return mock

async def test_clustering(mock_cosmos_client):
    # This passes even if real DB is completely broken
    stories = await mock_cosmos_client.query_stories_by_fingerprint(fp)
    assert len(stories) > 0  # Always passes (fake data)
```

**Why this is wrong:**
- Real Cosmos DB might be completely broken
- Real change feeds might not be firing
- Real articles might never be created
- But the test passes anyway with fake data

#### ❌ Mock API Responses in System Tests
```python
# WRONG: Mock API hides system-level failures
@patch('requests.get')
def test_api_stories(mock_get):
    mock_get.return_value.json.return_value = {
        'stories': [{'id': 'fake', 'sources': [1, 2, 3]}]  # FAKE DATA
    }
    
    stories = requests.get('/api/stories/feed').json()
    assert len(stories) > 0  # Always passes (fake data)
```

**Why this is wrong:**
- Real API might be down
- Real API might return 401/403
- Real API might return empty list
- But test passes with fake data

#### ❌ Mock Azure Functions
```python
# WRONG: Mock functions hide deployment issues
@patch('azure.functions')
def test_rss_ingestion(mock_func):
    mock_func.return_value = {'articles': [fake_article]}  # FAKE DATA
    
    result = run_rss_ingestion()
    assert result == success  # Always passes (fake)
```

**Why this is wrong:**
- Real function might not be deployed
- Real function might have errors
- Real function might not be triggered
- But test passes with fake data

---

## How to Test Real Systems

### Testing Against Deployed API

```python
# ✅ REAL: Test against actual deployed API
import requests
import os

API_URL = "https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io"
JWT_TOKEN = os.getenv('NEWSREEL_JWT_TOKEN')

def test_api_returns_stories():
    """Test REAL API with REAL JWT token"""
    
    response = requests.get(
        f"{API_URL}/api/stories/feed?limit=10",
        headers={'Authorization': f'Bearer {JWT_TOKEN}'}
    )
    
    # Real result
    if response.status_code != 200:
        print(f"❌ API returned {response.status_code}: {response.text}")
        # This is what we need to see - real problems!
    
    stories = response.json()
    assert len(stories) > 0  # Real assertion with real data
```

### Testing Cosmos DB Directly

```python
# ✅ REAL: Query actual Cosmos DB
from azure.cosmos import CosmosClient

def test_articles_in_cosmos():
    """Test REAL Cosmos DB"""
    
    client = CosmosClient.from_connection_string(connection_string)
    db = client.get_database_client("newsreel")
    container = db.get_container_client("raw_articles")
    
    # Query real database
    articles = list(container.query_items(
        query="SELECT * FROM c ORDER BY c._ts DESC LIMIT 10"
    ))
    
    # Real data from real DB
    if len(articles) == 0:
        print("❌ No articles in Cosmos DB - RSS ingestion broken!")
        # This is the real problem!
    
    assert len(articles) > 0
```

### Testing Azure Functions Directly

```python
# ✅ REAL: Test deployed Azure Function
import requests

def test_function_app_deployed():
    """Test REAL deployed function"""
    
    func_url = "https://newsreel-func-51689.azurewebsites.net/api/health"
    response = requests.get(func_url, timeout=10)
    
    # Real response from real function
    if response.status_code == 500:
        print(f"❌ Function error: {response.text}")
    
    assert response.status_code in [200, 404]  # Real deployment check
```

---

## When Mocks Are Acceptable

Mocks are ONLY acceptable in these specific scenarios:

### 1. Unit Tests for Pure Algorithms
```python
# ✅ OK: Testing pure math/logic that has no side effects
def test_fingerprint_generation():
    """Test fingerprinting algorithm consistency"""
    
    title = "President Announces Climate Policy"
    entities = extract_entities(title)
    
    fp1 = generate_fingerprint(title, entities)
    fp2 = generate_fingerprint(title, entities)
    
    assert fp1 == fp2  # Deterministic algorithm test
```

**Why this is acceptable:**
- Testing pure math, not system behavior
- Results are deterministic (same input = same output always)
- Doesn't involve I/O, databases, or network
- Low risk of hiding real issues

### 2. Isolated Function Logic Tests
```python
# ✅ OK: Testing specific function logic in isolation
def test_similarity_scoring():
    """Test similarity calculation algorithm"""
    
    score = calculate_similarity("text1", "text2")
    
    assert 0 <= score <= 1  # Score should be between 0 and 1
    assert isinstance(score, float)  # Type check
```

**Why this is acceptable:**
- Not testing system integration
- Only testing function contract (inputs/outputs)
- Doesn't hide real issues
- Used only to prevent regression

### 3. Component-Specific Debugging (With Real Data)
```python
# ✅ OK: Debug specific component with real data
async def test_clustering_logic_with_real_articles():
    """Test clustering logic with REAL articles from DB"""
    
    # Get REAL articles from actual Cosmos DB
    cosmos = connect_to_real_cosmos()
    real_articles = await cosmos.get_recent_articles(limit=100)
    
    # Test clustering logic with real data
    clusters = perform_clustering(real_articles)
    
    # Assert results make sense with real data
    assert len(clusters) > 0
    assert all(c.get('sources') for c in clusters)
```

**Why this is acceptable:**
- Uses REAL data from real system
- Only mocks the clustering function itself for testing
- Reveals real issues with real data
- Helps debug specific component

---

## The Testing Hierarchy (Correct Order)

### Level 1: System Tests (Highest Priority)
```
What: Test real deployed API/Functions/DB
Data: REAL data from live system
Mock: NOTHING
Result: If this fails, something is broken in production
Trust: 100% - this is ground truth
```

### Level 2: Integration Tests (For Debugging)
```
What: Test components working together
Data: REAL data where possible, minimal mocks
Mock: Only mock external services when necessary
Result: Helps debug specific components
Trust: High - uses mostly real data
```

### Level 3: Unit Tests (Regression Prevention)
```
What: Test individual functions
Data: Test data (OK to be synthetic)
Mock: OK to mock for isolated algorithm testing
Result: Catches regressions in specific code
Trust: Low - mostly mocked, only catches logic errors
```

---

## Implementation Rules

### Before Writing Integration Tests
```
MUST ASK:
1. Can I test this with REAL Cosmos DB? → YES → Do it
2. Can I test this with REAL API? → YES → Do it
3. Can I test this with REAL Azure Functions? → YES → Do it
4. Do I have to mock external service? → ONLY if necessary
5. Am I mocking something in my system? → PROBLEM → Reconsider
```

### When Cosmos DB Connection Is Required
```python
# If integration test needs Cosmos DB:
# ✅ ALWAYS use real connection string
# ✅ ALWAYS query actual database
# ✅ NEVER mock the database

# Configuration
COSMOS_ENDPOINT = os.getenv('COSMOS_ENDPOINT')
COSMOS_KEY = os.getenv('COSMOS_KEY')

# Real connection
client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
```

### When Azure API Key Is Required
```python
# If testing real API:
# ✅ ALWAYS use real JWT token from Firebase
# ✅ ALWAYS make real HTTP requests
# ✅ NEVER mock the API response

# Get real token
token = os.getenv('NEWSREEL_JWT_TOKEN')

# Real request
response = requests.get(
    f"{api_url}/api/stories/feed",
    headers={'Authorization': f'Bearer {token}'}
)
```

---

## Consequences of Violating This Policy

### Code Review: Mock Data Found
```
REVIEWER: "This test uses mock_cosmos_client"
DEVELOPER: "Yes, it's easier to test with mocks"
REVIEWER: "❌ REJECTED - This violates our testing policy"
          "Use REAL Cosmos DB connection"
          "Our system is broken. Mocks hide problems."
```

### System Tests Failing
```
System Test Result: ❌ 31% passing
Mock Test Result:   ✅ 97% passing
Difference:         Mock tests are LYING about system health

ACTION: Focus on system tests
        Ignore mock test pass rates
        System tests = ground truth
```

### Post-Mortem on Bug
```
Q: "Why didn't tests catch this?"
A: "Because we tested with mock data"

Q: "How do we prevent this?"
A: "Stop using mock data. Use real deployed system"

ACTION: Rewrite tests to use real system
        System tests must pass first
        Only add mocks if absolutely necessary
```

---

## Debugging Guidelines

### When System Test Fails

```
System Test: test_clustering_is_working ❌

Step 1: LOOK AT REAL DATA
  → Check actual Cosmos DB for stories
  → Query: SELECT COUNT(*) FROM story_clusters
  → If count = 0: clustering never happened
  
Step 2: TRACE BACKWARDS
  → Check if raw_articles has data
  → Query: SELECT COUNT(*) FROM raw_articles
  → If count = 0: RSS ingestion failed
  
Step 3: CHECK LOGS
  → Azure Function App logs for errors
  → Check change feed triggers firing
  → Check for Cosmos DB connection issues
  
Step 4: FIX BASED ON REAL DATA
  → Real problem revealed by real test
  → Not hidden by mock data
```

### When Integration Test Fails

```
Integration Test: test_xyz ❌

Step 1: NOT mock data issue
  → Integration tests use real DB/API
  → Real failure = real component issue
  
Step 2: CHECK COMPONENT
  → Run component locally with real data
  → Check error messages
  → Review Azure Function logs
  
Step 3: FIX AND RETEST
  → System test confirms fix works
  → Real data validates solution
```

---

## Summary

### The Golden Rule
**"When in doubt about test validity, check the real system."**

Mock data can't argue with:
- Real API responses
- Real database queries
- Real Azure Function logs
- Real network errors
- Real system behavior

### The New Standard
- ✅ System tests against real API = source of truth
- ✅ Integration tests with real data = debugging tool
- ✅ Unit tests for algorithms = regression prevention
- ❌ Mock data in any test = misleading
- ❌ High mock test pass rate = false confidence

### The Commitment
From now on:
1. **We measure system health by system tests, not mock tests**
2. **We debug with real data, not simulated data**
3. **We accept that 30% system test pass rate is better than 97% mock pass rate**
4. **We only add mocks when absolutely necessary for external services**
5. **We never mistake mock test success for real system success**

---

## References

- See: `CRITICAL_TESTING_LESSON.md` - Why 97% passing tests ≠ working system
- See: `TESTING_STRATEGY.md` - Correct testing hierarchy
- See: `test_deployed_api.py` - Real system tests (source of truth)

