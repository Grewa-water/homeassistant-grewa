"""Binary sensor platform for the Grewa integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import GrewaConfigEntry, GrewaDataUpdateCoordinator
from .entity import GrewaEntity


def _capability(data: dict[str, Any], key: str) -> Any:
    """Return a value from the nested capabilities object, or None."""
    capabilities = data.get("capabilities") or {}
    return capabilities.get(key)


def _is_running(data: dict[str, Any]) -> bool | None:
    """Return True when the motor is actually turning.

    ``power_on`` is the pump's power switch and stays on while the motor is
    parked, so it cannot stand in for "running". Motor activity is derived
    from speed and draw instead, matching how the Grewa app distinguishes
    "Standby" from "Running".
    """
    speed = _capability(data, "motor_speed")
    draw = _capability(data, "power_w")
    if speed is None and draw is None:
        return None
    return (speed or 0) > 0 or (draw or 0) > 0


@dataclass(frozen=True, kw_only=True)
class GrewaBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Grewa binary sensor."""

    value_fn: Callable[[dict[str, Any]], bool | None]


BINARY_SENSORS: tuple[GrewaBinarySensorEntityDescription, ...] = (
    GrewaBinarySensorEntityDescription(
        key="online",
        translation_key="online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda data: data.get("online"),
    ),
    GrewaBinarySensorEntityDescription(
        key="running",
        translation_key="running",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=_is_running,
    ),
    GrewaBinarySensorEntityDescription(
        key="power_switch",
        translation_key="power_switch",
        device_class=BinarySensorDeviceClass.POWER,
        value_fn=lambda data: _capability(data, "power_on"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GrewaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Grewa binary sensors from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        GrewaBinarySensor(coordinator, description) for description in BINARY_SENSORS
    )


class GrewaBinarySensor(GrewaEntity, BinarySensorEntity):
    """Representation of a Grewa binary sensor."""

    entity_description: GrewaBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: GrewaDataUpdateCoordinator,
        description: GrewaBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return True if the binary sensor is on."""
        return self.entity_description.value_fn(self.coordinator.data)
