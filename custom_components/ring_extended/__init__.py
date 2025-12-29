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

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "ring_entry": ring_entry,
    }

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
