"""The Ring Extended integration."""
from __future__ import annotations

import logging

from homeassistant.components.ring import DOMAIN as RING_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er

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
        "tracked_device_ids": set(),
    }

    # Set up coordinator listener for firmware tracking
    ring_data = ring_entry.runtime_data
    coordinator = getattr(ring_data, 'devices_coordinator', None)
    devices_dict = getattr(ring_data, 'devices', None)

    # Build initial set of device IDs
    current_device_ids: set[str] = set()
    if devices_dict:
        for family in DEVICE_FAMILIES:
            devices = getattr(devices_dict, family, []) or []
            for device in devices:
                device_id = str(getattr(device, "device_id", None) or getattr(device, "id", ""))
                if device_id:
                    current_device_ids.add(device_id)
    hass.data[DOMAIN][entry.entry_id]["tracked_device_ids"] = current_device_ids

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

            # Detect removed devices
            current_ids: set[str] = set()
            for family in DEVICE_FAMILIES:
                devices = getattr(devices_dict, family, []) or []
                for device in devices:
                    device_id = str(getattr(device, "device_id", None) or getattr(device, "id", ""))
                    if device_id:
                        current_ids.add(device_id)

            tracked_ids = hass.data[DOMAIN][entry.entry_id].get("tracked_device_ids", set())
            removed_ids = tracked_ids - current_ids

            if removed_ids:
                hass.async_create_task(
                    _cleanup_orphaned_entities(hass, entry, removed_ids, firmware_tracker)
                )
                # Update tracked IDs
                hass.data[DOMAIN][entry.entry_id]["tracked_device_ids"] = current_ids

        # Register the listener
        entry.async_on_unload(
            coordinator.async_add_listener(_check_firmware_updates)
        )

        # Do initial check
        _check_firmware_updates()
        await firmware_tracker.async_save()

    # Clean up orphaned entities on startup
    await _cleanup_orphaned_entities_on_startup(hass, entry, current_device_ids)

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


async def async_remove_config_entry_device(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    device_entry,
) -> bool:
    """Allow removal of orphaned devices from the UI."""
    return True


async def _cleanup_orphaned_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
    removed_device_ids: set[str],
    firmware_tracker: FirmwareHistoryTracker,
) -> None:
    """Remove entities for devices that no longer exist in Ring."""
    entity_registry = er.async_get(hass)

    entities_to_remove = []
    for entity_entry in entity_registry.entities.values():
        if entity_entry.platform != DOMAIN:
            continue
        for device_id in removed_device_ids:
            if entity_entry.unique_id.startswith(f"{device_id}_"):
                entities_to_remove.append(entity_entry.entity_id)
                break

    for entity_id in entities_to_remove:
        _LOGGER.info("Removing orphaned entity: %s", entity_id)
        entity_registry.async_remove(entity_id)

    # Clean up firmware history
    for device_id in removed_device_ids:
        firmware_tracker.remove_device(device_id)
        _LOGGER.info("Removed firmware history for device: %s", device_id)

    if removed_device_ids:
        await firmware_tracker.async_save()


async def _cleanup_orphaned_entities_on_startup(
    hass: HomeAssistant,
    entry: ConfigEntry,
    current_device_ids: set[str],
) -> None:
    """Remove entities that reference devices no longer in Ring."""
    entity_registry = er.async_get(hass)

    entities_to_remove = []
    for entity_entry in entity_registry.entities.values():
        if entity_entry.platform != DOMAIN:
            continue
        if entity_entry.config_entry_id != entry.entry_id:
            continue
        # Extract device_id from unique_id (format: {device_id}_{sensor_key})
        unique_id = entity_entry.unique_id
        # Skip coordinator health sensor (not device-specific)
        if unique_id.endswith("_coordinator_health"):
            continue
        # Split on first underscore to get device_id
        parts = unique_id.split("_", 1)
        if len(parts) >= 1:
            device_id = parts[0]
            if device_id and device_id not in current_device_ids:
                entities_to_remove.append(entity_entry.entity_id)

    for entity_id in entities_to_remove:
        _LOGGER.info("Removing orphaned entity on startup: %s", entity_id)
        entity_registry.async_remove(entity_id)
