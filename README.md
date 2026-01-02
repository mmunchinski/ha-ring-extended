# Ring Extended Sensors for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/mmunchinski/ha-ring-extended.svg)](https://github.com/mmunchinski/ha-ring-extended/releases)

Expose **249 hidden Ring device attributes** as Home Assistant sensors. This integration surfaces the health metrics, CV detection settings, subscription features, and device configurations that Ring's API provides but the core integration doesn't expose.

## Features

- **Zero additional API calls** - Piggybacks on the existing Ring integration's data
- **Attaches to existing devices** - Sensors appear under your current Ring devices
- **Selective categories** - Enable only the sensor groups you want
- **All device types** - Supports doorbells, stick-up cams, floodlights, and more
- **Firmware history tracking** - Persistent changelog of firmware updates with notifications

### Sensor Categories

| Category | Example Sensors |
|----------|-----------------|
| **Health** | WiFi signal (RSSI), bandwidth, packet loss, uptime, TX rate, video packets |
| **Power** | Battery %, voltage, AC power, transformer voltage, power mode |
| **Firmware** | Version, update status, OTA status, bitrate, version history |
| **Video** | Stream resolution, VOD status, HEVC, IR settings, night mode, camera placement |
| **Audio** | Recording enabled, doorbell volume, mic volume, live view audio |
| **Motion** | Detection enabled, sensitivity, loitering, RLMD, PIR validation, zones |
| **CV Detection** | Human/vehicle/animal/package/sound detection modes (17 types) |
| **CV Paid** | CV subscription feature flags |
| **Other Paid** | Live speak, closed caption, alarm recording, snapshot capture |
| **Notifications** | Rich notifications, face crop, scene source |
| **Recording** | Retention days, snapshot interval, 24/7 lite settings |
| **Floodlight** | Brightness, duration, always-on, light settings |
| **Radar** | Bird's Eye View, BEZ, auto motion sensitivity |
| **Local Processing** | Sheila CV/storage, Stark settings |
| **Features** | 40+ eligibility flags (AI warnings, person ID, unusual alerts, etc.) |
| **Device Status** | Timezone, LED status, siren countdown, setup flow |

## Requirements

- Home Assistant 2024.1.0 or newer
- **Ring integration must be configured and working**

## Installation

### HACS (Recommended)

1. Open HACS → Integrations
2. Click ⋮ menu → **Custom repositories**
3. Add `https://github.com/mmunchinski/ha-ring-extended` as **Integration**
4. Search for "Ring Extended" and download
5. Restart Home Assistant
6. Add integration: **Settings → Devices & Services → Add Integration → Ring Extended**

### Manual

1. Download the latest release
2. Extract and copy `custom_components/ring_extended` to your `<config>/custom_components/` directory
3. Restart Home Assistant
4. Add integration: **Settings → Devices & Services → Add Integration → Ring Extended**

## Configuration

When adding the integration, select which sensor categories to enable. You can always reconfigure later to add or remove categories.

## Example Sensors

After installation, you'll see sensors like:

```
sensor.front_door_wifi_signal          # -52 dBm
sensor.front_door_wifi_signal_quality  # good
sensor.front_door_battery_voltage      # 3926 mV
sensor.front_door_bandwidth            # 6947 kbps
sensor.front_door_uptime               # 1003992 s
sensor.front_door_cv_human_enabled     # true
sensor.front_door_cv_human_mode        # edge
sensor.front_door_firmware_version     # cam-1.28.10800
sensor.front_door_firmware_history     # cam-1.28.10800 (2 updates)
sensor.front_door_lite_24x7_enabled    # true
sensor.backyard_floodlight_brightness  # 8
sensor.backyard_birds_eye_view_enabled # true
```

## Use Cases

### Network Monitoring Dashboard
Track WiFi signal strength, bandwidth, and packet loss across all cameras to identify connectivity issues.

### Battery Health Alerts
Create automations that alert when battery voltage drops or battery health category changes.

### Feature Audit
See which subscription features are enabled across devices and verify CV detection modes.

### Firmware Tracking
Monitor firmware versions and OTA update status across your Ring fleet. Each device has a "Firmware: History" sensor that tracks:
- Current firmware version
- Date firmware was first seen
- Complete changelog with timestamps
- Automatic notifications when firmware updates

## Troubleshooting

### Sensors not appearing
- Verify the core Ring integration is working
- Check Home Assistant logs for errors
- Ensure you selected at least one category during setup

### Sensors show "Unknown"
- The attribute may not exist for that device type
- Check if the device supports the feature (e.g., floodlight sensors only work on floodlight cams)

### Sensors not updating
- Updates come from the Ring integration's coordinator (every ~5 minutes)
- Check that the Ring integration itself is updating

## Technical Details

This integration accesses the raw device data from the `ring_doorbell` Python library that the core Ring integration uses. The data is available in `device._attrs` and contains the full API response from Ring's servers.

No additional API calls are made - all data comes from the existing Ring integration's cached coordinator data.

## Contributing

Contributions welcome! Please open an issue first to discuss proposed changes.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Disclaimer

This project is not affiliated with or endorsed by Ring LLC or Amazon. Use at your own risk.

## Credits

- [Home Assistant Ring Integration](https://www.home-assistant.io/integrations/ring/)
- [python-ring-doorbell](https://github.com/tchellomello/python-ring-doorbell) library
