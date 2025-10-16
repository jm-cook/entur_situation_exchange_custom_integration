"""Constants for the Entur Situation Exchange integration."""
DOMAIN = "entur_sx"

# Configuration
CONF_OPERATOR = "operator"
CONF_LINES_TO_CHECK = "lines_to_check"
CONF_DEVICE_NAME = "device_name"

# Defaults
DEFAULT_DEVICE_NAME = "Entur Avvik"
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
