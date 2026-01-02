"""The Ring Extended integration."""
from __future__ import annotations

import logging

from homeassistant.components.ring import DOMAIN as RING_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, DEVICE_FAMILIES, get_nested
from .firmware_history import FirmwareHistoryTracker

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ring Extended from a config entry."""
    # Find Ring config entries
    ring_entries = [
        e for e in hass.config_entries.async_entries()
        if e.domain == RING_DOMAIN
    ]
    if not ring_entries:
        raise ConfigEntryNotReady(
            "Ring integration is not configured. Please set up Ring first."
        )

    # Check if Ring entries have runtime_data (new HA pattern)
    ring_entry = ring_entries[0]
    if not hasattr(ring_entry, 'runtime_data') or ring_entry.runtime_data is None:
        _LOGGER.debug("Ring runtime_data not yet available, will retry")
        raise ConfigEntryNotReady(
            "Ring integration is still loading. Will retry shortly."
        )

    _LOGGER.debug("Ring runtime_data found: %s", type(ring_entry.runtime_data))

    # Initialize firmware history tracker
    firmware_tracker = FirmwareHistoryTracker(hass)
    await firmware_tracker.async_load()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "ring_entry": ring_entry,
        "firmware_tracker": firmware_tracker,
    }

    # Set up coordinator listener for firmware tracking
    ring_data = ring_entry.runtime_data
    coordinator = getattr(ring_data, 'devices_coordinator', None)
    devices_dict = getattr(ring_data, 'devices', None)

    if coordinator and devices_dict:
        @callback
        def _check_firmware_updates() -> None:
            """Check for firmware updates on coordinator refresh."""
            changes = []
            for family in DEVICE_FAMILIES:
                devices = getattr(devices_dict, family, []) or []
                for device in devices:
                    device_attrs = getattr(device, "_attrs", {})
                    device_id = str(getattr(device, "device_id", None) or getattr(device, "id", ""))
                    device_name = getattr(device, "name", "Unknown")
                    firmware = get_nested(device_attrs, "health.firmware_version")

                    if firmware and device_id:
                        change = firmware_tracker.check_and_update(
                            device_id, device_name, firmware
                        )
                        if change and change.get("previous_version"):
                            changes.append(change)

            # Save if any changes detected and send notification
            if changes:
                hass.async_create_task(firmware_tracker.async_save())
                for change in changes:
                    hass.components.persistent_notification.async_create(
                        f"**{change['device_name']}** firmware updated\n\n"
                        f"`{change['previous_version']}` → `{change['version']}`",
                        title="Ring Firmware Update",
                        notification_id=f"ring_firmware_{change['device_name']}",
                    )

        # Register the listener
        entry.async_on_unload(
            coordinator.async_add_listener(_check_firmware_updates)
        )

        # Do initial check
        _check_firmware_updates()
        await firmware_tracker.async_save()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
