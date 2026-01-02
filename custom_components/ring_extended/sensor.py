"""Sensor platform for Ring Extended."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.ring import DOMAIN as RING_DOMAIN
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    ALL_SENSORS,
    CATEGORY_NAMES,
    CATEGORY_SENSORS,
    DEVICE_FAMILIES,
    DOMAIN,
    RingExtendedSensorDescription,
)
from .firmware_history import FirmwareHistoryTracker

# Short prefixes for sensor names (keep UI clean)
CATEGORY_PREFIXES = {
    "health": "Health",
    "power": "Power",
    "firmware": "Firmware",
    "video": "Video",
    "audio": "Audio",
    "motion": "Motion",
    "cv_detection": "CV",
    "cv_paid": "Paid CV",
    "other_paid": "Paid",
    "notifications": "Notify",
    "recording": "Recording",
    "floodlight": "Light",
    "radar": "Radar",
    "local_processing": "Local",
    "features": "Feature",
    "device_status": "Status",
}

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ring Extended sensors from a config entry."""
    # Get the ring_entry stored by __init__.py
    our_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    ring_entry = our_data.get("ring_entry")

    if not ring_entry or not hasattr(ring_entry, 'runtime_data'):
        _LOGGER.error("Ring entry or runtime_data not found")
        return

    ring_data = ring_entry.runtime_data

    # Access the devices coordinator and devices from runtime_data
    # RingData has: api, devices, devices_coordinator, listen_coordinator
    coordinator = getattr(ring_data, 'devices_coordinator', None)
    devices_dict = getattr(ring_data, 'devices', None)

    if coordinator is None:
        _LOGGER.error("Ring devices_coordinator not found in runtime_data")
        return

    if devices_dict is None:
        _LOGGER.error("Ring devices not found in runtime_data")
        return

    # Get enabled categories - these will be enabled by default
    enabled_categories: set[str] = set(entry.data.get("categories", []))

    entities: list[RingExtendedSensor] = []

    # devices_dict is a RingDevices object with doorbells, stickup_cams, chimes, other
    _LOGGER.debug("Ring devices type: %s", type(devices_dict))

    # Iterate through all device families
    for family in DEVICE_FAMILIES:
        devices = getattr(devices_dict, family, []) or []
        _LOGGER.debug("Found %d devices in family %s", len(devices), family)

        for device in devices:
            device_attrs = getattr(device, "_attrs", {})
            if not device_attrs:
                _LOGGER.debug("Device %s has no _attrs", getattr(device, "name", "unknown"))
                continue

            _LOGGER.debug("Processing device: %s with %d attrs",
                         getattr(device, "name", "unknown"), len(device_attrs))

            # Create sensors for ALL categories
            for description in ALL_SENSORS:
                # Check if this sensor's attribute exists for this device
                if description.is_available(device_attrs):
                    # Enable by default only if category was selected
                    is_enabled = description.category in enabled_categories
                    entities.append(
                        RingExtendedSensor(
                            device=device,
                            coordinator=coordinator,
                            description=description,
                            enabled_default=is_enabled,
                        )
                    )

    # Add per-device firmware history sensors
    firmware_tracker = our_data.get("firmware_tracker")
    if firmware_tracker:
        for family in DEVICE_FAMILIES:
            devices = getattr(devices_dict, family, []) or []
            for device in devices:
                device_attrs = getattr(device, "_attrs", {})
                # Only add for devices that have firmware info
                if device_attrs.get("health", {}).get("firmware_version"):
                    entities.append(
                        RingDeviceFirmwareHistorySensor(
                            device=device,
                            coordinator=coordinator,
                            firmware_tracker=firmware_tracker,
                        )
                    )
        _LOGGER.info("Added per-device firmware history sensors")

    _LOGGER.info("Setting up %d Ring Extended sensors", len(entities))
    async_add_entities(entities)


class RingExtendedSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Ring Extended sensor."""

    entity_description: RingExtendedSensorDescription
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        device: Any,
        coordinator: DataUpdateCoordinator,
        description: RingExtendedSensorDescription,
        enabled_default: bool = True,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device = device
        self.entity_description = description

        # Set whether entity is enabled by default based on category selection
        self._attr_entity_registry_enabled_default = enabled_default

        # Build unique ID
        device_id = getattr(device, "device_id", None) or getattr(device, "id", "unknown")
        self._attr_unique_id = f"{device_id}_{description.key}"

        # Build name with category prefix
        category = description.category
        prefix = CATEGORY_PREFIXES.get(category, category.title())
        self._category_prefix = prefix

        # Entity name uses translation_key for the base name
        self._attr_translation_key = description.translation_key

    @property
    def name(self) -> str:
        """Return the name with category prefix."""
        # Get the base name from translation or key
        base_name = self.entity_description.key.replace("_", " ").title()
        return f"{self._category_prefix}: {base_name}"

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


class RingDeviceFirmwareHistorySensor(CoordinatorEntity, SensorEntity):
    """Sensor showing firmware history for a specific Ring device."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:history"

    def __init__(
        self,
        device: Any,
        coordinator: DataUpdateCoordinator,
        firmware_tracker: FirmwareHistoryTracker,
    ) -> None:
        """Initialize the per-device firmware history sensor."""
        super().__init__(coordinator)
        self._device = device
        self._firmware_tracker = firmware_tracker

        device_id = str(getattr(device, "device_id", None) or getattr(device, "id", "unknown"))
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_firmware_history"
        self._attr_name = "Firmware: History"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info to link this sensor to the existing Ring device."""
        device_id = getattr(self._device, "device_id", None) or getattr(self._device, "id", None)
        if device_id is None:
            return None
        return {
            "identifiers": {(RING_DOMAIN, device_id)},
        }

    @property
    def native_value(self) -> str:
        """Return the current firmware version and change count."""
        history = self._firmware_tracker.get_device_history(self._device_id)
        current_version = self._firmware_tracker._current_versions.get(self._device_id, "Unknown")
        change_count = len(history)

        if change_count <= 1:
            return current_version
        else:
            return f"{current_version} ({change_count - 1} updates)"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return firmware history as attributes."""
        history = self._firmware_tracker.get_device_history(self._device_id)

        if not history:
            return {
                "current_version": "Unknown",
                "history": [],
                "total_changes": 0,
            }

        # Format history entries
        formatted_history = []
        for entry in reversed(history):  # Most recent first
            ts = entry.get("timestamp", "")
            if ts:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(ts)
                    date_str = dt.strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    date_str = ts[:16]
            else:
                date_str = "Unknown"

            prev = entry.get("previous_version")
            ver = entry.get("version", "?")

            if prev:
                formatted_history.append(f"{date_str}: {prev} -> {ver}")
            else:
                formatted_history.append(f"{date_str}: {ver} (initial)")

        current = history[-1] if history else {}
        first_seen = history[0].get("timestamp", "")[:10] if history else "Unknown"

        return {
            "current_version": current.get("version", "Unknown"),
            "first_seen": first_seen,
            "total_updates": max(0, len(history) - 1),
            "history": formatted_history,
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
