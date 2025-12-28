# Ring Camera API Attributes (from Home Assistant Diagnostic)

These are attributes advertised by Ring's cloud API, not Home Assistant inventions.

---

## Device Identity
- `id` - Internal Ring device ID
- `device_id` - Device identifier
- `kind` - Device type (e.g., `doorbell_oyster`, `cocoa_doorbell_v2`, `three_p_cam`, `base_station_v1`)
- `description` - User-assigned device name/alias
- `location_id` - Ring location grouping
- `schema_id` - API schema version hash
- `device_resource_id` - Full Ring resource URI
- `hardware_id` - Hardware identifier (third-party devices)
- `ring_id` - Ring network ID
- `ring_net_id` - Ring network identifier
- `owner.id` / `owner.email` / `owner.first_name` / `owner.last_name`
- `created_at` - Device registration timestamp
- `deactivated_at` - Deactivation timestamp (if applicable)
- `time_zone` - Device timezone
- `latitude` / `longitude` - Geolocation
- `address` - Location address
- `owned` - Ownership flag
- `stolen` - Stolen device flag
- `shared_at` - Share timestamp (if shared)

---

## Health & Connectivity
- `health.connected` - Online status
- `health.rssi` - WiFi signal strength (dBm)
- `health.rssi_category` - Signal quality rating (`good`, `okay`, `poor`)
- `health.wifi_name` - Connected SSID
- `health.wifi_is_ring_network` - Using Ring Chime Pro as extender
- `health.channel` - WiFi channel
- `health.network_connection_value` - Connection type (`wifi`)
- `health.sidewalk_connection` - Amazon Sidewalk connection status
- `health.rss_connected` - Ring server connection status
- `health.packet_loss` / `health.packet_loss_category`
- `health.bandwidth` / `health.current_bandwidth` / `health.current_bandwidth_mb`
- `health.bandwidth_last_time` - Last bandwidth test timestamp
- `health.egress_tx_rate` / `health.egress_tx_rate_category`
- `health.tx_rate` - Transmit rate
- `health.fast_ping_hop1_score` - First hop latency score
- `health.uptime_sec` - Device uptime in seconds
- `health.last_update_time` - Last health update timestamp
- `health.status_time` - Status timestamp
- `alerts.connection` - Connection alert status (`online`, `offline`)

---

## Power & Battery
- `health.ac_power` - AC power connected (0/1)
- `health.battery_percentage` / `health.battery_percentage_category`
- `health.battery_voltage` / `health.battery_voltage_category`
- `health.battery_present` - Battery installed
- `health.battery_save` - Battery saver mode
- `health.battery_error` - Battery error flag
- `health.second_battery_percentage_category` - Dual battery support
- `health.second_battery_voltage_category`
- `health.transformer_voltage` / `health.transformer_voltage_category` - Hardwired voltage
- `health.external_connection` - External power source
- `health.ext_power_state` - External power state
- `health.pref_run_mode` / `health.run_mode` - Power mode (`low_power`, etc.)
- `battery_life` - Battery level string
- `external_connection` - External power flag
- `ext_power_state` - Power state

---

## Firmware & OTA
- `firmware_version` - Firmware status string (`Up to Date`)
- `health.firmware_version` - Actual firmware version (e.g., `21.0.4`, `cam-1.28.10800`)
- `health.firmware_version_status` - Update status
- `health.ota_status` - OTA update status (`timeout`, etc.)
- `alerts.ota_status` - OTA alert status

---

## Video & Streaming
- `health.vod_enabled` - Video on Demand enabled
- `health.stream_resolution` - Stream resolution value
- `health.firmware_avg_bitrate` - Average bitrate
- `health.video_packets_total` - Total video packets
- `settings.enable_vod` - VOD enabled (0/1)
- `settings.vod_suspended` - VOD suspended flag
- `settings.vod_status` - VOD status (`enabled`, `disabled`)
- `settings.live_view_disabled` - Live view disabled flag
- `settings.live_view_preset_profile` - Quality preset (`low`, `middle`, `high`, `highest`)
- `settings.live_view_presets` - Available presets array
- `settings.extended_live_view` - Extended live view duration setting
- `settings.exposure_control` - Exposure control level
- `settings.max_resolution_mode` / `settings.max_resolution_mode_eligible`
- `settings.preroll_enabled` - Pre-roll video capture
- `settings.active_streaming_event_led_enabled` - LED during streaming
- `settings.video_settings.encryption_enabled` / `encryption_method`
- `settings.video_settings.hevc_enabled` - H.265 encoding
- `settings.video_settings.recording_24x7_mode`
- `features.video_rendering.max_digital_zoom_level`
- `features.live_view_pip_mode` - Picture-in-picture mode
- `features.video_recording.recording_mode` - (`motion_based`, etc.)
- `features.video_recording.recording_enabled` / `recording_state`

---

## Audio
- `settings.enable_audio_recording` - Audio recording enabled
- `settings.doorbell_volume` - Doorbell chime volume (0-11)
- `settings.voice_volume` - Two-way talk volume
- `settings.audio_settings.enable_live_view_audio_override`
- `settings.chime_settings.enable` / `type` / `duration`
- `features.live_view_audio_privacy_controls.eligibility`

---

## Motion Detection
- `settings.motion_detection_enabled` - Master motion toggle
- `settings.advanced_motion_detection_enabled` - Smart detection
- `settings.advanced_motion_detection_human_only_mode` - Person-only alerts
- `settings.advanced_motion_detection_types` - Detection types array (`human`, etc.)
- `settings.people_detection_eligible` - Person detection capable
- `settings.motion_snooze_preset_profile` - Snooze preset
- `settings.motion_snooze_presets` - Available snooze options
- `settings.motion_zones` - Zone enable array
- `settings.advanced_motion_zones_enabled`
- `settings.advanced_motion_zones_type` - (`8vertices`)
- `settings.advanced_motion_zones.zone1-3` - Zone definitions with vertices
- `settings.advanced_pir_motion_zones.zone1-6_sensitivity` - PIR sensitivity per zone
- `settings.pir_sensitivity_1` - Overall PIR sensitivity
- `settings.ignore_zones.zone1-4` - Privacy/ignore zones
- `settings.flick_elim_recommended_mode` - Flicker elimination
- `motion_snooze` - Current snooze state
- `snooze_settings` - Snooze configuration
- `subscribed_motions` - Motion subscription active
- `active_schedule_uuid` - Motion schedule ID

---

## Computer Vision (CV) Detection
- `settings.cv_settings.detection_types.human` - enabled, mode (`edge`/`cloud`/`none`), record, notification
- `settings.cv_settings.detection_types.motion`
- `settings.cv_settings.detection_types.other_motion`
- `settings.cv_settings.detection_types.loitering`
- `settings.cv_settings.detection_types.moving_vehicle`
- `settings.cv_settings.detection_types.vehicle`
- `settings.cv_settings.detection_types.animal`
- `settings.cv_settings.detection_types.package_delivery`
- `settings.cv_settings.detection_types.package_pickup`
- `settings.cv_settings.detection_types.unverified_motion`
- `settings.cv_settings.detection_types.motion_stop`
- `settings.cv_settings.threshold.loitering` - Seconds before loitering alert
- `settings.cv_settings.threshold.package_delivery`
- `settings.cv_settings.threshold.unverified_motion`
- `settings.cv_settings.triggers` - Custom triggers array
- `settings.cv_settings.search_types.natural_language_search` - NL video search

---

## Paid CV Features (Subscription Flags)
- `settings.cv_paid_features.human`
- `settings.cv_paid_features.motion`
- `settings.cv_paid_features.other_motion`
- `settings.cv_paid_features.loitering`
- `settings.cv_paid_features.vehicle`
- `settings.cv_paid_features.animal`
- `settings.cv_paid_features.package_delivery`
- `settings.cv_paid_features.package_pickup`
- `settings.cv_paid_features.baby_cry`
- `settings.cv_paid_features.car_alarm`
- `settings.cv_paid_features.co2_smoke_alarm`
- `settings.cv_paid_features.dog_bark`
- `settings.cv_paid_features.general_sound`
- `settings.cv_paid_features.glass_break`
- `settings.cv_paid_features.cv_triggers`

---

## Other Paid Features (Subscription Flags)
- `settings.other_paid_features.alexa_concierge`
- `settings.other_paid_features.sheila_cv` - Local CV processing
- `settings.other_paid_features.sheila_recording` - Local recording
- `settings.other_paid_features.critical_alerts`
- `settings.other_paid_features.system_level_pip`
- `settings.other_paid_features.extended_live_view`
- `settings.other_paid_features.snapshot_capture_plus`
- `settings.other_paid_features.live_speak`
- `settings.other_paid_features.closed_caption`
- `settings.other_paid_features.daily_digest`
- `settings.other_paid_features.ding_call`
- `settings.other_paid_features.natural_language_search`
- `settings.other_paid_features.multicam_live_view`
- `settings.other_paid_features.package_protection`
- `settings.other_paid_features.alarm_triggered_recording`
- `settings.other_paid_features.recording_24x7`

---

## Notifications
- `settings.enable_rich_notifications` - Rich notification thumbnails
- `settings.rich_notifications_billing_eligible`
- `settings.rich_notifications_face_crop_enabled` - Face crop in notifications
- `settings.rich_notifications_scene_source` - (`firmware`, `cloud`)
- `settings.loitering_threshold` - Loitering alert threshold (seconds)
- `features.rich_notifications_eligible`
- `subscribed` - Push notifications enabled

---

## Recording & Storage
- `settings.user_specified_recording_ttl` - Recording retention (days)
- `settings.lite_24x7.subscribed` / `enabled` - Snapshot history
- `settings.lite_24x7.frequency_secs` - Snapshot interval
- `settings.lite_24x7.resolution_p` - Snapshot resolution
- `settings.lite_24x7_footage_ttl` - Snapshot retention (hours)
- `settings.offline_motion_event_settings.subscribed` / `enabled`
- `settings.offline_motion_event_settings.max_upload_kb`
- `settings.offline_motion_event_settings.resolution_p`
- `settings.offline_motion_event_settings.frequency_after_secs`
- `settings.offline_motion_event_settings.period_after_secs`
- `features.show_recordings` - Recordings visible
- `features.show_24x7_lite` - 24/7 snapshots visible
- `features.recording_24x7_eligible`

---

## Floodlight Settings (Floodlight Cams)
- `settings.floodlight_settings.priority`
- `settings.floodlight_settings.duration` - Light duration (seconds)
- `settings.floodlight_settings.brightness` - Brightness level
- `settings.floodlight_settings.always_on` / `always_on_duration`
- `settings.light_snooze_settings.duration` / `always_on`
- `health.floodlight_on` - Current floodlight state
- `health.white_led_on` - White LED state

---

## Radar / Bird's Eye View (Supported Devices)
- `settings.radar_settings.birds_eye_view_enabled`
- `settings.radar_settings.bez_feature_enabled`
- `settings.radar_settings.bez_filtering_enabled`
- `settings.radar_settings.installation_height` - Height in meters
- `settings.radar_settings.auto_motion_sensitivity_enabled`

---

## Siren
- `health.siren_on` - Siren active

---

## Concierge / Auto-Reply
- `settings.concierge_settings.mode` - (`disabled`, etc.)
- `settings.concierge_settings.alexa_settings.delay_ms`
- `settings.concierge_settings.autoreply_settings.delay_ms`
- `features.alexa_plus_greetings`

---

## Local Processing (Sheila)
- `settings.sheila_settings.cv_processing_enabled` - On-device CV
- `settings.sheila_settings.local_storage_enabled` - Local storage
- `features.sheila_camera_eligible`
- `features.sheila_camera_processing_eligible`

---

## Network Configuration
- `settings.network_settings.mac_address_ble`
- `settings.network_settings.mac_address_wifi_24`
- `settings.network_settings.mac_address_wifi_5`
- `settings.network_settings.multi_net_pref` - Network preference
- `settings.network_settings.max_dynamic_listen_interval`
- `settings.network_settings.network_diagnosis.*` - Diagnostic settings
- `features.dynamic_network_switching_eligible`

---

## Server / Infrastructure
- `settings.server_settings.ring_media_server_enabled`
- `settings.server_settings.ring_media_server_host` - Media server endpoint
- `encryption_group.id` / `account_group_revision_id`

---

## Feature Eligibility Flags
- `features.cfes_eligible` - Cloud feature eligibility
- `features.motions_enabled`
- `features.show_vod_settings`
- `features.show_offline_motion_events`
- `features.motion_zone_recommendation`
- `features.chime_auto_detect_capable`
- `features.chime_settings.is_eligible`
- `features.package_warning.*` - Package alert eligibility
- `features.smart_video_search.eligibility.*`
- `features.smart_video_description.eligibility.*`
- `features.person_identification.eligibility.*`
- `features.retinal_tuning.eligibility.*` - Digital zoom enhancement
- `features.retinal_tuning.rt_max_digital_zoom_level`
- `features.single_alert.eligibility.*`
- `features.unusual_alert.eligibility.*` - Unusual activity detection
- `features.video_donation.eligibility.*`
- `features.auto_zoom_track`
- `features.ai_automated_warnings`
- `features.remote_access_control`
- `features.transformer_score`

---

## Third-Party Device Metadata (Blink/Amazon Cams)
- `third_party_manufacturer` - (`amazon1p`)
- `third_party_model` - Model code
- `third_party_dsn` - Device serial
- `third_party_tags`
- `metadata.legacy_fw_migrated`
- `metadata.imported_from_amazon`
- `metadata.is_sidewalk_gateway`

---

## Sidewalk Gateway
- `is_sidewalk_gateway` - Acts as Amazon Sidewalk bridge

---

## Miscellaneous
- `settings.stark_enabled` / `stark_enrolled` - Unknown feature flag
- `settings.terms_of_service_accepted`
- `health.night_mode_on` - IR night vision active
- `health.hatch_open` - Battery compartment open
- `health.supported_rpc_commands` - Available RPC commands
- `flick_elim_recommended_mode` - Recommended flicker elimination
