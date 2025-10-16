# Options Flow Fixes

## Issues Fixed

### 1. Deprecated `self.config_entry` Assignment
**Problem:** Home Assistant 2025.12 will deprecate explicitly setting `config_entry` in options flow.

**Error Message:**
```
Detected that custom integration 'entur_sx' sets option flow config_entry explicitly, 
which is deprecated at custom_components/entur_sx/config_flow.py, line 197: 
self.config_entry = config_entry
```

**Solution:** Removed the explicit assignment. The `config_entry` is automatically available via `self.config_entry` from the parent class.

**Changes:**
- Removed line: `self.config_entry = config_entry` from `EnturSXOptionsFlow.__init__()`
- Now uses inherited `self.config_entry` property directly

---

### 2. New Lines Not Getting Added
**Problem:** When adding new lines in the options flow, they weren't being saved properly.

**Root Cause:** The options flow was only checking `entry.data` for current lines, not `entry.options` where updated values are stored.

**Solution:** Check `entry.options` first, then fall back to `entry.data`:

```python
# Check both data and options for current lines (options takes precedence)
current_lines = self.config_entry.options.get(
    CONF_LINES_TO_CHECK,
    self.config_entry.data.get(CONF_LINES_TO_CHECK, [])
)
```

**Why This Works:**
- Initial setup stores lines in `entry.data`
- Options flow updates store lines in `entry.options`
- `__init__.py` merges both: `{**entry.data, **entry.options}` (options override data)
- Now the UI correctly shows the current effective line selection

---

### 3. Operator Sorting
**Problem:** Operators weren't clearly sorted alphabetically by name.

**Solution:** 
- Already sorted by name: `sorted(self._operators.items(), key=lambda x: x[1])`
- Changed label format for clarity: `"Skyss (SKY)"` instead of `"SKY:Authority:SKY - Skyss"`

**Example:**
```
Before: SKY:Authority:SKY - Skyss
After:  Skyss (SKY)
```

---

### 4. Line Sorting
**Problem:** Lines were sorted alphabetically by full display name, which doesn't match user expectations for numbered lines.

**Solution:** Added numeric sorting that extracts the line number and sorts numerically:

```python
def _extract_line_number(line_display_name: str) -> tuple[int, str]:
    """Extract numeric line number for sorting.
    
    Args:
        line_display_name: Display name like "925 - Bergen-Nordheimsund (bus)"
        
    Returns:
        Tuple of (line_number, original_name) for sorting
    """
    match = re.match(r'^(\d+)', line_display_name)
    if match:
        return (int(match.group(1)), line_display_name)
    # If no number, sort alphabetically at the end
    return (999999, line_display_name)
```

**Sorting Examples:**

Before (alphabetical):
```
1 - City Center (bus)
10 - Airport Express (bus)
2 - Harbor Route (bus)
925 - Bergen-Nordheimsund (bus)
```

After (numerical):
```
1 - City Center (bus)
2 - Harbor Route (bus)
10 - Airport Express (bus)
925 - Bergen-Nordheimsund (bus)
```

**Applied To:**
- Initial config flow line selection (`async_step_select_lines`)
- Options flow line reconfiguration (`async_step_init`)

---

## Files Modified

### `custom_components/entur_sx/config_flow.py`

**Imports Added:**
```python
import re  # For line number extraction
```

**New Helper Function:**
```python
def _extract_line_number(line_display_name: str) -> tuple[int, str]:
    """Extract numeric line number for sorting."""
```

**Changes in `EnturSXOptionsFlow.__init__()`:**
- ❌ Removed: `self.config_entry = config_entry`
- ✅ Fixed: Now uses inherited property

**Changes in `EnturSXOptionsFlow.async_step_init()`:**
- ✅ Fixed: Check `entry.options` then `entry.data` for current lines
- ✅ Fixed: Sort lines numerically with `_extract_line_number()`

**Changes in `EnturSXConfigFlow.async_step_select_operator()`:**
- ✅ Improved: Operator label format `"Name (CODE)"`

**Changes in `EnturSXConfigFlow.async_step_select_lines()`:**
- ✅ Fixed: Sort lines numerically with `_extract_line_number()`

---

## Testing Checklist

- [ ] Initial setup: Operators appear sorted alphabetically by name
- [ ] Initial setup: Lines appear sorted numerically by line number
- [ ] Options flow: "Configure" button appears in Devices & Services
- [ ] Options flow: Current line selection is pre-checked
- [ ] Options flow: Can add new lines
- [ ] Options flow: Can remove lines
- [ ] Options flow: Changes persist after save
- [ ] Options flow: Integration reloads with new line selection
- [ ] Options flow: No deprecation warnings in logs
- [ ] Sensors: Update to reflect new line configuration

---

## Implementation Notes

### Why Not Store Options in Data Initially?

Home Assistant convention:
- `entry.data` = Immutable setup configuration (operator, device name)
- `entry.options` = Mutable user preferences (line selection)

This separation allows:
- Initial setup with sensible defaults
- User modifications without recreating the integration
- Clean distinction between "what operator" vs "which lines"

### Why the Merge Pattern?

```python
config_data = {**entry.data, **entry.options}
```

This pattern:
- Starts with initial setup data
- Overlays any user-modified options
- Provides a single unified config to the API client
- Is standard Home Assistant practice

### Numeric Sorting Edge Cases

The `_extract_line_number()` function handles:
- Normal numbered lines: `"925 - Name"` → sorts as 925
- Multi-digit numbers: `"1234 - Name"` → sorts as 1234
- Non-numbered lines: `"Airport Express"` → sorts at end (999999)
- Mixed formats: Works as long as number is at the start

---

## Migration Notes

**For Existing Installations:**

No migration needed! The code handles both old and new formats:

1. Old entries have lines in `entry.data`
2. Options flow first checks `entry.options` (empty for old entries)
3. Falls back to `entry.data` (contains the lines)
4. When user saves, new values go to `entry.options`
5. Merge pattern ensures both work: `{**entry.data, **entry.options}`

This provides backward compatibility without any breaking changes.
