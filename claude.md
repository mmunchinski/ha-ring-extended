# Claude Code Context - Ring Extended

## Project Overview

This is a Home Assistant custom component called `ring_extended` that exposes additional Ring camera/doorbell attributes as sensor entities. The integration piggybacks on the existing core Ring integration's data coordinator - it makes NO additional API calls.

## Key Architecture Decisions

1. **No new devices** - All sensors attach to existing Ring devices using matching `device_info` identifiers
2. **No API calls** - Data comes from `device._attrs` via the existing Ring coordinator
3. **Category-based filtering** - Users select which sensor groups to enable during setup
4. **HACS-compatible** - Standard custom component structure

## File Structure

```
ha-ring-extended/
├── claude.md                 # This file - project context for Claude
├── hacs.json                 # HACS configuration
├── README.md                 # User documentation
├── ring_extended_spec.md     # Original specification
├── ring_extended_attributes.json  # Attribute reference
├── ring_attributes.md        # Human-readable attribute list
└── custom_components/
    └── ring_extended/
        ├── __init__.py       # Integration setup, hooks into Ring coordinator
        ├── manifest.json     # HA manifest with ring dependency
        ├── const.py          # Sensor definitions (130+ sensors, 16 categories)
        ├── sensor.py         # RingExtendedSensor entity class
        ├── config_flow.py    # Setup UI with category selection
        ├── strings.json      # UI strings
        └── translations/
            └── en.json       # English translations
```

## Sensor Categories

| Category | Description |
|----------|-------------|
| health | WiFi signal, bandwidth, packet loss, uptime |
| power | Battery percentage, voltage, AC power, transformer |
| firmware | Version, OTA status |
| video | VOD, resolution, HEVC, streaming settings |
| audio | Volumes, chime settings, audio recording |
| motion | Detection enabled, sensitivity, zones |
| cv_detection | Human/vehicle/animal/package detection modes |
| cv_paid | CV subscription feature flags |
| other_paid | Other subscription features |
| notifications | Rich notifications, face crop |
| recording | Retention, snapshot history (lite 24x7) |
| floodlight | Brightness, duration, always-on |
| radar | Bird's Eye View settings |
| local_processing | Sheila/edge processing settings |
| features | Feature eligibility flags |
| device_status | Night mode, siren, stolen, device type |

## Technical Details

### Accessing Ring Data (HA 2024.1+)

The Ring integration uses the modern `runtime_data` pattern. Data is stored on the config entry, not in `hass.data`:

```python
from homeassistant.components.ring import DOMAIN as RING_DOMAIN

# Find Ring config entries
ring_entries = [
    e for e in hass.config_entries.async_entries()
    if e.domain == RING_DOMAIN
]
ring_entry = ring_entries[0]

# Access RingData from runtime_data
ring_data = ring_entry.runtime_data
# RingData has: api, devices, devices_coordinator, listen_coordinator

coordinator = ring_data.devices_coordinator
devices = ring_data.devices  # RingDevices object

# Iterate device families
for device in devices.doorbells:
    attrs = device._attrs  # Raw API data
```

### Device Linking
```python
@property
def device_info(self):
    return {"identifiers": {("ring", self._device.device_id)}}
```

## Development Workflow

### IMPORTANT: Documentation and Git Updates

**After every change to the codebase, you MUST:**

1. **Update README.md** if the change affects:
   - Features or capabilities
   - Installation or configuration steps
   - Sensor categories or available sensors
   - Requirements or compatibility

2. **Update claude.md** if the change affects:
   - Architecture or file structure
   - Technical implementation details
   - Development workflows or conventions
   - New patterns or approaches used

3. **Commit changes to git** with a descriptive message:
   ```bash
   git add -A
   git commit -m "Description of changes"
   ```

### Commit Message Guidelines

- Use present tense ("Add feature" not "Added feature")
- Be specific about what changed
- Reference sensor categories or files when relevant

Examples:
- `Add new cv_detection sensors for motion_stop type`
- `Fix battery_voltage value extraction for battery devices`
- `Update README with new floodlight sensor documentation`

### Adding New Sensors

1. Add sensor definition to appropriate tuple in `const.py`
2. Add translation in both `strings.json` and `translations/en.json`
3. Update README.md if it's a notable addition
4. Update claude.md if it affects architecture
5. Commit changes

### Testing Checklist

- [ ] Integration loads when Ring is configured
- [ ] Sensors appear under existing Ring devices
- [ ] Sensors update when coordinator refreshes
- [ ] Missing attributes don't cause errors
- [ ] Category filtering works in config flow
- [ ] Options flow allows reconfiguration

## Dependencies

- Home Assistant 2024.1.0+
- Core Ring integration must be configured and working
- No additional Python packages required

## Common Issues

1. **Sensors not appearing**: Verify Ring integration is loaded first
2. **"Unknown" values**: Attribute doesn't exist for that device type
3. **No updates**: Updates come from Ring coordinator (~5 min interval)
4. **Timestamp sensor errors**: If a sensor with `device_class=TIMESTAMP` throws errors about `'int' object has no attribute 'tzinfo'`, the Ring API is returning a Unix timestamp integer instead of a datetime. Use a `value_fn` to convert:
   ```python
   value_fn=lambda attrs: _unix_to_datetime(get_nested(attrs, "path.to.timestamp"))
   ```

## Data Type Handling

### Timestamps
Ring API returns timestamps as Unix integers (e.g., `1766949790`). Home Assistant's timestamp device class expects datetime objects with timezone. Use the `_unix_to_datetime()` helper in const.py:

```python
def _unix_to_datetime(timestamp: int | None) -> datetime | None:
    """Convert Unix timestamp to datetime with timezone."""
    if timestamp is None:
        return None
    try:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        return None
```

### Booleans
Some Ring attributes use integers (0/1) instead of booleans. Convert with `value_fn=lambda attrs: bool(get_nested(attrs, "path"))`.

### Duration/Uptime
Ring returns uptime as raw seconds. Use `_format_uptime()` helper for human-readable format:

```python
def _format_uptime(seconds: int | None) -> str | None:
    """Convert seconds to human-readable uptime format."""
    if seconds is None:
        return None
    try:
        seconds = int(seconds)
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        mins = (seconds % 3600) // 60
        return f"{days}d {hours}h {mins}m"
    except (ValueError, TypeError):
        return None
```

## Version History

- **1.0.2**: Add human-readable `uptime_formatted` sensor (e.g., "5d 12h 30m")
- **1.0.1**: Fix timestamp conversion for `last_update_time` sensor (Unix int → datetime)
- **1.0.0**: Initial release with 130+ sensors across 16 categories
