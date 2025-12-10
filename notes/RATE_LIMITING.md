# Rate Limiting Implementation

## Overview
Added comprehensive rate limiting to the Entur SIRI-SX API client to prevent throttling and respect API limits.

## API Rate Limits (from headers)
- **Per-minute limit**: 5 requests/minute (`rate-limit-allowed: 5`)
- **Spike arrest**: 1 request per 100ms minimum (`spike-arrest-allowed: 1 requests per 100 ms`)
- **Response headers**:
  - `rate-limit-allowed`: Total quota per window
  - `rate-limit-available`: Remaining requests in current window
  - `rate-limit-used`: Requests consumed in current window
  - `rate-limit-expiry-time`: When the current window resets

## Implementation Details

### RateLimitTracker Class
New class in `api.py` that tracks rate limits:

```python
class RateLimitTracker:
    - allowed: int = 5        # Quota per minute
    - available: int = 5      # Remaining in current window
    - used: int = 0           # Consumed in current window
    - expiry_time: str        # Window reset time
    - last_request_time: float  # For spike arrest enforcement
    - min_interval_ms: int = 100  # Spike arrest threshold
```

**Key Methods**:
1. `update_from_headers(headers)` - Parse rate limit info from API response
2. `wait_if_needed(delay_ms=200)` - Enforce 200ms delay between requests (safety margin)
3. `can_make_request()` - Check if quota available before making request

### API Client Changes

**Initialization**:
- Added `self._rate_limiter = RateLimitTracker()` to `__init__`

**async_get_deviations() Updates**:
1. **Before each request**: 
   - Check `can_make_request()` - stops pagination if quota exhausted
   - Wait 200ms via `wait_if_needed(delay_ms=200)` to respect spike arrest

2. **After each response**:
   - Parse headers: `update_from_headers(response.headers)`
   - Log rate limit status in debug/info messages

3. **Safety behaviors**:
   - Stop pagination if quota exhausted (logs warning)
   - Include rate limit info in all pagination logs
   - Warn when quota low (≤2 requests remaining)
   - Critical warning when nearly exhausted (≤1 request)

## Safety Margins

### 200ms Inter-Request Delay
- API requires: 100ms minimum (spike arrest)
- Implementation uses: **200ms** (2x safety margin)
- Rationale: Accounts for network jitter, processing time, clock skew

### Quota Checking
- Check `available > 0` before each request
- Stop pagination gracefully if quota exhausted
- Prevents 429 rate limit errors

## Testing

### Test Results (test_rate_limiting.py)
✅ Initial state tracking  
✅ Header parsing (available/allowed/used/expiry)  
✅ Near-limit warnings (≤2 requests)  
✅ Critical warnings (≤1 request)  
✅ Quota exhaustion detection  
✅ Spike arrest enforcement (200ms delays verified)  

**Timing test**:
- First request: 0ms delay (initial)
- Second request: 205ms delay ✓ (expected ~200ms)
- Third request: 406ms delay ✓ (expected ~400ms cumulative)

## Logging Levels

**DEBUG**: Rate limit status on every page
```
Retrieved page 2: 10 situations (total: 20). Rate limit: 3/5 remaining
```

**INFO**: Pagination progress with rate limit
```
MoreData=true, fetching next page (page 2, 20 situations). Rate limit: 3/5
```

**WARNING**: 
- Near quota exhaustion (≤2 requests)
- Quota exhausted during pagination
- Max page limit reached

## Production Scenarios

### Normal Operation (1 request)
- Single API call per update cycle
- Rate limit tracked but no delays needed
- Logs show quota consumption: "4/5 remaining"

### Pagination (2-5 requests)
- 200ms delay between each page fetch
- Quota tracking prevents over-consumption
- Example: 5 pages = 5 requests over 1 second (well under 5/minute limit)

### Extreme Weather (many situations)
- Could trigger 10+ page scenario
- Rate limiter stops at quota exhaustion
- Prevents 429 errors
- User gets partial data + warning log

### Multiple Instances
- Each HA instance has independent rate limit tracker
- Each consumes from shared API quota (5/minute total)
- Future enhancement: Cross-instance coordination (see architecture docs)

## Future Enhancements
1. **Retry with backoff**: Wait until `rate-limit-expiry-time` and retry
2. **Cross-instance coordination**: Shared rate limit state via HA data registry
3. **Adaptive delays**: Increase delay if approaching quota limit
4. **429 handling**: Exponential backoff on rate limit errors

## Files Modified
- `custom_components/entur_sx/api.py` - Added RateLimitTracker class + integration
- `tests/test_rate_limiting.py` - Standalone test suite

## Verification
```bash
python tests/test_rate_limiting.py
```

All tests pass ✅
