# Entur SX Integration - Changes Summary

## Major Changes Made

### 1. HACS Configuration ✅
- Added `hacs.json` for HACS compatibility
- Added GitHub Actions workflow (`.github/workflows/validate.yaml`) for HACS validation

### 2. Removed `include_future` Filter ✅
**Why:** Instead of filtering on-the-fly, we now collect ALL relevant deviations and add status indicators.

**Changes:**
- Removed `CONF_INCLUDE_FUTURE` constant
- Removed `include_future` parameter from API client
- Removed from config flow (user step)
- Removed from integration initialization
- Removed from strings/translations

### 3. Added Status Indicators ✅
**New status attribute with three values:**
- `open` - Deviation is currently active
- `planned` - Deviation is scheduled but hasn't started yet
- `expired` - Deviation has ended or been resolved

**Logic:**
```python
# If API marks as closed, it's expired
if progress == "closed":
    status = "expired"
elif now < start_time:
    status = "planned"
elif end_time and now > end_time:
    status = "expired"
else:
    status = "open"
```

**Note:** Expired situations (including `Progress=closed`) remain visible until the API stops returning them. This provides context about recently resolved situations.

### 4. Added Start and End Times ✅
**New attributes:**
- `valid_from` - When deviation starts (ISO timestamp)
- `valid_to` - When deviation ends (ISO timestamp, may be null)

### 5. Lowercase Progress Comparison ✅
**Problem:** API sometimes returns "OPEN", sometimes "open", sometimes "closed"

**Solution:**
```python
progress = element.get("Progress", "")
progress_lower = progress.lower()

# Lowercase comparison
if progress_lower == "closed":
    continue
```

**Benefits:**
- Handles API inconsistencies
- Future-proof against API changes
- Still stores original `progress` value in attributes for reference

### 6. Enhanced Attributes ✅
**All sensor attributes now include:**
```python
{
  "valid_from": "2025-10-16T10:00:00+00:00",
  "valid_to": "2025-10-16T14:00:00+00:00",  # or null
  "description": "Full description of deviation",
  "status": "open",  # or "planned" or "expired"
  "progress": "OPEN",  # Raw API value for reference
  "line_ref": "SKY:Line:1",
  "all_deviations": [...],  # If multiple exist
  "total_deviations": 2,
  "deviations_by_status": {
    "open": 1,
    "planned": 1
  }
}
```

## Use Cases Enabled

### 1. Filter by Status in Automations
```yaml
# Alert only on active deviations
trigger:
  - platform: state
    entity_id: sensor.entur_sx_sky_line_1
    attribute: status
    to: "open"
```

### 2. Advance Warnings
```yaml
# Get notified about planned disruptions
trigger:
  - platform: state
    entity_id: sensor.entur_sx_sky_line_1
    attribute: status
    to: "planned"
```

### 3. Show Duration
```yaml
# Display start and end times in cards
Valid from: {{ state_attr('sensor.entur_sx_sky_line_1', 'valid_from') }}
Valid to: {{ state_attr('sensor.entur_sx_sky_line_1', 'valid_to') }}
```

### 4. Conditional Visibility
```yaml
# Only show card for active deviations
conditions:
  - condition: template
    value_template: "{{ state_attr('sensor.entur_sx_sky_line_1', 'status') == 'open' }}"
```

## Files Changed

### New Files:
- `hacs.json`
- `.github/workflows/validate.yaml`

### Modified Files:
- `custom_components/entur_sx/const.py` - Removed include_future, added status constants
- `custom_components/entur_sx/api.py` - Enhanced parsing with status logic, lowercase comparison
- `custom_components/entur_sx/__init__.py` - Removed include_future parameter
- `custom_components/entur_sx/config_flow.py` - Removed include_future from UI
- `custom_components/entur_sx/sensor.py` - Enhanced attributes
- `custom_components/entur_sx/strings.json` - Removed include_future
- `custom_components/entur_sx/translations/en.json` - Removed include_future
- `README_new.md` - Updated documentation with new features

## Testing Checklist

- [ ] Install via HACS
- [ ] Run GitHub Actions validation
- [ ] Add integration through UI
- [ ] Verify operators load from API
- [ ] Verify lines load for operator
- [ ] Check sensor creation
- [ ] Verify status attribute appears
- [ ] Test with planned deviation (if available)
- [ ] Test with expired deviation
- [ ] Verify lowercase progress handling
- [ ] Check all_deviations attribute
- [ ] Test automations with status triggers

## Breaking Changes from AppDaemon Version

1. **No `include_future` configuration option**
   - Migration: Remove from automations, use `status` attribute instead
   
2. **Entity naming changed**
   - Old: `sensor.sky_line_1`
   - New: `sensor.entur_sx_sky_line_1`

3. **Attribute structure enhanced**
   - Added: `status`, `valid_to`, `progress`, `total_deviations`, `deviations_by_status`

## Benefits

✅ More flexible - filter by status in automations instead of config
✅ Better visibility - see planned, current, and expired deviations
✅ More robust - handles API changes (lowercase progress)
✅ Richer data - start and end times for all deviations
✅ Better UX - count deviations by status
