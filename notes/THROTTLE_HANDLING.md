# Throttle Handling Implementation - December 10, 2025

## Problem

The integration was occasionally hitting 429 "Too Many Requests" errors from the Entur API, causing sensors to become unavailable for exactly 1 minute. This triggered unwanted automations due to state changes.

### Log Evidence
```
2025-12-10 00:05:14.588 ERROR (MainThread) [custom_components.entur_sx.api] Error fetching data from Entur API: 429, message='Too Many Requests', url='https://api.entur.io/realtime/v1/rest/sx?datasetId=SKY'
2025-12-10 00:06:14.679 INFO (MainThread) [custom_components.entur_sx.coordinator] Fetching entur_sx data recovered
```

## Solution Implemented

### 1. Smart Exponential Back-off
- **First throttle**: Wait 2 minutes before retry
- **Second throttle**: Wait 5 minutes (2 × 2.5)
- **Third+ throttle**: Wait 10 minutes (capped at maximum)
- **Auto-reset**: Counter resets after 30 minutes of successful polling

### 2. State Preservation
Instead of sensors becoming "unavailable", the integration:
- Returns cached data from the last successful fetch
- Keeps sensors showing last known disruption state
- Prevents automation triggers from state changes
- Only fails if throttled on very first fetch (no cache)

### 3. Automatic Recovery
- Detects when API accepts requests again
- Logs recovery event
- Resets update interval back to normal (60 seconds)
- Continues normal operation

## Code Changes

### custom_components/entur_sx/const.py
Added back-off configuration constants:
```python
# Back-off configuration for rate limiting
BACKOFF_INITIAL = 120  # 2 minutes on first throttle
BACKOFF_MULTIPLIER = 2.5  # Exponential increase
BACKOFF_MAX = 600  # Max 10 minutes
BACKOFF_RESET_AFTER = 1800  # Reset to normal after 30 min of success
```

### custom_components/entur_sx/coordinator.py

#### Added State Tracking
```python
# Throttle/back-off management
self._throttle_count = 0
self._last_success_time: datetime | None = None
self._in_backoff = False
self._cached_data: dict[str, Any] | None = None
```

#### Enhanced _async_update_data Method
- Catches `aiohttp.ClientResponseError` with status 429
- Calls `_handle_throttle()` for smart back-off
- Caches successful data
- Resets interval and flags on recovery
- Resets throttle count after 30 min of success

#### New _handle_throttle Method
- Increments throttle counter
- Calculates exponential back-off time
- Adjusts coordinator update interval
- Returns cached data to preserve sensor state
- Logs detailed warning with throttle event number

### README.md
Added new "Rate Limiting and Throttle Handling" section documenting:
- How the smart back-off works
- State preservation behavior
- Log messages to expect
- Reasons why throttling might occur
- No manual intervention needed

## Testing

### Back-off Progression Validation
```
Throttle #1: 120s (2.0 min)
Throttle #2: 300s (5.0 min)
Throttle #3: 600s (10.0 min)
Throttle #4: 600s (10.0 min)  ← Stays capped
Throttle #5: 600s (10.0 min)
```

### Test Coverage
Created `tests/test_throttle_backoff.py` with test cases for:
- ✓ Back-off calculation progression
- ✓ Throttle preserves cached state
- ✓ Throttle without cache raises UpdateFailed
- ✓ Recovery resets update interval
- ✓ Throttle count resets after success period

## Expected Behavior After Deployment

### Normal Operation (No Throttling)
- Polls every 60 seconds
- Updates all sensors
- No special logging

### When Throttled (429 Error)
1. **First occurrence**:
   ```
   WARNING: Rate limit hit (429 Too Many Requests) - throttle event #1. 
   Applying 120 second back-off. Will retry after cooldown. 
   Preserving last known state to keep sensors available.
   ```
   - Waits 2 minutes
   - Sensors show last known disruptions
   - No "unavailable" state

2. **If throttled again**:
   - Increases wait time to 5 minutes, then 10 minutes (max)
   - Continues showing cached data
   - Logs throttle event number

3. **Recovery**:
   ```
   INFO: API access recovered after throttling (back-off ended)
   DEBUG: Update interval reset to 60 seconds
   ```
   - Returns to normal 60-second polling
   - Sensors update with fresh data

4. **After 30 min success**:
   - Throttle counter silently resets to 0
   - Next throttle starts at 2-minute back-off again

## Why This Matters

### Before This Fix
- 429 error → UpdateFailed exception raised
- Sensors become "unavailable" immediately
- State change triggers automations
- Retry happens at normal 60s interval
- Could trigger rapid repeated failures

### After This Fix
- 429 error → Smart back-off applied
- Sensors stay available with cached data
- No unwanted automation triggers
- Progressively longer wait times
- Self-healing when API recovers

## Deployment Notes

1. The back-off state is **not persisted** across HA restarts
   - This is intentional - restart resets to clean state
   - Prevents being stuck in long back-off after restart

2. Each integration instance has independent throttle tracking
   - If you have multiple Entur SX integrations (different operators)
   - They each track their own throttle state
   - This is correct since they query different datasets

3. Config flow validations are separate
   - Setup/options flow API calls don't share the coordinator session
   - Won't contribute to coordinator's throttle state
   - Could still independently hit rate limits during setup

## Monitoring

To track throttle events in production, watch for these log messages:

```
# When throttling occurs
custom_components.entur_sx.coordinator: WARNING: Rate limit hit (429 Too Many Requests) - throttle event #N

# When recovering
custom_components.entur_sx.coordinator: INFO: API access recovered after throttling

# When count resets (debug level)
custom_components.entur_sx.coordinator: DEBUG: Resetting throttle count after N seconds of success
```

## Possible Causes of Throttling

Even with 60-second intervals (1 req/min vs 4 req/min limit):
1. **Network retries**: Connection issues causing aiohttp to retry
2. **Multiple instances**: Running integration in test/prod simultaneously
3. **Config flow**: Frequent reconfiguration triggering validations
4. **Shared network**: Other services on same network querying Entur
5. **API-side issues**: Temporary stricter rate limits or API issues

The smart back-off handles all these cases gracefully.
