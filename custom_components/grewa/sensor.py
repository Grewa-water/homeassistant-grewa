"""Sensor platform for the Grewa integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import GrewaConfigEntry, GrewaDataUpdateCoordinator
from .entity import GrewaEntity


def _capability(data: dict[str, Any], key: str) -> Any:
    """Return a value from the nested capabilities object, or None."""
    capabilities = data.get("capabilities") or {}
    return capabilities.get(key)


def _reported_at(data: dict[str, Any]) -> datetime | None:
    """Convert the reported_at_ms epoch into a timezone-aware datetime."""
    reported_ms = data.get("reported_at_ms")
    if reported_ms is None:
        return None
    return dt_util.utc_from_timestamp(reported_ms / 1000)


def _error_code(data: dict[str, Any]) -> int | None:
    """Return the error code as an integer."""
    value = _capability(data, "error_code")
    return None if value is None else int(value)


def _faults(data: dict[str, Any]) -> str:
    """Return a human-readable summary of active fault codes."""
    codes = data.get("fault_codes") or []
    return ", ".join(str(code) for code in codes) or "None"


def _pump_status(data: dict[str, Any]) -> str | None:
    """Return the pump's overall state as off, standby or running.

    Mirrors the status badge in the Grewa app: motor activity wins, otherwise
    the power switch decides between standby and off.
    """
    power_on = _capability(data, "power_on")
    speed = _capability(data, "motor_speed")
    draw = _capability(data, "power_w")
    if power_on is None and speed is None and draw is None:
        return None
    if (speed or 0) > 0 or (draw or 0) > 0:
        return "running"
    return "standby" if power_on else "off"


@dataclass(frozen=True, kw_only=True)
class GrewaSensorEntityDescription(SensorEntityDescription):
    """Describes a Grewa sensor."""

    value_fn: Callable[[dict[str, Any]], Any]


SENSORS: tuple[GrewaSensorEntityDescription, ...] = (
    GrewaSensorEntityDescription(
        key="pump_status",
        translation_key="pump_status",
        device_class=SensorDeviceClass.ENUM,
        options=["off", "standby", "running"],
        value_fn=_pump_status,
    ),
    GrewaSensorEntityDescription(
        key="pressure",
        translation_key="pressure",
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.KPA,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _capability(data, "pressure_kpa"),
    ),
    GrewaSensorEntityDescription(
        key="target_pressure",
        translation_key="target_pressure",
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.KPA,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _capability(data, "target_pressure_kpa"),
    ),
    GrewaSensorEntityDescription(
        key="start_pressure",
        translation_key="start_pressure",
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.KPA,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _capability(data, "start_pressure_kpa"),
    ),
    GrewaSensorEntityDescription(
        key="start_pressure_pct",
        translation_key="start_pressure_pct",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _capability(data, "start_pressure_pct"),
    ),
    GrewaSensorEntityDescription(
        key="power",
        translation_key="power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _capability(data, "power_w"),
    ),
    GrewaSensorEntityDescription(
        key="voltage",
        translation_key="voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _capability(data, "voltage_v"),
    ),
    GrewaSensorEntityDescription(
        key="water_temp",
        translation_key="water_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _capability(data, "water_temp_c"),
    ),
    GrewaSensorEntityDescription(
        key="motor_speed",
        translation_key="motor_speed",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _capability(data, "motor_speed"),
    ),
    GrewaSensorEntityDescription(
        key="runtime",
        translation_key="runtime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: _capability(data, "runtime_h"),
    ),
    GrewaSensorEntityDescription(
        key="error_code",
        translation_key="error_code",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_error_code,
    ),
    GrewaSensorEntityDescription(
        key="faults",
        translation_key="faults",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_faults,
    ),
    GrewaSensorEntityDescription(
        key="reported_at",
        translation_key="reported_at",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_reported_at,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GrewaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Grewa sensors from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        GrewaSensor(coordinator, description) for description in SENSORS
    )


class GrewaSensor(GrewaEntity, SensorEntity):
    """Representation of a Grewa sensor."""

    entity_description: GrewaSensorEntityDescription

    def __init__(
        self,
        coordinator: GrewaDataUpdateCoordinator,
        description: GrewaSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the current value of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)
