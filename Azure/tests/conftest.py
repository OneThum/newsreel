"""
Shared pytest fixtures for Newsreel API tests
"""
import os
import sys
import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from dotenv import load_dotenv

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../functions')))

# Load environment variables
load_dotenv()


def pytest_configure(config):
    """
    Pytest hook that runs before test collection
    
    Automatically generates Firebase JWT token if not already set
    """
    # Skip if token already set
    if os.getenv('NEWSREEL_JWT_TOKEN'):
        print("✅ Using existing NEWSREEL_JWT_TOKEN from environment")
        return
    
    # Try to generate token
    try:
        from scripts.firebase_auth_helper import FirebaseAuthHelper
        
        print("\n🔐 Generating Firebase JWT token for tests...")
        helper = FirebaseAuthHelper(verbose=True)
        token = helper.get_token()
        
        if token:
            os.environ['NEWSREEL_JWT_TOKEN'] = token
            print(f"✅ JWT token ready: {token[:30]}...{token[-10:]}")
        else:
            print("⚠️  Could not generate JWT token - tests will skip authenticated endpoints")
    except Exception as e:
        print(f"⚠️  Error generating JWT token: {e}")
        print("   Tests will skip authenticated endpoints")


# Import app modules
from functions.shared.config import config
from functions.shared.cosmos_client import CosmosDBClient
from functions.shared.models import RawArticle, StoryCluster

# ============================================================================
# TEST DATA HELPERS - Create objects with correct schemas
# ============================================================================

def create_test_article_dict(article_id: str, source: str = "test_source") -> Dict[str, Any]:
    """Create a properly formatted article dictionary for source_articles list"""
    now = datetime.now(timezone.utc)
    return {
        "id": article_id,
        "source": source,
        "title": f"Article from {source}",
        "url": f"https://{source}.com/article/{article_id}",
        "source_tier": 1,
        "description": "Test article description",
        "published_at": now.isoformat(),
        "fetched_at": now.isoformat(),
        "category": "world",
        "language": "en"
    }


def create_test_source_articles(count: int = 3) -> List[Dict[str, Any]]:
    """Create a list of properly formatted source article dictionaries"""
    sources = ["reuters", "bbc", "cnn", "ap", "nyt"]
    articles = []
    for i in range(min(count, len(sources))):
        source = sources[i]
        articles.append(create_test_article_dict(f"{source}_article_{i}", source))
    return articles


# ============================================================================
# SESSION FIXTURES (Setup once per test session)
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config():
    """Load test configuration"""
    return {
        'cosmos_connection_string': os.getenv('COSMOS_CONNECTION_STRING'),
        'cosmos_database_name': os.getenv('COSMOS_DATABASE_NAME', 'newsreel-db'),
        'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
        'api_url': os.getenv('API_URL'),
        'api_test_user_email': os.getenv('API_TEST_USER_EMAIL'),
        'api_test_user_password': os.getenv('API_TEST_USER_PASSWORD'),
        'test_mode': os.getenv('TEST_MODE', 'integration'),
        'test_timeout': int(os.getenv('TEST_TIMEOUT', '300')),
        'mock_external_apis': os.getenv('MOCK_EXTERNAL_APIS', 'true').lower() == 'true'
    }


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
async def cosmos_client(test_config):
    """Create Cosmos DB client for tests"""
    if not test_config['cosmos_connection_string']:
        pytest.skip("Cosmos DB connection string not configured")
    
    client = CosmosDBClient()
    client.connect()
    yield client
    # No cleanup needed - client is stateless


@pytest.fixture(scope="function")
async def cosmos_client_for_tests(test_config):
    """
    ✅ REAL Cosmos DB client for integration tests
    
    This fixture connects to the ACTUAL Cosmos DB database,
    not a mock. This ensures tests use real data and fail when
    the system is actually broken.
    
    Usage:
        async def test_something(cosmos_client_for_tests, clean_test_data):
            article = create_test_article()
            result = await cosmos_client_for_tests.create_article(article)
            clean_test_data.register_article(result['id'])
            
            # Query real database
            stories = await cosmos_client_for_tests.query_stories_by_fingerprint(...)
            assert len(stories) > 0
    """
    if not test_config['cosmos_connection_string']:
        pytest.skip("Cosmos DB connection string not configured")
    
    client = CosmosDBClient()
    client.connect()
    
    yield client
    
    # Client is stateless, no cleanup needed


@pytest.fixture
async def clean_test_data(cosmos_client):
    """
    Clean up test data after each test
    
    Usage:
        @pytest.fixture
        async def test_article_creation(clean_test_data):
            # Your test code here
            # Test data will be cleaned up automatically
    """
    test_article_ids = []
    test_story_ids = []
    
    def register_article(article_id: str):
        test_article_ids.append(article_id)
    
    def register_story(story_id: str):
        test_story_ids.append(story_id)
    
    yield {
        'register_article': register_article,
        'register_story': register_story
    }
    
    # Cleanup after test
    for article_id in test_article_ids:
        try:
            # Delete test articles
            container = cosmos_client._get_container("raw_articles")
            # Extract date from ID for partition key
            parts = article_id.split('_')
            if len(parts) >= 2:
                date_str = parts[1]
                partition_key = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                container.delete_item(item=article_id, partition_key=partition_key)
        except Exception as e:
            print(f"Warning: Failed to clean up test article {article_id}: {e}")
    
    for story_id in test_story_ids:
        try:
            # Delete test stories
            container = cosmos_client._get_container("story_clusters")
            # Try common categories
            for category in ['test', 'world', 'tech', 'general']:
                try:
                    container.delete_item(item=story_id, partition_key=category)
                    break
                except:
                    continue
        except Exception as e:
            print(f"Warning: Failed to clean up test story {story_id}: {e}")


# ============================================================================
# SAMPLE DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_rss_entry():
    """Sample RSS feed entry"""
    return {
        'title': 'Test Article: Breaking News Event',
        'link': 'https://example.com/test-article-123',
        'description': 'This is a test article about a breaking news event. It contains important information.',
        'published': 'Mon, 26 Oct 2025 14:30:00 GMT',
        'author': 'Test Author',
        'summary': 'Summary of the test article'
    }


@pytest.fixture
def sample_article() -> RawArticle:
    """Sample raw article"""
    return RawArticle(
        id=f"test_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_abc123",
        source="reuters",
        source_url="https://www.reuters.com/rss",
        source_tier=1,
        article_url="https://www.reuters.com/test-article",
        title="Test Article: Breaking News Event",
        description="This is a test article about a breaking news event.",
        published_at=datetime.now(timezone.utc),
        fetched_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        published_date=datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        content="Full article content here. This is a test article with multiple paragraphs.",
        author="Test Author",
        entities=[
            {"text": "Test", "type": "KEYWORD"},
            {"text": "Breaking", "type": "KEYWORD"}
        ],
        category="world",
        tags=["test", "breaking"],
        language="en",
        story_fingerprint="test_breaking_news_event",
        processed=False,
        processing_attempts=0
    )


@pytest.fixture
def sample_story() -> StoryCluster:
    """Sample story cluster"""
    return StoryCluster(
        id=f"story_test_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
        event_fingerprint="test_breaking_news_event",
        title="Test Story: Breaking News Event",
        category="world",
        tags=["test", "breaking"],
        status="DEVELOPING",
        verification_level=2,
        first_seen=datetime.now(timezone.utc),
        last_updated=datetime.now(timezone.utc),
        source_articles=[
            {
                'id': 'reuters_20251026_143000_abc123',
                'source': 'reuters',
                'title': 'Test Article 1',
                'url': 'https://example.com/1',
                'published_at': datetime.now(timezone.utc).isoformat(),
                'content': 'Content 1'
            },
            {
                'id': 'bbc_20251026_143100_def456',
                'source': 'bbc',
                'title': 'Test Article 2',
                'url': 'https://example.com/2',
                'published_at': datetime.now(timezone.utc).isoformat(),
                'content': 'Content 2'
            }
        ],
        importance_score=75,
        confidence_score=80,
        breaking_news=False
    )


@pytest.fixture
def sample_articles_batch() -> List[RawArticle]:
    """Batch of sample articles for testing clustering"""
    articles = []
    sources = ['reuters', 'bbc', 'ap', 'cnn', 'nyt']
    
    for i, source in enumerate(sources):
        article = RawArticle(
            id=f"{source}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{i}",
            source=source,
            source_url=f"https://www.{source}.com/rss",
            source_tier=1,
            article_url=f"https://www.{source}.com/test-article-{i}",
            title=f"Earthquake Strikes Japan - {source.upper()} Report",
            description=f"A magnitude 7.2 earthquake struck northern Japan. Report from {source}.",
            published_at=datetime.now(timezone.utc),
            fetched_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            published_date=datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            content=f"Full article content from {source}. Details about the earthquake.",
            author=f"{source.upper()} Reporter",
            entities=[
                {"text": "Japan", "type": "LOCATION"},
                {"text": "earthquake", "type": "EVENT"}
            ],
            category="world",
            tags=["earthquake", "japan", "disaster"],
            language="en",
            story_fingerprint="earthquake_japan_7.2",
            processed=False,
            processing_attempts=0
        )
        articles.append(article)
    
    return articles


# ============================================================================
# API FIXTURES
# ============================================================================

@pytest.fixture
def api_client(test_config):
    """HTTP client for API testing"""
    import requests
    
    class APIClient:
        def __init__(self, base_url):
            self.base_url = base_url
            self.session = requests.Session()
            self.token = None
        
        def authenticate(self, email, password):
            """Authenticate and store token"""
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json={"email": email, "password": password}
            )
            if response.status_code == 200:
                self.token = response.json()['token']
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
            return response
        
        def get(self, endpoint, **kwargs):
            return self.session.get(f"{self.base_url}{endpoint}", **kwargs)
        
        def post(self, endpoint, **kwargs):
            return self.session.post(f"{self.base_url}{endpoint}", **kwargs)
        
        def put(self, endpoint, **kwargs):
            return self.session.put(f"{self.base_url}{endpoint}", **kwargs)
        
        def delete(self, endpoint, **kwargs):
            return self.session.delete(f"{self.base_url}{endpoint}", **kwargs)
    
    if not test_config['api_url']:
        pytest.skip("API URL not configured")
    
    client = APIClient(test_config['api_url'])
    yield client
    client.session.close()


# ============================================================================
# FIREBASE AUTHENTICATION FIXTURES (For System Tests)
# ============================================================================

@pytest.fixture(scope="session")
def firebase_auth_helper():
    """Firebase authentication helper for tests"""
    try:
        from scripts.firebase_auth_helper import FirebaseAuthHelper
        helper = FirebaseAuthHelper(verbose=False)
        return helper
    except ImportError:
        pytest.skip("Firebase auth helper not available")


@pytest.fixture(scope="session")
def auth_token(firebase_auth_helper):
    """Get a Firebase JWT token for API authentication
    
    Uses real Firebase anonymous authentication which is always available.
    
    Priority order:
    1. Cached token
    2. NEWSREEL_JWT_TOKEN environment variable
    3. Local firebase_token.txt file
    4. Generate new token via Firebase anonymous auth
    """
    token = firebase_auth_helper.get_token()
    if not token:
        raise RuntimeError(
            "❌ CRITICAL: Failed to obtain Firebase JWT token!\n"
            "This is required for all API tests.\n"
            "Firebase anonymous authentication should always work.\n"
            "Check your Firebase API key and network connectivity."
        )
    return token


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    """Get authorization headers for authenticated API requests"""
    return {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture(scope="session")
def api_base_url():
    """Get API base URL from environment"""
    return os.getenv(
        'API_BASE_URL',
        'https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io'
    )


@pytest.fixture(scope="session")
def api_client_authenticated(auth_headers, api_base_url):
    """Create authenticated HTTP client for API requests"""
    import requests
    
    client = requests.Session()
    client.headers.update(auth_headers)
    client.base_url = api_base_url
    
    # Add convenience method to make requests with base URL
    def make_request(method, endpoint, **kwargs):
        url = f"{api_base_url}{endpoint}"
        return client.request(method, url, **kwargs)
    
    client.make_request = make_request
    return client


@pytest.fixture
def api_client_unauthenticated(api_base_url):
    """Create unauthenticated HTTP client for testing public endpoints"""
    import requests
    
    client = requests.Session()
    client.base_url = api_base_url
    
    def make_request(method, endpoint, **kwargs):
        url = f"{api_base_url}{endpoint}"
        return client.request(method, url, **kwargs)
    
    client.make_request = make_request
    return client


# ============================================================================
# MOCK FIXTURES (DEPRECATED - Use real Cosmos DB instead)
# ============================================================================

@pytest.fixture
def mock_cosmos_client():
    """
    ⚠️  DEPRECATED: This fixture uses FAKE data and hides real issues
    
    DO NOT USE for new tests. Use cosmos_client_for_tests instead.
    
    Why? We proved that mocks lead to:
    - 97% test pass rate while system is completely broken
    - False confidence in system health
    - Hidden bugs that users experience
    
    The policy is: NEVER use mock data for testing or debugging.
    Use the real system instead.
    
    See: TESTING_POLICY_NO_MOCKS.md
    """
    import warnings
    warnings.warn(
        "❌ DEPRECATED: mock_cosmos_client uses fake data and hides real issues\n"
        "   Use cosmos_client_for_tests instead (connects to REAL Cosmos DB)\n"
        "   Policy: Never use mock data for testing. See TESTING_POLICY_NO_MOCKS.md",
        DeprecationWarning,
        stacklevel=2
    )
    
    from unittest.mock import AsyncMock, MagicMock

    mock_client = MagicMock()

    mock_client.upsert_article = AsyncMock(return_value={'id': 'test_article_1'})
    mock_client.upsert_story = AsyncMock(return_value={'id': 'test_story_1'})
    mock_client.query_stories_by_fingerprint = AsyncMock(return_value=[])
    mock_client.query_stories_needing_summaries = AsyncMock(return_value=[])
    mock_client.get_story = AsyncMock(return_value=None)
    mock_client.update_story = AsyncMock(return_value={'id': 'test_story_1'})
    mock_client.get_feed_poll_states = AsyncMock(return_value={})
    mock_client.update_feed_poll_state = AsyncMock(return_value=None)

    return mock_client


@pytest.fixture
def mock_anthropic_client(mocker):
    """Mock Anthropic client for testing without API calls"""
    mock_client = mocker.MagicMock()
    
    # Mock successful summary generation
    mock_response = mocker.MagicMock()
    mock_response.content = [mocker.MagicMock(text="This is a test summary of the news story. It contains key facts and details.")]
    mock_response.usage = mocker.MagicMock(
        input_tokens=1000,
        output_tokens=100,
        cache_read_input_tokens=200
    )
    
    mock_client.messages.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_rss_feed():
    """Mock RSS feed for testing"""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Test News Feed</title>
            <link>https://example.com</link>
            <description>Test RSS Feed</description>
            <item>
                <title>Test Article 1: Breaking News</title>
                <link>https://example.com/article1</link>
                <description>This is a test article about breaking news.</description>
                <pubDate>Mon, 26 Oct 2025 14:30:00 GMT</pubDate>
                <author>Test Author</author>
            </item>
            <item>
                <title>Test Article 2: Update on Event</title>
                <link>https://example.com/article2</link>
                <description>This is an update on the breaking news event.</description>
                <pubDate>Mon, 26 Oct 2025 14:35:00 GMT</pubDate>
                <author>Test Author 2</author>
            </item>
        </channel>
    </rss>
    """


# ============================================================================
# HELPER FIXTURES
# ============================================================================

@pytest.fixture
def wait_for_condition():
    """Helper to wait for a condition to be true"""
    async def _wait(condition_func, timeout=30, interval=1):
        """
        Wait for condition_func to return True
        
        Args:
            condition_func: Async function that returns bool
            timeout: Maximum seconds to wait
            interval: Seconds between checks
        """
        import asyncio
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            if await condition_func():
                return True
            await asyncio.sleep(interval)
        return False
    
    return _wait


@pytest.fixture
def assert_eventually():
    """Helper to assert that something becomes true eventually"""
    async def _assert(condition_func, timeout=30, message="Condition not met"):
        """
        Assert that condition_func returns True within timeout
        
        Args:
            condition_func: Async function that returns bool
            timeout: Maximum seconds to wait
            message: Error message if condition not met
        """
        import asyncio
        start = asyncio.get_event_loop().time()
        last_result = None
        
        while asyncio.get_event_loop().time() - start < timeout:
            last_result = await condition_func()
            if last_result:
                return
            await asyncio.sleep(1)
        
        raise AssertionError(f"{message} (last result: {last_result})")
    
    return _assert


# ============================================================================
# PYTEST HOOKS
# ============================================================================

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Add markers based on test location
    for item in items:
        if "unit/" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "end_to_end/" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "performance/" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)


@pytest.fixture(autouse=True)
def test_logging(caplog):
    """Configure logging for tests"""
    import logging
    caplog.set_level(logging.INFO)
    yield caplog


# ============================================================================
# INTEGRATION TEST FIXTURES
# ============================================================================

@pytest.fixture
def sample_verified_story():
    """Sample verified story (3+ sources) for integration tests"""
    # Return the actual story data, not a fixture function call
    return {
        'id': 'story_12345',
        'fingerprint': 'president announces climate',
        'headline': 'President Announces Major Climate Initiative',
        'summary': None,
        'status': 'VERIFIED',
        'category': 'world',
        'sources': [
            {'source': 'reuters', 'source_name': 'Reuters', 'article_id': 'reuters_article1', 'title': 'President Announces Climate Initiative'},
            {'source': 'bbc', 'source_name': 'BBC News', 'article_id': 'bbc_article1', 'title': 'President Unveils Climate Plan'},
            {'source': 'cnn', 'source_name': 'CNN', 'article_id': 'cnn_article1', 'title': 'New Climate Policy Revealed'}
        ],
        'article_count': 3,
        'entities': {'people': ['President']},
        'first_seen': (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
    }


@pytest.fixture
def sample_story_cluster():
    """Sample story cluster for integration tests"""
    return {
        'id': 'story_12345',
        'fingerprint': 'president announces climate',
        'headline': 'President Announces Major Climate Initiative',
        'summary': None,
        'status': 'DEVELOPING',
        'category': 'world',
        'sources': [
            {'source': 'reuters', 'source_name': 'Reuters', 'article_id': 'reuters_article1'},
            {'source': 'bbc', 'source_name': 'BBC News', 'article_id': 'bbc_article1'}
        ],
        'article_count': 2
    }


@pytest.fixture
def sample_breaking_story():
    """Sample breaking news story for integration tests"""
    return {
        'id': 'story_breaking_1',
        'headline': 'Earthquake Strikes Major City',
        'summary': 'A powerful earthquake has struck.',
        'status': 'BREAKING',
        'category': 'world',
        'sources': [
            {'source': 'reuters', 'source_name': 'Reuters', 'article_id': 'reuters_eq1'}
        ],
        'article_count': 4,
        'first_seen': (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat(),
        'breaking_triggered_at': (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
        'notification_sent': True
    }


@pytest.fixture
def sample_batch_request():
    """Sample batch summarization request for integration tests"""
    return {
        'id': 'batch_req_123',
        'batch_id': 'batch_ant_20251026_001',
        'anthropic_batch_id': 'batch_ant_20251026_001',  # Same as batch_id for consistency
        'story_ids': ['story_1', 'story_2', 'story_3', 'story_4', 'story_5'],
        'status': 'submitted',
        'submitted_at': '2025-10-26T08:00:00Z',
        'request_count': 5
    }


@pytest.fixture
def sample_completed_batch():
    """Sample completed batch with results for integration tests"""
    return {
        'id': 'batch_req_123',
        'status': 'completed',
        'results': [
            {'custom_id': 'story_1', 'result': {'type': 'succeeded', 'message': {'content': [{'text': 'Summary 1'}]}}},
            {'custom_id': 'story_2', 'result': {'type': 'succeeded', 'message': {'content': [{'text': 'Summary 2'}]}}},
            {'custom_id': 'story_3', 'result': {'type': 'succeeded', 'message': {'content': [{'text': 'Summary 3'}]}}}
        ],
        'succeeded_count': 3,
        'failed_count': 0,
        'total_cost': 0.0015
    }


@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response for integration tests"""
    return {
        'id': 'msg_123abc',
        'type': 'message',
        'role': 'assistant',
        'content': [{'type': 'text', 'text': 'This is a summary sentence. It contains multiple sentences. Each sentence ends with a period.'}],
        'model': 'claude-3-5-haiku-20241022',
        'usage': {
            'input_tokens': 500,
            'output_tokens': 50
        }
    }

