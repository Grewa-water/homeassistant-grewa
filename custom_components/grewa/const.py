"""Constants for the Grewa integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "grewa"

CONF_API_KEY = "api_key"
CONF_DEVICE_ID = "device_id"
CONF_BASE_URL = "base_url"

DEFAULT_BASE_URL = "https://grewa-production.up.railway.app"

MANUFACTURER = "Grewa"

# The pump reports roughly every few seconds; polling every 30s is a good
# balance between freshness and load on the cloud service.
SCAN_INTERVAL = timedelta(seconds=30)
