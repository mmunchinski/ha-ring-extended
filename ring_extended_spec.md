# Ring Extended - Custom Component Specification

## Overview

Create a Home Assistant custom component called `ring_extended` that exposes additional Ring device attributes as sensor entities. The component piggybacks on the existing core `ring` integration's data coordinator rather than making separate API calls.

---

## Key Concept: Sensor Attachment to Existing Devices

**Important:** This integration does NOT create new devices. All sensors created by `ring_extended` attach to the existing Ring devices already in Home Assistant.

When a user has a Ring device called "Front Door Doorbell", the extended sensors will appear under that same device entry:
- `sensor.front_door_doorbell_wifi_signal` 
- `sensor.front_door_doorbell_battery_voltage`
- `sensor.front_door_doorbell_cv_human_enabled`
- etc.

This is achieved by using the same device identifiers as the core Ring integration:

```python
@property
def device_info(self):
    """Link to existing Ring device."""
    return {
        "identifiers": {("ring", self._device.device_id)},
        # No other fields - this links to existing device, doesn't create new one
    }
```

The `("ring", device_id)` tuple must match exactly what the core integration uses.

---

## Project Goals

1. Expose 100+ Ring device attributes that the core integration fetches but doesn't create entities for
2. Create sensors grouped by category (health, CV settings, features, paid features, etc.)
3. Support all Ring camera/doorbell device types
4. No additional API calls - reuse the existing Ring integration's coordinator data
5. HACS-compatible for easy installation

---

## Architecture

```
custom_components/
└── ring_extended/
    ├── __init__.py           # Integration setup, hooks into Ring coordinator
    ├── manifest.json         # HACS/HA manifest with ring dependency
    ├── const.py              # Constants, sensor definitions
    ├── sensor.py             # Sensor entity implementations
    ├── coordinator.py        # Optional: wrapper coordinator if needed
    └── strings.json          # Translations (optional)
```

---

## Technical Approach

### Dependency on Core Ring Integration

The `manifest.json` must declare a dependency on the core `ring` integration:

```json
{
  "domain": "ring_extended",
  "name": "Ring Extended Sensors",
  "codeowners": ["@your-github"],
  "config_flow": true,
  "dependencies": ["ring"],
  "documentation": "https://github.com/your-repo",
  "iot_class": "cloud_polling",
  "issue_tracker": "https://github.com/your-repo/issues",
  "requirements": [],
  "version": "1.0.0"
}
```

### Accessing the Ring Coordinator

The core Ring integration stores its coordinator in `hass.data[RING_DOMAIN]`. The structure is:

```python
from homeassistant.components.ring import DOMAIN as RING_DOMAIN
from homeassistant.components.ring.coordinator import RingDataCoordinator

# In async_setup_entry:
ring_data = hass.data.get(RING_DOMAIN)
if ring_data is None:
    _LOGGER.error("Ring integration not found")
    return False

# ring_data is a dict with config_entry_id keys
# Each entry contains the coordinator and Ring API object
for entry_id, entry_data in ring_data.items():
    coordinator: RingDataCoordinator = entry_data["coordinator"]
    ring_api = entry_data["ring"]  # ring_doorbell.Ring instance
```

### Ring Device Data Structure

The `ring_doorbell` library (v0.9.13) returns device objects with these key attributes accessible via the device's `_attrs` dict or properties:

```python
device._attrs  # Raw dict from Ring API - THIS IS THE GOLD MINE
device.id
device.name  # Same as description
device.device_id
device.kind  # doorbell_oyster, cocoa_doorbell_v2, stickup_cam, etc.
device.family  # doorbells, stickup_cams, chimes, other
```

The `device._attrs` dictionary contains the full API response including:
- `health` - All health/connectivity data
- `settings` - All device settings
- `features` - Feature flags and eligibility
- And all other attributes from the diagnostic export

### Recommended Implementation Pattern

```python
# sensor.py

from dataclasses import dataclass
from typing import Any, Callable
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT

@dataclass(frozen=True)
class RingExtendedSensorDescription(SensorEntityDescription):
    """Describes Ring extended sensor entity."""
    value_fn: Callable[[dict], Any] = None
    category: str = "health"  # For grouping in UI
    available_fn: Callable[[dict], bool] = lambda x: True

# Example sensor definitions
SENSOR_DESCRIPTIONS: list[RingExtendedSensorDescription] = [
    # Health sensors
    RingExtendedSensorDescription(
        key="rssi",
        name="WiFi Signal",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        category="health",
        value_fn=lambda attrs: attrs.get("health", {}).get("rssi"),
    ),
    RingExtendedSensorDescription(
        key="rssi_category",
        name="WiFi Signal Quality",
        category="health",
        value_fn=lambda attrs: attrs.get("health", {}).get("rssi_category"),
    ),
    RingExtendedSensorDescription(
        key="bandwidth",
        name="Bandwidth",
        native_unit_of_measurement="kbps",
        state_class=SensorStateClass.MEASUREMENT,
        category="health",
        value_fn=lambda attrs: attrs.get("health", {}).get("bandwidth"),
    ),
    # ... continue for all attributes
]
```

---

## Sensor Categories and Definitions

Below are all sensors to implement, organized by category. Each entry shows:
- `key`: Unique identifier for the sensor
- `path`: JSON path to extract value from `device._attrs`
- `name`: Human-readable name
- `unit`: Unit of measurement (if applicable)
- `device_class`: HA device class (if applicable)

### Category: Health & Connectivity

| Key | Path | Name | Unit | Device Class |
|-----|------|------|------|--------------|
| `rssi` | `health.rssi` | WiFi Signal Strength | dBm | signal_strength |
| `rssi_category` | `health.rssi_category` | WiFi Signal Quality | - | enum |
| `connected` | `health.connected` | Connected | - | connectivity |
| `packet_loss` | `health.packet_loss` | Packet Loss | % | - |
| `packet_loss_category` | `health.packet_loss_category` | Packet Loss Quality | - | enum |
| `bandwidth` | `health.bandwidth` | Bandwidth | kbps | data_rate |
| `current_bandwidth_mb` | `health.current_bandwidth_mb` | Current Bandwidth | Mbps | data_rate |
| `egress_tx_rate` | `health.egress_tx_rate` | Upload Rate | Mbps | data_rate |
| `egress_tx_rate_category` | `health.egress_tx_rate_category` | Upload Quality | - | enum |
| `wifi_channel` | `health.channel` | WiFi Channel | - | - |
| `uptime_sec` | `health.uptime_sec` | Uptime | s | duration |
| `network_connection_value` | `health.network_connection_value` | Connection Type | - | enum |
| `sidewalk_connection` | `health.sidewalk_connection` | Sidewalk Connected | - | connectivity |

### Category: Power & Battery

| Key | Path | Name | Unit | Device Class |
|-----|------|------|------|--------------|
| `battery_percentage` | `health.battery_percentage` | Battery | % | battery |
| `battery_percentage_category` | `health.battery_percentage_category` | Battery Health | - | enum |
| `battery_voltage` | `health.battery_voltage` | Battery Voltage | mV | voltage |
| `battery_voltage_category` | `health.battery_voltage_category` | Voltage Quality | - | enum |
| `battery_save` | `health.battery_save` | Battery Saver | - | - |
| `ac_power` | `health.ac_power` | AC Power | - | plug |
| `transformer_voltage` | `health.transformer_voltage` | Transformer Voltage | V | voltage |
| `transformer_voltage_category` | `health.transformer_voltage_category` | Transformer Quality | - | enum |
| `ext_power_state` | `health.ext_power_state` | External Power State | - | - |
| `run_mode` | `health.run_mode` | Power Mode | - | enum |

### Category: Firmware

| Key | Path | Name | Unit | Device Class |
|-----|------|------|------|--------------|
| `firmware_version` | `health.firmware_version` | Firmware Version | - | - |
| `firmware_version_status` | `health.firmware_version_status` | Firmware Status | - | enum |
| `ota_status` | `health.ota_status` | OTA Update Status | - | enum |

### Category: Video & Streaming

| Key | Path | Name | Unit | Device Class |
|-----|------|------|------|--------------|
| `vod_enabled` | `health.vod_enabled` | Video on Demand | - | - |
| `vod_status` | `settings.vod_status` | VOD Status | - | enum |
| `stream_resolution` | `health.stream_resolution` | Stream Resolution | - | - |
| `firmware_avg_bitrate` | `health.firmware_avg_bitrate` | Average Bitrate | kbps | data_rate |
| `live_view_preset_profile` | `settings.live_view_preset_profile` | Live View Quality | - | enum |
| `extended_live_view` | `settings.extended_live_view` | Extended Live View | - | - |
| `exposure_control` | `settings.exposure_control` | Exposure Control | - | - |
| `preroll_enabled` | `settings.preroll_enabled` | Pre-roll Enabled | - | - |
| `max_resolution_mode` | `settings.max_resolution_mode` | Max Resolution Mode | - | - |
| `hevc_enabled` | `settings.video_settings.hevc_enabled` | HEVC/H.265 Enabled | - | - |

### Category: Audio

| Key | Path | Name | Unit | Device Class |
|-----|------|------|------|--------------|
| `enable_audio_recording` | `settings.enable_audio_recording` | Audio Recording | - | - |
| `doorbell_volume` | `settings.doorbell_volume` | Doorbell Volume | - | - |
| `voice_volume` | `settings.voice_volume` | Voice Volume | - | - |
| `chime_enabled` | `settings.chime_settings.enable` | Chime Enabled | - | - |
| `chime_duration` | `settings.chime_settings.duration` | Chime Duration | s | duration |

### Category: Motion Detection

| Key | Path | Name | Unit | Device Class |
|-----|------|------|------|--------------|
| `motion_detection_enabled` | `settings.motion_detection_enabled` | Motion Detection | - | - |
| `advanced_motion_detection_enabled` | `settings.advanced_motion_detection_enabled` | Smart Detection | - | - |
| `advanced_motion_detection_human_only_mode` | `settings.advanced_motion_detection_human_only_mode` | Person Only Mode | - | - |
| `motion_snooze_preset_profile` | `settings.motion_snooze_preset_profile` | Motion Snooze | - | enum |
| `loitering_threshold` | `settings.loitering_threshold` | Loitering Threshold | s | duration |

### Category: CV Detection Types

For each detection type in `settings.cv_settings.detection_types`, create a sensor group:

Detection types: `human`, `motion`, `other_motion`, `loitering`, `moving_vehicle`, `vehicle`, `animal`, `package_delivery`, `package_pickup`, `unverified_motion`, `motion_stop`

For each type, expose:
| Key Pattern | Path Pattern | Name Pattern |
|-------------|--------------|--------------|
| `cv_{type}_enabled` | `settings.cv_settings.detection_types.{type}.enabled` | CV {Type} Enabled |
| `cv_{type}_mode` | `settings.cv_settings.detection_types.{type}.mode` | CV {Type} Mode |
| `cv_{type}_notification` | `settings.cv_settings.detection_types.{type}.notification` | CV {Type} Notification |

### Category: Paid Features (CV)

Boolean sensors for subscription features:
| Key | Path | Name |
|-----|------|------|
| `paid_human` | `settings.cv_paid_features.human` | Paid: Human Detection |
| `paid_vehicle` | `settings.cv_paid_features.vehicle` | Paid: Vehicle Detection |
| `paid_animal` | `settings.cv_paid_features.animal` | Paid: Animal Detection |
| `paid_package_delivery` | `settings.cv_paid_features.package_delivery` | Paid: Package Detection |
| `paid_loitering` | `settings.cv_paid_features.loitering` | Paid: Loitering |
| `paid_glass_break` | `settings.cv_paid_features.glass_break` | Paid: Glass Break |
| `paid_baby_cry` | `settings.cv_paid_features.baby_cry` | Paid: Baby Cry |
| `paid_dog_bark` | `settings.cv_paid_features.dog_bark` | Paid: Dog Bark |
| `paid_car_alarm` | `settings.cv_paid_features.car_alarm` | Paid: Car Alarm |
| `paid_co2_smoke_alarm` | `settings.cv_paid_features.co2_smoke_alarm` | Paid: Smoke/CO2 Alarm |

### Category: Other Paid Features

| Key | Path | Name |
|-----|------|------|
| `paid_extended_live_view` | `settings.other_paid_features.extended_live_view` | Paid: Extended Live View |
| `paid_recording_24x7` | `settings.other_paid_features.recording_24x7` | Paid: 24/7 Recording |
| `paid_natural_language_search` | `settings.other_paid_features.natural_language_search` | Paid: Video Search |
| `paid_multicam_live_view` | `settings.other_paid_features.multicam_live_view` | Paid: Multi-cam View |
| `paid_daily_digest` | `settings.other_paid_features.daily_digest` | Paid: Daily Digest |
| `paid_package_protection` | `settings.other_paid_features.package_protection` | Paid: Package Protection |

### Category: Notifications

| Key | Path | Name |
|-----|------|------|
| `rich_notifications` | `settings.enable_rich_notifications` | Rich Notifications |
| `rich_notifications_face_crop` | `settings.rich_notifications_face_crop_enabled` | Face Crop Notifications |
| `rich_notifications_scene_source` | `settings.rich_notifications_scene_source` | Notification Source |

### Category: Recording & Storage

| Key | Path | Name | Unit |
|-----|------|------|------|
| `recording_ttl` | `settings.user_specified_recording_ttl` | Recording Retention | days |
| `lite_24x7_enabled` | `settings.lite_24x7.enabled` | Snapshot History | - |
| `lite_24x7_frequency` | `settings.lite_24x7.frequency_secs` | Snapshot Interval | s |
| `lite_24x7_resolution` | `settings.lite_24x7.resolution_p` | Snapshot Resolution | p |
| `lite_24x7_ttl` | `settings.lite_24x7_footage_ttl` | Snapshot Retention | hours |

### Category: Floodlight (if applicable)

| Key | Path | Name | Unit |
|-----|------|------|------|
| `floodlight_on` | `health.floodlight_on` | Floodlight On | - |
| `floodlight_duration` | `settings.floodlight_settings.duration` | Floodlight Duration | s |
| `floodlight_brightness` | `settings.floodlight_settings.brightness` | Floodlight Brightness | - |
| `floodlight_always_on` | `settings.floodlight_settings.always_on` | Floodlight Always On | - |

### Category: Radar / Bird's Eye (if applicable)

| Key | Path | Name |
|-----|------|------|
| `birds_eye_view_enabled` | `settings.radar_settings.birds_eye_view_enabled` | Bird's Eye View |
| `installation_height` | `settings.radar_settings.installation_height` | Installation Height |
| `bez_feature_enabled` | `settings.radar_settings.bez_feature_enabled` | BEZ Feature |

### Category: Feature Eligibility

| Key | Path | Name |
|-----|------|------|
| `sheila_camera_eligible` | `features.sheila_camera_eligible` | Local Processing Eligible |
| `sheila_camera_processing_eligible` | `features.sheila_camera_processing_eligible` | Local CV Eligible |
| `rich_notifications_eligible` | `features.rich_notifications_eligible` | Rich Notifications Eligible |
| `recording_mode` | `features.video_recording.recording_mode` | Recording Mode |
| `recording_state` | `features.video_recording.recording_state` | Recording State |

### Category: Local Processing (Sheila)

| Key | Path | Name |
|-----|------|------|
| `sheila_cv_enabled` | `settings.sheila_settings.cv_processing_enabled` | Local CV Processing |
| `sheila_storage_enabled` | `settings.sheila_settings.local_storage_enabled` | Local Storage |

### Category: Device Flags

| Key | Path | Name |
|-----|------|------|
| `night_mode_on` | `health.night_mode_on` | Night Vision Active |
| `siren_on` | `health.siren_on` | Siren Active |
| `hatch_open` | `health.hatch_open` | Battery Hatch Open |
| `stolen` | `stolen` | Marked Stolen |
| `is_sidewalk_gateway` | `is_sidewalk_gateway` | Sidewalk Gateway |

---

## Config Flow

Implement a simple config flow that:
1. Checks if the Ring integration is configured
2. Allows user to select which sensor categories to enable
3. Allows selection of which devices to create sensors for

```python
# config_flow.py

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.ring import DOMAIN as RING_DOMAIN

SENSOR_CATEGORIES = [
    "health",
    "power",
    "firmware", 
    "video",
    "audio",
    "motion",
    "cv_detection",
    "paid_features",
    "notifications",
    "recording",
    "floodlight",
    "radar",
    "features",
    "local_processing",
    "device_flags",
]

class RingExtendedConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    
    async def async_step_user(self, user_input=None):
        errors = {}
        
        # Check Ring integration exists
        if RING_DOMAIN not in self.hass.data:
            return self.async_abort(reason="ring_not_configured")
        
        if user_input is not None:
            return self.async_create_entry(
                title="Ring Extended",
                data=user_input
            )
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("categories", default=SENSOR_CATEGORIES): 
                    cv.multi_select({cat: cat.replace("_", " ").title() 
                                    for cat in SENSOR_CATEGORIES}),
            }),
            errors=errors,
        )
```

---

## Entity Naming Convention

Entity IDs should follow:
```
sensor.ring_extended_{device_name}_{category}_{attribute}
```

Examples:
- `sensor.ring_extended_front_door_health_rssi`
- `sensor.ring_extended_front_door_health_battery_percentage`
- `sensor.ring_extended_backyard_cv_human_enabled`

Friendly names should be:
```
{Device Name} {Attribute Name}
```

Examples:
- "Front Door WiFi Signal"
- "Front Door Battery"
- "Backyard CV Human Enabled"

---

## Device Linking

All sensors should be linked to the parent Ring device using device_info:

```python
@property
def device_info(self):
    return {
        "identifiers": {(RING_DOMAIN, self._device.device_id)},
        # Links to existing Ring device, don't create new device entry
    }
```

This ensures sensors appear under the existing Ring device in the HA UI.

---

## Update Coordination

The component should listen to the Ring integration's coordinator updates:

```python
async def async_setup_entry(hass, entry, async_add_entities):
    ring_data = hass.data[RING_DOMAIN]
    
    entities = []
    for entry_id, data in ring_data.items():
        coordinator = data["coordinator"]
        devices = coordinator.data["devices"]
        
        for device_type in ["doorbells", "stickup_cams", "chimes"]:
            for device in devices.get(device_type, []):
                for description in SENSOR_DESCRIPTIONS:
                    if description.available_fn(device._attrs):
                        entities.append(
                            RingExtendedSensor(device, coordinator, description)
                        )
    
    async_add_entities(entities)
```

---

## Error Handling

1. Handle missing attributes gracefully - many attributes are device-specific
2. Use `available_fn` to check if an attribute exists before creating sensor
3. Return `None` for sensor state if attribute becomes unavailable
4. Log warnings for unexpected data structures

```python
@property
def native_value(self):
    try:
        return self.entity_description.value_fn(self._device._attrs)
    except (KeyError, TypeError, AttributeError):
        return None

@property
def available(self) -> bool:
    return (
        self.coordinator.last_update_success
        and self.entity_description.available_fn(self._device._attrs)
    )
```

---

## Testing Considerations

1. Test with diagnostic export data structure
2. Handle devices with varying capability sets
3. Test coordinator update propagation
4. Verify entity state restoration on HA restart

---

## HACS Configuration

Include `hacs.json` for HACS compatibility:

```json
{
  "name": "Ring Extended Sensors",
  "homeassistant": "2024.1.0",
  "render_readme": true,
  "zip_release": true,
  "filename": "ring_extended.zip"
}
```

---

## Implementation Notes

### Accessing device._attrs

The `ring_doorbell` library's device objects store raw API data in `_attrs`. This is technically a private attribute but is stable and the only way to access the full data:

```python
# This is how to get the raw data
device._attrs  # Returns full dict matching diagnostic export structure
```

### Coordinator Data Structure

The RingDataCoordinator stores data like:
```python
coordinator.data = {
    "devices": {
        "doorbells": [RingDoorBell, ...],
        "stickup_cams": [RingStickUpCam, ...],
        "chimes": [RingChime, ...],
        "other": [RingOther, ...]
    }
}
```

### Diagnostic Export Reference

The uploaded diagnostic file (`config_entry-ring-*.json`) shows the exact structure. The `device_data` array contains the raw API response for each device. Use this as the authoritative reference for attribute paths.

---

## Files to Generate

1. `__init__.py` - Integration setup
2. `manifest.json` - Integration manifest
3. `const.py` - Constants and sensor descriptions
4. `sensor.py` - Sensor entity class
5. `config_flow.py` - Configuration UI
6. `strings.json` - UI strings
7. `README.md` - Documentation
8. `hacs.json` - HACS metadata

---

## Reference: Device Types

| Kind Value | Device Type | Family |
|------------|-------------|--------|
| `doorbell_oyster` | Battery Doorbell | doorbells |
| `cocoa_doorbell_v2` | Doorbell 4 | doorbells |
| `doorbell_portal` | Doorbell Pro | doorbells |
| `jbox_v1` | Doorbell Elite | doorbells |
| `lpd_v1` | Doorbell Wired | doorbells |
| `lpd_v2` | Doorbell Wired (Gen 2) | doorbells |
| `stickup_cam` | Stick Up Cam | stickup_cams |
| `stickup_cam_v4` | Stick Up Cam Battery | stickup_cams |
| `spotlightw_v2` | Spotlight Cam Wired | stickup_cams |
| `hp_cam_v1` | Floodlight Cam | stickup_cams |
| `hp_cam_v2` | Floodlight Cam Pro | stickup_cams |
| `cocoa_floodlight` | Floodlight Cam Wired Plus | stickup_cams |
| `three_p_cam` | Third-party Camera (Blink) | stickup_cams |
| `base_station_v1` | Ring Alarm Base Station | other |
| `chime` | Ring Chime | chimes |
| `chime_pro` | Ring Chime Pro | chimes |

---

## Summary

This custom component will expose the ~200 Ring device attributes identified in the diagnostic export as Home Assistant sensor entities. By reusing the existing Ring integration's coordinator, it avoids duplicate API calls while providing deep visibility into device health, settings, and features.

The implementation should be straightforward since all the data is already being fetched - it just needs to be exposed as entities.

---

## Installation Instructions

### Prerequisites

The core **Ring integration must already be configured and working** in Home Assistant. This custom component depends on it and will not load without it.

### Method 1: HACS Installation (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed in Home Assistant
2. Open HACS from the sidebar
3. Click the three-dot menu (top right) → **Custom repositories**
4. Enter the GitHub repository URL
5. Select **Integration** as the category
6. Click **Add**
7. Search for "Ring Extended" in HACS integrations
8. Click **Download**
9. **Restart Home Assistant**
10. Go to **Settings → Devices & Services → Add Integration**
11. Search for "Ring Extended" and configure

### Method 2: Manual Installation

1. Download or clone the repository
2. Copy the `custom_components/ring_extended` folder to your Home Assistant config directory:
   ```
   <config_dir>/custom_components/ring_extended/
   ```
3. Verify the file structure:
   ```
   custom_components/
   └── ring_extended/
       ├── __init__.py
       ├── manifest.json
       ├── const.py
       ├── sensor.py
       ├── config_flow.py
       ├── strings.json
       └── translations/
           └── en.json
   ```
4. **Restart Home Assistant**
5. Go to **Settings → Devices & Services → Add Integration**
6. Search for "Ring Extended" and configure

### Configuration

During setup, you'll be prompted to select which sensor categories to enable:
- **Health** - WiFi signal, connectivity, bandwidth, uptime
- **Power** - Battery percentage, voltage, AC power status
- **Firmware** - Version, update status
- **Video** - Streaming settings, resolution, VOD status
- **Audio** - Volume levels, recording settings
- **Motion** - Detection settings, sensitivity, zones
- **CV Detection** - Computer vision detection types (human, vehicle, package, etc.)
- **Paid Features** - Subscription feature flags
- **Notifications** - Rich notification settings
- **Recording** - Storage and retention settings
- **Floodlight** - Light settings (floodlight devices only)
- **Radar** - Bird's Eye View settings (supported devices only)
- **Features** - Feature eligibility flags
- **Local Processing** - Sheila/edge processing settings
- **Device Flags** - Night mode, siren, stolen status

### Post-Installation

After configuration, sensors will automatically appear under your existing Ring devices. Navigate to any Ring device in **Settings → Devices & Services → Ring** to see the new sensors.

---

## Implementation Guidance for Claude Code

### Critical Implementation Details

1. **Accessing Device Data**
   
   The `ring_doorbell` library stores the full API response in `device._attrs`. This is technically a private attribute but is the only way to access the complete data:
   ```python
   # This returns the full dict matching the diagnostic export structure
   raw_data = device._attrs
   health_data = raw_data.get("health", {})
   settings_data = raw_data.get("settings", {})
   features_data = raw_data.get("features", {})
   ```

2. **Hooking Into the Ring Coordinator**
   
   The Ring integration stores its data in `hass.data["ring"]`. The structure varies slightly by HA version, so implement defensive access:
   ```python
   from homeassistant.components.ring import DOMAIN as RING_DOMAIN
   
   ring_data = hass.data.get(RING_DOMAIN)
   if not ring_data:
       raise ConfigEntryNotReady("Ring integration not loaded")
   
   # ring_data contains config entries with coordinators
   # Access pattern may be:
   # - ring_data[entry.entry_id] for newer versions
   # - Direct coordinator access for older versions
   ```

3. **Device Families**
   
   Ring devices are organized by family. Iterate all families when creating sensors:
   ```python
   DEVICE_FAMILIES = ["doorbells", "stickup_cams", "chimes", "other"]
   
   for family in DEVICE_FAMILIES:
       devices = ring_api.devices().get(family, [])
       for device in devices:
           # Create sensors for this device
   ```

4. **Graceful Attribute Handling**
   
   Not all devices have all attributes. Always use defensive access:
   ```python
   def get_nested(data: dict, path: str, default=None):
       """Safely get nested dictionary value."""
       keys = path.split(".")
       for key in keys:
           if isinstance(data, dict):
               data = data.get(key)
           else:
               return default
           if data is None:
               return default
       return data
   
   # Usage
   rssi = get_nested(device._attrs, "health.rssi")
   cv_human = get_nested(device._attrs, "settings.cv_settings.detection_types.human.enabled")
   ```

5. **Entity Availability**
   
   Mark entities unavailable when their attribute doesn't exist:
   ```python
   @property
   def available(self) -> bool:
       if not self.coordinator.last_update_success:
           return False
       value = get_nested(self._device._attrs, self.entity_description.path)
       return value is not None
   ```

6. **Coordinator Updates**
   
   Extend `CoordinatorEntity` to automatically receive updates:
   ```python
   from homeassistant.helpers.update_coordinator import CoordinatorEntity
   
   class RingExtendedSensor(CoordinatorEntity, SensorEntity):
       def __init__(self, device, coordinator, description):
           super().__init__(coordinator)
           self._device = device
           self.entity_description = description
   ```

### Common Pitfalls

1. **Don't create a new device entry** - Use `device_info` with only `identifiers` to link to existing Ring device

2. **Don't make API calls** - All data comes from the existing coordinator's cached data

3. **Handle type coercion** - Some Ring API values are strings that should be numbers:
   ```python
   # "465" -> 465
   bitrate = get_nested(attrs, "health.firmware_avg_bitrate")
   if bitrate:
       bitrate = int(bitrate)
   ```

4. **Handle null vs missing** - Ring API sometimes returns `null` explicitly vs omitting the key entirely. Both should result in `None`.

5. **Category filtering** - Respect the user's category selections from config flow. Don't create sensors for disabled categories.

### Suggested File Implementation Order

1. **const.py** - Define DOMAIN, sensor descriptions, categories
2. **manifest.json** - Integration metadata with ring dependency  
3. **sensor.py** - Sensor entity class and setup
4. **config_flow.py** - User configuration UI
5. **__init__.py** - Integration setup, coordinator hookup
6. **strings.json** / **translations/en.json** - UI strings

### Testing Checklist

- [ ] Integration loads only when Ring integration is configured
- [ ] Sensors appear under existing Ring devices (not new devices)
- [ ] Sensors update when Ring coordinator refreshes
- [ ] Missing attributes don't cause errors
- [ ] Category filtering works correctly
- [ ] Entity IDs follow naming convention
- [ ] Sensor values match diagnostic export data
- [ ] Floodlight/radar sensors only appear on applicable devices

---

## GitHub Repository Structure

```
ring_extended/
├── README.md
├── LICENSE
├── hacs.json
├── custom_components/
│   └── ring_extended/
│       ├── __init__.py
│       ├── manifest.json
│       ├── const.py
│       ├── sensor.py
│       ├── config_flow.py
│       ├── strings.json
│       └── translations/
│           └── en.json
└── .github/
    └── workflows/
        └── validate.yaml  # Optional: HACS validation
```
