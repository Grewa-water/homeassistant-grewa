"""Config flow for the Grewa integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GrewaApiClient, GrewaAuthError, GrewaConnectionError
from .const import (
    CONF_API_KEY,
    CONF_BASE_URL,
    CONF_DEVICE_ID,
    DEFAULT_BASE_URL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): str,
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
    }
)

STEP_REAUTH_DATA_SCHEMA = vol.Schema({vol.Required(CONF_API_KEY): str})


class GrewaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Grewa."""

    VERSION = 1

    async def _async_validate(self, data: Mapping[str, Any]) -> dict[str, Any]:
        """Validate credentials by fetching the device record."""
        session = async_get_clientsession(self.hass)
        client = GrewaApiClient(
            session,
            data[CONF_API_KEY],
            data.get(CONF_BASE_URL, DEFAULT_BASE_URL),
        )
        return await client.async_get_device(data[CONF_DEVICE_ID])

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
            self._abort_if_unique_id_configured()
            try:
                device = await self._async_validate(user_input)
            except GrewaAuthError:
                errors["base"] = "invalid_auth"
            except GrewaConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error validating Grewa credentials")
                errors["base"] = "unknown"
            else:
                title = device.get("nickname") or "Grewa Pump"
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle re-authentication when the API key is rejected."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm re-authentication with a new API key."""
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()
        if user_input is not None:
            data = {**reauth_entry.data, CONF_API_KEY: user_input[CONF_API_KEY]}
            try:
                await self._async_validate(data)
            except GrewaAuthError:
                errors["base"] = "invalid_auth"
            except GrewaConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during Grewa reauth")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(reauth_entry, data=data)

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_REAUTH_DATA_SCHEMA,
            errors=errors,
        )
