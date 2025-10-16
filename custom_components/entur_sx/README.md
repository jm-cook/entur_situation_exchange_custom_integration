# Entur Situation Exchange Custom Integration for Home Assistant

This directory contains the Entur Situation Exchange custom integration.

## Structure

- `__init__.py` - Integration setup and entry point
- `manifest.json` - Integration metadata
- `const.py` - Constants and configuration
- `api.py` - API client for Entur Situation Exchange service
- `coordinator.py` - Data update coordinator
- `config_flow.py` - UI configuration flow
- `sensor.py` - Sensor platform implementation
- `strings.json` - UI strings
- `translations/` - Localization files

## Development

To test this integration:

1. Copy the `custom_components/entur_sx` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Add the integration through the UI: Settings → Devices & Services → Add Integration → Entur Situation Exchange

## API Reference

The integration uses the Entur Situation Exchange API:
- Base URL: https://api.entur.io/realtime/v1/rest/sx
- Optional operator filter: `?datasetId={operator}`

## Features

- Async API client with aiohttp
- DataUpdateCoordinator for efficient updates (60 second polling)
- Config flow for UI-based setup
- Proper device and entity registry integration
- Deviation details as sensor attributes
- Support for multiple operators and lines
- Optional future deviation filtering
