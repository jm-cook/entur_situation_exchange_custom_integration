"""API client for Entur Situation Exchange."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

import aiohttp
import async_timeout

from .const import API_BASE_URL, API_GRAPHQL_URL, CODESPACE_NAMES, STATE_NORMAL, STATUS_EXPIRED, STATUS_PLANNED, STATUS_OPEN

_LOGGER = logging.getLogger(__name__)


class EnturSXApiClient:
    """API client for Entur Situation Exchange."""

    def __init__(
        self,
        operator: str | None = None,
        lines: list[str] | None = None,
    ) -> None:
        """Initialize the API client.
        
        Args:
            operator: Codespace (e.g., "SKY", "SOF")
            lines: List of line IDs to monitor
        """
        self._operator = operator
        self._lines = lines or []
        self._session: aiohttp.ClientSession | None = None

        # The operator is now the codespace directly (e.g., "SKY", "SOF")
        # This is what we use for the SIRI-SX datasetId parameter
        self._operator_code = operator if operator else None
        
        if operator:
            self._service_url = f"{API_BASE_URL}?datasetId={operator}"
        else:
            self._service_url = API_BASE_URL

    def set_session(self, session: aiohttp.ClientSession) -> None:
        """Set the aiohttp session."""
        self._session = session

    async def async_get_deviations(self) -> dict[str, Any]:
        """Fetch deviation data for configured lines.
        
        Returns:
            Dict mapping line reference to list of deviations with status, e.g.
            {"SKY:Line:1": [{"valid_from": "...", "valid_to": "...", "summary": "...", 
                             "description": "...", "status": "open"}]}
        """
        if not self._session:
            _LOGGER.error("Session not set")
            return {}

        headers = {"Content-Type": "application/json"}

        try:
            async with async_timeout.timeout(30):
                async with self._session.get(
                    self._service_url, headers=headers
                ) as response:
                    response.raise_for_status()
                    # API returns JSON but with incorrect content-type header sometimes
                    # Use text() and json.loads() to handle this
                    text = await response.text()
                    import json
                    data = json.loads(text)

                    return self._parse_response(data)

        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout fetching data from Entur API: %s", err)
            raise
        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching data from Entur API: %s", err)
            raise
        except Exception as err:
            _LOGGER.error("Unexpected error fetching Entur data: %s", err, exc_info=True)
            raise

    def _parse_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse the Entur API response.
        
        Args:
            data: JSON response from Entur API
            
        Returns:
            Dict mapping line reference to list of situations with status
        """
        allitems_dict = {}
        now_timestamp = datetime.now().timestamp()

        for look_for in self._lines:
            items = []

            try:
                siri = data.get("Siri", {})
                service_delivery = siri.get("ServiceDelivery", {})
                sx_delivery = service_delivery.get("SituationExchangeDelivery", [])

                for sed in sx_delivery:
                    situations = sed.get("Situations", {})
                    elements = situations.get("PtSituationElement", [])

                    for element in elements:
                        progress = element.get("Progress", "")
                        
                        # Lowercase comparison for progress (API sometimes returns lowercase)
                        progress_lower = progress.lower()

                        affects = element.get("Affects", {})
                        networks = affects.get("Networks")

                        if not networks:
                            continue

                        # Get validity period
                        validity_periods = element.get("ValidityPeriod", [])
                        if not validity_periods:
                            continue

                        validity_period = validity_periods[0]
                        start_time = validity_period.get("StartTime")
                        end_time = validity_period.get("EndTime")
                        
                        if not start_time:
                            continue

                        # Determine status based on time and Progress field
                        start_timestamp = datetime.fromisoformat(start_time).timestamp()
                        
                        # Determine status primarily based on time validity
                        if now_timestamp < start_timestamp:
                            # Future event - always planned regardless of progress
                            status = STATUS_PLANNED
                        elif end_time:
                            end_timestamp = datetime.fromisoformat(end_time).timestamp()
                            if now_timestamp > end_timestamp:
                                # Past the end time - expired
                                status = STATUS_EXPIRED
                            else:
                                # Currently active
                                # Check Progress field - if closed, it's been resolved
                                if progress_lower == "closed":
                                    status = STATUS_EXPIRED
                                else:
                                    status = STATUS_OPEN
                        else:
                            # No end time specified
                            # Check Progress field - if closed, treat as expired
                            if progress_lower == "closed":
                                status = STATUS_EXPIRED
                            else:
                                # No end time and not closed - consider it open if started
                                status = STATUS_OPEN

                        # Check if this situation affects our line
                        affected_networks = networks.get("AffectedNetwork", [])
                        for an in affected_networks:
                            affected_lines = an.get("AffectedLine", [])
                            if not affected_lines:
                                continue

                            # Check ALL affected lines, not just the first one
                            for affected_line in affected_lines:
                                line_ref_obj = affected_line.get("LineRef", {})
                                line_ref = line_ref_obj.get("value")

                                if look_for == line_ref:
                                    # Extract summary and description
                                    summaries = element.get("Summary", [])
                                    descriptions = element.get("Description", [])

                                    summary = summaries[0].get("value") if summaries else STATE_NORMAL
                                    description = descriptions[0].get("value") if descriptions else STATE_NORMAL

                                    items.append({
                                        "valid_from": start_time,
                                        "valid_to": end_time,
                                        "summary": summary,
                                        "description": description,
                                        "status": status,
                                        "progress": progress.lower(),  # Normalize to lowercase
                                    })
                                    # Don't break - a situation might affect the same line multiple times
                                    # (though unlikely, we should handle it)

                # Sort by relevance: OPEN first, then PLANNED, then EXPIRED
                # Within each status group, sort by start time (most recent first)
                if items:
                    status_priority = {STATUS_OPEN: 0, STATUS_PLANNED: 1, STATUS_EXPIRED: 2}
                    items.sort(key=lambda x: (status_priority.get(x["status"], 3), -datetime.fromisoformat(x["valid_from"]).timestamp()))
                else:
                    # No situation for this line, set default
                    items.append({
                        "valid_from": datetime.now().isoformat(),
                        "valid_to": None,
                        "summary": STATE_NORMAL,
                        "description": STATE_NORMAL,
                        "status": STATUS_OPEN,
                        "progress": "normal",
                    })

                allitems_dict[look_for] = items

            except Exception as err:
                _LOGGER.error("Error parsing data for line %s: %s", look_for, err, exc_info=True)
                # Add default entry on error
                allitems_dict[look_for] = [{
                    "valid_from": datetime.now().isoformat(),
                    "valid_to": None,
                    "summary": STATE_NORMAL,
                    "description": STATE_NORMAL,
                    "status": STATUS_OPEN,
                    "progress": "error",
                }]

        _LOGGER.debug("Parsed deviations for %d lines", len(allitems_dict))
        return allitems_dict

    @staticmethod
    async def async_get_operators(session: aiohttp.ClientSession) -> dict[str, str]:
        """Fetch list of operators (codespaces) from Entur GraphQL API.
        
        Extracts all unique 3-letter codespaces from the operators API and maps them
        to friendly names. Falls back to CODESPACE_NAMES constant for better naming.
        
        Returns:
            Dict mapping codespace to display name, e.g. {"SKY": "Skyss (SKY)", "SOF": "Sogn og Fjordane (SOF)"}
        """
        query = """
        query {
          operators {
            id
            name
          }
        }
        """

        headers = {
            "Content-Type": "application/json",
            "ET-Client-Name": "homeassistant-entur-sx",
        }

        try:
            async with async_timeout.timeout(10):
                async with session.post(
                    API_GRAPHQL_URL,
                    json={"query": query},
                    headers=headers,
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

                    all_operators = data.get("data", {}).get("operators", [])
                    
                    # Extract unique codespaces and find best names
                    codespace_names = {}
                    
                    for operator in all_operators:
                        op_id = operator.get("id", "")
                        op_name = operator.get("name", "")
                        
                        if not op_id:
                            continue
                        
                        # Extract codespace (first part before colon)
                        if ":" in op_id:
                            parts = op_id.split(":")
                            codespace = parts[0]
                            
                            # Only include 3-letter uppercase codespaces
                            if len(codespace) == 3 and codespace.isupper():
                                # Prefer canonical operator names (XXX:Operator:XXX)
                                is_canonical = (len(parts) == 3 and 
                                              parts[0] == parts[2] and 
                                              parts[1] == "Operator")
                                
                                if is_canonical or codespace not in codespace_names:
                                    # Use CODESPACE_NAMES if available, otherwise API name
                                    friendly_name = CODESPACE_NAMES.get(codespace, op_name)
                                    codespace_names[codespace] = friendly_name
                    
                    # Build final operator dict with display names
                    operators = {}
                    for codespace in sorted(codespace_names.keys()):
                        friendly_name = codespace_names[codespace]
                        display_name = f"{friendly_name} ({codespace})"
                        operators[codespace] = display_name
                    
                    _LOGGER.debug("Found %d operators from GraphQL API", len(operators))
                    return operators

        except Exception as err:
            _LOGGER.error("Error fetching operators from GraphQL: %s", err, exc_info=True)
            # Fallback to CODESPACE_NAMES constant
            _LOGGER.info("Falling back to CODESPACE_NAMES constant")
            operators = {}
            for codespace, friendly_name in sorted(CODESPACE_NAMES.items()):
                display_name = f"{friendly_name} ({codespace})"
                operators[codespace] = display_name
            return operators

    @staticmethod
    async def async_get_lines_for_operator(
        session: aiohttp.ClientSession, operator: str
    ) -> dict[str, str]:
        """Fetch list of lines for a specific operator (codespace) from Entur GraphQL API.
        
        Args:
            session: aiohttp session
            operator: Codespace (e.g., "SKY", "SOF")
            
        Returns:
            Dict mapping line ref to line name, e.g. {"SKY:Line:1": "Line 1 - Bergen sentrum"}
        """
        # Query all lines and filter by codespace
        # We can't use authority query since we only have the codespace now
        query = """
        query {
          lines {
            id
            name
            publicCode
            transportMode
            authority {
              id
            }
          }
        }
        """

        headers = {
            "Content-Type": "application/json",
            "ET-Client-Name": "homeassistant-entur-sx",
        }

        try:
            async with async_timeout.timeout(30):
                async with session.post(
                    API_GRAPHQL_URL,
                    json={"query": query},
                    headers=headers,
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

                    lines = {}
                    all_lines = data.get("data", {}).get("lines", [])
                    
                    # Filter lines by codespace
                    for line in all_lines:
                        line_id = line.get("id", "")
                        
                        # Check if line belongs to this codespace
                        if not line_id.startswith(f"{operator}:"):
                            continue
                        
                        line_name = line.get("name", "")
                        public_code = line.get("publicCode", "")
                        transport_mode = line.get("transportMode", "")
                        
                        # Create a friendly display name
                        display_name = f"{public_code}"
                        if line_name:
                            display_name += f" - {line_name}"
                        if transport_mode:
                            display_name += f" ({transport_mode})"
                        
                        lines[line_id] = display_name

                    _LOGGER.debug("Found %d lines for codespace %s", len(lines), operator)
                    return lines

        except Exception as err:
            _LOGGER.error("Error fetching lines for codespace %s: %s", operator, err, exc_info=True)
            return {}
