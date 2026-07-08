"""The Grewa integration."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GrewaApiClient
from .const import CONF_API_KEY, CONF_BASE_URL, CONF_DEVICE_ID, DEFAULT_BASE_URL
from .coordinator import GrewaConfigEntry, GrewaDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: GrewaConfigEntry) -> bool:
    """Set up Grewa from a config entry."""
    session = async_get_clientsession(hass)
    client = GrewaApiClient(
        session,
        entry.data[CONF_API_KEY],
        entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL),
    )
    coordinator = GrewaDataUpdateCoordinator(
        hass, entry, client, entry.data[CONF_DEVICE_ID]
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: GrewaConfigEntry) -> bool:
    """Unload a Grewa config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
