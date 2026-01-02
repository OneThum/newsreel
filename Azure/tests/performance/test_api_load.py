"""
API Load and Performance Tests

Tests the API's ability to handle concurrent requests and measures response times.
"""

import pytest
import requests
import asyncio
import aiohttp
import os
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any


@pytest.fixture(scope="module")
def auth_token():
    """Load auth token from file"""
    token_file = os.path.join(os.path.dirname(__file__), '..', 'firebase_token.txt')
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            return f.read().strip()
    
    token = os.getenv('FIREBASE_TOKEN')
    if token:
        return token
    
    pytest.skip("No auth token available")


@pytest.fixture(scope="module")
def api_base_url():
    """Get API base URL"""
    return os.getenv(
        'API_URL',
        'https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io'
    )


@pytest.mark.performance
class TestAPIResponseTimes:
    """Test API response times meet SLA"""
    
    def test_health_endpoint_fast(self, api_base_url):
        """Test health endpoint responds in under 2000ms (including network latency)"""
        times = []
        
        for _ in range(5):
            start = time.time()
            response = requests.get(f"{api_base_url}/health", timeout=10)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            
            assert response.status_code == 200
        
        avg_time = statistics.mean(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]
        
        print(f"📊 Health endpoint - Avg: {avg_time:.0f}ms, P95: {p95_time:.0f}ms")
        
        # 2000ms threshold accounts for network latency from test environment
        # Actual API response time is much faster
        assert avg_time < 2000, f"Health endpoint too slow: {avg_time:.0f}ms avg"
    
    def test_feed_endpoint_acceptable(self, api_base_url, auth_token):
        """Test feed endpoint responds in under 3 seconds"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        times = []
        
        for _ in range(5):
            start = time.time()
            response = requests.get(
                f"{api_base_url}/api/stories/feed?limit=20",
                headers=headers,
                timeout=30
            )
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            
            assert response.status_code == 200
        
        avg_time = statistics.mean(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]
        
        print(f"📊 Feed endpoint - Avg: {avg_time:.0f}ms, P95: {p95_time:.0f}ms")
        
        # Feed should respond in under 3 seconds even with cold start
        assert avg_time < 3000, f"Feed endpoint too slow: {avg_time:.0f}ms avg"
    
    def test_auth_rejection_fast(self, api_base_url):
        """Test that auth rejection is fast (no unnecessary processing)"""
        times = []
        
        for _ in range(5):
            start = time.time()
            response = requests.get(
                f"{api_base_url}/api/stories/feed",
                headers={'Authorization': 'Bearer invalid_token'},
                timeout=10
            )
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            
            assert response.status_code in [401, 403]
        
        avg_time = statistics.mean(times)
        
        print(f"📊 Auth rejection - Avg: {avg_time:.0f}ms")
        
        # Auth rejection should be fast
        assert avg_time < 1000, f"Auth rejection too slow: {avg_time:.0f}ms avg"


@pytest.mark.performance
class TestConcurrentRequests:
    """Test API handles concurrent requests"""
    
    def test_concurrent_health_checks(self, api_base_url):
        """Test 10 concurrent health check requests"""
        def make_request():
            start = time.time()
            response = requests.get(f"{api_base_url}/health", timeout=10)
            elapsed = time.time() - start
            return {
                'status': response.status_code,
                'time': elapsed
            }
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in as_completed(futures)]
        
        # All should succeed
        success_count = sum(1 for r in results if r['status'] == 200)
        times = [r['time'] * 1000 for r in results]
        
        print(f"📊 10 concurrent health - {success_count}/10 success, avg {statistics.mean(times):.0f}ms")
        
        assert success_count >= 9, f"Only {success_count}/10 succeeded"
    
    def test_concurrent_feed_requests(self, api_base_url, auth_token):
        """Test 5 concurrent feed requests"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        def make_request():
            start = time.time()
            response = requests.get(
                f"{api_base_url}/api/stories/feed?limit=10",
                headers=headers,
                timeout=30
            )
            elapsed = time.time() - start
            return {
                'status': response.status_code,
                'time': elapsed,
                'stories': len(response.json()) if response.status_code == 200 else 0
            }
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [f.result() for f in as_completed(futures)]
        
        success_count = sum(1 for r in results if r['status'] == 200)
        times = [r['time'] * 1000 for r in results]
        
        print(f"📊 5 concurrent feed - {success_count}/5 success, avg {statistics.mean(times):.0f}ms")
        
        assert success_count >= 4, f"Only {success_count}/5 succeeded"


@pytest.mark.performance
class TestAsyncLoad:
    """Test API under async load"""
    
    @pytest.mark.asyncio
    async def test_async_burst_requests(self, api_base_url, auth_token):
        """Test burst of 20 async requests"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        async def fetch(session, url):
            start = time.time()
            try:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    await response.json()
                    return {
                        'status': response.status,
                        'time': time.time() - start
                    }
            except Exception as e:
                return {
                    'status': 'error',
                    'time': time.time() - start,
                    'error': str(e)
                }
        
        url = f"{api_base_url}/api/stories/feed?limit=5"
        
        async with aiohttp.ClientSession() as session:
            tasks = [fetch(session, url) for _ in range(20)]
            results = await asyncio.gather(*tasks)
        
        success_count = sum(1 for r in results if r.get('status') == 200)
        times = [r['time'] * 1000 for r in results if r.get('status') == 200]
        
        if times:
            print(f"📊 20 async burst - {success_count}/20 success")
            print(f"   Avg: {statistics.mean(times):.0f}ms, P95: {sorted(times)[int(len(times)*0.95)]:.0f}ms")
        
        # Allow some failures under burst load, but majority should succeed
        assert success_count >= 15, f"Only {success_count}/20 succeeded under burst"
    
    @pytest.mark.asyncio
    async def test_sustained_load(self, api_base_url, auth_token):
        """Test sustained load over 10 seconds"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        results = []
        start_time = time.time()
        duration = 10  # seconds
        
        async def fetch(session, url):
            req_start = time.time()
            try:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    await response.json()
                    return {
                        'status': response.status,
                        'time': time.time() - req_start
                    }
            except Exception as e:
                return {
                    'status': 'error',
                    'time': time.time() - req_start
                }
        
        url = f"{api_base_url}/api/stories/feed?limit=5"
        
        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < duration:
                # 2 concurrent requests per second
                tasks = [fetch(session, url) for _ in range(2)]
                batch_results = await asyncio.gather(*tasks)
                results.extend(batch_results)
                await asyncio.sleep(0.5)  # ~2 req/sec
        
        success_count = sum(1 for r in results if r.get('status') == 200)
        total_requests = len(results)
        success_rate = (success_count / total_requests) * 100 if total_requests > 0 else 0
        
        times = [r['time'] * 1000 for r in results if r.get('status') == 200]
        
        print(f"📊 Sustained load test ({duration}s)")
        print(f"   Total requests: {total_requests}")
        print(f"   Success rate: {success_rate:.1f}%")
        if times:
            print(f"   Avg response: {statistics.mean(times):.0f}ms")
        
        assert success_rate >= 90, f"Success rate too low: {success_rate:.1f}%"


@pytest.mark.performance
class TestMemoryAndCaching:
    """Test caching and memory efficiency"""
    
    def test_repeated_requests_consistent(self, api_base_url, auth_token):
        """Test that repeated requests return consistent data"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        results = []
        for _ in range(5):
            response = requests.get(
                f"{api_base_url}/api/stories/feed?limit=10",
                headers=headers,
                timeout=30
            )
            assert response.status_code == 200
            results.append(response.json())
        
        # First story ID should be consistent (sorted by last_updated)
        first_ids = [r[0]['id'] if len(r) > 0 else None for r in results]
        
        # At least 4/5 should have same first ID (allowing for updates)
        from collections import Counter
        most_common_id, count = Counter(first_ids).most_common(1)[0]
        
        assert count >= 4, \
            f"Feed results inconsistent - first ID varies: {first_ids}"
        
        print(f"✅ Feed results consistent across 5 requests")
    
    def test_etag_caching_works(self, api_base_url, auth_token):
        """Test that ETag caching works if implemented"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        # First request
        response1 = requests.get(
            f"{api_base_url}/api/stories/feed?limit=5",
            headers=headers,
            timeout=30
        )
        
        assert response1.status_code == 200
        
        # Check if ETag is returned
        etag = response1.headers.get('ETag')
        
        if etag:
            # Second request with If-None-Match
            headers['If-None-Match'] = etag
            response2 = requests.get(
                f"{api_base_url}/api/stories/feed?limit=5",
                headers=headers,
                timeout=30
            )
            
            # Should return 304 Not Modified or 200 with data
            assert response2.status_code in [200, 304], \
                f"Unexpected status with ETag: {response2.status_code}"
            
            if response2.status_code == 304:
                print("✅ ETag caching working - 304 Not Modified")
            else:
                print("ℹ️ Content changed since last request")
        else:
            print("ℹ️ ETag not implemented for caching")


@pytest.mark.performance
class TestEndpointSpecificPerformance:
    """Test performance of specific endpoints"""
    
    def test_search_endpoint_performance(self, api_base_url, auth_token):
        """Test search endpoint response time"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        start = time.time()
        response = requests.get(
            f"{api_base_url}/api/stories/search?q=technology&limit=10",
            headers=headers,
            timeout=30
        )
        elapsed = (time.time() - start) * 1000
        
        if response.status_code == 404:
            print("ℹ️ Search endpoint not available")
            return
        
        assert response.status_code == 200
        
        print(f"📊 Search endpoint: {elapsed:.0f}ms")
        
        # Search should be reasonably fast
        assert elapsed < 5000, f"Search too slow: {elapsed:.0f}ms"
    
    def test_admin_metrics_performance(self, api_base_url, auth_token):
        """Test admin metrics endpoint response time"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        start = time.time()
        response = requests.get(
            f"{api_base_url}/api/admin/metrics",
            headers=headers,
            timeout=30
        )
        elapsed = (time.time() - start) * 1000
        
        if response.status_code in [403, 401]:
            print("ℹ️ Admin endpoint requires admin privileges")
            return
        
        assert response.status_code == 200
        
        print(f"📊 Admin metrics endpoint: {elapsed:.0f}ms")
        
        # Admin metrics involves DB queries, allow more time
        assert elapsed < 10000, f"Admin metrics too slow: {elapsed:.0f}ms"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

