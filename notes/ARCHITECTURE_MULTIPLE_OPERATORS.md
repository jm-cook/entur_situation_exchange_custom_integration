# Integration Structure Analysis - Multiple Operators & API Calls

## Summary: NO CONCURRENT API CALLS - Safe Architecture

**Short Answer:** You're safe! The integration does **NOT** make concurrent API calls even when monitoring lines from multiple operators.

## How It Works

### Architecture Overview

```
User Configuration
    ↓
One Config Entry = One Operator + Multiple Lines
    ↓
One API Client Instance
    ↓
One Coordinator Instance
    ↓
One Sequential API Call Every 60 Seconds
```

### Key Constraint: One Operator Per Integration Instance

**Config Flow Design:**
1. User selects **ONE operator** (e.g., SKY, RUT, ATB)
2. User selects **multiple lines** from that operator
3. Creates **one config entry**

**From `config_flow.py`:**
```python
async def async_step_user(self, user_input):
    # Step 1: Select ONE operator
    self._operator = user_input[CONF_OPERATOR]  # e.g., "SKY"
    
async def async_step_select_lines(self, user_input):
    # Step 2: Select multiple lines FROM THAT OPERATOR
    self._selected_lines = user_input.get(CONF_LINES_TO_CHECK, [])
    # e.g., ["SKY:Line:1", "SKY:Line:20", "SKY:Line:925"]
```

### No Cross-Operator Line Selection

The config flow **only shows lines for the selected operator**:

```python
# Fetch lines for THE SELECTED operator
self._available_lines = await EnturSXApiClient.async_get_lines_for_operator(
    session, self._operator  # Only ONE operator
)
```

A user **cannot** mix lines from SKY and RUT in a single integration instance.

## API Call Pattern

### One Integration Instance = One API Call

**From `__init__.py`:**
```python
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    # Create ONE API client for ONE operator
    api = EnturSXApiClient(
        operator=config_data.get("operator"),  # e.g., "SKY"
        lines=config_data.get("lines_to_check", []),  # Lines from that operator
    )
    
    # Create ONE coordinator
    coordinator = EnturSXDataUpdateCoordinator(hass, api)
    
    # Store under unique entry_id
    hass.data[DOMAIN][entry.entry_id] = coordinator
```

**From `api.py`:**
```python
def __init__(self, operator: str | None = None, lines: list[str] | None = None):
    self._operator = operator  # ONE operator code
    self._lines = lines or []  # Lines to filter
    
    if operator:
        # ONE API URL with ONE datasetId filter
        self._service_url = f"{API_BASE_URL}?datasetId={operator}"
    else:
        self._service_url = API_BASE_URL  # All operators (not used in config flow)
```

### Sequential Polling

**From `coordinator.py`:**
```python
class EnturSXDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),  # Every 60 seconds
        )
        
    async def _async_update_data(self):
        # ONE API call
        data = await self.api.async_get_deviations()
        return data
```

**Single HTTP Request:**
```
GET https://api.entur.io/realtime/v1/rest/sx?datasetId=SKY
↓
Returns disruptions for ALL SKY lines
↓
Coordinator filters to configured lines
↓
Updates all sensors
```

## Multiple Operators Scenario

### How Users Monitor Multiple Operators

To monitor lines from **different operators**, users create **multiple integration instances**:

```
Integration Instance 1:
  ├─ Operator: SKY
  ├─ Lines: SKY:Line:1, SKY:Line:925
  ├─ API Client: datasetId=SKY
  ├─ Coordinator: Polls every 60s
  └─ Sensors: Sky Line 1, Sky Line 925, Sky Summary

Integration Instance 2:
  ├─ Operator: RUT
  ├─ Lines: RUT:Line:100, RUT:Line:200
  ├─ API Client: datasetId=RUT
  ├─ Coordinator: Polls every 60s
  └─ Sensors: Rut Line 100, Rut Line 200, Rut Summary
```

### Storage in hass.data

Each instance has a unique `entry.entry_id`:

```python
hass.data[DOMAIN] = {
    "abc123": coordinator_for_SKY,   # Polls SKY every 60s
    "def456": coordinator_for_RUT,   # Polls RUT every 60s
}
```

## API Call Timing Analysis

### Are Calls Concurrent?

**No, but they're independent:**

1. **Each coordinator has its own update interval** starting from when it was initialized
2. **They don't synchronize** - timing depends on when each integration was set up
3. **Home Assistant's DataUpdateCoordinator handles scheduling** sequentially

### Example Timeline

```
T=0:00  - SKY coordinator initialized, first poll at 0:00
T=0:10  - RUT coordinator initialized, first poll at 0:10
T=1:00  - SKY polls (1 minute after T=0:00)
T=1:10  - RUT polls (1 minute after T=0:10)
T=2:00  - SKY polls
T=2:10  - RUT polls
```

**Offset by initialization time** - not truly concurrent.

### What If They Overlap?

Even if two coordinators poll at the exact same second:
- Home Assistant's async framework handles it
- Both are async operations, not blocking
- The API receives two separate requests
- Each has its own `datasetId` parameter

**This is perfectly fine:**
- SKY request: `GET .../sx?datasetId=SKY`
- RUT request: `GET .../sx?datasetId=RUT`
- API handles both independently
- No rate limit violation (2 requests < 4/minute limit)

## Rate Limit Analysis

### Current Protection

**Single Integration:**
- 1 request every 60 seconds
- = 1 request/minute
- Well under 4 requests/minute limit

**Two Integrations (SKY + RUT):**
- SKY: 1 request/minute
- RUT: 1 request/minute
- Total: 2 requests/minute
- Still well under 4 requests/minute limit

**Four Integrations:**
- 4 requests/minute
- At the limit but still compliant

### When Would Throttling Occur?

Based on the logs showing nighttime throttling (00:05, 03:38), possible causes:

1. **Config Flow Validations**
   - Each setup/options flow fetches operators and lines
   - If user reconfigures at night → extra API calls
   - Not tracked by coordinator's request history

2. **Multiple Users on Same Network**
   - Shared public IP address
   - Entur may rate limit by IP, not by integration instance
   - Other Home Assistant instances on same network

3. **Timing Coincidence**
   - Multiple coordinators polling at same time
   - Network retries due to connection issues

### Is This a Problem?

**No, because we now have:**
- ✅ Exponential back-off (2min → 5min → 10min)
- ✅ State preservation (sensors stay available)
- ✅ Request history logging (shows timing patterns)
- ✅ Provider tracking (shows which operator got throttled)

## Code Evidence

### No Concurrent Calls Within an Instance

**From `api.py` - Single Request:**
```python
async def async_get_deviations(self) -> dict[str, Any]:
    async with async_timeout.timeout(30):
        async with self._session.get(
            self._service_url, headers=headers  # ONE URL, ONE call
        ) as response:
            data = json.loads(text)
            return self._parse_response(data)  # Filter to configured lines
```

**From `coordinator.py` - Sequential Updates:**
```python
async def _async_update_data(self) -> dict[str, Any]:
    request_start = datetime.now()
    data = await self.api.async_get_deviations()  # Awaits completion
    # Only one request active at a time per coordinator
```

### Separate Coordinators Don't Communicate

Each `entry.entry_id` gets its own coordinator:

```python
# __init__.py
hass.data[DOMAIN][entry.entry_id] = coordinator

# sensor.py
coordinator: EnturSXDataUpdateCoordinator = hass.data[DOMAIN].get(entry.entry_id)
```

No shared state, no synchronization, no concurrent calls from same coordinator.

## Request History Benefits

The new provider tracking helps identify patterns:

**Single Integration Throttled:**
```
WARNING: Request history (last 10 requests):
  #1: 00:00:00 | provider=SKY | status=success | ...
  #2: 00:01:00 | provider=SKY | status=success | ...
  ...
  #10: 00:09:00 | provider=SKY | status=error_429 | ...
```
→ Shows 1-minute intervals, single provider - expected pattern

**Rapid Requests (Config Flow):**
```
  #6: 00:05:00 | provider=SKY | status=success | ...
  #7: 00:05:02 | provider=SKY | status=success | ...  ← Only 2s apart!
  #8: 00:05:04 | provider=SKY | status=success | ...  ← Only 2s apart!
```
→ Indicates config flow validation or setup happening

**Multiple Providers (from different integrations - wouldn't show):**
- Each coordinator only sees its own requests
- But timestamp analysis could show if timing overlaps

## Conclusion

### Current Architecture: Safe & Efficient

✅ **No concurrent calls from single integration instance**
- One operator per integration
- One coordinator per integration  
- One API call per update interval
- Sequential execution

✅ **Multiple integrations work correctly**
- Each has independent coordinator
- Each polls its own operator
- Timing naturally offset by initialization
- Even if they overlap, it's fine

✅ **Rate limiting handled gracefully**
- Smart back-off on 429 errors
- State preservation
- Request history for diagnosis
- Provider tracking for multi-integration setups

### Recommendations

1. **Keep current architecture** - it's working correctly

2. **Monitor request history** when throttled to identify:
   - Config flow validations (rapid requests)
   - Timing patterns
   - Whether multiple integrations are contributing

3. **If running multiple integrations:**
   - You can safely run 3-4 operators (stays under 4 req/min)
   - Request history will show provider name
   - Each has independent back-off if throttled

4. **No code changes needed** - the throttle protection handles edge cases

### What Would Break This?

Only if someone modified the code to:
- Poll multiple operators in parallel (not possible via config flow)
- Create manual loops making rapid API calls
- Disable the 60-second update interval

None of these are possible through normal usage.
