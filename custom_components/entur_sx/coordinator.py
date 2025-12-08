"""DataUpdateCoordinator for Entur Situation Exchange."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EnturSXApiClient
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)
_DISRUPTION_LOGGER = logging.getLogger(f"{__name__}.disruptions")


class EnturSXDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Entur SX data."""

    def __init__(self, hass: HomeAssistant, api: EnturSXApiClient) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.api = api
        # Set the session for the API client
        session = async_get_clientsession(hass)
        self.api.set_session(session)
        
        # Track active disruptions to detect changes
        self._previous_disruptions: dict[str, set[str]] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Entur API."""
        try:
            data = await self.api.async_get_deviations()
            _LOGGER.debug("Fetched data for %d lines", len(data))
            
            # Track disruption changes
            self._track_disruption_changes(data)
            
            return data
        except Exception as err:
            _LOGGER.error("Error updating Entur SX data: %s", err)
            raise UpdateFailed(f"Error communicating with Entur API: {err}") from err
    
    def _track_disruption_changes(self, data: dict[str, Any]) -> None:
        """Track when disruptions appear and disappear."""
        current_disruptions: dict[str, set[str]] = {}
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Build current state
        for line_ref, deviations in data.items():
            if not deviations:
                current_disruptions[line_ref] = set()
                continue
            
            # Track unique disruption IDs (summary + status is unique enough)
            disruption_ids = set()
            for dev in deviations:
                summary = dev.get("summary", "")
                status = dev.get("status", "")
                valid_from = dev.get("valid_from", "")
                # Create unique ID
                disruption_id = f"{summary[:50]}|{status}|{valid_from}"
                disruption_ids.add(disruption_id)
            
            current_disruptions[line_ref] = disruption_ids
        
        # Compare with previous state
        for line_ref in current_disruptions:
            current = current_disruptions.get(line_ref, set())
            previous = self._previous_disruptions.get(line_ref, set())
            
            # New disruptions appeared
            new_disruptions = current - previous
            for disruption_id in new_disruptions:
                parts = disruption_id.split("|")
                summary = parts[0] if len(parts) > 0 else "Unknown"
                status = parts[1] if len(parts) > 1 else "unknown"
                valid_from = parts[2] if len(parts) > 2 else ""
                
                _DISRUPTION_LOGGER.info(
                    "[%s] NEW disruption on %s (status: %s) - %s - "
                    "valid from: %s",
                    timestamp,
                    line_ref,
                    status,
                    summary,
                    valid_from,
                )
            
            # Disruptions disappeared
            removed_disruptions = previous - current
            for disruption_id in removed_disruptions:
                parts = disruption_id.split("|")
                summary = parts[0] if len(parts) > 0 else "Unknown"
                status = parts[1] if len(parts) > 1 else "unknown"
                
                _DISRUPTION_LOGGER.info(
                    "[%s] REMOVED disruption from %s (was: %s) - %s",
                    timestamp,
                    line_ref,
                    status,
                    summary,
                )
        
        # Update previous state
        self._previous_disruptions = current_disruptions
