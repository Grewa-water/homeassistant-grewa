"""Data update coordinator for the Grewa integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GrewaApiClient, GrewaAuthError, GrewaConnectionError
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

type GrewaConfigEntry = ConfigEntry[GrewaDataUpdateCoordinator]


class GrewaDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate polling of a single Grewa pump."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: GrewaConfigEntry,
        client: GrewaApiClient,
        device_id: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            config_entry=entry,
        )
        self.client = client
        self.device_id = device_id
        # Populated once in _async_setup and used to build the device registry entry.
        self.device_metadata: dict[str, Any] = {}

    async def _async_setup(self) -> None:
        """Fetch static device metadata once, before the first data refresh."""
        try:
            self.device_metadata = await self.client.async_get_device(self.device_id)
        except GrewaAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except GrewaConnectionError as err:
            raise UpdateFailed(str(err)) from err

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest live reading from the pump."""
        try:
            return await self.client.async_get_live(self.device_id)
        except GrewaAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except GrewaConnectionError as err:
            raise UpdateFailed(str(err)) from err
