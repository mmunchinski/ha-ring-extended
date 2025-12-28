"""Sensor platform for Ring Extended."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.ring import DOMAIN as RING_DOMAIN
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    CATEGORY_SENSORS,
    DEVICE_FAMILIES,
    DOMAIN,
    RingExtendedSensorDescription,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ring Extended sensors from a config entry."""
    ring_data = hass.data.get(RING_DOMAIN)
    if not ring_data:
        _LOGGER.error("Ring integration data not found")
        return

    enabled_categories: list[str] = entry.data.get("categories", [])
    if not enabled_categories:
        _LOGGER.warning("No sensor categories enabled")
        return

    # Collect sensor descriptions for enabled categories
    sensor_descriptions: list[RingExtendedSensorDescription] = []
    for category in enabled_categories:
        if category in CATEGORY_SENSORS:
            sensor_descriptions.extend(CATEGORY_SENSORS[category])

    entities: list[RingExtendedSensor] = []

    # Iterate through all Ring config entries
    for ring_entry_id, ring_entry_data in ring_data.items():
        if not isinstance(ring_entry_data, dict):
            continue

        coordinator = ring_entry_data.get("coordinator")
        ring_api = ring_entry_data.get("ring")

        if coordinator is None or ring_api is None:
            _LOGGER.debug("Skipping entry %s: missing coordinator or ring API", ring_entry_id)
            continue

        # Get devices from the Ring API
        try:
            devices_dict = ring_api.devices()
        except Exception as err:
            _LOGGER.error("Failed to get Ring devices: %s", err)
            continue

        # Iterate through all device families
        for family in DEVICE_FAMILIES:
            devices = devices_dict.get(family, [])
            for device in devices:
                device_attrs = getattr(device, "_attrs", {})
                if not device_attrs:
                    _LOGGER.debug("Device %s has no _attrs", getattr(device, "name", "unknown"))
                    continue

                # Create sensors for this device
                for description in sensor_descriptions:
                    # Check if this sensor's attribute exists for this device
                    if description.is_available(device_attrs):
                        entities.append(
                            RingExtendedSensor(
                                device=device,
                                coordinator=coordinator,
                                description=description,
                            )
                        )

    _LOGGER.info("Setting up %d Ring Extended sensors", len(entities))
    async_add_entities(entities)


class RingExtendedSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Ring Extended sensor."""

    entity_description: RingExtendedSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        device: Any,
        coordinator: DataUpdateCoordinator,
        description: RingExtendedSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device = device
        self.entity_description = description

        # Build unique ID
        device_id = getattr(device, "device_id", None) or getattr(device, "id", "unknown")
        self._attr_unique_id = f"{device_id}_{description.key}"

        # Entity name uses translation_key
        self._attr_translation_key = description.translation_key

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info to link this sensor to the existing Ring device."""
        device_id = getattr(self._device, "device_id", None) or getattr(self._device, "id", None)
        if device_id is None:
            return None

        return {
            "identifiers": {(RING_DOMAIN, device_id)},
            # Only identifiers - this links to existing Ring device, doesn't create new one
        }

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        try:
            attrs = getattr(self._device, "_attrs", {})
            return self.entity_description.get_value(attrs)
        except (KeyError, TypeError, AttributeError) as err:
            _LOGGER.debug(
                "Error getting value for %s: %s",
                self.entity_description.key,
                err,
            )
            return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self.coordinator.last_update_success:
            return False

        try:
            attrs = getattr(self._device, "_attrs", {})
            return self.entity_description.is_available(attrs)
        except (KeyError, TypeError, AttributeError):
            return False

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
