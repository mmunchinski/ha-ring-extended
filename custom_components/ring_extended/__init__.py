"""The Ring Extended integration."""
from __future__ import annotations

import logging

from homeassistant.components.ring import DOMAIN as RING_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ring Extended from a config entry."""
    # Verify Ring integration is loaded and has data
    ring_data = hass.data.get(RING_DOMAIN)
    if not ring_data:
        raise ConfigEntryNotReady(
            "Ring integration is not loaded. Please configure the Ring integration first."
        )

    # Check if any Ring config entries have data
    has_valid_data = False
    for ring_entry_id, ring_entry_data in ring_data.items():
        if isinstance(ring_entry_data, dict) and ring_entry_data.get("coordinator"):
            has_valid_data = True
            break

    if not has_valid_data:
        raise ConfigEntryNotReady(
            "Ring integration has no valid data. Please wait for Ring to finish loading."
        )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

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
