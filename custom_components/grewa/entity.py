"""Base entity for the Grewa integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import GrewaDataUpdateCoordinator


class GrewaEntity(CoordinatorEntity[GrewaDataUpdateCoordinator]):
    """Base class for all Grewa entities, tied to a single pump device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: GrewaDataUpdateCoordinator, key: str) -> None:
        """Initialize the entity and its device registry entry."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_{key}"

        metadata = coordinator.device_metadata
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.device_id)},
            manufacturer=MANUFACTURER,
            name=metadata.get("nickname") or "Grewa Pump",
            model=metadata.get("model"),
            model_id=metadata.get("model_code"),
            serial_number=metadata.get("serial"),
        )

    @property
    def available(self) -> bool:
        """Return True when the coordinator has data to serve."""
        return super().available and self.coordinator.data is not None
