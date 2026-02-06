# Changelog

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
