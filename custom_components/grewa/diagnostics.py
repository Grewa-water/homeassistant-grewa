"""Diagnostics support for the Grewa integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .const import CONF_API_KEY
from .coordinator import GrewaConfigEntry

TO_REDACT = {
    CONF_API_KEY,
    "customer_id",
    "serial",
    "nameplate_serial",
    "provider_device_id",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: GrewaConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "device_metadata": async_redact_data(coordinator.device_metadata, TO_REDACT),
        "live_data": coordinator.data,
    }
