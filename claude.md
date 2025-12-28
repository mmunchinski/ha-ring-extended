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

### Accessing Ring Data
```python
from homeassistant.components.ring import DOMAIN as RING_DOMAIN

ring_data = hass.data[RING_DOMAIN]
for entry_id, entry_data in ring_data.items():
    coordinator = entry_data["coordinator"]
    ring_api = entry_data["ring"]
    devices = ring_api.devices()
    for device in devices.get("doorbells", []):
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

## Version History

- **1.0.0**: Initial release with 130+ sensors across 16 categories
