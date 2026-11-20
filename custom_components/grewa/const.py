"""Constants for the Grewa integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "grewa"

CONF_API_KEY = "api_key"
CONF_DEVICE_ID = "device_id"
CONF_BASE_URL = "base_url"

DEFAULT_BASE_URL = "https://api.grewa.com.au"

MANUFACTURER = "Grewa"

# The Grewa API serves API-key readings at most 5 minutes old (one shared
# cloud read per pump), so polling faster only re-reads the same values.
SCAN_INTERVAL = timedelta(minutes=5)
