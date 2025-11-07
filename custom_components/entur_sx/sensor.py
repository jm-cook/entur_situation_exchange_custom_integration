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

from .const import (
    CONF_CREATE_SUMMARY_SENSORS,
    CONF_DEVICE_NAME,
    CONF_SUMMARY_ICON,
    DEFAULT_SUMMARY_ICON,
    DOMAIN,
    STATE_NORMAL,
    STATUS_EXPIRED,
    STATUS_OPEN,
    STATUS_PLANNED,
)
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
    
    # Add summary sensor unique ID if enabled
    if config_data.get("create_summary_sensors", False):
        expected_unique_ids.add(f"{entry.entry_id}_summary")
    
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

    # Create summary sensor if configured
    if config_data.get("create_summary_sensors", False):
        entities.append(EnturSXSummarySensor(coordinator, entry, lines))

    _LOGGER.info("Setting up %d Entur SX sensors", len(entities))
    # Update entities immediately with coordinator's existing data before adding
    async_add_entities(entities, True)


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

        # Get the first (most relevant) item
        first_item = line_data[0]
        first_status = first_item.get("status")

        # If there's only one disruption, return its summary
        if len(line_data) == 1:
            return first_item.get("summary")

        # Count how many disruptions have the same status as the first one
        same_status_count = sum(1 for item in line_data if item.get("status") == first_status)

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

        # Different statuses - return the first one's summary
        return first_item.get("summary")

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


class EnturSXSummarySensor(CoordinatorEntity[EnturSXDataUpdateCoordinator], SensorEntity):
    """Summary sensor with markdown-ready content for all monitored lines."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EnturSXDataUpdateCoordinator,
        entry: ConfigEntry,
        lines: list[str],
    ) -> None:
        """Initialize the summary sensor."""
        super().__init__(coordinator)
        self.lines = lines
        
        device_name = entry.data.get(CONF_DEVICE_NAME, "Entur Disruption")
        config_data = {**entry.data, **entry.options}
        icon = config_data.get(CONF_SUMMARY_ICON, DEFAULT_SUMMARY_ICON)

        # Unique ID
        self._attr_unique_id = f"{entry.entry_id}_summary"

        # Entity name
        self._attr_name = "Summary"

        # Icon
        self._attr_icon = icon

        # Device info - belongs to the same device as line sensors
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=device_name,
            manufacturer="Entur AS",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://entur.no",
        )

    @property
    def native_value(self) -> str:
        """Return simple state based on active (open) disruption count."""
        if not self.coordinator.data:
            return STATE_NORMAL

        active_count = 0
        for line_ref in self.lines:
            line_data = self.coordinator.data.get(line_ref, [])
            if line_data and line_data[0].get("summary") != STATE_NORMAL:
                status = line_data[0].get("status")
                # Only count active (open) disruptions in state
                if status == STATUS_OPEN:
                    active_count += 1

        if active_count == 0:
            return STATE_NORMAL
        elif active_count == 1:
            return "1 active disruption"
        else:
            return f"{active_count} active disruptions"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes including separate markdown for active and planned disruptions."""
        if not self.coordinator.data:
            return {
                "total_lines": len(self.lines),
                "active_disruptions": 0,
                "planned_disruptions": 0,
                "normal_lines": len(self.lines),
                "markdown_active": STATE_NORMAL,
                "markdown_planned": "No planned disruptions",
            }

        active_lines = []
        planned_lines = []
        normal = []
        active_details = []
        planned_details = []

        for line_ref in self.lines:
            line_data = self.coordinator.data.get(line_ref, [])
            if not line_data or line_data[0].get("summary") == STATE_NORMAL:
                normal.append(line_ref)
            else:
                first_item = line_data[0]
                status = first_item.get("status")
                
                # Skip expired deviations
                if status == STATUS_EXPIRED:
                    normal.append(line_ref)
                    continue
                
                # Build markdown for this disruption
                line_markdown = f"### {line_ref}\n\n"
                line_markdown += f"**{first_item.get('summary', 'Unknown disruption')}**\n\n"
                
                # Add description
                description = first_item.get('description', '')
                if description:
                    line_markdown += f"{description}\n\n"
                
                # Add validity times
                valid_from = first_item.get('valid_from', '')
                valid_to = first_item.get('valid_to', '')
                line_markdown += f"*From: {valid_from}*"
                if valid_to:
                    line_markdown += f" • *To: {valid_to}*\n\n"
                else:
                    line_markdown += " • *Until further notice*\n\n"
                
                # Add status/progress
                progress = first_item.get('progress', 'unknown')
                line_markdown += f"*Status: {status}* • *Progress: {progress}*\n\n"
                line_markdown += "---\n\n"
                
                # Categorize by status
                if status == STATUS_OPEN:
                    active_lines.append(line_ref)
                    active_details.append(line_markdown)
                elif status == STATUS_PLANNED:
                    planned_lines.append(line_ref)
                    planned_details.append(line_markdown)
                else:
                    # Unknown status - include in active for safety
                    active_lines.append(line_ref)
                    active_details.append(line_markdown)

        # Build markdown for active disruptions
        device_name = self.device_info.get("name", "Transit") if self.device_info else "Transit"
        
        if not active_details:
            markdown_active = STATE_NORMAL
        else:
            markdown_active = f'**<ha-alert alert-type="error"><ha-icon icon="{self._attr_icon}"></ha-icon> {device_name} - Active Disruptions</ha-alert>**\n\n'
            markdown_active += ''.join(active_details)
            if normal or planned_lines:
                markdown_active += f"*{len(normal) + len(planned_lines)} line(s) with normal service*\n"

        # Build markdown for planned disruptions
        if not planned_details:
            markdown_planned = "No planned disruptions"
        else:
            markdown_planned = f'**<ha-alert alert-type="info"><ha-icon icon="{self._attr_icon}"></ha-icon> {device_name} - Planned Disruptions</ha-alert>**\n\n'
            markdown_planned += ''.join(planned_details)
            if normal or active_lines:
                markdown_planned += f"*{len(normal) + len(active_lines)} line(s) with normal service*\n"

        return {
            "total_lines": len(self.lines),
            "active_disruptions": len(active_lines),
            "planned_disruptions": len(planned_lines),
            "normal_lines": len(normal),
            "active_line_refs": active_lines,
            "planned_line_refs": planned_lines,
            "normal_line_refs": normal,
            "markdown_active": markdown_active,
            "markdown_planned": markdown_planned,
        }

