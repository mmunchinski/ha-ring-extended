"""The Ring Extended integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.ring import DOMAIN as RING_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, DEVICE_FAMILIES, ALL_SENSORS, get_nested
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

    # Run entity reconciliation: remove stale, identify missing
    devices_needing_entities, _ = await _reconcile_entities(hass, entry, devices_dict)
    hass.data[DOMAIN][entry.entry_id]["reconcile_devices"] = devices_needing_entities

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Clean up all entities when integration is permanently removed."""
    entity_registry = er.async_get(hass)

    # Remove all entities for this config entry
    entities_to_remove = [
        entity.entity_id
        for entity in entity_registry.entities.values()
        if entity.platform == DOMAIN and entity.config_entry_id == entry.entry_id
    ]

    for entity_id in entities_to_remove:
        entity_registry.async_remove(entity_id)

    _LOGGER.info("Removed %d entities on integration removal", len(entities_to_remove))

    # Clean up firmware history storage
    firmware_tracker = FirmwareHistoryTracker(hass)
    await firmware_tracker.async_load()
    await firmware_tracker.async_clear_all()


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


async def _reconcile_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
    devices_dict: Any,
) -> tuple[set[str], list[str]]:
    """
    Full entity reconciliation: add missing, remove stale.

    Returns (device_ids_needing_new_entities, entity_ids_removed).
    """
    entity_registry = er.async_get(hass)

    # Build map of existing entities: {unique_id: entity_entry}
    existing_entities: dict[str, er.RegistryEntry] = {}
    for entity in entity_registry.entities.values():
        if entity.platform != DOMAIN or entity.config_entry_id != entry.entry_id:
            continue
        existing_entities[entity.unique_id] = entity

    # Build set of expected unique_ids based on current sensor definitions + device attrs
    expected_unique_ids: set[str] = set()
    current_device_ids: set[str] = set()

    for family in DEVICE_FAMILIES:
        devices = getattr(devices_dict, family, []) or []
        for device in devices:
            device_attrs = getattr(device, "_attrs", {})
            if not device_attrs:
                continue

            device_id = str(getattr(device, "device_id", None) or getattr(device, "id", ""))
            if not device_id:
                continue

            current_device_ids.add(device_id)

            # Determine which sensors should exist for this device
            for description in ALL_SENSORS:
                if description.is_available(device_attrs):
                    expected_unique_ids.add(f"{device_id}_{description.key}")

    # Add special entities (firmware history for devices that have firmware info)
    for family in DEVICE_FAMILIES:
        devices = getattr(devices_dict, family, []) or []
        for device in devices:
            device_attrs = getattr(device, "_attrs", {})
            if device_attrs.get("health", {}).get("firmware_version"):
                device_id = str(getattr(device, "device_id", None) or getattr(device, "id", ""))
                if device_id:
                    expected_unique_ids.add(f"{device_id}_firmware_history")

    # Add coordinator health sensor
    expected_unique_ids.add(f"{entry.entry_id}_coordinator_health")

    # REMOVALS: Entities that exist but shouldn't
    # (sensor deprecated OR device attribute no longer present OR device removed)
    entities_removed: list[str] = []
    for unique_id, entity_entry in existing_entities.items():
        if unique_id not in expected_unique_ids:
            entities_removed.append(entity_entry.entity_id)
            _LOGGER.info(
                "Removing stale entity: %s (unique_id: %s)",
                entity_entry.entity_id,
                unique_id,
            )
            entity_registry.async_remove(entity_entry.entity_id)

    # ADDITIONS: Expected entities that don't exist yet
    existing_unique_ids = set(existing_entities.keys())
    missing_unique_ids = expected_unique_ids - existing_unique_ids

    # Flag devices that need new entities created
    devices_needing_entities: set[str] = set()
    for unique_id in missing_unique_ids:
        # Extract device_id from unique_id
        # Format: {device_id}_{sensor_key} or {entry_id}_coordinator_health
        if unique_id.endswith("_coordinator_health"):
            # Coordinator health sensor needs to be added
            devices_needing_entities.add("__coordinator__")
        else:
            parts = unique_id.split("_", 1)
            if parts[0]:
                devices_needing_entities.add(parts[0])
                _LOGGER.debug("Will add missing entity: %s", unique_id)

    _LOGGER.info(
        "Entity reconciliation: %d entities removed, %d devices need new entities, %d missing sensors",
        len(entities_removed),
        len(devices_needing_entities),
        len(missing_unique_ids),
    )

    return devices_needing_entities, entities_removed
