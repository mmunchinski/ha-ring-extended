# Changelog

## v1.9.10

API audit 2026-06-04.

- Add 3 conditional battery sensors, newly visible because a Doorbell 4's battery is low (these fields are only emitted by the API while a battery is low):
  - `alert_battery` - `alerts.battery` (also covers `health.alert_battery` via the merge alias)
  - `battery_level` - `health.battery_level` (categorical, e.g. `lowest`)
  - `battery_temp` - `health.battery_temp` (raw numeric; the API does not document its unit/scale, so it is exposed unconverted, with no device_class or unit)
- Note: `alert_battery` and `battery_level` were originally added in v1.9.3 and wrongly removed in v1.9.5 as "stale" during a healthy-battery window. They are **conditional** fields, not removed-from-API ones. The audit "stale" heuristic flags a path absent on all devices, which conflates *permanently gone* with *conditionally absent*; known-conditional `health.*`/`alerts.*` fields should be monitored, not removed.
- Add `enable_ir_led_root` - root-level `enable_ir_led` (a distinct path from the existing `settings.enable_ir_led` sensor), following the existing root/settings dual-sensor precedent (`*_root` keys).
- Remove 3 permanently-dead `*_disallow_reason` sensors for features whose Ring API schema has no usable `enablement.disallow_reasons` (verified structurally absent on all 20 devices / 7 models — `enablement` is null or a reduced `{enabled}`-only object): `ai_labs_daily_clip`, `live_view_audio_privacy_controls`, `video_donation`. Their `*_ineligibility_reason` sensors (eligibility node, present 20/20) are kept.

## v1.9.9

- Remove a duplicate `motion_snooze_preset_profile` sensor definition. Two definitions shared the same sensor key (different attr_paths: `settings.motion_snooze_preset_profile` vs `settings.motion_settings.motion_snooze_preset_profile`), so HA rejected the second as a duplicate unique_id and logged a startup warning per device. Both paths return identical values, so no sensor data changes — this only removes the dead definition and the recurring warning. The surviving sensor keeps reading `settings.motion_snooze_preset_profile`.

## v1.9.8

- Add the **Network Backup** feature group, newly exposed by the Ring API on **100% of devices/models** (API audit 2026-05-28):
  - `network_backup_eligible` - `features.network_backup.eligibility.eligible`
  - `network_backup_allowed` - `features.network_backup.enablement.allowed`
  - `network_backup_enabled` - `features.network_backup.enablement.enabled`
  - `network_backup_host_eligible` - `features.network_backup_host.eligibility.eligible` (host feature is eligibility-only; no enablement block in the API)
- Add `network_backup` to `FEATURES_WITH_REASON_LISTS`, auto-generating its two reason sensors (both paths carry real data, e.g. `unsupported_device` / `not_subscribed`):
  - `network_backup_ineligibility_reason`
  - `network_backup_disallow_reason`

## v1.9.7

- Generalize the v1.9.6 reason-list pattern to **11 features**. Adding a feature to `FEATURES_WITH_REASON_LISTS` in const.py now auto-creates both reason sensors (no hand-coded entries needed).
- New sensors (10 features × 2 sensors each = 20 sensors per device; the 2 from v1.9.6 are regenerated under the same keys):
  - `ai_automated_warnings_ineligibility_reason` / `_disallow_reason`
  - `ai_labs_daily_clip_ineligibility_reason` / `_disallow_reason`
  - `alexa_plus_greetings_ineligibility_reason` / `_disallow_reason`
  - `live_view_audio_privacy_controls_ineligibility_reason` / `_disallow_reason`
  - `retinal_tuning_ineligibility_reason` / `_disallow_reason`
  - `single_alert_ineligibility_reason` / `_disallow_reason`
  - `smart_video_description_ineligibility_reason` / `_disallow_reason`
  - `smart_video_search_ineligibility_reason` / `_disallow_reason`
  - `unusual_alert_ineligibility_reason` / `_disallow_reason`
  - `video_donation_ineligibility_reason` / `_disallow_reason`
- All report **Unavailable** when the underlying list is missing or empty. Most `unsupported_language` reasons surface here, which previously had no per-device visibility.

## v1.9.6

- Add 2 Familiar Faces (person_identification) reason sensors exposing previously-hidden ineligibility detail:
  - `person_id_ineligibility_reason` - first entry from `features.person_identification.eligibility.ineligibility_reasons` (e.g. `unsupported_device`)
  - `person_id_disallow_reason` - first entry from `features.person_identification.enablement.disallow_reasons` (e.g. `ineligible`)
- Sensors report unavailable when the reason list is missing or empty (i.e. on devices fully eligible for Familiar Faces)

## v1.9.5

- Add new sensor: `alerts.sidewalk_connection` - Amazon Sidewalk connection alert (71% of models)
- Remove 4 stale sensors no longer present in Ring API:
  - `alerts.battery` (added v1.9.3, since removed by Ring)
  - `health.battery_level` (added v1.9.3, since removed by Ring)
  - `health.rssi_risk_level` (re-added v1.9.4, since removed again by Ring)

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
