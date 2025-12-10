# requestorId Investigation - December 10, 2025

## Summary

Investigated how the Entur SIRI-SX API handles `requestorId` parameter for incremental updates and pagination.

## Key Findings

### 1. requestorId Behavior

**WITHOUT requestorId parameter:**
- API response does NOT include `RequestMessageRef` field
- MoreData flag still works correctly (`<MoreData>true</MoreData>` or `<MoreData>false</MoreData>`)
- No ID is created or returned by the API

**WITH requestorId parameter:**
- API echoes back the provided ID in TWO places:
  1. HTTP Response Header: `requestorid: <your-uuid>`
  2. XML Body: `<RequestMessageRef>your-uuid</RequestMessageRef>`
- The echoed ID is EXACTLY what you provided

### 2. MoreData Location

- `MoreData` flag is in the **XML/JSON body**, NOT in response headers
- Located in: `Siri → ServiceDelivery → MoreData`
- Values: `true` (response truncated) or `false` (complete response)

### 3. Incremental Updates - DOES NOT WORK

Testing revealed that `requestorId` does **NOT** provide incremental updates as initially hoped:

```
Polling every 60 seconds with same requestorId:
- Request 1: 618 KB (full dataset, ~364 situations)
- Request 2: 1-3 KB (empty response)  
- Request 3: 618 KB (full dataset again)
- Request 4: 1-3 KB (empty response)
Pattern: Alternating full/empty responses
```

**Conclusion:** requestorId is NOT useful for reducing API load in normal polling operations.

### 4. Pagination - WORKS PERFECTLY

Testing with `maxSize=50` parameter to force pagination:

```
Using SAME requestorId across multiple requests:
- Request 1: 50 situations (IDs: RUT:740057, RUT:2025-41161-1, ...), MoreData=true
- Request 2: 50 different situations (IDs: KOL:8d3f3791, GCO:6-0-190-26449, ...), MoreData=true  
- Request 3: 50 more situations (IDs: VKT:2883, RUT:2025-41154-2, ...)

Total: 150 unique situations
Overlap: 0 (zero duplicates)
```

**Conclusion:** requestorId DOES work for pagination when `MoreData=true`.

## Implementation Strategy

### Pagination Algorithm

When fetching deviations:

1. Generate a UUID: `requestor_id = str(uuid.uuid4())`
2. Make initial request with `?requestorId={requestor_id}`
3. Parse response and check `MoreData` flag
4. **If MoreData=true:**
   - Make another request with **same requestorId**
   - API returns next batch of situations
   - Merge with previous results
   - Repeat until `MoreData=false`

### Safety Measures

- **Page limit:** 20 pages maximum (prevents infinite loops)
- **Timeout:** 30 seconds total for all pages
- **Logging:**
  - Debug: Page number, count, running total
  - Info: Multi-page completion summary
  - Warning: Max page limit reached

### Code Location

Implemented in: `custom_components/entur_sx/api.py`
- Method: `async_get_deviations()`
- Lines: ~50-140

## Saturday Mystery

The saved `sky_response.xml` from Saturday (when a disruption was missed) shows:
- `<MoreData>false</MoreData>` - response was complete
- No `RequestMessageRef` present (no requestorId was used in that request)

**Conclusion:** The missing disruption was NOT due to truncated response or pagination issues. The mystery remains unsolved.

## Current Status

- Normal operation: ~364 situations for SKY operator
- maxSize default: 1500 (safe margin)
- Extreme weather threshold: If situations exceed ~1500, pagination will activate
- System behavior: Will automatically handle multi-page responses without user intervention

## Testing

All pagination tests passed:
- `test_pagination_implementation.py`: Verified pagination logic
- `test_requestor_deep_dive.py`: Confirmed API echo-back behavior
- `test_more_data.py`: Validated maxSize threshold behavior

## Documentation

API behavior documented in:
- This file
- `notes/THROTTLE_SOLUTION_OPTIONS.md` (requestorId section)
- Code comments in `api.py`
