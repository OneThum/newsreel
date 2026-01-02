"""
Unit tests for Circuit Breaker pattern

Tests the circuit breaker logic that prevents hammering failing feeds.
This is a self-contained test that doesn't require external dependencies.
"""
import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any


# Self-contained CircuitBreaker implementation for testing
# (Matches the production implementation in rss-worker/worker.py)
class CircuitBreaker:
    """
    Circuit breaker pattern to prevent hammering failing feeds.
    
    States:
    - CLOSED: Normal operation, requests allowed
    - OPEN: Feed is failing, requests blocked
    - HALF_OPEN: Testing if feed recovered
    """
    
    def __init__(self, threshold: int = 3, timeout_minutes: int = 30):
        self.threshold = threshold
        self.timeout = timedelta(minutes=timeout_minutes)
        # feed_id -> (failure_count, last_failure_time, is_open)
        self._states: Dict[str, tuple] = {}
        self._lock = asyncio.Lock()
    
    async def record_success(self, feed_id: str):
        """Reset circuit on success"""
        async with self._lock:
            self._states[feed_id] = (0, None, False)
    
    async def record_failure(self, feed_id: str) -> bool:
        """Record failure, return True if circuit is now open"""
        async with self._lock:
            count, _, _ = self._states.get(feed_id, (0, None, False))
            count += 1
            now = datetime.now(timezone.utc)
            
            is_open = count >= self.threshold
            self._states[feed_id] = (count, now, is_open)
            
            return is_open
    
    async def should_allow(self, feed_id: str) -> bool:
        """Check if request should be allowed"""
        async with self._lock:
            if feed_id not in self._states:
                return True
            
            count, last_failure, is_open = self._states[feed_id]
            
            if not is_open:
                return True
            
            # Check if timeout expired (half-open state)
            if last_failure and datetime.now(timezone.utc) - last_failure > self.timeout:
                return True
            
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status for monitoring"""
        open_circuits = [
            feed_id for feed_id, (_, _, is_open) in self._states.items() if is_open
        ]
        return {
            'total_tracked': len(self._states),
            'open_circuits': len(open_circuits),
            'open_feeds': open_circuits[:10]
        }


@pytest.mark.unit
class TestCircuitBreakerLogic:
    """Test circuit breaker state machine logic"""
    
    @pytest.mark.asyncio
    async def test_initial_state_allows_requests(self):
        """Test that new feeds are allowed by default"""
        cb = CircuitBreaker(threshold=3, timeout_minutes=30)
        
        # New feed should be allowed
        result = await cb.should_allow('test_feed')
        assert result is True
    
    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold_failures(self):
        """Test circuit opens after hitting failure threshold"""
        cb = CircuitBreaker(threshold=3, timeout_minutes=30)
        
        # Record 3 failures
        is_open = False
        for i in range(3):
            is_open = await cb.record_failure('test_feed')
        
        # After 3 failures, circuit should be open
        assert is_open is True
        
        # Requests should now be blocked
        allowed = await cb.should_allow('test_feed')
        assert allowed is False
    
    @pytest.mark.asyncio
    async def test_circuit_stays_closed_under_threshold(self):
        """Test circuit stays closed with fewer failures than threshold"""
        cb = CircuitBreaker(threshold=3, timeout_minutes=30)
        
        # Record 2 failures (below threshold)
        is_open = False
        for i in range(2):
            is_open = await cb.record_failure('test_feed')
        
        # Circuit should still be closed
        assert is_open is False
        
        # Requests should still be allowed
        allowed = await cb.should_allow('test_feed')
        assert allowed is True
    
    @pytest.mark.asyncio
    async def test_success_resets_circuit(self):
        """Test that success resets the circuit breaker"""
        cb = CircuitBreaker(threshold=3, timeout_minutes=30)
        
        # Record failures to open circuit
        for i in range(3):
            await cb.record_failure('test_feed')
        
        # Verify circuit is open
        allowed = await cb.should_allow('test_feed')
        assert allowed is False
        
        # Record success
        await cb.record_success('test_feed')
        
        # Circuit should be closed again
        allowed = await cb.should_allow('test_feed')
        assert allowed is True
    
    @pytest.mark.asyncio
    async def test_different_feeds_independent(self):
        """Test that different feeds have independent circuit states"""
        cb = CircuitBreaker(threshold=3, timeout_minutes=30)
        
        # Open circuit for feed1
        for i in range(3):
            await cb.record_failure('feed1')
        
        # feed1 should be blocked
        assert await cb.should_allow('feed1') is False
        
        # feed2 should still be allowed
        assert await cb.should_allow('feed2') is True
    
    @pytest.mark.asyncio
    async def test_get_status_returns_correct_info(self):
        """Test status reporting"""
        cb = CircuitBreaker(threshold=3, timeout_minutes=30)
        
        # Open circuit for one feed
        for i in range(3):
            await cb.record_failure('failing_feed')
        
        # Record some activity on another feed
        await cb.record_failure('partial_feed')
        
        status = cb.get_status()
        
        assert status['total_tracked'] == 2
        assert status['open_circuits'] == 1
        assert 'failing_feed' in status['open_feeds']
        assert 'partial_feed' not in status['open_feeds']


@pytest.mark.unit
class TestCircuitBreakerTimeout:
    """Test circuit breaker timeout/half-open behavior"""
    
    @pytest.mark.asyncio
    async def test_circuit_allows_after_timeout(self):
        """Test that circuit allows requests after timeout expires"""
        # Use a very short timeout for testing
        cb = CircuitBreaker(threshold=3, timeout_minutes=0)  # 0 minutes = immediate
        
        # Open circuit
        for i in range(3):
            await cb.record_failure('test_feed')
        
        # Manually set last_failure to past to simulate timeout
        cb._states['test_feed'] = (
            3,  # failure count
            datetime.now(timezone.utc) - timedelta(minutes=31),  # past timeout
            True  # circuit open
        )
        
        # After timeout, should allow (half-open state)
        allowed = await cb.should_allow('test_feed')
        assert allowed is True
    
    @pytest.mark.asyncio
    async def test_circuit_stays_open_before_timeout(self):
        """Test that circuit stays open before timeout expires"""
        cb = CircuitBreaker(threshold=3, timeout_minutes=30)
        
        # Open circuit
        for i in range(3):
            await cb.record_failure('test_feed')
        
        # Should still be blocked (within timeout)
        allowed = await cb.should_allow('test_feed')
        assert allowed is False


@pytest.mark.unit
class TestCircuitBreakerConcurrency:
    """Test circuit breaker thread safety"""
    
    @pytest.mark.asyncio
    async def test_concurrent_failures(self):
        """Test circuit breaker handles concurrent failures correctly"""
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
    
    @pytest.mark.asyncio
    async def test_concurrent_mixed_operations(self):
        """Test circuit breaker handles mixed concurrent operations"""
        cb = CircuitBreaker(threshold=3, timeout_minutes=30)
        
        async def mixed_operation(feed_id: str, succeed: bool):
            if succeed:
                await cb.record_success(feed_id)
            else:
                await cb.record_failure(feed_id)
            return await cb.should_allow(feed_id)
        
        # Mix of successes and failures
        tasks = [
            mixed_operation('feed_a', False),  # fail
            mixed_operation('feed_a', False),  # fail
            mixed_operation('feed_b', True),   # success
            mixed_operation('feed_a', True),   # success (reset)
            mixed_operation('feed_b', False),  # fail
        ]
        
        await asyncio.gather(*tasks)
        
        # Both feeds should be accessible (feed_a reset, feed_b has 1 failure)
        assert await cb.should_allow('feed_a') is True
        assert await cb.should_allow('feed_b') is True


@pytest.mark.unit
class TestCircuitBreakerEdgeCases:
    """Test circuit breaker edge cases"""
    
    @pytest.mark.asyncio
    async def test_threshold_of_one(self):
        """Test circuit breaker with threshold of 1"""
        cb = CircuitBreaker(threshold=1, timeout_minutes=30)
        
        # Single failure should open circuit
        is_open = await cb.record_failure('sensitive_feed')
        assert is_open is True
        
        allowed = await cb.should_allow('sensitive_feed')
        assert allowed is False
    
    @pytest.mark.asyncio
    async def test_high_threshold(self):
        """Test circuit breaker with high threshold"""
        cb = CircuitBreaker(threshold=100, timeout_minutes=30)
        
        # 50 failures shouldn't open circuit
        for i in range(50):
            is_open = await cb.record_failure('resilient_feed')
            assert is_open is False
        
        allowed = await cb.should_allow('resilient_feed')
        assert allowed is True
    
    @pytest.mark.asyncio
    async def test_empty_feed_id(self):
        """Test circuit breaker with empty feed ID"""
        cb = CircuitBreaker(threshold=3, timeout_minutes=30)
        
        # Empty string is a valid (if unusual) feed ID
        for i in range(3):
            await cb.record_failure('')
        
        assert await cb.should_allow('') is False
        assert await cb.should_allow('other') is True
    
    @pytest.mark.asyncio
    async def test_unicode_feed_id(self):
        """Test circuit breaker with unicode feed ID"""
        cb = CircuitBreaker(threshold=3, timeout_minutes=30)
        
        unicode_id = '日本語フィード_🔥'
        
        for i in range(3):
            await cb.record_failure(unicode_id)
        
        assert await cb.should_allow(unicode_id) is False
        assert await cb.should_allow('normal_feed') is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
