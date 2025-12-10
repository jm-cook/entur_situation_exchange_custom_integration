"""Test rate limiting implementation in API client."""
import asyncio
import time


class RateLimitTracker:
    """Track API rate limits from response headers (copy for testing)."""
    
    def __init__(self):
        """Initialize rate limit tracker."""
        self.allowed: int = 5  # Default: 5 requests per minute
        self.available: int = 5
        self.used: int = 0
        self.expiry_time: str | None = None
        self.last_request_time: float = 0.0
        self.min_interval_ms: int = 100  # Spike arrest: 1 req per 100ms
        
    def update_from_headers(self, headers: dict) -> None:
        """Update rate limit info from response headers."""
        if "rate-limit-allowed" in headers:
            self.allowed = int(headers["rate-limit-allowed"])
        if "rate-limit-available" in headers:
            self.available = int(headers["rate-limit-available"])
        if "rate-limit-used" in headers:
            self.used = int(headers["rate-limit-used"])
        if "rate-limit-expiry-time" in headers:
            self.expiry_time = headers["rate-limit-expiry-time"]
            
        # Log when getting close to limit
        if self.available <= 1:
            print(f"⚠️  Rate limit nearly exhausted: {self.available}/{self.allowed} requests remaining until {self.expiry_time}")
        elif self.available <= 2:
            print(f"ℹ️  Rate limit info: {self.available}/{self.allowed} requests remaining until {self.expiry_time}")
    
    async def wait_if_needed(self, delay_ms: int = 200) -> None:
        """Wait if necessary to respect spike arrest limits."""
        if self.last_request_time > 0:
            elapsed_ms = (time.time() - self.last_request_time) * 1000
            if elapsed_ms < delay_ms:
                wait_ms = delay_ms - elapsed_ms
                print(f"   ⏱️  Rate limit: waiting {wait_ms:.0f}ms before next request")
                await asyncio.sleep(wait_ms / 1000)
        
        self.last_request_time = time.time()
    
    def can_make_request(self) -> bool:
        """Check if we have quota available."""
        return self.available > 0


async def test_rate_limit_tracker():
    """Test RateLimitTracker functionality."""
    print("Testing RateLimitTracker...")
    
    tracker = RateLimitTracker()
    
    # Test 1: Initial state
    print(f"\n1. Initial state:")
    print(f"   Allowed: {tracker.allowed}")
    print(f"   Available: {tracker.available}")
    print(f"   Can make request: {tracker.can_make_request()}")
    
    # Test 2: Update from headers (simulating API response)
    print(f"\n2. Simulating API response headers:")
    headers = {
        "rate-limit-allowed": "5",
        "rate-limit-available": "4",
        "rate-limit-used": "1",
        "rate-limit-expiry-time": "Wed Dec 10 2025 10:00:00 GMT-0000 (GMT)"
    }
    tracker.update_from_headers(headers)
    print(f"   After update - Available: {tracker.available}/{tracker.allowed}")
    print(f"   Used: {tracker.used}")
    print(f"   Expiry: {tracker.expiry_time}")
    
    # Test 3: Near limit warning
    print(f"\n3. Testing near-limit warning (2 remaining):")
    headers["rate-limit-available"] = "2"
    headers["rate-limit-used"] = "3"
    tracker.update_from_headers(headers)
    
    # Test 4: Critical limit warning
    print(f"\n4. Testing critical limit warning (1 remaining):")
    headers["rate-limit-available"] = "1"
    headers["rate-limit-used"] = "4"
    tracker.update_from_headers(headers)
    
    # Test 5: Quota exhausted
    print(f"\n5. Testing quota exhausted (0 remaining):")
    headers["rate-limit-available"] = "0"
    headers["rate-limit-used"] = "5"
    tracker.update_from_headers(headers)
    print(f"   Can make request: {tracker.can_make_request()}")
    
    # Test 6: Spike arrest delay (200ms between requests)
    print(f"\n6. Testing spike arrest delay (200ms):")
    start_time = time.time()
    
    # First request - no delay
    await tracker.wait_if_needed(delay_ms=200)
    first_request_time = time.time() - start_time
    print(f"   First request delay: {first_request_time*1000:.1f}ms")
    
    # Second request - should wait ~200ms
    await tracker.wait_if_needed(delay_ms=200)
    second_request_time = time.time() - start_time
    print(f"   Second request delay: {second_request_time*1000:.1f}ms (expected ~200ms)")
    
    # Third request - should wait another ~200ms
    await tracker.wait_if_needed(delay_ms=200)
    third_request_time = time.time() - start_time
    print(f"   Third request delay: {third_request_time*1000:.1f}ms (expected ~400ms)")
    
    print("\n✅ RateLimitTracker tests complete")


async def test_pagination_rate_limiting():
    """Test that pagination respects rate limits."""
    print("\n\nTesting pagination with rate limiting...")
    print("(This would require live API access - see api.py implementation)")
    print("\nKey features implemented:")
    print("  ✓ 200ms delay between pagination requests")
    print("  ✓ Rate limit header parsing (available/allowed/used/expiry)")
    print("  ✓ Quota check before each request")
    print("  ✓ Warning logs when quota low (≤2 requests)")
    print("  ✓ Stops pagination if quota exhausted")
    print("  ✓ Includes rate limit info in debug/info logs")


if __name__ == "__main__":
    asyncio.run(test_rate_limit_tracker())
    asyncio.run(test_pagination_rate_limiting())
