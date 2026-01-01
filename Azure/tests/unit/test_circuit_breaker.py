"""
Unit tests for Circuit Breaker pattern in RSS Worker

Tests the circuit breaker logic that prevents hammering failing feeds.
"""
import pytest
import asyncio
from datetime import datetime, timezone, timedelta
import sys
import os

# Skip all tests if azure.servicebus is not installed
pytest.importorskip("azure.servicebus", reason="azure-servicebus not installed")

# Add rss-worker to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../rss-worker')))


@pytest.mark.unit
class TestCircuitBreakerLogic:
    """Test circuit breaker state machine logic"""
    
    def test_initial_state_allows_requests(self):
        """Test that new feeds are allowed by default"""
        from worker import CircuitBreaker
        
        cb = CircuitBreaker(threshold=3, timeout_minutes=30)
        
        # New feed should be allowed
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(cb.should_allow('test_feed'))
        loop.close()
        
        assert result is True
    
    def test_circuit_opens_after_threshold_failures(self):
        """Test circuit opens after hitting failure threshold"""
        from worker import CircuitBreaker
        
        cb = CircuitBreaker(threshold=3, timeout_minutes=30)
        loop = asyncio.new_event_loop()
        
        # Record 3 failures
        for i in range(3):
            is_open = loop.run_until_complete(cb.record_failure('test_feed'))
        
        # After 3 failures, circuit should be open
        assert is_open is True
        
        # Requests should now be blocked
        allowed = loop.run_until_complete(cb.should_allow('test_feed'))
        assert allowed is False
        
        loop.close()
    
    def test_circuit_stays_closed_under_threshold(self):
        """Test circuit stays closed with fewer failures than threshold"""
        from worker import CircuitBreaker
        
        cb = CircuitBreaker(threshold=3, timeout_minutes=30)
        loop = asyncio.new_event_loop()
        
        # Record 2 failures (below threshold)
        for i in range(2):
            is_open = loop.run_until_complete(cb.record_failure('test_feed'))
        
        # Circuit should still be closed
        assert is_open is False
        
        # Requests should still be allowed
        allowed = loop.run_until_complete(cb.should_allow('test_feed'))
        assert allowed is True
        
        loop.close()
    
    def test_success_resets_circuit(self):
        """Test that success resets the circuit breaker"""
        from worker import CircuitBreaker
        
        cb = CircuitBreaker(threshold=3, timeout_minutes=30)
        loop = asyncio.new_event_loop()
        
        # Record failures to open circuit
        for i in range(3):
            loop.run_until_complete(cb.record_failure('test_feed'))
        
        # Verify circuit is open
        allowed = loop.run_until_complete(cb.should_allow('test_feed'))
        assert allowed is False
        
        # Record success
        loop.run_until_complete(cb.record_success('test_feed'))
        
        # Circuit should be closed again
        allowed = loop.run_until_complete(cb.should_allow('test_feed'))
        assert allowed is True
        
        loop.close()
    
    def test_different_feeds_independent(self):
        """Test that different feeds have independent circuit states"""
        from worker import CircuitBreaker
        
        cb = CircuitBreaker(threshold=3, timeout_minutes=30)
        loop = asyncio.new_event_loop()
        
        # Open circuit for feed1
        for i in range(3):
            loop.run_until_complete(cb.record_failure('feed1'))
        
        # feed1 should be blocked
        assert loop.run_until_complete(cb.should_allow('feed1')) is False
        
        # feed2 should still be allowed
        assert loop.run_until_complete(cb.should_allow('feed2')) is True
        
        loop.close()
    
    def test_get_status_returns_correct_info(self):
        """Test status reporting"""
        from worker import CircuitBreaker
        
        cb = CircuitBreaker(threshold=3, timeout_minutes=30)
        loop = asyncio.new_event_loop()
        
        # Open circuit for one feed
        for i in range(3):
            loop.run_until_complete(cb.record_failure('failing_feed'))
        
        # Record some activity on another feed
        loop.run_until_complete(cb.record_failure('partial_feed'))
        
        status = cb.get_status()
        
        assert status['total_tracked'] == 2
        assert status['open_circuits'] == 1
        assert 'failing_feed' in status['open_feeds']
        assert 'partial_feed' not in status['open_feeds']
        
        loop.close()


@pytest.mark.unit
class TestCircuitBreakerTimeout:
    """Test circuit breaker timeout/half-open behavior"""
    
    def test_circuit_allows_after_timeout(self):
        """Test that circuit allows requests after timeout expires"""
        from worker import CircuitBreaker
        
        # Use a very short timeout for testing
        cb = CircuitBreaker(threshold=3, timeout_minutes=0)  # 0 minutes = immediate
        loop = asyncio.new_event_loop()
        
        # Open circuit
        for i in range(3):
            loop.run_until_complete(cb.record_failure('test_feed'))
        
        # Manually set last_failure to past to simulate timeout
        cb._states['test_feed'] = (
            3,  # failure count
            datetime.now(timezone.utc) - timedelta(minutes=31),  # past timeout
            True  # circuit open
        )
        
        # After timeout, should allow (half-open state)
        allowed = loop.run_until_complete(cb.should_allow('test_feed'))
        assert allowed is True
        
        loop.close()


@pytest.mark.unit
class TestCircuitBreakerConcurrency:
    """Test circuit breaker thread safety"""
    
    @pytest.mark.asyncio
    async def test_concurrent_failures(self):
        """Test circuit breaker handles concurrent failures correctly"""
        from worker import CircuitBreaker
        
        cb = CircuitBreaker(threshold=5, timeout_minutes=30)
        
        # Simulate 10 concurrent failures
        async def record_failure():
            return await cb.record_failure('concurrent_feed')
        
        tasks = [record_failure() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Circuit should be open after threshold
        assert any(results), "Circuit should have opened"
        
        # Verify state is consistent
        allowed = await cb.should_allow('concurrent_feed')
        assert allowed is False, "Circuit should be open after concurrent failures"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

