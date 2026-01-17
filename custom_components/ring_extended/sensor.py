"""Sensor platform for Ring Extended."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.components.ring import DOMAIN as RING_DOMAIN
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
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


def _get_device_merged_attrs(device: Any) -> dict:
    """Get merged attributes from device _attrs and _health_attrs.

    Ring library stores some health data in _attrs.health (from main API)
    and additional health data in _health_attrs (from health API endpoint).
    We merge both to get the complete picture.
    """
    attrs = dict(getattr(device, "_attrs", {}) or {})

    # Start with health data from _attrs (if any)
    base_health = dict(attrs.get("health", {}) or {})

    # Merge in _health_attrs (from separate health API call)
    health_attrs = getattr(device, "_health_attrs", {}) or {}
    if health_attrs:
        base_health.update(health_attrs)

    # Also check for alert-related data that might be nested
    alerts = attrs.get("alerts", {})
    if alerts:
        # Add alert data with "alert_" prefix
        for key, value in alerts.items():
            base_health[f"alert_{key}"] = value

    if base_health:
        attrs["health"] = base_health

    return attrs


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
            device_attrs = _get_device_merged_attrs(device)
            if not device_attrs:
                _LOGGER.debug("Device %s has no _attrs", getattr(device, "name", "unknown"))
                continue

            device_id = str(getattr(device, "device_id", None) or getattr(device, "id", ""))

            _LOGGER.debug("Processing device: %s with %d merged health keys",
                          getattr(device, "name", "unknown"),
                          len(device_attrs.get("health", {})))

            # Create sensors for ALL categories
            for description in ALL_SENSORS:
                # Check if this sensor's attribute exists for this device
                if description.is_available(device_attrs):
                    unique_id = f"{device_id}_{description.key}"

                    # Enable by default only if category was selected
                    is_enabled = description.category in enabled_categories
                    entities.append(
                        RingExtendedSensor(
                            device=device,
                            coordinator=coordinator,
                            description=description,
                            enabled_default=is_enabled,
                            ring_entry=ring_entry,
                        )
                    )

    # Add per-device firmware history sensors
    firmware_tracker = our_data.get("firmware_tracker")
    if firmware_tracker:
        for family in DEVICE_FAMILIES:
            devices = getattr(devices_dict, family, []) or []
            for device in devices:
                device_attrs = _get_device_merged_attrs(device)
                # Only add for devices that have firmware info
                if device_attrs.get("health", {}).get("firmware_version"):
                    device_id = str(getattr(device, "device_id", None) or getattr(device, "id", ""))

                    entities.append(
                        RingDeviceFirmwareHistorySensor(
                            device=device,
                            coordinator=coordinator,
                            firmware_tracker=firmware_tracker,
                            ring_entry=ring_entry,
                        )
                    )
        _LOGGER.info("Added per-device firmware history sensors")

    # Add coordinator health sensor
    entities.append(
        RingCoordinatorHealthSensor(
            hass=hass,
            coordinator=coordinator,
            entry_id=entry.entry_id,
        )
    )
    _LOGGER.info("Added coordinator health sensor")

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
        ring_entry: Any = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device = device
        self._ring_entry = ring_entry
        self.entity_description = description

        # Store device identification for refreshing the reference
        self._device_id = str(getattr(device, "device_id", None) or getattr(device, "id", "unknown"))
        self._device_family = self._detect_device_family(device)

        # Set whether entity is enabled by default based on category selection
        self._attr_entity_registry_enabled_default = enabled_default

        # Build unique ID
        self._attr_unique_id = f"{self._device_id}_{description.key}"

        # Build name with category prefix
        category = description.category
        prefix = CATEGORY_PREFIXES.get(category, category.title())
        self._category_prefix = prefix

        # Entity name uses translation_key for the base name
        self._attr_translation_key = description.translation_key

    def _detect_device_family(self, device: Any) -> str:
        """Detect which device family this device belongs to."""
        device_type = type(device).__name__.lower()
        if "doorbell" in device_type:
            return "doorbells"
        elif "chime" in device_type:
            return "chimes"
        elif "stickup" in device_type or "cam" in device_type:
            return "stickup_cams"
        return "other"

    def _refresh_device(self) -> None:
        """Refresh the device reference from the coordinator's devices."""
        if self._ring_entry is None:
            return

        # Get fresh devices from runtime_data
        try:
            devices_dict = self._ring_entry.runtime_data.devices
        except AttributeError:
            return

        # Search for the device in its family first, then others
        families_to_search = [self._device_family] + [
            f for f in DEVICE_FAMILIES if f != self._device_family
        ]

        for family in families_to_search:
            devices = getattr(devices_dict, family, []) or []
            for device in devices:
                dev_id = str(getattr(device, "device_id", None) or getattr(device, "id", ""))
                if dev_id == self._device_id:
                    self._device = device
                    return

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

    def _get_merged_attrs(self) -> dict:
        """Get merged attributes from device _attrs and _health_attrs."""
        return _get_device_merged_attrs(self._device)

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        try:
            attrs = self._get_merged_attrs()
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
        try:
            attrs = self._get_merged_attrs()
            return self.entity_description.is_available(attrs)
        except (KeyError, TypeError, AttributeError):
            return False

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Refresh the device reference to get fresh data
        self._refresh_device()
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
        ring_entry: Any = None,
    ) -> None:
        """Initialize the per-device firmware history sensor."""
        super().__init__(coordinator)
        self._device = device
        self._ring_entry = ring_entry
        self._firmware_tracker = firmware_tracker

        device_id = str(getattr(device, "device_id", None) or getattr(device, "id", "unknown"))
        self._device_id = device_id
        self._device_family = self._detect_device_family(device)
        self._attr_unique_id = f"{device_id}_firmware_history"
        self._attr_name = "Firmware: History"

    def _detect_device_family(self, device: Any) -> str:
        """Detect which device family this device belongs to."""
        device_type = type(device).__name__.lower()
        if "doorbell" in device_type:
            return "doorbells"
        elif "chime" in device_type:
            return "chimes"
        elif "stickup" in device_type or "cam" in device_type:
            return "stickup_cams"
        return "other"

    def _refresh_device(self) -> None:
        """Refresh the device reference from the coordinator's devices."""
        if self._ring_entry is None:
            return

        try:
            devices_dict = self._ring_entry.runtime_data.devices
        except AttributeError:
            return

        families_to_search = [self._device_family] + [
            f for f in DEVICE_FAMILIES if f != self._device_family
        ]

        for family in families_to_search:
            devices = getattr(devices_dict, family, []) or []
            for device in devices:
                dev_id = str(getattr(device, "device_id", None) or getattr(device, "id", ""))
                if dev_id == self._device_id:
                    self._device = device
                    return

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
        self._refresh_device()
        self.async_write_ha_state()


class RingCoordinatorHealthSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing the health status of the Ring coordinator."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:heart-pulse"
    _attr_name = "Coordinator Health"

    # Thresholds for health status (in minutes)
    HEALTHY_THRESHOLD = 10  # Up to 10 minutes = healthy
    STALE_THRESHOLD = 30  # 10-30 minutes = stale
    # Over 30 minutes = critical

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: DataUpdateCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the coordinator health sensor."""
        super().__init__(coordinator)
        self._hass = hass
        self._entry_id = entry_id
        self._attr_unique_id = f"{entry_id}_coordinator_health"
        self._update_count = 0
        self._last_update_time: datetime | None = datetime.now(timezone.utc)
        self._unsub_timer: callable | None = None

    @property
    def available(self) -> bool:
        """Return True - this sensor is always available."""
        return True

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()
        # Update every minute to keep minutes_since_update accurate
        self._unsub_timer = async_track_time_interval(
            self._hass,
            self._async_update_time,
            timedelta(minutes=1),
        )

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity is removed from hass."""
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None
        await super().async_will_remove_from_hass()

    @callback
    def _async_update_time(self, _now: datetime) -> None:
        """Update the sensor to refresh minutes_since_update."""
        self.async_write_ha_state()

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info for this sensor."""
        return {
            "identifiers": {(DOMAIN, "ring_extended_diagnostics")},
            "name": "Ring Extended Diagnostics",
            "manufacturer": "Ring Extended",
            "model": "Coordinator Monitor",
        }

    @property
    def native_value(self) -> str:
        """Return the health status."""
        if not self.coordinator.last_update_success:
            return "Failed"

        if self._last_update_time is None:
            return "Unknown"

        minutes_ago = self._minutes_since_update
        if minutes_ago is None:
            return "Unknown"

        if minutes_ago <= self.HEALTHY_THRESHOLD:
            return "Healthy"
        elif minutes_ago <= self.STALE_THRESHOLD:
            return "Stale"
        else:
            return "Critical"

    @property
    def _minutes_since_update(self) -> float | None:
        """Calculate minutes since the last update."""
        if self._last_update_time is None:
            return None
        now = datetime.now(timezone.utc)
        delta = now - self._last_update_time
        return delta.total_seconds() / 60

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        minutes_ago = self._minutes_since_update

        attrs = {
            "last_update": self._last_update_time.isoformat() if self._last_update_time else None,
            "minutes_since_update": round(minutes_ago, 1) if minutes_ago is not None else None,
            "update_count": self._update_count,
            "last_update_success": self.coordinator.last_update_success,
            "healthy_threshold_minutes": self.HEALTHY_THRESHOLD,
            "stale_threshold_minutes": self.STALE_THRESHOLD,
        }

        # Add status explanation
        if minutes_ago is not None:
            if minutes_ago <= self.HEALTHY_THRESHOLD:
                attrs["status_detail"] = f"Updated {round(minutes_ago, 1)} min ago - normal operation"
            elif minutes_ago <= self.STALE_THRESHOLD:
                attrs["status_detail"] = f"Updated {round(minutes_ago, 1)} min ago - updates may be delayed"
            else:
                attrs["status_detail"] = f"Updated {round(minutes_ago, 1)} min ago - coordinator may be stuck"

        return attrs

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._last_update_time = datetime.now(timezone.utc)
        self._update_count += 1
        self.async_write_ha_state()
