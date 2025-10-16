"""Sensor platform for Entur Situation Exchange."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_NAME, DOMAIN, STATE_NORMAL
from .coordinator import EnturSXDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Entur SX sensors from a config entry."""
    coordinator: EnturSXDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Get the list of lines to monitor - merge data and options (options takes precedence)
    config_data = {**entry.data, **entry.options}
    lines = config_data.get("lines_to_check", [])

    # Clean up entities for lines that are no longer configured
    entity_registry = er.async_get(hass)
    
    # Get all entities for this config entry
    current_entities = er.async_entries_for_config_entry(
        entity_registry, entry.entry_id
    )
    
    # Build set of expected unique IDs
    expected_unique_ids = {
        f"{entry.entry_id}_{line_ref.replace(':', '_')}" 
        for line_ref in lines
    }
    
    # Remove entities that are no longer configured
    for entity_entry in current_entities:
        if entity_entry.unique_id not in expected_unique_ids:
            _LOGGER.info(
                "Removing entity %s (unique_id: %s) - line no longer configured",
                entity_entry.entity_id,
                entity_entry.unique_id,
            )
            entity_registry.async_remove(entity_entry.entity_id)

    # Create a sensor for each line
    entities = []
    for line_ref in lines:
        # Clean the line name for entity ID (replace : with _)
        line_name = line_ref.replace(":", "_")
        entities.append(EnturSXSensor(coordinator, entry, line_ref, line_name))

    _LOGGER.info("Setting up %d Entur SX sensors", len(entities))
    async_add_entities(entities, False)


class EnturSXSensor(CoordinatorEntity[EnturSXDataUpdateCoordinator], SensorEntity):
    """Sensor for a single Entur transit line deviation status."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EnturSXDataUpdateCoordinator,
        entry: ConfigEntry,
        line_ref: str,
        line_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.line_ref = line_ref
        self.line_name = line_name

        device_name = entry.data.get(CONF_DEVICE_NAME, "Entur Avvik")

        # Unique ID
        self._attr_unique_id = f"{entry.entry_id}_{line_name}"

        # Entity name is the line reference
        self._attr_name = line_ref

        # Device info - all lines belong to the same device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=device_name,
            manufacturer="Entur AS",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://entur.no",
        )

        # Icon
        self._attr_icon = "mdi:bus-alert"

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor (the summary of the most recent deviation)."""
        if not self.coordinator.data:
            return None

        line_data = self.coordinator.data.get(self.line_ref, [])
        if not line_data:
            return None

        # Return the summary of the first (most recent) item
        return line_data[0].get("summary")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional attributes."""
        if not self.coordinator.data:
            return None

        line_data = self.coordinator.data.get(self.line_ref, [])
        if not line_data:
            return None

        # Get the most recent deviation
        current = line_data[0]

        attrs = {
            "valid_from": current.get("valid_from"),
            "valid_to": current.get("valid_to"),
            "description": current.get("description"),
            "status": current.get("status"),
            "progress": current.get("progress"),
            "line_ref": self.line_ref,
        }

        # Include all deviations if there are multiple
        if len(line_data) > 1:
            attrs["all_deviations"] = line_data
            attrs["total_deviations"] = len(line_data)
            
            # Count by status
            status_counts = {}
            for item in line_data:
                status = item.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            attrs["deviations_by_status"] = status_counts

        return attrs
