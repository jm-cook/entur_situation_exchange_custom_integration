# Throttling Analysis: Multiple Operators Deep Dive

## requestorId Feature Test Results (2025-12-10)

**Test Duration**: 10 minutes (10 polls @ 60s intervals)  
**Conclusion**: ❌ requestorId does NOT provide incremental updates as documented

### Findings:
1. **Alternating Pattern**: API returned full dataset (618KB) and empty responses (1-3KB) alternating
   - Even polls (#2, #4, #5, #7, #9): Full 618KB responses  
   - Odd polls (#3, #6, #8, #10): Empty 1-3KB responses
2. **No Incremental Behavior**: Despite using same requestorId, API did not track state or return only changes
3. **No Session Management**: No clear 5-minute timeout; alternating pattern suggests API bug
4. **Impact**: requestorId feature is **not viable** for reducing API load or supporting global coordinator

### Architecture Decision:
✅ **Phase 1 (Cross-Instance Throttle) is the correct solution**
- Simple, effective, supports up to 4 operators
- No dependency on broken requestorId feature
- Global coordinator would add complexity without benefit

---

## The Real Risk

You're right to be concerned. Here's the actual problem:

### Scenario: 4+ Operators
```
User adds integration instances at 00:00:00:
- Instance 1 (SKY): First poll at 00:00:00, then every 60s
- Instance 2 (RUT): First poll at 00:00:01, then every 60s  
- Instance 3 (ATB): First poll at 00:00:02, then every 60s
- Instance 4 (VKT): First poll at 00:00:03, then every 60s

At 00:01:00 - 00:01:03:
  → 4 requests within 3 seconds
  → All counted within same 1-minute window
  → Exactly at the 4 requests/minute limit
```

**If network latency or retry causes any overlap:** 💥 Rate limit hit

### Config Flow Makes It Worse
Every time user opens config/options:
- Fetches operators list (1 API call)
- Fetches lines for operator (1 API call)
- Both bypass coordinator, go straight to API
- Not tracked in request history

**Example:**
```
00:00:00 - Instance 1 polls (coordinator)
00:00:15 - User opens options for Instance 2
00:00:16 - Fetches operators (config flow)
00:00:17 - Fetches lines (config flow)
00:00:30 - Instance 2 polls (coordinator)
00:00:45 - Instance 3 polls (coordinator)

→ 5 requests in 45 seconds = rate limit exceeded!
```

## Solution Comparison

### Option 1: Cross-Instance Throttle Coordination

**Architecture:**
```python
# Shared singleton in hass.data
hass.data[f"{DOMAIN}_api_lock"] = {
    "last_request_time": None,
    "lock": asyncio.Lock(),
}

class EnturSXDataUpdateCoordinator:
    async def _async_update_data(self):
        # Acquire global lock
        api_lock = self.hass.data[f"{DOMAIN}_api_lock"]
        async with api_lock["lock"]:
            # Ensure 15 seconds since last request
            if api_lock["last_request_time"]:
                elapsed = (datetime.now() - api_lock["last_request_time"]).total_seconds()
                if elapsed < 15:
                    await asyncio.sleep(15 - elapsed)
            
            # Make request
            data = await self.api.async_get_deviations()
            api_lock["last_request_time"] = datetime.now()
            return data
```

**Pros:**
✅ Simple to implement
✅ Works across all coordinators
✅ Prevents rate limiting completely
✅ Each instance still updates every 60s (just with staggered actual API calls)

**Cons:**
❌ **Doesn't scale** - With 10 operators:
  - Each needs 15s gap
  - 10 × 15s = 150 seconds minimum
  - Some coordinators won't get updates within their 60s window
  - Creates cascading delays

❌ **Doesn't help config flow** - Config flow calls bypass coordinator
❌ **Artificial serialization** - Wastes the 4 req/min capacity

**Math:**
- 4 req/min = 1 request every 15 seconds (to stay safe)
- Max sustainable operators = 60s / 15s = **4 operators max**
- Beyond that, delays stack up

### Option 2: Shared Global Coordinator (Your Better Idea!)

**Architecture:**
```python
# Single shared coordinator in hass.data
hass.data[f"{DOMAIN}_global"] = {
    "coordinator": GlobalEnturSXCoordinator(hass),
    "registered_instances": {},  # entry_id -> {operator, lines}
}

class GlobalEnturSXCoordinator(DataUpdateCoordinator):
    """Fetches ALL disruptions once, distributes to instances."""
    
    def __init__(self, hass):
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_global",
            update_interval=timedelta(seconds=60),
        )
        self._api = EnturSXApiClient(operator=None)  # No filter = all operators
    
    async def _async_update_data(self):
        # ONE API call without datasetId filter
        all_data = await self._api.async_get_deviations()
        # Returns disruptions for ALL operators
        return all_data

class EnturSXDataUpdateCoordinator(DataUpdateCoordinator):
    """Per-instance coordinator - filters global data."""
    
    def __init__(self, hass, api, entry_id):
        # Don't poll! Just listen to global coordinator
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry_id}",
            update_interval=None,  # No automatic updates
        )
        self._global_coord = hass.data[f"{DOMAIN}_global"]["coordinator"]
        self._operator = api._operator
        self._lines = api._lines
        
        # Register for global updates
        self._global_coord.async_add_listener(self._handle_global_update)
    
    async def _handle_global_update(self):
        """Called when global coordinator updates."""
        all_data = self._global_coord.data
        
        # Filter to our operator and lines
        filtered_data = {
            line_ref: deviations
            for line_ref, deviations in all_data.items()
            if line_ref.startswith(f"{self._operator}:")
            and line_ref in self._lines
        }
        
        # Update our data
        self.async_set_updated_data(filtered_data)
```

**Pros:**
✅ **Scales perfectly** - 100 operators = still 1 request/minute
✅ **Actually more efficient** - Single API call gets ALL data
✅ **No coordination needed** - Global coordinator is the only one polling
✅ **Works with requestorId** - Can optimize incremental updates
✅ **Config flow still separate** - But less of an issue with lower base load

**Cons:**
❌ **Bigger refactor** - Significant architecture change
❌ **More memory** - Global data includes all operators (but we parse it anyway)
❌ **Shared failure** - If global coordinator fails, all instances fail
❌ **Complexity** - Listener pattern, lifecycle management

**API Response Size:**
Testing needed, but likely:
- Filtered (datasetId=SKY): ~50-100 KB
- Unfiltered (all operators): ~500 KB - 2 MB (?)
- Still acceptable for 60s polling

### Option 3: Hybrid Approach

**Smart throttle with fallback:**
```python
class GlobalRequestManager:
    """Manages API requests across all instances."""
    
    def __init__(self):
        self._lock = asyncio.Lock()
        self._last_requests = deque(maxlen=4)  # Track last 4 requests
        
    async def make_request(self, api_call):
        async with self._lock:
            now = datetime.now()
            
            # Clean old requests (>60s ago)
            while self._last_requests and (now - self._last_requests[0]).total_seconds() > 60:
                self._last_requests.popleft()
            
            # If we've made 4 requests in last 60s, wait
            if len(self._last_requests) >= 4:
                oldest = self._last_requests[0]
                wait_time = 60 - (now - oldest).total_seconds()
                if wait_time > 0:
                    _LOGGER.warning("Rate limit protection: waiting %.1fs", wait_time)
                    await asyncio.sleep(wait_time)
                    now = datetime.now()
            
            # Make request
            result = await api_call()
            self._last_requests.append(now)
            return result
```

**Pros:**
✅ **Dynamic throttling** - Only waits when needed
✅ **Scales to 4 operators** without delays
✅ **Simple to add** - Minimal changes to existing code
✅ **Protects config flow** - Can wrap those calls too

**Cons:**
❌ **Still has 4-operator limit** - Beyond that, delays accumulate
❌ **Doesn't leverage unfiltered API** - Missing optimization opportunity

## Recommendation: Phased Approach

### Phase 1: Immediate (Hybrid Throttle Protection)
Implement global request manager to prevent rate limiting **now**:

```python
# __init__.py
async def async_setup(hass, config):
    hass.data[f"{DOMAIN}_request_manager"] = GlobalRequestManager()
    return True

# coordinator.py
async def _async_update_data(self):
    manager = self.hass.data[f"{DOMAIN}_request_manager"]
    return await manager.make_request(self.api.async_get_deviations)
```

**Result:**
- ✅ Prevents rate limiting for up to 4 operators
- ✅ Minimal code changes
- ✅ Works immediately
- ✅ Protects against config flow overlap

### Phase 2: Future (Global Coordinator)
For users with 5+ operators, implement shared coordinator:

```python
# Detect number of instances
if len(hass.data[DOMAIN]) > 4:
    _LOGGER.info("Multiple operators detected, using shared polling")
    use_global_coordinator = True
```

**Result:**
- ✅ Scales to unlimited operators
- ✅ More efficient API usage
- ✅ Enables requestorId optimization
- ✅ Only adds complexity when needed

## Deep Dive: Why Global Coordinator is Better Long-Term

### Current: Filtered Requests
```
GET /sx?datasetId=SKY   → Returns ~24 lines, ~50KB
GET /sx?datasetId=RUT   → Returns ~30 lines, ~60KB  
GET /sx?datasetId=ATB   → Returns ~25 lines, ~55KB
GET /sx?datasetId=VKT   → Returns ~8 lines, ~20KB

Total: 4 requests, ~185KB total data
```

### Proposed: Unfiltered Request
```
GET /sx                 → Returns ~200 lines, ~800KB

Total: 1 request, 800KB data
```

**Bandwidth trade-off:**
- More data per request
- But WAY fewer requests
- Better for API, better for rate limits

### With requestorId (Incremental Updates)
```
Initial:
GET /sx?requestorId=ha_instance_123
→ Returns all disruptions + requestorId

Subsequent (60s later):
GET /sx?requestorId=ha_instance_123
→ Returns ONLY changes since last request
→ Maybe 10-50KB instead of 800KB
→ Server remembers what we've seen

Total: 1 request every 60s, minimal data after initial fetch
```

**This is the real win!**

## Config Flow Problem

Both solutions miss this:

```python
# config_flow.py
async def async_step_user(self, user_input):
    session = async_get_clientsession(self.hass)
    self._operators = await EnturSXApiClient.async_get_operators(session)
    # ↑ Direct API call, bypasses coordinator

async def async_step_device_name(self, user_input):
    session = async_get_clientsession(self.hass)
    self._available_lines = await EnturSXApiClient.async_get_lines_for_operator(
        session, self._operator
    )
    # ↑ Direct API call, bypasses coordinator
```

**Fix for Phase 1:**
```python
# Wrap config flow calls too
async def async_step_user(self, user_input):
    manager = self.hass.data.get(f"{DOMAIN}_request_manager")
    if manager:
        self._operators = await manager.make_request(
            lambda: EnturSXApiClient.async_get_operators(session)
        )
    else:
        self._operators = await EnturSXApiClient.async_get_operators(session)
```

## Testing the Limits

Want me to create a test to measure actual API response sizes?

```python
async def test_api_response_sizes():
    """Measure response size filtered vs unfiltered."""
    
    # Filtered
    for operator in ["SKY", "RUT", "ATB", "VKT"]:
        response = await fetch(f"/sx?datasetId={operator}")
        print(f"{operator}: {len(response)} bytes")
    
    # Unfiltered
    response = await fetch("/sx")
    print(f"ALL: {len(response)} bytes")
```

This would tell us if global coordinator is practical or if the response is too large.

## Your Call

Which direction do you want to go?

1. **Quick fix (Phase 1)**: Global request manager with 15s spacing - Ready in 30 minutes
2. **Full solution (Phase 2)**: Global coordinator architecture - 2-3 hours work
3. **Test first**: Measure API response sizes to inform decision
4. **Hybrid**: Phase 1 now, Phase 2 later if users hit limits

I'm leaning toward **Phase 1 immediately** because:
- Solves the immediate problem
- Low risk
- Doesn't break anything
- Buys time to test Phase 2 properly
