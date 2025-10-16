"""Constants for the Entur Situation Exchange integration."""
DOMAIN = "entur_sx"

# Configuration
CONF_OPERATOR = "operator"
CONF_LINES_TO_CHECK = "lines_to_check"
CONF_DEVICE_NAME = "device_name"

# Defaults
DEFAULT_DEVICE_NAME = "Entur Disruption"  # Fallback only, translations preferred
UPDATE_INTERVAL = 60  # seconds

# API
API_BASE_URL = "https://api.entur.io/realtime/v1/rest/sx"
API_GRAPHQL_URL = "https://api.entur.io/journey-planner/v3/graphql"

# States
STATE_NORMAL = "Normal service"

# Status values
STATUS_PLANNED = "planned"
STATUS_OPEN = "open"
STATUS_EXPIRED = "expired"

# Codespace to friendly name mapping
#
# WHY THIS MAPPING EXISTS:
# The SIRI-SX API uses 3-letter codespaces (e.g., "SKY", "SOF") to identify regional
# transport authorities. However, Entur's public APIs don't provide a way to map these
# codespaces to user-friendly regional authority names:
#
# - The GraphQL operators/authorities APIs return individual transport company names
#   (e.g., "GulenSkyss AS", "Fjord1 ASA") not regional authority names
# - The Organizations API v3 has the data we need (/v3/codespaces endpoint) but it's
#   an internal/partner API requiring authentication (returns 401 for public access)
# - The official codespace documentation (https://enturas.atlassian.net/wiki/spaces/PUBLIC/pages/637370434/)
#   is the authoritative public source for regional transport authority names
#
# This mapping bridges that gap, allowing users to select their region by name
# (e.g., "Sogn og Fjordane") rather than having to know the codespace identifier.
#
# Source: Official Entur codespace documentation + dynamic discovery from operators API
# The codespace (3-letter code) is what's used in SIRI-SX datasetId parameter
CODESPACE_NAMES = {
    # Major regional transport authorities
    "AKT": "Agder Kollektivtrafikk",
    "ATB": "AtB",
    "BRA": "Brakar",
    "GOA": "Go-Ahead Norge",
    "INN": "Innlandstrafikk",
    "KOL": "Kolumbus",
    "MOR": "FRAM",
    "NBU": "Flybussen Connect",
    "OST": "Østfold kollektivtrafikk",
    "RUT": "Ruter",
    "SJN": "SJ Nord",
    "SKY": "Skyss",
    "SOF": "Sogn og Fjordane",  # Kringom regional authority
    "TEL": "Farte",
    "TRO": "Troms fylkestrafikk",
    "VKT": "VKT",
    "VYB": "Vy Bus4You",
    "VYG": "Vy",
    "VYX": "Vy Buss",
    
    # Codespaces found in SIRI-SX but not fully mapped
    "CTS": "CTS",
    "GCO": "GCO",
    "NSB": "NSB",
}

