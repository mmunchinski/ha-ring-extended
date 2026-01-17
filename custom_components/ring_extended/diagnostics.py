"""Diagnostics support for Ring Extended."""
from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.components.ring import DOMAIN as RING_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import ALL_SENSORS, DEVICE_FAMILIES, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Keys to redact from diagnostics for privacy
TO_REDACT = {
    "address",
    "latitude",
    "longitude",
    "email",
    "first_name",
    "last_name",
    "location_id",
    "ring_id",
    "owner",
    "shared_users",
    "description",
    "time_zone",
}


def _extract_all_attribute_paths(attrs: dict, prefix: str = "") -> set[str]:
    """Recursively extract all attribute paths from a nested dict."""
    paths: set[str] = set()
    for key, value in attrs.items():
        full_path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            paths.update(_extract_all_attribute_paths(value, full_path))
        else:
            paths.add(full_path)
    return paths


def _get_sensor_coverage(device_attrs: dict) -> dict[str, Any]:
    """Analyze sensor coverage for a device."""
    # Get all attribute paths in the device
    all_attr_paths = _extract_all_attribute_paths(device_attrs)

    # Get defined sensor paths
    defined_paths: set[str] = set()
    available_sensors: list[str] = []
    unavailable_sensors: list[str] = []

    for description in ALL_SENSORS:
        defined_paths.add(description.attr_path)
        if description.is_available(device_attrs):
            available_sensors.append(description.key)
        else:
            unavailable_sensors.append(description.key)

    # Find uncovered attributes (in API but no sensor defined)
    uncovered_paths = all_attr_paths - defined_paths

    # Find stale sensor definitions (sensor defined but not in API)
    stale_paths = defined_paths - all_attr_paths

    return {
        "total_api_attributes": len(all_attr_paths),
        "total_sensor_definitions": len(ALL_SENSORS),
        "available_sensors": len(available_sensors),
        "unavailable_sensors": len(unavailable_sensors),
        "uncovered_attribute_paths": sorted(uncovered_paths),
        "stale_sensor_paths": sorted(stale_paths),
        "available_sensor_keys": sorted(available_sensors),
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    # Get Ring data
    ring_entries = [
        e for e in hass.config_entries.async_entries()
        if e.domain == RING_DOMAIN
    ]

    if not ring_entries:
        return {"error": "Ring integration not found"}

    ring_entry = ring_entries[0]
    if not hasattr(ring_entry, "runtime_data") or ring_entry.runtime_data is None:
        return {"error": "Ring runtime_data not available"}

    ring_data = ring_entry.runtime_data
    devices_dict = getattr(ring_data, "devices", None)

    if devices_dict is None:
        return {"error": "Ring devices not found"}

    # Get entity registry info
    entity_registry = er.async_get(hass)
    ring_extended_entities = [
        {
            "entity_id": entity.entity_id,
            "unique_id": entity.unique_id,
            "disabled": entity.disabled,
        }
        for entity in entity_registry.entities.values()
        if entity.platform == DOMAIN and entity.config_entry_id == entry.entry_id
    ]

    # Collect device information
    devices_info: dict[str, Any] = {}
    model_comparison: dict[str, list[str]] = {}

    for family in DEVICE_FAMILIES:
        devices = getattr(devices_dict, family, []) or []
        for device in devices:
            name = getattr(device, "name", "unknown")
            model = getattr(device, "model", "unknown")
            device_id = str(
                getattr(device, "device_id", None) or getattr(device, "id", "")
            )
            attrs = getattr(device, "_attrs", {})

            if not attrs:
                continue

            # Redact sensitive data
            redacted_attrs = async_redact_data(attrs, TO_REDACT)

            # Analyze sensor coverage
            coverage = _get_sensor_coverage(attrs)

            # Count entities for this device
            device_entities = [
                e for e in ring_extended_entities
                if e["unique_id"].startswith(f"{device_id}_")
            ]

            devices_info[name] = {
                "device_id": device_id,
                "model": model,
                "family": family,
                "entity_count": len(device_entities),
                "sensor_coverage": coverage,
                "attrs": redacted_attrs,
            }

            # Track models for comparison
            if model not in model_comparison:
                model_comparison[model] = []
            model_comparison[model].append(name)

    # Find inconsistencies between same-model devices
    inconsistencies: list[dict[str, Any]] = []
    for model, device_names in model_comparison.items():
        if len(device_names) < 2:
            continue

        # Compare attribute paths between devices of same model
        attr_paths_by_device: dict[str, set[str]] = {}
        for name in device_names:
            device_info = devices_info.get(name, {})
            attrs = device_info.get("attrs", {})
            attr_paths_by_device[name] = _extract_all_attribute_paths(attrs)

        # Find differences
        all_paths = set()
        for paths in attr_paths_by_device.values():
            all_paths.update(paths)

        for name, paths in attr_paths_by_device.items():
            missing = all_paths - paths
            if missing:
                inconsistencies.append({
                    "model": model,
                    "device": name,
                    "missing_attributes": sorted(missing),
                })

    return {
        "config_entry": {
            "entry_id": entry.entry_id,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
        },
        "total_entities": len(ring_extended_entities),
        "total_devices": len(devices_info),
        "model_comparison": model_comparison,
        "inconsistencies": inconsistencies,
        "devices": devices_info,
        "entities": ring_extended_entities,
    }
