# Multiple Situations & Options Flow Fixes - October 16, 2025

## Issues Fixed

### 1. Multiple Situations Lost/Swallowed
**Problem**: When a situation affected multiple lines, only the first affected line was checked. Lines appearing later in the affected lines list were missed.

**Code Issue**:
```python
# OLD CODE - Only checked first line
affected_line = an.get("AffectedLine", [])
line_ref_obj = affected_line[0].get("LineRef", {})  # ❌ Only [0]
```

**Solution**:
```python
# NEW CODE - Check ALL affected lines
affected_lines = an.get("AffectedLine", [])
for affected_line in affected_lines:  # ✓ Iterate through all
    line_ref_obj = affected_line.get("LineRef", {})
    # ... process each line
```

### 2. JSON Parsing Error (Content-Type Mismatch)
**Problem**: API sometimes returns `Content-Type: text/plain;charset=utf-8` even though the body is JSON. aiohttp's `response.json()` is strict about content types and throws an error.

**Error Message**:
```
Attempt to decode JSON with unexpected mimetype: text/plain;charset=utf-8
```

**Solution**:
```python
# OLD CODE
data = await response.json()  # ❌ Strict content-type checking

# NEW CODE
text = await response.text()
import json
data = json.loads(text)  # ✓ Parse manually, ignore content-type
```

### 3. No Options Flow (Can't Modify Lines After Setup)
**Problem**: Once the integration was set up, there was no way to add/remove lines without deleting and recreating the entire integration.

**Solution**: Added `EnturSXOptionsFlow` class that allows users to:
- Open integration settings in Home Assistant UI
- Select/deselect lines for the existing operator
- Changes are applied without recreating the integration

**Files Modified**:
- `config_flow.py`: Added `EnturSXOptionsFlow` class and `async_get_options_flow()` method
- `__init__.py`: Merge options with data, add reload listener for options changes

## Implementation Details

### config_flow.py Changes

Added options flow class:
```python
class EnturSXOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Entur Situation Exchange."""
    
    async def async_step_init(self, user_input):
        # Fetch current operator's lines
        # Show multi-select with current selection as default
        # Update config entry with new line selection
```

Added static method to config flow:
```python
@staticmethod
@callback
def async_get_options_flow(config_entry):
    return EnturSXOptionsFlow(config_entry)
```

### __init__.py Changes

Updated setup to merge data and options:
```python
# Merge data and options for backward compatibility
config_data = {**entry.data, **entry.options}

api = EnturSXApiClient(
    operator=config_data.get("operator"),
    lines=config_data.get("lines_to_check", []),
)
```

Added reload listener:
```python
entry.async_on_unload(entry.add_update_listener(async_reload_entry))

async def async_reload_entry(hass, entry):
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
```

### api.py Changes

Fixed affected lines parsing:
```python
# Check ALL affected lines, not just the first one
for affected_line in affected_lines:
    line_ref_obj = affected_line.get("LineRef", {})
    line_ref = line_ref_obj.get("value")
    
    if look_for == line_ref:
        # ... collect situation
        # Don't break - handle edge case of same line multiple times
```

Fixed JSON parsing:
```python
# Get text first, then parse manually to avoid content-type issues
text = await response.text()
import json
data = json.loads(text)
```

## Testing

### Test Results for Line 925
Using `tests/test_multiple_situations.py`:
- ✓ API client correctly fetches deviations
- ✓ Currently 1 situation affecting line 925 (validated against raw API)
- ✓ Multiple situations would be captured correctly with new code
- ✓ JSON parsing works despite content-type mismatch

### Test for Headers
Using `tests/test_sx_headers.py`:
- ✓ Confirmed `Content-Type: application/json` header triggers JSON response
- ✗ `Accept: application/json` returns text/plain (wrong header!)
- ✓ Current code already uses correct header

## User Experience

### Before:
1. ❌ Only first affected line in multi-line situations was processed
2. ❌ Intermittent JSON parse errors
3. ❌ Had to delete and recreate integration to change lines

### After:
1. ✓ All affected lines in situations are processed
2. ✓ Robust JSON parsing (ignores content-type header)
3. ✓ Can modify lines via integration settings in UI

### How to Use Options Flow:
1. Go to Settings → Devices & Services
2. Find "Entur Situation Exchange" integration
3. Click "Configure" button
4. Select/deselect lines
5. Click "Submit"
6. Integration reloads automatically with new line selection

## Notes

- **Backward Compatibility**: Existing config entries work without changes (data + options merged)
- **Operator Can't Change**: Options flow only allows changing lines, not operator (by design - operator determines available lines)
- **Automatic Reload**: When lines are changed, integration reloads automatically to apply changes

## Files Modified

1. `custom_components/entur_sx/api.py`:
   - Fixed affected lines iteration (loop instead of [0])
   - Fixed JSON parsing (text + json.loads instead of response.json())

2. `custom_components/entur_sx/config_flow.py`:
   - Added `EnturSXOptionsFlow` class
   - Added `async_get_options_flow()` static method

3. `custom_components/entur_sx/__init__.py`:
   - Merge entry.data and entry.options
   - Added reload listener for options changes
   - Added `async_reload_entry()` function

4. Test files created:
   - `tests/test_multiple_situations.py` - Validates situation parsing
   - `tests/test_sx_headers.py` - Tests API content negotiation

## Next Steps

- [ ] Test options flow in Home Assistant UI
- [ ] Verify reload works correctly when changing lines
- [ ] Consider adding option to change operator (would require more complex flow)
- [ ] Add documentation for users on how to modify line selection
