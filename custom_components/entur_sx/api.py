"""API client for Entur Situation Exchange."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

import aiohttp
import async_timeout

from .const import API_BASE_URL, API_GRAPHQL_URL, STATE_NORMAL, STATUS_EXPIRED, STATUS_PLANNED, STATUS_OPEN

_LOGGER = logging.getLogger(__name__)


class EnturSXApiClient:
    """API client for Entur Situation Exchange."""

    def __init__(
        self,
        operator: str | None = None,
        lines: list[str] | None = None,
    ) -> None:
        """Initialize the API client."""
        self._operator = operator
        self._lines = lines or []
        self._session: aiohttp.ClientSession | None = None

        # Build the service URL
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
                    data = await response.json()

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
                        
                        # If Progress is closed, mark as expired (resolved but still returned by API)
                        if progress_lower == "closed":
                            status = STATUS_EXPIRED
                        elif now_timestamp < start_timestamp:
                            status = STATUS_PLANNED
                        elif end_time:
                            end_timestamp = datetime.fromisoformat(end_time).timestamp()
                            if now_timestamp > end_timestamp:
                                status = STATUS_EXPIRED
                            else:
                                status = STATUS_OPEN
                        else:
                            # No end time specified, consider it open if started
                            status = STATUS_OPEN

                        # Check if this situation affects our line
                        affected_networks = networks.get("AffectedNetwork", [])
                        for an in affected_networks:
                            affected_line = an.get("AffectedLine", [])
                            if not affected_line:
                                continue

                            line_ref_obj = affected_line[0].get("LineRef", {})
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
                                    "progress": progress,  # Keep original for reference
                                })

                # Sort by timestamp (most recent first)
                if items:
                    items.sort(reverse=True, key=lambda x: x["valid_from"])
                else:
                    # No situation for this line, set default
                    items.append({
                        "valid_from": datetime.now().isoformat(),
                        "valid_to": None,
                        "summary": STATE_NORMAL,
                        "description": STATE_NORMAL,
                        "status": STATUS_OPEN,
                        "progress": "NORMAL",
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
                    "progress": "ERROR",
                }]

        _LOGGER.debug("Parsed deviations for %d lines", len(allitems_dict))
        return allitems_dict

    @staticmethod
    async def async_get_operators(session: aiohttp.ClientSession) -> dict[str, str]:
        """Fetch list of operators from Entur GraphQL API.
        
        Returns:
            Dict mapping operator code to friendly name, e.g. {"SKY": "Skyss", "RUT": "Ruter"}
        """
        query = """
        query {
          authorities {
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

                    operators = {}
                    authorities = data.get("data", {}).get("authorities", [])
                    
                    for authority in authorities:
                        authority_id = authority.get("id", "")
                        authority_name = authority.get("name", "")
                        
                        # Extract the operator code from the authority ID
                        # Format is usually like "NSR:Authority:SKY" or similar
                        if ":" in authority_id:
                            parts = authority_id.split(":")
                            operator_code = parts[-1] if parts else authority_id
                        else:
                            operator_code = authority_id
                        
                        if operator_code and authority_name:
                            operators[operator_code] = authority_name

                    _LOGGER.debug("Found %d operators", len(operators))
                    return operators

        except Exception as err:
            _LOGGER.error("Error fetching operators: %s", err, exc_info=True)
            # Return fallback list
            return {
                "SKY": "Skyss",
                "RUT": "Ruter",
                "ATB": "AtB",
                "KOL": "Kolumbus",
                "TRO": "Troms fylkestrafikk",
                "NOR": "Nordland fylkeskommune",
            }

    @staticmethod
    async def async_get_lines_for_operator(
        session: aiohttp.ClientSession, operator: str
    ) -> dict[str, str]:
        """Fetch list of lines for a specific operator from Entur GraphQL API.
        
        Args:
            session: aiohttp session
            operator: Operator code (e.g., "SKY")
            
        Returns:
            Dict mapping line ref to line name, e.g. {"SKY:Line:1": "Line 1 - Bergen sentrum"}
        """
        # Build authority filter - need to find the full authority ID
        query = """
        query($authority: String!) {
          lines(authorities: [$authority]) {
            id
            name
            publicCode
            transportMode
          }
        }
        """

        # Construct the full authority ID
        authority_id = f"NSR:Authority:{operator}"

        headers = {
            "Content-Type": "application/json",
            "ET-Client-Name": "homeassistant-entur-sx",
        }

        try:
            async with async_timeout.timeout(10):
                async with session.post(
                    API_GRAPHQL_URL,
                    json={"query": query, "variables": {"authority": authority_id}},
                    headers=headers,
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

                    lines = {}
                    line_list = data.get("data", {}).get("lines", [])
                    
                    for line in line_list:
                        line_id = line.get("id", "")
                        line_name = line.get("name", "")
                        public_code = line.get("publicCode", "")
                        transport_mode = line.get("transportMode", "")
                        
                        if line_id:
                            # Create a friendly display name
                            display_name = f"{public_code}"
                            if line_name:
                                display_name += f" - {line_name}"
                            if transport_mode:
                                display_name += f" ({transport_mode})"
                            
                            lines[line_id] = display_name

                    _LOGGER.debug("Found %d lines for operator %s", len(lines), operator)
                    return lines

        except Exception as err:
            _LOGGER.error("Error fetching lines for operator %s: %s", operator, err, exc_info=True)
            return {}
