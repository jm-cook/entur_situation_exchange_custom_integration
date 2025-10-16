"""Config flow for Entur Situation Exchange integration."""
from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EnturSXApiClient
from .const import (
    CONF_DEVICE_NAME,
    CONF_LINES_TO_CHECK,
    CONF_OPERATOR,
    DEFAULT_DEVICE_NAME,
    DEFAULT_DEVICE_NAME_SUFFIX,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _extract_line_number(line_display_name: str) -> tuple[int, str]:
    """Extract numeric line number for sorting.
    
    Args:
        line_display_name: Display name like "925 - Bergen-Nordheimsund (bus)"
        
    Returns:
        Tuple of (line_number, original_name) for sorting
    """
    # Try to extract leading number from the display name
    match = re.match(r'^(\d+)', line_display_name)
    if match:
        return (int(match.group(1)), line_display_name)
    # If no number, sort alphabetically at the end
    return (999999, line_display_name)


class EnturSXConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Entur Situation Exchange."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._device_name: str | None = None
        self._operator: str | None = None
        self._operator_name: str | None = None
        self._selected_lines: list[str] = []
        self._operators: dict[str, str] = {}
        self._available_lines: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - select operator."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._operator = user_input[CONF_OPERATOR]
            self._operator_name = self._operators.get(self._operator, "")
            
            # Move to device name step
            return await self.async_step_device_name()

        # Fetch operators
        session = async_get_clientsession(self.hass)
        self._operators = await EnturSXApiClient.async_get_operators(session)
        
        if not self._operators:
            errors["base"] = "cannot_connect"
            return self.async_abort(reason="cannot_connect")

        # Create operator options with friendly names, sorted alphabetically by name
        operator_options = [
            selector.SelectOptionDict(
                value=code,
                label=f"{name} ({code.split(':')[-1]})"
            )
            for code, name in sorted(self._operators.items(), key=lambda x: x[1])
        ]

        data_schema = vol.Schema(
            {
                vol.Required(CONF_OPERATOR): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=operator_options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_device_name(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle device name step - shown after operator selection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._device_name = user_input[CONF_DEVICE_NAME]
            
            # Fetch lines for the selected operator
            session = async_get_clientsession(self.hass)
            self._available_lines = await EnturSXApiClient.async_get_lines_for_operator(
                session, self._operator
            )
            
            if not self._available_lines:
                errors["base"] = "no_lines_found"
            else:
                return await self.async_step_select_lines()

        # Construct default device name: "<Operator> Avvik"
        # e.g., "Skyss Avvik", "Ruter Avvik", etc.
        if self._operator_name:
            default_name = f"{self._operator_name} {DEFAULT_DEVICE_NAME_SUFFIX}"
        else:
            default_name = DEFAULT_DEVICE_NAME

        # Show the form
        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_DEVICE_NAME, default=default_name
                ): str,
            }
        )

        return self.async_show_form(
            step_id="device_name",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "operator": self._operator_name or "",
            },
        )

    async def async_step_select_operator(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle operator selection step (deprecated - redirects to user step)."""
        # This step is kept for backward compatibility but redirects to user step
        return await self.async_step_user(user_input)

    async def async_step_select_lines(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle line selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            selected_lines = user_input.get(CONF_LINES_TO_CHECK, [])
            
            if not selected_lines:
                errors[CONF_LINES_TO_CHECK] = "no_lines"
            else:
                self._selected_lines = selected_lines
                
                # Check if this combination already exists
                unique_id = f"{self._operator}_{'-'.join(sorted(self._selected_lines))}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                
                # Create the entry
                return self.async_create_entry(
                    title=self._device_name or DEFAULT_DEVICE_NAME,
                    data={
                        CONF_DEVICE_NAME: self._device_name,
                        CONF_OPERATOR: self._operator,
                        CONF_LINES_TO_CHECK: self._selected_lines,
                    },
                )

        # Create line options with friendly names, sorted numerically by line number
        line_options = [
            selector.SelectOptionDict(
                value=line_id,
                label=line_name
            )
            for line_id, line_name in sorted(
                self._available_lines.items(), 
                key=lambda x: _extract_line_number(x[1])
            )
        ]

        data_schema = vol.Schema(
            {
                vol.Required(CONF_LINES_TO_CHECK): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=line_options,
                        multiple=True,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="select_lines",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "device_name": self._device_name or "",
                "operator": f"{self._operator} - {self._operators.get(self._operator, '')}"
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return EnturSXOptionsFlow(config_entry)


class EnturSXOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Entur Situation Exchange."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._available_lines: dict[str, str] = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Update the config entry with new line selection
            return self.async_create_entry(
                title="",
                data={
                    CONF_LINES_TO_CHECK: user_input[CONF_LINES_TO_CHECK],
                },
            )

        # Get current operator from config entry
        operator = self.config_entry.data.get(CONF_OPERATOR)
        # Check both data and options for current lines (options takes precedence)
        current_lines = self.config_entry.options.get(
            CONF_LINES_TO_CHECK,
            self.config_entry.data.get(CONF_LINES_TO_CHECK, [])
        )

        # Fetch available lines for the operator
        session = async_get_clientsession(self.hass)
        try:
            self._available_lines = await EnturSXApiClient.async_get_lines_for_operator(
                session, operator
            )
            
            if not self._available_lines:
                errors["base"] = "no_lines"
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Error fetching lines: %s", err)
            errors["base"] = "cannot_connect"

        if errors:
            return self.async_abort(reason=errors.get("base", "unknown"))

        # Create line options with friendly names, sorted numerically by line number
        line_options = [
            selector.SelectOptionDict(
                value=line_id,
                label=line_name
            )
            for line_id, line_name in sorted(
                self._available_lines.items(), 
                key=lambda x: _extract_line_number(x[1])
            )
        ]

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_LINES_TO_CHECK,
                    default=current_lines
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=line_options,
                        multiple=True,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "device_name": self.config_entry.data.get(CONF_DEVICE_NAME, ""),
                "operator_name": self._available_lines.get(list(self._available_lines.keys())[0], "").split("(")[0] if self._available_lines else operator,
            },
        )