# Changelog

## v1.9.4

- Add 4 new sensors from Ring API diagnostics audit:
  - `features.ai_labs_daily_clip.eligibility.eligible` - AI Labs Daily Clip eligibility flag (pairs with existing `ai_labs_daily_clip_enabled`)
  - `health.rssi_risk_level` - WiFi signal risk level (re-added; Ring API reintroduced the field since v1.9.0 removal)
  - `health.privacy_shutter` - Privacy shutter state (integer, distinct from `alerts.privacy_cover_enabled` bool)
  - `settings.floodlight_settings.always_on_duration_secs` - Floodlight always-on duration in seconds (pairs with existing minutes sensor)

## v1.9.3

- Add 3 new sensors from Ring API diagnostics audit:
  - `features.ai_labs_daily_clip.enablement.enabled` - AI Labs Daily Clip feature flag (all devices)
  - `alerts.battery` - Battery alert status (doorbell models)
  - `health.battery_level` - Battery level indicator (doorbell models)

## v1.9.2

- Fix diagnostics false positives for alert path aliases (alerts.X / health.alert_X dedup)

## v1.9.1

- Add 7 new health sensors from Ring health check endpoint:
  - `health.average_signal_strength`, `health.average_signal_category` (averaged WiFi signal)
  - `health.latest_signal_strength`, `health.latest_signal_category` (latest WiFi signal)
  - `health.firmware` (firmware update status text, e.g. "Up to Date")
  - `health.packet_loss_strength` (raw packet loss measurement)
  - `health.updated_at` (health data update timestamp)

## v1.9.0

- Add new sensor: `health.encryption_group_error` (encryption group error status)
- Remove 9 stale sensor definitions no longer present in Ring API:
  - `alerts.rssi`, `health.rssi_risk_level`, `hardware_id`, `settings.powered_on`
  - `metadata.imported_from_amazon`, `metadata.is_sidewalk_gateway` (duplicate), `metadata.legacy_fw_migrated`, `metadata.third_party_manufacturer`, `metadata.third_party_model`
- Fix diagnostics to use merged device attributes (matches sensor data pipeline)
- Add new `analyze_new_sensors.py` tool replacing 3 deprecated analysis scripts

## v1.8.0

- Add 35 new sensor definitions from Ring API diagnostics audit
- New health sensors: wifi_name, rssi_risk_level, package_warning_active, alert_rssi, alert_privacy_cover, multi_net_pref
- New PTZ sensors: tilt_step_size, pan/tilt max_acceleration
- New hybrid motion zone sensors: active_motion_filter, advanced_motion_zones_enabled/type, enable_audio, enable_pir_validation, enable_rlmd, motion_snooze_privacy_timeout, rlmd_distance, sensitivity
- New motion_zones sensors: active_motion_filter, enable_audio, sensitivity, PIR sensitivity 1-3, zone_mask
- New motion_zones advanced object settings: human_detection_confidence, motion_zone_overlap, object_size_max/min, object_time_overlap (day/night)
- Pruned 29 sensor definitions that had null values across all devices

## v1.7.0

- Fix sensor data freshness by refreshing device references on coordinator updates
- Remove unavailable attributes from sensor state

## v1.6.0

- Add entity reconciliation to automatically add missing sensors on update
- Add clean uninstall support to fully purge entities and storage on removal

## v1.5.2

- Add automatic device cleanup for orphaned entities

## v1.5.1

- Add hybrid_motion_zones CV tuning sensors
- Fix options flow

## v1.5.0

- Add 76 new sensors from live API audit

## v1.4.0

- Add 32 new sensors from live API audit

## v1.3.0

- Fix iperf_tcp_throughput sensor crashing coordinator updates
- Add coordinator health monitoring sensor

## v1.2.0

- Add firmware history tracking with per-device sensors

## v1.1.0

- Initial release
