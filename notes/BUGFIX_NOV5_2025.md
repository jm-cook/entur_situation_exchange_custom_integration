# Bug Fix: November 5, 2025 - SKY:Line:1 Disruption Not Detected

## Problem Description

On November 5, 2025, the integration failed to properly display an active disruption for SKY:Line:1. The issue manifested as:

1. **The sensor state showed a future/closed event instead of the active one**
2. **The primary state had an empty/incorrect summary**
3. **An active disruption with `progress: open` was being ignored**

### Raw State Data (from Developer Tools)

```yaml
valid_from: "2025-11-15T15:15:00+01:00"  # Future date (Nov 15)
valid_to: "2025-11-05T18:51:54.301702294+01:00"  # Past date (Nov 5)
status: expired
progress: closed
all_deviations:
  - valid_from: "2025-11-15T15:15:00+01:00"  # THIS was shown as primary (wrong!)
    summary: Nonneseter siste stopp til ca. kl. 17.30
    status: expired
    progress: closed
  - valid_from: "2025-11-05T16:59:00+01:00"  # THIS should have been primary
    valid_to: "2025-11-06T02:23:00+01:00"
    summary: Forseinkingar etter driftsstans
    status: open  # Active disruption!
    progress: open
  - [... 2 more expired events ...]
```

## Root Causes

### Issue 1: Status Determination Logic
The `Progress` field was checked **before** time-based validation in `api.py`:

```python
# OLD (BUGGY) CODE:
if progress_lower == "closed":
    status = STATUS_EXPIRED  # This ran first!
elif now_timestamp < start_timestamp:
    status = STATUS_PLANNED
# ... rest of logic
```

**Problem:** A future event (Nov 15) with `progress=closed` was marked as `expired` instead of `planned`.

### Issue 2: Sorting Strategy
Events were sorted by `valid_from` descending (most recent first):

```python
# OLD (BUGGY) CODE:
items.sort(reverse=True, key=lambda x: x["valid_from"])
```

**Problem:** This put the future event (Nov 15) at position [0], making it the "primary" state, even though an active disruption existed.

## The Fix

### 1. Fixed Status Determination (`api.py` lines ~133-158)

**Time-based logic now takes priority:**

```python
# Determine status primarily based on time validity
if now_timestamp < start_timestamp:
    # Future event - always planned regardless of progress
    status = STATUS_PLANNED
elif end_time:
    end_timestamp = datetime.fromisoformat(end_time).timestamp()
    if now_timestamp > end_timestamp:
        status = STATUS_EXPIRED
    else:
        # Currently active - check Progress field
        if progress_lower == "closed":
            status = STATUS_EXPIRED
        else:
            status = STATUS_OPEN
else:
    # No end time - check Progress field
    if progress_lower == "closed":
        status = STATUS_EXPIRED
    else:
        status = STATUS_OPEN
```

**Key improvement:** Future events are now **always** marked as `PLANNED`, regardless of the `Progress` field value.

### 2. Fixed Sorting Strategy (`api.py` lines ~185-188)

**Now sorts by relevance (status priority), then by time:**

```python
# Sort by relevance: OPEN first, then PLANNED, then EXPIRED
# Within each status group, sort by start time (most recent first)
status_priority = {STATUS_OPEN: 0, STATUS_PLANNED: 1, STATUS_EXPIRED: 2}
items.sort(key=lambda x: (status_priority.get(x["status"], 3), -datetime.fromisoformat(x["valid_from"]).timestamp()))
```

**Key improvement:** Active (`OPEN`) disruptions are now **always** shown first in the list, making them the primary sensor state.

## Expected Behavior After Fix

With the same API data:

1. **Position [0] (Primary state):** The ACTIVE disruption
   - `valid_from: "2025-11-05T16:59:00+01:00"`
   - `status: open`
   - `summary: "Forseinkingar etter driftsstans"`

2. **Position [1]:** The future planned event
   - `valid_from: "2025-11-15T15:15:00+01:00"`
   - `status: planned` (corrected from `expired`)
   - `summary: "Nonneseter siste stopp til ca. kl. 17.30"`

3. **Positions [2], [3]:** Expired events

## Testing

A test file has been created at `tests/test_nov5_bug.py` to verify this fix with the exact data from November 5th.

## Files Modified

- `custom_components/entur_sx/api.py`
  - Lines ~133-158: Status determination logic
  - Lines ~185-188: Sorting logic

## Impact

- ✅ Active disruptions will now be displayed correctly as the primary sensor state
- ✅ Future events with `progress=closed` will be correctly marked as `planned`
- ✅ Users will see the most relevant disruption (active ones) first
- ✅ Historical/expired disruptions will appear after active and planned ones

## Next Steps

1. Test with live disruption data when available
2. Monitor logs for any edge cases
3. Verify sensor state shows active disruptions correctly in Home Assistant UI

---

## Enhancement: Multiple Disruptions with Same Status (November 7, 2025)

### Problem

When a line has **multiple disruptions with the same status** (e.g., 2 OPEN or 2 PLANNED disruptions), only the first one was shown in the sensor's `summary` field (native_value). This made it appear as if only one disruption existed, even though all disruptions were correctly stored in the `all_deviations` attribute.

### Example from SKY:Line:27 (November 6, 2025)

The line had **3 simultaneous disruptions**:
1. **OPEN** - "Fløyfjellstunnelen varsla stengd frå kl. 22.00"
2. **OPEN** - "Glaskar- og Selviktunnelen varsla stengd frå kl. 21.00"
3. **PLANNED** - "Glaskar- og Selviktunnelen varsla stengd frå kl. 00.01"

**Before fix:** Only the first summary was shown: "Fløyfjellstunnelen varsla stengd frå kl. 22.00"

**After fix:** Both OPEN disruptions are combined: "Fløyfjellstunnelen varsla stengd frå kl. 22.00 | Glaskar- og Selviktunnelen varsla stengd frå kl. 21.00"

### Solution

Enhanced the `native_value` property in `sensor.py` (lines ~126-165) to:

1. **Count disruptions with the same status** as the primary (first) disruption
2. **Combine summaries** when multiple disruptions share the same status
3. **Use a separator** (` | `) to make multiple summaries readable
4. **Handle long summaries** by truncating if combined text exceeds 255 characters

```python
# If there are multiple disruptions with the same status, combine them
if same_status_count > 1:
    # Get all summaries for disruptions with the same status
    summaries = [
        item.get("summary", "Unknown disruption")
        for item in line_data
        if item.get("status") == first_status
    ]
    
    # Join with separator for readability
    combined = " | ".join(summaries)
    
    # If the combined summary is too long, use a count instead
    if len(combined) > 255:
        return f"{same_status_count} {first_status} disruptions: {summaries[0]}"
    
    return combined
```

### Benefits

- ✅ Users now see **all active disruptions** in the sensor summary
- ✅ Multiple planned disruptions are also visible
- ✅ The `all_deviations` attribute still contains full details
- ✅ Long summaries are handled gracefully with truncation
- ✅ Backwards compatible - single disruptions work exactly as before

### Files Modified

- `custom_components/entur_sx/sensor.py`
  - Lines ~126-165: Enhanced `native_value` property to combine multiple disruptions

