# Changelog

## v1.11.1

Fix newly-added Ring devices landing under an **"Unnamed device"** in the HA UI.

- **`device_info` now supplies `name`, `manufacturer`, and `model`.** Both `RingExtendedSensor.device_info` and `RingDeviceFirmwareHistorySensor.device_info` previously returned `identifiers` only, on the assumption (stated in a code comment since the first release) that this merely *links* to the device row created by the base `ring` integration. It does not. Current HA gives each config entry its own device registry row, so `ring_extended` has always created its own row per camera — verified on a live 309-device registry, where **no** device has more than one config entry and all 24 identifier collisions are Ring cameras holding a `ring` row (7-10 entities) alongside a `ring_extended` row (300+ entities). Rows created in earlier HA versions inherited a name from the `ring` row, which hid the defect; any device added to the Ring account now produced a `ring_extended` row with `name: null`, rendered as "Unnamed device" with several hundred sensors under it.
- Uses `name` rather than `default_name` deliberately: `default_name` applies only when a row is first created and would leave already-nameless rows nameless forever. With `name`, HA backfills the existing unnamed rows on the next restart — no entity IDs, `unique_id`s, or user-assigned names (`name_by_user`) are affected.

## v1.11.0

API audit 2026-07-25 (21 devices / 7 models) plus a recorder-warning fix surfaced by the HA log.

**New sensors (7)** — two new Ring features and a new AI-Labs-wide flag. None of these paths existed in the previous audit snapshots.

- `features.ai_labs_memorable_moments` — a new AI Labs feature carrying Ring's standard schema on all 21 devices. Adds 4 sensors: `ai_labs_memorable_moments_enabled` (`.enablement.enabled`), `ai_labs_memorable_moments_eligible` (`.eligibility.eligible`), `ai_labs_memorable_moments_allows_no_location`, and `ai_labs_memorable_moments_ineligibility_reason` (via `FEATURES_WITH_REASON_LISTS`; currently `unsupported_language`, from the list `[unsupported_language, not_subscribed, svd_not_eligible, svs_not_eligible]`). Its `enablement` is a reduced `{enabled}`-only object, so it is also added to `FEATURES_WITHOUT_DISALLOW_REASONS` — no permanently-Unavailable `_disallow_reason` sensor is generated (same treatment as `ai_labs_daily_clip` in v1.9.10).
- `ai_labs_daily_clip_allows_no_location` - `features.ai_labs_daily_clip.allows_no_location`. `allows_no_location` is an AI-Labs-wide flag: it appears on exactly the two `features.ai_labs_*` nodes (21/21 devices each) and nowhere else in the features tree.
- `property_view_enabled` - `features.property_view.enablement.enabled`. New feature, present on 18/21 devices (`False` on all of them). Exposes an `enablement` node only — no `eligibility`, so it gets no eligibility/reason sensors. The whole node is null on 3 devices (both doorbells plus Basement Office), where the sensor reports Unknown.
- `original_video_quality_download_offer_enabled` - `features.original_video_quality_download_offer.is_enabled`. New feature with a flat `{is_enabled}` shape rather than the usual eligibility/enablement pair. The only new flag with live variation: `True` on 5 devices (Front Door, Garage, Driveway, Porch, Deck), `False` on 15, node absent on 1.

**Bug fix**

- `video_packets_total` state class changed from `TOTAL_INCREASING` to `MEASUREMENT`. Despite the name, `health.video_packets_total` is not a cumulative counter — Ring reports a per-health-report window sample, so the value routinely steps down (e.g. front_yard 2846 → 2807, basement_single_door 8692 → 8615) and does not track uptime (3D Printers: 1,638 packets against 2.9 M seconds of uptime). Every dip made the recorder log `state is not strictly increasing` and ask for a bug report; 5 entities warned 9 times over 2026-07-23/24. Long-term statistics for this sensor restart under the new state class.

**Translations**

- Add the 7 new entity names, plus the missing `ai_labs_daily_clip_ineligibility_reason` name (its sensor has existed since v1.9.10 but had no translation entry). `strings.json` and `en.json` stay in sync.

Audit notes: no paths were removed from the API this cycle. The analyzer's other two "high priority" hits are the same value-identical duplicates rejected in v1.10.0, re-verified against live data here — `health.current_bandwidth` (15097) equals the `bandwidth` sensor (15097), and `settings.motion_settings.motion_snooze_preset_profile` equals `settings.motion_snooze_preset_profile` on 21/21 devices. The 5 "stale" leaves are the known conditional battery/RSSI alert fields (absent while devices are healthy — monitor, do not remove).

## v1.10.0

Reduce the enabled-entity surface to stop the startup websocket flood (companion-app tablets hitting "Client unable to keep up with pending messages. Reached 4096 pending messages" during boot). The root cause was cardinality, not state churn: ~900+ enabled entities each emit a per-entity websocket *add* frame at startup, overrunning a slow client's outbound queue. The paid/CV/eligibility flags that dominate the count are static config values, not a runtime `state_changed` firehose.

- **Deselecting a category now actually disables its entities.** `entity_registry_enabled_default` only applies to entities at first registration, so a category deselected in Options previously left its (already enabled) entities live forever. Setup now reconciles the registry: entities in a deselected category are disabled (`disabled_by = INTEGRATION`) and are re-enabled if the category is reselected. A user's manual disables (`disabled_by = USER`) are never overridden, and the coordinator-health sensor is always kept enabled. This makes the Options category picker a real lever for shrinking the live set.
- **Leaner defaults on fresh installs.** The default enabled categories are now `health`, `power`, and `firmware` (connectivity/signal, battery, firmware) instead of all 16. The remaining categories are informational static config/eligibility flags and can be opted back in via Options.
- No entity definitions changed and no `unique_id`s changed; this is non-breaking for existing installs until the user narrows their category selection.

API audit 2026-06-13.

- Add `alert_rssi` - `alerts.rssi` (also covers `health.alert_rssi` via the merge alias). A conditional Wi-Fi signal-risk flag the API emits only while a device's signal is weak (currently `low` on 2/20 devices: Garage Doorbell, Front Yard), distinct from the numeric `health.rssi` / `rssi_category` sensors. `health.rssi_risk_level` mirrors the same value. Like the `alert_battery` family this is a **conditional** `health.*`/`alerts.*` field — `rssi` is already in the audit's `CONDITIONAL_FIELD_SUBSTRINGS`, so a healthy-Wi-Fi window won't flag it as stale-removed.
- Audit confirmed no other genuinely-new metrics. The analyzer's two "high priority" hits were value-identical duplicates of existing sensors, not gaps: `health.current_bandwidth` equals the `bandwidth` sensor (cf. v1.9.11's `current_bandwidth_raw` removal) and `settings.motion_settings.motion_snooze_preset_profile` equals the `motion_snooze_preset_profile` sensor (cf. v1.9.9's dedup). The remaining candidates are always-null config keys or raw list containers already covered by scalar sensors.

## v1.9.11

Project health audit (2026-06-04) — a multi-dimensional review of the integration code, sensor definitions, translations, and docs.

**Bug fixes (integration)**

- **Entity reconciliation no longer deletes valid entities on every reload.** It previously rebuilt the "expected" set from raw `_attrs` (which omits the merged health/alert data sensors actually read) and removed any entity whose value was momentarily unavailable — destroying conditional sensors (e.g. low-battery alerts) and their history each reload. Reconciliation now removes an entity only when its **device is gone** or its **sensor key was deleted from the code**; live availability is handled by the entity itself.
- Replace the deprecated `hass.components.persistent_notification.async_create` (raises on current HA cores) with the module API, and key the firmware-update notification on `device_id` instead of device name.
- `value_fn` crash/zero safety: numeric coercions for `egress_tx_rate`, `firmware_avg_bitrate`, and `ac_power` now use safe helpers that preserve a genuine `0` and never raise `ValueError` (which the value handler did not catch).
- `unique_id` no longer falls back to the literal `"unknown"` (which collided across id-less devices); such devices are skipped instead.
- Firmware-history sensor uses a public `get_current_version()` accessor instead of a private attribute; correct the `device_info` return-type annotations; remove a dead, never-called cleanup function.

**Sensor cleanup** (these change/remove entities)

- Remove 11 always-Unavailable sensors that never held a value on any device (vestigial config keys whose live data is already exposed via nested sensors): `enable_ir`, `enable_audio`, `enable_pir_validation`, `enable_rlmd`, `rlmd_distance`, `sensitivity`, `active_motion_filter`, `motion_snooze_privacy_timeout`, `light_settings`, `device_placement_info`, `terms_of_service_accepted`.
- Remove `current_bandwidth_raw` — a byte-identical duplicate of `bandwidth` (both expose `health.bandwidth`). `current_bandwidth_mb` and `current_bandwidth_category` are unaffected.
- Move `second_battery_percentage_category` and `second_battery_voltage_category` to the **Power** category to match every other battery sensor. This renames their entity IDs (`*_health_second_battery_*` → `*_power_second_battery_*`).
- Remove the incorrect `Mbps` unit from `tx_rate` (its values are a small WiFi PHY/link-rate index, not Mbps).

**Translations**

- Remove 8 fully-orphaned entity names for sensors that no longer exist; rename the `concierge_alexa_delay` / `concierge_autoreply_delay` entries to their current `_ms` keys. `strings.json` and `en.json` stay in sync.

**Docs**

- Fix the README "Example Sensors" entity IDs (they omitted the mandatory category prefix) and document the `sensor.{device}_{category}_{key}` pattern; refresh the sensor count; correct a v1.9.5 changelog miscount ("4" → "3"); update the `claude.md` count and add `diagnostics.py` to the file tree; label the static API snapshots as point-in-time and add a superseded-spec banner.

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
- Remove 3 stale sensors no longer present in Ring API:
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
