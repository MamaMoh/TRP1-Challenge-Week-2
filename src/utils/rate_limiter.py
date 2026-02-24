"""Rate limiting utilities for OpenAI API calls."""
import time
from typing import Optional
from collections import deque


class RateLimiter:
    """Simple rate limiter using token bucket algorithm."""
    
    def __init__(self, max_calls: int = 60, time_window: int = 60):
        """Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.call_times = deque()
    
    def acquire(self) -> bool:
        """Try to acquire a rate limit slot.
        
        Returns:
            True if call is allowed, False if rate limit exceeded
        """
        now = time.time()
        
        # Remove old call times outside the window
        while self.call_times and self.call_times[0] < now - self.time_window:
            self.call_times.popleft()
        
        # Check if we're at the limit
        if len(self.call_times) >= self.max_calls:
            return False
        
        # Record this call
        self.call_times.append(now)
        return True
    
    def wait_if_needed(self) -> float:
        """Wait if rate limit would be exceeded, return wait time.
        
        Returns:
            Number of seconds waited (0 if no wait needed)
        """
        if self.acquire():
            return 0.0
        
        # Calculate wait time
        now = time.time()
        oldest_call = self.call_times[0]
        wait_time = self.time_window - (now - oldest_call) + 0.1  # Small buffer
        
        if wait_time > 0:
            time.sleep(wait_time)
            # Clean up and record new call
            self.call_times.popleft()
            self.call_times.append(time.time())
            return wait_time
        
        return 0.0


# Global rate limiter instance (60 calls per minute default)
_global_rate_limiter = RateLimiter(max_calls=60, time_window=60)


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return _global_rate_limiter


def set_rate_limit(max_calls: int = 60, time_window: int = 60):
    """Configure global rate limiter.
    
    Args:
        max_calls: Maximum number of calls allowed
        time_window: Time window in seconds
    """
    global _global_rate_limiter
    _global_rate_limiter = RateLimiter(max_calls=max_calls, time_window=time_window)
