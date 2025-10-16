"""DataUpdateCoordinator for Entur Situation Exchange."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EnturSXApiClient
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


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

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Entur API."""
        try:
            data = await self.api.async_get_deviations()
            _LOGGER.debug("Fetched data for %d lines", len(data))
            return data
        except Exception as err:
            _LOGGER.error("Error updating Entur SX data: %s", err)
            raise UpdateFailed(f"Error communicating with Entur API: {err}") from err
