"""Async API client for the Grewa cloud service."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import DEFAULT_BASE_URL

_LOGGER = logging.getLogger(__name__)

API_PATH = "/api/v1"
REQUEST_TIMEOUT = 20


class GrewaError(Exception):
    """Base error for the Grewa client."""


class GrewaConnectionError(GrewaError):
    """Raised when the service cannot be reached or returns an error."""


class GrewaAuthError(GrewaError):
    """Raised when the API key is rejected."""


class GrewaApiClient:
    """Minimal async client for the Grewa device API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    async def _request(self, path: str) -> dict[str, Any]:
        """Perform an authenticated GET request and return the JSON body."""
        url = f"{self._base_url}{API_PATH}{path}"
        headers = {"Authorization": f"Bearer {self._api_key}"}
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                response = await self._session.get(url, headers=headers)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise GrewaConnectionError(f"Error communicating with Grewa: {err}") from err

        if response.status in (401, 403):
            raise GrewaAuthError("Invalid API key")
        if response.status == 404:
            raise GrewaConnectionError("Device not found")
        if response.status >= 400:
            raise GrewaConnectionError(f"Unexpected response status {response.status}")

        try:
            return await response.json()
        except (aiohttp.ContentTypeError, ValueError) as err:
            raise GrewaConnectionError("Invalid JSON response from Grewa") from err

    async def async_get_device(self, device_id: str) -> dict[str, Any]:
        """Return the device metadata record."""
        return await self._request(f"/devices/{device_id}")

    async def async_get_live(self, device_id: str) -> dict[str, Any]:
        """Return the latest live reading for the device."""
        return await self._request(f"/devices/{device_id}/live-read")
