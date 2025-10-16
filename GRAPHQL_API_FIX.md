# GraphQL API Fix - October 16, 2025

## Issues Identified

1. **Operator list had "noise"**: Non-transit authorities like "AM008 - AMBU Pendlerrute" were appearing in the operator selection
2. **SKY operator returned no lines**: Selecting "SKY" (Skyss - major Bergen operator) resulted in "No lines found" error
3. **Incorrect authority ID format**: Code was constructing `NSR:Authority:SKY` but API requires `SKY:Authority:SKY`

## Root Causes

### Issue 1: Authority ID Format Mismatch
- The `async_get_operators()` method fetched authorities and extracted the operator code (e.g., `SKY` from `SKY:Authority:SKY`)
- The `async_get_lines_for_operator()` method then constructed `NSR:Authority:{code}` 
- The GraphQL API rejected this format and returned `null`
- The correct format is the **full authority ID** as returned by the authorities query (e.g., `SKY:Authority:SKY`)

### Issue 2: No Filtering of Non-Transit Authorities
- The authorities query returns all types of authorities, not just transit operators
- Some entries like ambulance routes (`MOR:Authority:AM008 - AMBU Pendlerrute`) were included
- No filtering logic was in place to remove these entries

## Solutions Implemented

### 1. Use Full Authority IDs Throughout

**Before:**
```python
# Extract just the code
parts = authority_id.split(":")
operator_code = parts[-1]
operators[operator_code] = authority_name  # Stores: {"SKY": "Skyss"}

# Later, construct wrong format
authority_id = f"NSR:Authority:{operator}"  # Wrong!
```

**After:**
```python
# Store the full authority ID as-is
operators[authority_id] = authority_name  # Stores: {"SKY:Authority:SKY": "Skyss"}

# Use it directly in queries
# No construction needed - use the full ID
```

### 2. Filter Non-Transit Authorities

Added filtering logic in `async_get_operators()`:

```python
# Skip entries without standard Authority pattern
if ":Authority:" not in authority_id:
    continue

# Skip known non-transit authorities (ambulance routes, etc.)
if "AMBU" in authority_name.upper() or authority_id.startswith("MOR:Authority:AM"):
    continue
```

### 3. Updated Fallback List

Changed fallback operator list to use full IDs:

```python
# Before
{"SKY": "Skyss", "RUT": "Ruter", ...}

# After
{"SKY:Authority:SKY": "Skyss", "RUT:Authority:RUT": "Ruter", ...}
```

### 4. Updated GraphQL Query Approach

Changed from `lines(authorities: [...])` query to more reliable `authority(id: ...).lines` query:

```python
query = """
query($authority: String!) {
  authority(id: $authority) {
    id
    name
    lines {
      id
      name
      publicCode
      transportMode
    }
  }
}
"""
```

## Files Modified

- `custom_components/entur_sx/api.py`:
  - `async_get_operators()`: Added filtering logic, store full authority IDs
  - `async_get_lines_for_operator()`: Use full authority ID, updated query structure
  - Updated fallback list with full authority IDs
  - Updated docstrings to reflect parameter changes

## Testing

Created comprehensive test suite (`test_final.py`) that imports and tests the actual `api.py` module:

### Test Results ✅
- ✓ Operators list: 68 authorities (down from 69 - AMBU entry removed)
- ✓ No AMBU or other noise entries in operator list
- ✓ SKY operator found: `SKY:Authority:SKY - Skyss`
- ✓ SKY lines fetched successfully: **329 lines** (previously returned 0)
- ✓ RUT (Oslo/Ruter): **403 lines** found
- ✓ Invalid authority ID handling: Returns empty dict gracefully

### Sample Output
```
TEST 2: Fetching lines for SKY using EnturSXApiClient.async_get_lines_for_operator()
Using authority ID: SKY:Authority:SKY
✓ PASSED - Found 329 lines

First 10 lines:
  SKY:Line:6: 6 - Birkelundstoppen-Lyngbø (bus)
  SKY:Line:5: 5 - Sletten - Fyllingsdalen terminal (bus)
  SKY:Line:2: 2 - Bybane Fyllingsdalen (tram)
  SKY:Line:1: 1 - Bergen lufthavn Flesland- Lagunen - Byparken (tram)
  ...
```

## Impact

### User Experience
- ✅ Config flow operator list is now clean (no AMBU noise)
- ✅ SKY operator (major Bergen transit authority) now works correctly
- ✅ All 329 Skyss lines are available for selection
- ✅ Other major operators (RUT, etc.) continue to work correctly

### Code Quality
- ✅ Correct use of GraphQL API authority IDs
- ✅ Proper filtering of non-transit authorities
- ✅ Better error handling for invalid authority IDs
- ✅ Comprehensive test coverage

## Breaking Changes

⚠️ **Config Flow Storage Format Changed**

The operator field in config entries will now store the **full authority ID** instead of just the code:

- Old format: `"operator": "SKY"`
- New format: `"operator": "SKY:Authority:SKY"`

**Migration Required**: Existing config entries may need to be recreated, or a migration function should be added to the integration's `__init__.py` to convert old operator codes to full authority IDs.

## Recommendations

1. **Test in Home Assistant**: Reload the integration and verify config flow works correctly
2. **Check Existing Entities**: Existing entities with old operator format may need reconfiguration
3. **Monitor Logs**: Watch for any "Authority not found" warnings that might indicate migration issues
4. **Document for Users**: Update README to note that existing integrations should be reconfigured after update

## Next Steps

- [ ] Test the fix in actual Home Assistant environment
- [ ] Add migration code for existing config entries (if needed)
- [ ] Update CHANGES.md with this fix
- [ ] Consider adding unit tests to prevent regression
- [ ] Update README with any necessary user instructions
