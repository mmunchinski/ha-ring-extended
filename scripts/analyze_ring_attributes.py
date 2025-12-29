#!/usr/bin/env python3
"""
Ring Attribute Analyzer

Compares Ring device attributes from HA diagnostics against
the sensors defined in ring_extended to find:
- New attributes not yet exposed as sensors
- Defined sensors whose attributes no longer exist

Usage:
  # Manual mode - analyze downloaded diagnostic file:
  python analyze_ring_attributes.py /path/to/diagnostics.json

  # API mode - fetch directly from HA (requires token):
  python analyze_ring_attributes.py --host 192.168.1.201 --token YOUR_TOKEN

  # Show all attributes (not just differences):
  python analyze_ring_attributes.py diagnostics.json --show-all
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path to import const
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components" / "ring_extended"))

try:
    from const import ALL_SENSORS, get_nested
except ImportError:
    print("Error: Could not import from const.py")
    print("Make sure you're running from the ring_extended repository root")
    sys.exit(1)


def extract_all_paths(data: dict, prefix: str = "") -> set[str]:
    """Recursively extract all attribute paths from a dictionary."""
    paths = set()

    if not isinstance(data, dict):
        return paths

    for key, value in data.items():
        current_path = f"{prefix}.{key}" if prefix else key

        # Skip certain keys that are not useful as sensors
        skip_keys = {
            "id", "device_id", "location_id", "owner", "address",
            "latitude", "longitude", "wifi_name", "description",
            "ring_id", "schema_id", "device_resource_id", "alerts",
            "motion_zones", "advanced_motion_zones", "ignore_zones",
            "advanced_pir_motion_zones", "motion_snooze_presets",
            "live_view_presets", "supported_rpc_commands"
        }
        if key in skip_keys:
            continue

        if isinstance(value, dict):
            # Recurse into nested dicts
            paths.update(extract_all_paths(value, current_path))
        elif isinstance(value, list):
            # Skip lists (usually complex nested structures)
            pass
        else:
            # Leaf value - add the path
            paths.add(current_path)

    return paths


def get_defined_paths() -> set[str]:
    """Get all attribute paths defined in our sensors."""
    paths = set()
    for sensor in ALL_SENSORS:
        if sensor.attr_path:
            paths.add(sensor.attr_path)
    return paths


def load_diagnostics(file_path: str) -> dict:
    """Load diagnostics from a JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data


def fetch_diagnostics(host: str, token: str, entry_id: str) -> dict:
    """Fetch diagnostics from HA API."""
    import urllib.request
    import ssl

    url = f"http://{host}:8123/api/diagnostics/config_entry/{entry_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    req = urllib.request.Request(url, headers=headers)

    # Allow self-signed certs
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
        return json.loads(response.read().decode())


def extract_device_data(diagnostics: dict) -> list[dict]:
    """Extract device data from diagnostics structure."""
    # Try different possible structures
    if "data" in diagnostics:
        data = diagnostics["data"]
        if "device_data" in data:
            return data["device_data"]
        if "devices" in data:
            return data["devices"]

    if "device_data" in diagnostics:
        return diagnostics["device_data"]

    # Maybe it's already the device list
    if isinstance(diagnostics, list):
        return diagnostics

    return []


def analyze(diagnostics: dict, show_all: bool = False) -> None:
    """Analyze Ring attributes and compare with defined sensors."""
    devices = extract_device_data(diagnostics)

    if not devices:
        print("Error: Could not find device data in diagnostics")
        print("Expected structure: data.device_data[] or device_data[]")
        return

    print(f"\nFound {len(devices)} Ring device(s)\n")
    print("=" * 70)

    defined_paths = get_defined_paths()
    all_ring_paths: set[str] = set()

    for i, device in enumerate(devices):
        device_name = device.get("description", device.get("name", f"Device {i+1}"))
        device_kind = device.get("kind", "unknown")

        print(f"\nDevice: {device_name} ({device_kind})")
        print("-" * 50)

        # Extract all paths from this device
        device_paths = extract_all_paths(device)
        all_ring_paths.update(device_paths)

        # Find new attributes (in Ring but not in our sensors)
        new_attrs = device_paths - defined_paths

        # Find missing attributes (in our sensors but not in Ring)
        missing_attrs = defined_paths - device_paths

        if show_all:
            print(f"\nAll attributes ({len(device_paths)}):")
            for path in sorted(device_paths):
                value = get_nested(device, path)
                value_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                status = "NEW" if path in new_attrs else "   "
                print(f"  {status} {path}: {value_str}")

        if new_attrs:
            print(f"\nNew attributes not exposed as sensors ({len(new_attrs)}):")
            for path in sorted(new_attrs):
                value = get_nested(device, path)
                value_type = type(value).__name__
                print(f"  + {path} ({value_type}): {value}")

        # Only show missing for attributes that could apply to this device type
        relevant_missing = set()
        for path in missing_attrs:
            # Check if the parent path exists (e.g., if health.x is missing but health exists)
            parts = path.split(".")
            if len(parts) > 1:
                parent = parts[0]
                if parent in device:
                    relevant_missing.add(path)

        if relevant_missing:
            print(f"\nDefined sensors with missing attributes ({len(relevant_missing)}):")
            for path in sorted(relevant_missing):
                print(f"  - {path}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total unique Ring attributes found: {len(all_ring_paths)}")
    print(f"Sensors defined in ring_extended:  {len(defined_paths)}")

    total_new = all_ring_paths - defined_paths
    total_missing = defined_paths - all_ring_paths

    print(f"\nNew attributes (potential sensors):  {len(total_new)}")
    print(f"Missing attributes (may be removed): {len(total_missing)}")

    if total_new:
        print("\n--- Suggested new sensors ---")
        for path in sorted(total_new)[:20]:  # Show first 20
            print(f"  {path}")
        if len(total_new) > 20:
            print(f"  ... and {len(total_new) - 20} more")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Ring device attributes from HA diagnostics"
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Path to downloaded diagnostics JSON file"
    )
    parser.add_argument(
        "--host",
        help="Home Assistant host (for API mode)"
    )
    parser.add_argument(
        "--token",
        help="Long-lived access token (for API mode)"
    )
    parser.add_argument(
        "--entry-id",
        default="01JDM8BKMNN9MKQ06DNE71HZ1T",
        help="Ring config entry ID"
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Show all attributes, not just differences"
    )

    args = parser.parse_args()

    if args.host and args.token:
        print(f"Fetching diagnostics from {args.host}...")
        try:
            diagnostics = fetch_diagnostics(args.host, args.token, args.entry_id)
        except Exception as e:
            print(f"Error fetching diagnostics: {e}")
            sys.exit(1)
    elif args.file:
        print(f"Loading diagnostics from {args.file}...")
        try:
            diagnostics = load_diagnostics(args.file)
        except Exception as e:
            print(f"Error loading file: {e}")
            sys.exit(1)
    else:
        parser.print_help()
        print("\nError: Provide either a diagnostics file or --host and --token")
        sys.exit(1)

    analyze(diagnostics, args.show_all)


if __name__ == "__main__":
    main()
