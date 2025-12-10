# Entur Situation Exchange Custom Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/jm-cook/ha-entur_sx)
[![Validate with HACS](https://github.com/jm-cook/ha-entur_sx/actions/workflows/validate.yaml/badge.svg)](https://github.com/jm-cook/ha-entur_sx/actions/workflows/validate.yaml)
[![GitHub Release](https://img.shields.io/github/release/jm-cook/ha-entur_sx.svg)](https://github.com/jm-cook/ha-entur_sx/releases)
![Project Maintenance](https://img.shields.io/maintenance/yes/2025.svg)

A Home Assistant custom integration for monitoring public transport service deviations from Entur.no.

This integration creates sensors for each monitored transit line, showing the current service status and any active deviations. It integrates directly with Home Assistant without requiring AppDaemon or MQTT.


## What is Entur Situation Exchange?

Entur is a Norwegian government-owned company that operates the national public transport travel planner and sales system, sharing data with anyone who wants it, for free under the NLOD license. The situation-exchange service provides real-time information about service disruptions, delays, and deviations for public transport across Norway. This integration monitors specific transit lines and alerts you when there are issues affecting your regular routes.

Example status message:

<img width="1254" height="331" alt="image" src="https://github.com/user-attachments/assets/4c9749f8-eb2a-47ac-bccf-698e5c74eddf" />

With this integration you can create sensors for just the routes you are interested in monitoring. This is useful if you use the same routes regularly and want a quick update before you leave your home, or you can get a notification on your mobile device.


## Installation

### Installation with HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add the URL: `https://github.com/jm-cook/ha-entur_sx`
6. Select category: "Integration"
7. Click "Add"
8. Search for "Entur Situation Exchange" in HACS
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/entur_sx` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

After installation, add the integration through the Home Assistant UI:

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Entur Situation Exchange"
4. Follow the configuration wizard:

### Step 1: Device Name
   - **Device name**: A descriptive name for this collection of lines (e.g., "Skyss Disruption" or "My Daily Commute")

### Step 2: Select Operator
   - Choose from a list of all Norwegian public transport operators
   - Shows both the operator code (e.g., SKY) and friendly name (e.g., Skyss)
   - Common operators:
     - **SKY** - Skyss (Bergen area)
     - **RUT** - Ruter (Oslo area)
     - **ATB** - AtB (Trondheim area)
     - **KOL** - Kolumbus (Stavanger area)
     - And many more...

### Step 3: Select Lines
   - Choose one or more lines to monitor
   - Shows line numbers with route names and transport mode
   - Example: "1 - Bergen lufthavn Flesland- Lagunen - Byparken (tram)"

The integration will create one sensor for each selected line.

### Finding Line References

The config flow automatically:
- Fetches all available operators from Entur
- Shows operator codes and friendly names
- Fetches all lines for your selected operator
- Displays line numbers, names, and transport modes

You can add multiple monitoring devices for different operators or groups of lines by repeating the process.

## Use

The integration creates one sensor for each monitored line. Each sensor shows:

- **State**: The current status summary (e.g., "Normal service" or description of the deviation)
- **Attributes**:
  - `status`: Current status - `open` (active now), `planned` (scheduled), or `expired` (ended)
  - `valid_from`: When the deviation started/starts (ISO timestamp)
  - `valid_to`: When the deviation ends (ISO timestamp, may be null)
  - `description`: Detailed description of the deviation
  - `progress`: Raw progress value from API (OPEN, CLOSED, etc.)
  - `line_ref`: The line reference
  - `all_deviations`: Array of all deviations if multiple exist
  - `total_deviations`: Count of all deviations
  - `deviations_by_status`: Count of deviations grouped by status

## Features

- 🚌 Monitor multiple transit lines
- 🔄 Automatic updates every 60 seconds
- 🌐 Support for all Norwegian operators
- 📊 Detailed deviation information in attributes
- ⏰ **Status indicators** - planned, open, or expired deviations
- 🕐 **Start and end times** - know exactly when deviations apply
- 🎯 Clean entity IDs based on line references
- 💡 Native Home Assistant integration (no AppDaemon or MQTT required)
- ✨ **Dynamic operator and line discovery** - no need to look up codes manually!
- 🎨 **User-friendly config flow** - select operators and lines from dropdown lists
- 🔍 **Lowercase-safe progress detection** - handles API changes gracefully
- 📝 **Disruption tracking log** - optional detailed logging of when disruptions appear and disappear

## Disruption Tracking Log

The integration can maintain a detailed log of when disruptions appear and disappear from the Entur API. This is useful for:
- Tracking patterns in what disruptions are published to the API
- Comparing with operator websites to identify missing disruptions
- Monitoring the reliability of the data feed

### Enabling Disruption Logging

Add this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    # Regular integration logs (optional - for debugging)
    custom_components.entur_sx: debug
    
    # Disruption tracking log (recommended)
    custom_components.entur_sx.coordinator.disruptions: info
```

Restart Home Assistant after making changes.

### Log Output

The disruption log will show entries like:

```
2025-12-06 20:15:00 INFO (MainThread) [custom_components.entur_sx.coordinator.disruptions] [2025-12-06 20:15:00] NEW disruption on SKY:Line:1 (status: open) - Det er forseinkingar på linja etter driftsst... - valid from: 2025-12-06T18:30:00+01:00

2025-12-06 21:45:00 INFO (MainThread) [custom_components.entur_sx.coordinator.disruptions] [2025-12-06 21:45:00] REMOVED disruption from SKY:Line:1 (was: open) - Det er forseinkingar på linja etter driftsst...
```

### Viewing the Log

**Option 1: Via Home Assistant UI**
1. Go to **Settings** → **System** → **Logs**
2. Filter by `custom_components.entur_sx.coordinator.disruptions`

**Option 2: In home-assistant.log file**
1. Open `/config/home-assistant.log`
2. Search for `custom_components.entur_sx.coordinator.disruptions`

**Option 3: Create a persistent log file** (recommended for long-term tracking)

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.entur_sx.coordinator.disruptions: info
  filters:
    custom_components.entur_sx.coordinator.disruptions:
      - "/config/entur_sx_disruptions.log"
```

Note: The filters option requires Home Assistant 2023.4 or later. For older versions, the disruptions will only appear in the main `home-assistant.log` file.

## Rate Limiting and Throttle Handling

The integration implements smart throttle handling to protect against API rate limits and keep your sensors available during temporary issues.

### How It Works

**Normal Operation:**
- Polls Entur API every 60 seconds (well within the 4 requests/minute limit)
- Each successful update refreshes all monitored lines

**If Rate Limited (429 Error):**
1. **Smart Back-off**: Automatically increases polling interval
   - First throttle: waits 2 minutes before retry
   - Repeated throttles: exponentially increases to max 10 minutes
   - Resets to normal (60s) after 30 minutes of successful polling
   
2. **State Preservation**: Sensors **stay available** showing last known data
   - No "unavailable" state during cooldown period
   - Prevents unwanted automation triggers
   - Maintains service status visibility

3. **Automatic Recovery**: Resumes normal polling once API accepts requests again

### Log Messages

You'll see these messages if throttling occurs:

```
WARNING: Rate limit hit (429 Too Many Requests) - throttle event #1. Applying 120 second back-off. Will retry after cooldown. Preserving last known state to keep sensors available.

INFO: API access recovered after throttling (back-off ended)
```

### Why Throttling Might Occur

Even with 60-second intervals, throttling can happen due to:
- Multiple Home Assistant instances using the same API
- Config flow validations during setup/reconfiguration
- Network issues causing request retries
- Shared API quota across your network

The smart back-off ensures the integration handles these situations gracefully without manual intervention.

## Example Dashboard Configuration

### Basic Status Card
```yaml
type: entities
title: Transit Status
entities:
  - entity: sensor.skyss_disruption_sky_line_1
  - entity: sensor.skyss_disruption_sky_line_2
  - entity: sensor.skyss_disruption_sky_line_20
```

### Conditional Card (only show when deviations exist)
```yaml
type: conditional
conditions:
  - condition: state
  entity: sensor.skyss_disruption_sky_line_1
    state_not: Normal service
card:
  type: markdown
  content: >
  ## ⚠️ {{ states('sensor.skyss_disruption_sky_line_1') }}
    
  **Line:** {{ state_attr('sensor.skyss_disruption_sky_line_1', 'line_ref') }}
    
  **Status:** {{ state_attr('sensor.skyss_disruption_sky_line_1', 'status') }}
    
  **Valid from:** {{ state_attr('sensor.skyss_disruption_sky_line_1', 'valid_from') }}
    
  {% if state_attr('sensor.skyss_disruption_sky_line_1', 'valid_to') %}
  **Valid to:** {{ state_attr('sensor.skyss_disruption_sky_line_1', 'valid_to') }}
    {% endif %}
    
    **Description:**
  {{ state_attr('sensor.skyss_disruption_sky_line_1', 'description') }}
```

### Show Only Active (Open) Deviations
```yaml
type: conditional
conditions:
  - condition: template
  value_template: "{{ state_attr('sensor.skyss_disruption_sky_line_1', 'status') == 'open' }}"
card:
  type: markdown
  content: >
    ## 🚨 Active Deviation on Line 1
  {{ states('sensor.skyss_disruption_sky_line_1') }}
```

### Multiple Lines with Icons
```yaml
type: glance
title: My Transit Lines
entities:
  - entity: sensor.skyss_disruption_sky_line_1
    name: Line 1
  - entity: sensor.skyss_disruption_sky_line_2
  - entity: sensor.skyss_disruption_sky_line_20
    name: Line 20
show_state: true
```

## Automations

### Alert on Deviation
```yaml
automation:
  - alias: "Transit Deviation Alert"
    trigger:
      - platform: state
  entity_id: sensor.skyss_disruption_sky_line_1
        attribute: status
        to: "open"
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.state != 'Normal service' }}"
    action:
      - service: notify.mobile_app
        data:
          title: "Transit Deviation - Line 1"
          message: >
            {{ states('sensor.skyss_disruption_sky_line_1') }}
            
            Valid from: {{ state_attr('sensor.skyss_disruption_sky_line_1', 'valid_from') }}
```

### Alert on Planned Deviation (Get Advance Warning)
```yaml
automation:
  - alias: "Planned Transit Deviation Alert"
    trigger:
      - platform: state
  entity_id: sensor.skyss_disruption_sky_line_1
        attribute: status
        to: "planned"
    action:
      - service: notify.mobile_app
        data:
          title: "Upcoming Transit Deviation - Line 1"
          message: >
            Scheduled: {{ states('sensor.skyss_disruption_sky_line_1') }}
            
            Starts: {{ state_attr('sensor.skyss_disruption_sky_line_1', 'valid_from') }}
```

## Migration from AppDaemon

If you're migrating from the AppDaemon version:

1. Install this custom integration
2. Configure it with the same lines you had in `apps.yaml`
3. Update your dashboard cards to use the new entity IDs (format: `sensor.skyss_disruption_{operator}_line_{number}`)
4. Update automations to use the new `status` attribute instead of checking state
5. The MQTT sensors will become unavailable - you can safely remove them
6. Uninstall the AppDaemon app

Key differences:
- **No MQTT broker required**
- **No AppDaemon required**
- Entity IDs follow HA naming conventions: `sensor.skyss_disruption_sky_line_1` instead of `sensor.sky_line_1`
- Attributes are directly on the sensor (no separate attribute topic)
- UI-based configuration (no need to edit YAML files)
- **No `include_future` setting** - all deviations are collected with `status` indicator
- **New attributes**: `status` (planned/open/expired), `valid_to`, `progress`
- **Lowercase-safe progress detection** - handles API changes

## Known Limitations

### Not All Disruptions May Be Available

This integration uses Entur's SIRI-SX (Situation Exchange) API, which is the official public API for service disruptions in Norway. However, some transport operators may publish certain disruptions only to their own websites and not to the Entur API.

**Examples of potentially missing disruptions:**
- Real-time operational delays (short-term delays from incidents)
- Light rail/tram disruptions in some regions
- Very recent disruptions that haven't been published to the API yet

**What you can do:**
- If you notice systematic gaps (e.g., disruptions consistently appearing on the operator's website but not in Home Assistant), please report this to both the operator and to Entur
- For critical routes, consider also monitoring the operator's official website or app as a backup
- The integration shows all data that is published to Entur's public API - any missing disruptions are due to the operator not publishing them to this feed

**Confirmed cases:**
- Skyss (Bergen area): Some Bybane (light rail) disruptions and short-term delays may only appear on [skyss.no/avvik](https://www.skyss.no/avvik/)

This is not a bug in the integration - it correctly retrieves all available data from the official API.

## Troubleshooting

### "Integration not found"
- Ensure folder is named exactly `entur_sx`
- Check it's in `custom_components/entur_sx/`
- Restart Home Assistant

### Sensors show "Unavailable"
- Wait 60 seconds for first update
- Check Home Assistant logs for errors
- Verify line references are correct
- Test the API URL manually: https://api.entur.io/realtime/v1/rest/sx

### Wrong operator data
- Specify the operator filter in configuration
- Use the correct operator code (SKY, RUT, ATB, etc.)

### Missing disruptions that appear on operator's website
- See "Known Limitations" section above
- This is due to operators not publishing all disruptions to Entur's public API
- Contact the operator to request they publish all disruptions to the SIRI-SX feed

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Credits

- Original AppDaemon version by Jeremy Cook
- Converted to native Home Assistant custom integration
- Data provided by [Entur AS](https://entur.no)
