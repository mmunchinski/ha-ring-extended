"""Firmware history tracking for Ring devices."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

_LOGGER = logging.getLogger(__name__)

STORAGE_KEY = "ring_extended_firmware_history"
STORAGE_VERSION = 1


class FirmwareHistoryTracker:
    """Track firmware version changes for Ring devices."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the firmware history tracker."""
        self.hass = hass
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._history: dict[str, list[dict[str, Any]]] = {}
        self._current_versions: dict[str, str] = {}
        self._loaded = False

    async def async_load(self) -> None:
        """Load firmware history from storage."""
        if self._loaded:
            return

        data = await self._store.async_load()
        if data:
            self._history = data.get("history", {})
            self._current_versions = data.get("current_versions", {})
        self._loaded = True
        _LOGGER.debug("Loaded firmware history for %d devices", len(self._history))

    async def async_save(self) -> None:
        """Save firmware history to storage."""
        await self._store.async_save({
            "history": self._history,
            "current_versions": self._current_versions,
        })

    def check_and_update(
        self, device_id: str, device_name: str, firmware_version: str
    ) -> dict[str, Any] | None:
        """Check for firmware change and update history.

        Returns change info if firmware changed, None otherwise.
        """
        if not firmware_version or firmware_version in ("unavailable", "unknown"):
            return None

        # Get the previous version for this device
        previous_version = self._current_versions.get(device_id)

        # If this is a new device or version changed
        if previous_version != firmware_version:
            timestamp = datetime.now().isoformat()

            change_entry = {
                "version": firmware_version,
                "previous_version": previous_version,
                "timestamp": timestamp,
                "device_name": device_name,
            }

            # Initialize history for device if needed
            if device_id not in self._history:
                self._history[device_id] = []

            # Add to history
            self._history[device_id].append(change_entry)
            self._current_versions[device_id] = firmware_version

            _LOGGER.info(
                "Firmware change detected for %s: %s -> %s",
                device_name,
                previous_version or "initial",
                firmware_version,
            )

            return change_entry

        return None

    def get_device_history(self, device_id: str) -> list[dict[str, Any]]:
        """Get firmware history for a specific device."""
        return self._history.get(device_id, [])

    def get_all_history(self) -> dict[str, list[dict[str, Any]]]:
        """Get all firmware history."""
        return self._history

    def get_recent_changes(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get most recent firmware changes across all devices."""
        all_changes = []
        for device_id, history in self._history.items():
            for entry in history:
                entry_with_id = {**entry, "device_id": device_id}
                all_changes.append(entry_with_id)

        # Sort by timestamp descending
        all_changes.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return all_changes[:limit]

    def get_changelog_text(self) -> str:
        """Get a formatted changelog string for display."""
        changes = self.get_recent_changes(50)
        if not changes:
            return "No firmware changes recorded yet"

        lines = []
        for change in changes:
            ts = change.get("timestamp", "")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts)
                    date_str = dt.strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    date_str = ts[:16]
            else:
                date_str = "Unknown"

            device = change.get("device_name", "Unknown")
            version = change.get("version", "?")
            prev = change.get("previous_version")

            if prev:
                lines.append(f"{date_str} | {device}: {prev} -> {version}")
            else:
                lines.append(f"{date_str} | {device}: {version} (initial)")

        return "\n".join(lines)

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of firmware status."""
        # Group devices by current version
        version_groups: dict[str, list[str]] = {}
        for device_id, version in self._current_versions.items():
            if version not in version_groups:
                version_groups[version] = []
            # Try to get device name from history
            device_history = self._history.get(device_id, [])
            if device_history:
                device_name = device_history[-1].get("device_name", device_id)
            else:
                device_name = device_id
            version_groups[version].append(device_name)

        # Count total changes
        total_changes = sum(len(h) for h in self._history.values())

        return {
            "total_devices": len(self._current_versions),
            "unique_versions": len(version_groups),
            "total_changes": total_changes,
            "version_groups": version_groups,
        }
