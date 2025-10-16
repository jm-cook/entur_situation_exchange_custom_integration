# Status Logic Improvement - Keeping Closed Situations Visible

## Date: 2025-10-16

## The Change

**Previous behavior:**
- Situations with `Progress=closed` were completely filtered out
- Users never saw resolved situations

**New behavior:**
- Situations with `Progress=closed` are shown with `status=expired`
- Users can see recently resolved situations for context
- Situations naturally disappear when the API stops returning them

## Rationale

### Why Keep Closed Situations?

1. **User Context**: Users benefit from seeing that a situation was recently resolved
   - "The bus delay from this morning is now cleared"
   - "The road closure that affected my commute has been reopened"

2. **Consistent Treatment**: Both types of "ended" situations are now treated the same:
   - `Progress=closed` (formally resolved by operator)
   - `Progress=open` but past `EndTime` (ended but not yet marked closed)
   - Both show as `status=expired`

3. **Natural Lifecycle**: The API handles cleanup for us
   - Closed situations remain in the feed for a few hours
   - They automatically disappear when the API stops returning them
   - No need to manually filter or manage history

4. **User Control**: Users can still filter if they want:
   ```yaml
   # Show only active deviations
   condition: template
   value_template: "{{ state_attr('sensor.line_123', 'status') != 'expired' }}"
   ```

## Implementation

### Code Change (api.py)

```python
# BEFORE - filtered out closed situations
if progress_lower == "closed":
    continue

# AFTER - treat closed as expired
if progress_lower == "closed":
    status = STATUS_EXPIRED
elif now_timestamp < start_timestamp:
    status = STATUS_PLANNED
# ... rest of logic
```

### Status Assignment

| Condition | Status | Explanation |
|-----------|--------|-------------|
| `Progress=closed` | `expired` | Situation has been formally resolved |
| `Progress=open` + before StartTime | `planned` | Planned disruption not yet active |
| `Progress=open` + between Start/End | `open` | Currently active |
| `Progress=open` + after EndTime | `expired` | Ended but not formally closed yet |
| `Progress=open` + no EndTime | `open` | Ongoing with unknown duration |

## Benefits

1. **Better UX**: Users see the full picture including recent resolutions
2. **Transparency**: Clear status indicator shows what's active vs resolved
3. **Flexibility**: Users can choose to filter expired situations if desired
4. **Simplicity**: API manages the lifecycle; we don't need cleanup logic

## Real-World Example

User checks their sensor at 10:00:
```yaml
sensor.line_123:
  state: "1 deviation"
  attributes:
    status: expired
    description: "Bus delayed due to traffic. Delay cleared at 09:45."
    valid_to: "2025-10-16T09:45:00+02:00"
```

By 14:00, the API stops returning this situation, and it naturally disappears from the sensor.

## User Filtering Examples

### Show Only Active Situations
```yaml
automation:
  - condition: template
    value_template: "{{ state_attr('sensor.line_123', 'status') == 'open' }}"
```

### Alert on Active + Planned
```yaml
automation:
  - condition: template
    value_template: "{{ state_attr('sensor.line_123', 'status') in ['open', 'planned'] }}"
```

### Count by Status
```yaml
template:
  - sensor:
      - name: "Active Deviations"
        state: >
          {{ state_attr('sensor.line_123', 'deviations_by_status').get('open', 0) }}
      - name: "Resolved Deviations"
        state: >
          {{ state_attr('sensor.line_123', 'deviations_by_status').get('expired', 0) }}
```

## Alignment with API Specification

Per the [Norwegian SIRI Profile](https://enturas.atlassian.net/wiki/spaces/PUBLIC/pages/637370605/SIRI-SX):

> "Please note that when Progress is set to 'closed' the message is considered expired and should not be presented to the public."

**Our interpretation**: 
- We mark it as `expired` ✅
- We let users decide whether to show it (via filtering) ✅
- We don't permanently store it (it disappears when API removes it) ✅

This is a reasonable enhancement that provides value while staying true to the spec's intent.
