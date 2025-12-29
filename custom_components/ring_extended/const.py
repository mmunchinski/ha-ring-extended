"""Constants for Ring Extended integration."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfTime,
    UnitOfElectricPotential,
    UnitOfDataRate,
)

DOMAIN = "ring_extended"

# Device families to scan
DEVICE_FAMILIES = ["doorbells", "stickup_cams", "chimes", "other"]

# Sensor categories for config flow
SENSOR_CATEGORIES = [
    "health",
    "power",
    "firmware",
    "video",
    "audio",
    "motion",
    "cv_detection",
    "cv_paid",
    "other_paid",
    "notifications",
    "recording",
    "floodlight",
    "radar",
    "local_processing",
    "features",
    "device_status",
]

CATEGORY_NAMES = {
    "health": "Health & Connectivity",
    "power": "Power & Battery",
    "firmware": "Firmware",
    "video": "Video & Streaming",
    "audio": "Audio",
    "motion": "Motion Detection",
    "cv_detection": "CV Detection Types",
    "cv_paid": "CV Paid Features",
    "other_paid": "Other Paid Features",
    "notifications": "Notifications",
    "recording": "Recording & Storage",
    "floodlight": "Floodlight",
    "radar": "Radar / Bird's Eye",
    "local_processing": "Local Processing",
    "features": "Feature Eligibility",
    "device_status": "Device Status",
}


def get_nested(data: dict, path: str, default: Any = None) -> Any:
    """Safely get nested dictionary value using dot notation."""
    if data is None:
        return default
    keys = path.split(".")
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return default
        if data is None:
            return default
    return data


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


def _value_exists(attrs: dict, path: str) -> bool:
    """Check if a value exists at the given path."""
    return get_nested(attrs, path) is not None


def _unix_to_datetime(timestamp: int | None) -> datetime | None:
    """Convert Unix timestamp to datetime with timezone."""
    if timestamp is None:
        return None
    try:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        return None


@dataclass(frozen=True, kw_only=True)
class RingExtendedSensorDescription(SensorEntityDescription):
    """Describes Ring extended sensor entity."""

    category: str = "health"
    attr_path: str = ""
    value_fn: Callable[[dict], Any] | None = None
    available_fn: Callable[[dict], bool] | None = None

    def get_value(self, attrs: dict) -> Any:
        """Get the sensor value from device attributes."""
        if self.value_fn is not None:
            return self.value_fn(attrs)
        return get_nested(attrs, self.attr_path)

    def is_available(self, attrs: dict) -> bool:
        """Check if sensor is available."""
        if self.available_fn is not None:
            return self.available_fn(attrs)
        return _value_exists(attrs, self.attr_path)


# Health & Connectivity sensors
HEALTH_SENSORS: tuple[RingExtendedSensorDescription, ...] = (
    RingExtendedSensorDescription(
        key="rssi",
        translation_key="rssi",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        category="health",
        attr_path="health.rssi",
        entity_registry_enabled_default=True,
    ),
    RingExtendedSensorDescription(
        key="rssi_category",
        translation_key="rssi_category",
        category="health",
        attr_path="health.rssi_category",
    ),
    RingExtendedSensorDescription(
        key="connected",
        translation_key="connected",
        category="health",
        attr_path="health.connected",
    ),
    RingExtendedSensorDescription(
        key="packet_loss",
        translation_key="packet_loss",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        category="health",
        attr_path="health.packet_loss",
    ),
    RingExtendedSensorDescription(
        key="packet_loss_category",
        translation_key="packet_loss_category",
        category="health",
        attr_path="health.packet_loss_category",
    ),
    RingExtendedSensorDescription(
        key="bandwidth",
        translation_key="bandwidth",
        native_unit_of_measurement="kbps",
        state_class=SensorStateClass.MEASUREMENT,
        category="health",
        attr_path="health.bandwidth",
    ),
    RingExtendedSensorDescription(
        key="current_bandwidth_mb",
        translation_key="current_bandwidth_mb",
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        category="health",
        attr_path="health.current_bandwidth_mb",
    ),
    RingExtendedSensorDescription(
        key="egress_tx_rate",
        translation_key="egress_tx_rate",
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        category="health",
        attr_path="health.egress_tx_rate",
        value_fn=lambda attrs: float(v) if (v := get_nested(attrs, "health.egress_tx_rate")) else None,
    ),
    RingExtendedSensorDescription(
        key="egress_tx_rate_category",
        translation_key="egress_tx_rate_category",
        category="health",
        attr_path="health.egress_tx_rate_category",
    ),
    RingExtendedSensorDescription(
        key="wifi_channel",
        translation_key="wifi_channel",
        category="health",
        attr_path="health.channel",
    ),
    RingExtendedSensorDescription(
        key="network_connection_value",
        translation_key="network_connection_value",
        category="health",
        attr_path="health.network_connection_value",
    ),
    RingExtendedSensorDescription(
        key="sidewalk_connection",
        translation_key="sidewalk_connection",
        category="health",
        attr_path="health.sidewalk_connection",
    ),
    RingExtendedSensorDescription(
        key="uptime_sec",
        translation_key="uptime_sec",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        category="health",
        attr_path="health.uptime_sec",
    ),
    RingExtendedSensorDescription(
        key="uptime_formatted",
        translation_key="uptime_formatted",
        category="health",
        attr_path="health.uptime_sec",
        value_fn=lambda attrs: _format_uptime(get_nested(attrs, "health.uptime_sec")),
    ),
    RingExtendedSensorDescription(
        key="last_update_time",
        translation_key="last_update_time",
        device_class=SensorDeviceClass.TIMESTAMP,
        category="health",
        attr_path="health.last_update_time",
        value_fn=lambda attrs: _unix_to_datetime(get_nested(attrs, "health.last_update_time")),
    ),
    RingExtendedSensorDescription(
        key="wifi_is_ring_network",
        translation_key="wifi_is_ring_network",
        category="health",
        attr_path="health.wifi_is_ring_network",
    ),
)

# Power & Battery sensors
POWER_SENSORS: tuple[RingExtendedSensorDescription, ...] = (
    RingExtendedSensorDescription(
        key="battery_percentage",
        translation_key="battery_percentage",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        category="power",
        attr_path="health.battery_percentage",
    ),
    RingExtendedSensorDescription(
        key="battery_percentage_category",
        translation_key="battery_percentage_category",
        category="power",
        attr_path="health.battery_percentage_category",
    ),
    RingExtendedSensorDescription(
        key="battery_voltage",
        translation_key="battery_voltage",
        native_unit_of_measurement="mV",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        category="power",
        attr_path="health.battery_voltage",
    ),
    RingExtendedSensorDescription(
        key="battery_voltage_category",
        translation_key="battery_voltage_category",
        category="power",
        attr_path="health.battery_voltage_category",
    ),
    RingExtendedSensorDescription(
        key="battery_present",
        translation_key="battery_present",
        category="power",
        attr_path="health.battery_present",
    ),
    RingExtendedSensorDescription(
        key="battery_save",
        translation_key="battery_save",
        category="power",
        attr_path="health.battery_save",
    ),
    RingExtendedSensorDescription(
        key="battery_error",
        translation_key="battery_error",
        category="power",
        attr_path="health.battery_error",
    ),
    RingExtendedSensorDescription(
        key="ac_power",
        translation_key="ac_power",
        category="power",
        attr_path="health.ac_power",
        value_fn=lambda attrs: bool(int(v)) if (v := get_nested(attrs, "health.ac_power")) is not None else None,
    ),
    RingExtendedSensorDescription(
        key="transformer_voltage",
        translation_key="transformer_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        category="power",
        attr_path="health.transformer_voltage",
    ),
    RingExtendedSensorDescription(
        key="transformer_voltage_category",
        translation_key="transformer_voltage_category",
        category="power",
        attr_path="health.transformer_voltage_category",
    ),
    RingExtendedSensorDescription(
        key="ext_power_state",
        translation_key="ext_power_state",
        category="power",
        attr_path="health.ext_power_state",
    ),
    RingExtendedSensorDescription(
        key="run_mode",
        translation_key="run_mode",
        category="power",
        attr_path="health.run_mode",
    ),
    RingExtendedSensorDescription(
        key="pref_run_mode",
        translation_key="pref_run_mode",
        category="power",
        attr_path="health.pref_run_mode",
    ),
)

# Firmware sensors
FIRMWARE_SENSORS: tuple[RingExtendedSensorDescription, ...] = (
    RingExtendedSensorDescription(
        key="firmware_version",
        translation_key="firmware_version",
        category="firmware",
        attr_path="health.firmware_version",
    ),
    RingExtendedSensorDescription(
        key="firmware_version_status",
        translation_key="firmware_version_status",
        category="firmware",
        attr_path="health.firmware_version_status",
    ),
    RingExtendedSensorDescription(
        key="ota_status",
        translation_key="ota_status",
        category="firmware",
        attr_path="health.ota_status",
    ),
    RingExtendedSensorDescription(
        key="firmware_avg_bitrate",
        translation_key="firmware_avg_bitrate",
        native_unit_of_measurement="kbps",
        state_class=SensorStateClass.MEASUREMENT,
        category="firmware",
        attr_path="health.firmware_avg_bitrate",
        value_fn=lambda attrs: int(v) if (v := get_nested(attrs, "health.firmware_avg_bitrate")) else None,
    ),
)

# Video & Streaming sensors
VIDEO_SENSORS: tuple[RingExtendedSensorDescription, ...] = (
    RingExtendedSensorDescription(
        key="vod_enabled",
        translation_key="vod_enabled",
        category="video",
        attr_path="health.vod_enabled",
    ),
    RingExtendedSensorDescription(
        key="vod_status",
        translation_key="vod_status",
        category="video",
        attr_path="settings.vod_status",
    ),
    RingExtendedSensorDescription(
        key="vod_suspended",
        translation_key="vod_suspended",
        category="video",
        attr_path="settings.vod_suspended",
    ),
    RingExtendedSensorDescription(
        key="stream_resolution",
        translation_key="stream_resolution",
        category="video",
        attr_path="health.stream_resolution",
    ),
    RingExtendedSensorDescription(
        key="live_view_preset_profile",
        translation_key="live_view_preset_profile",
        category="video",
        attr_path="settings.live_view_preset_profile",
    ),
    RingExtendedSensorDescription(
        key="live_view_disabled",
        translation_key="live_view_disabled",
        category="video",
        attr_path="settings.live_view_disabled",
    ),
    RingExtendedSensorDescription(
        key="extended_live_view",
        translation_key="extended_live_view",
        category="video",
        attr_path="settings.extended_live_view",
    ),
    RingExtendedSensorDescription(
        key="exposure_control",
        translation_key="exposure_control",
        category="video",
        attr_path="settings.exposure_control",
    ),
    RingExtendedSensorDescription(
        key="preroll_enabled",
        translation_key="preroll_enabled",
        category="video",
        attr_path="settings.preroll_enabled",
    ),
    RingExtendedSensorDescription(
        key="max_resolution_mode",
        translation_key="max_resolution_mode",
        category="video",
        attr_path="settings.max_resolution_mode",
    ),
    RingExtendedSensorDescription(
        key="encryption_enabled",
        translation_key="encryption_enabled",
        category="video",
        attr_path="settings.video_settings.encryption_enabled",
    ),
    RingExtendedSensorDescription(
        key="hevc_enabled",
        translation_key="hevc_enabled",
        category="video",
        attr_path="settings.video_settings.hevc_enabled",
    ),
    RingExtendedSensorDescription(
        key="max_digital_zoom_level",
        translation_key="max_digital_zoom_level",
        category="video",
        attr_path="features.video_rendering.max_digital_zoom_level",
    ),
)

# Audio sensors
AUDIO_SENSORS: tuple[RingExtendedSensorDescription, ...] = (
    RingExtendedSensorDescription(
        key="enable_audio_recording",
        translation_key="enable_audio_recording",
        category="audio",
        attr_path="settings.enable_audio_recording",
    ),
    RingExtendedSensorDescription(
        key="doorbell_volume",
        translation_key="doorbell_volume",
        category="audio",
        attr_path="settings.doorbell_volume",
    ),
    RingExtendedSensorDescription(
        key="voice_volume",
        translation_key="voice_volume",
        category="audio",
        attr_path="settings.voice_volume",
    ),
    RingExtendedSensorDescription(
        key="chime_enable",
        translation_key="chime_enable",
        category="audio",
        attr_path="settings.chime_settings.enable",
    ),
    RingExtendedSensorDescription(
        key="chime_duration",
        translation_key="chime_duration",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        category="audio",
        attr_path="settings.chime_settings.duration",
    ),
)

# Motion Detection sensors
MOTION_SENSORS: tuple[RingExtendedSensorDescription, ...] = (
    RingExtendedSensorDescription(
        key="motion_detection_enabled",
        translation_key="motion_detection_enabled",
        category="motion",
        attr_path="settings.motion_detection_enabled",
    ),
    RingExtendedSensorDescription(
        key="advanced_motion_detection_enabled",
        translation_key="advanced_motion_detection_enabled",
        category="motion",
        attr_path="settings.advanced_motion_detection_enabled",
    ),
    RingExtendedSensorDescription(
        key="advanced_motion_detection_human_only_mode",
        translation_key="advanced_motion_detection_human_only_mode",
        category="motion",
        attr_path="settings.advanced_motion_detection_human_only_mode",
    ),
    RingExtendedSensorDescription(
        key="people_detection_eligible",
        translation_key="people_detection_eligible",
        category="motion",
        attr_path="settings.people_detection_eligible",
    ),
    RingExtendedSensorDescription(
        key="motion_snooze_preset_profile",
        translation_key="motion_snooze_preset_profile",
        category="motion",
        attr_path="settings.motion_snooze_preset_profile",
    ),
    RingExtendedSensorDescription(
        key="loitering_threshold",
        translation_key="loitering_threshold",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        category="motion",
        attr_path="settings.loitering_threshold",
    ),
    RingExtendedSensorDescription(
        key="advanced_motion_zones_enabled",
        translation_key="advanced_motion_zones_enabled",
        category="motion",
        attr_path="settings.advanced_motion_zones_enabled",
    ),
    RingExtendedSensorDescription(
        key="pir_sensitivity_1",
        translation_key="pir_sensitivity_1",
        category="motion",
        attr_path="settings.pir_sensitivity_1",
    ),
)

# CV Detection Types - these will be generated dynamically
CV_DETECTION_TYPES = [
    "human",
    "motion",
    "other_motion",
    "loitering",
    "moving_vehicle",
    "vehicle",
    "animal",
    "package_delivery",
    "package_pickup",
    "unverified_motion",
    "motion_stop",
]

CV_DETECTION_TYPE_NAMES = {
    "human": "Human",
    "motion": "Motion",
    "other_motion": "Other Motion",
    "loitering": "Loitering",
    "moving_vehicle": "Moving Vehicle",
    "vehicle": "Vehicle",
    "animal": "Animal",
    "package_delivery": "Package Delivery",
    "package_pickup": "Package Pickup",
    "unverified_motion": "Unverified Motion",
    "motion_stop": "Motion Stop",
}


def _create_cv_detection_sensors() -> tuple[RingExtendedSensorDescription, ...]:
    """Create CV detection sensors for all detection types."""
    sensors = []
    for det_type in CV_DETECTION_TYPES:
        base_path = f"settings.cv_settings.detection_types.{det_type}"
        name = CV_DETECTION_TYPE_NAMES[det_type]

        sensors.append(
            RingExtendedSensorDescription(
                key=f"cv_{det_type}_enabled",
                translation_key=f"cv_{det_type}_enabled",
                category="cv_detection",
                attr_path=f"{base_path}.enabled",
            )
        )
        sensors.append(
            RingExtendedSensorDescription(
                key=f"cv_{det_type}_mode",
                translation_key=f"cv_{det_type}_mode",
                category="cv_detection",
                attr_path=f"{base_path}.mode",
            )
        )
        sensors.append(
            RingExtendedSensorDescription(
                key=f"cv_{det_type}_notification",
                translation_key=f"cv_{det_type}_notification",
                category="cv_detection",
                attr_path=f"{base_path}.notification",
            )
        )
    return tuple(sensors)


CV_DETECTION_SENSORS = _create_cv_detection_sensors()

# CV Threshold sensors
CV_THRESHOLD_SENSORS: tuple[RingExtendedSensorDescription, ...] = (
    RingExtendedSensorDescription(
        key="cv_threshold_loitering",
        translation_key="cv_threshold_loitering",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        category="cv_detection",
        attr_path="settings.cv_settings.threshold.loitering",
    ),
    RingExtendedSensorDescription(
        key="cv_threshold_package_delivery",
        translation_key="cv_threshold_package_delivery",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        category="cv_detection",
        attr_path="settings.cv_settings.threshold.package_delivery",
    ),
    RingExtendedSensorDescription(
        key="natural_language_search_enabled",
        translation_key="natural_language_search_enabled",
        category="cv_detection",
        attr_path="settings.cv_settings.search_types.natural_language_search.enabled",
    ),
)

# CV Paid Features sensors
CV_PAID_SENSORS: tuple[RingExtendedSensorDescription, ...] = (
    RingExtendedSensorDescription(
        key="paid_human",
        translation_key="paid_human",
        category="cv_paid",
        attr_path="settings.cv_paid_features.human",
    ),
    RingExtendedSensorDescription(
        key="paid_motion",
        translation_key="paid_motion",
        category="cv_paid",
        attr_path="settings.cv_paid_features.motion",
    ),
    RingExtendedSensorDescription(
        key="paid_other_motion",
        translation_key="paid_other_motion",
        category="cv_paid",
        attr_path="settings.cv_paid_features.other_motion",
    ),
    RingExtendedSensorDescription(
        key="paid_loitering",
        translation_key="paid_loitering",
        category="cv_paid",
        attr_path="settings.cv_paid_features.loitering",
    ),
    RingExtendedSensorDescription(
        key="paid_vehicle",
        translation_key="paid_vehicle",
        category="cv_paid",
        attr_path="settings.cv_paid_features.vehicle",
    ),
    RingExtendedSensorDescription(
        key="paid_animal",
        translation_key="paid_animal",
        category="cv_paid",
        attr_path="settings.cv_paid_features.animal",
    ),
    RingExtendedSensorDescription(
        key="paid_package_delivery",
        translation_key="paid_package_delivery",
        category="cv_paid",
        attr_path="settings.cv_paid_features.package_delivery",
    ),
    RingExtendedSensorDescription(
        key="paid_package_pickup",
        translation_key="paid_package_pickup",
        category="cv_paid",
        attr_path="settings.cv_paid_features.package_pickup",
    ),
    RingExtendedSensorDescription(
        key="paid_baby_cry",
        translation_key="paid_baby_cry",
        category="cv_paid",
        attr_path="settings.cv_paid_features.baby_cry",
    ),
    RingExtendedSensorDescription(
        key="paid_car_alarm",
        translation_key="paid_car_alarm",
        category="cv_paid",
        attr_path="settings.cv_paid_features.car_alarm",
    ),
    RingExtendedSensorDescription(
        key="paid_co2_smoke_alarm",
        translation_key="paid_co2_smoke_alarm",
        category="cv_paid",
        attr_path="settings.cv_paid_features.co2_smoke_alarm",
    ),
    RingExtendedSensorDescription(
        key="paid_dog_bark",
        translation_key="paid_dog_bark",
        category="cv_paid",
        attr_path="settings.cv_paid_features.dog_bark",
    ),
    RingExtendedSensorDescription(
        key="paid_glass_break",
        translation_key="paid_glass_break",
        category="cv_paid",
        attr_path="settings.cv_paid_features.glass_break",
    ),
    RingExtendedSensorDescription(
        key="paid_general_sound",
        translation_key="paid_general_sound",
        category="cv_paid",
        attr_path="settings.cv_paid_features.general_sound",
    ),
)

# Other Paid Features sensors
OTHER_PAID_SENSORS: tuple[RingExtendedSensorDescription, ...] = (
    RingExtendedSensorDescription(
        key="paid_alexa_concierge",
        translation_key="paid_alexa_concierge",
        category="other_paid",
        attr_path="settings.other_paid_features.alexa_concierge",
    ),
    RingExtendedSensorDescription(
        key="paid_sheila_cv",
        translation_key="paid_sheila_cv",
        category="other_paid",
        attr_path="settings.other_paid_features.sheila_cv",
    ),
    RingExtendedSensorDescription(
        key="paid_sheila_recording",
        translation_key="paid_sheila_recording",
        category="other_paid",
        attr_path="settings.other_paid_features.sheila_recording",
    ),
    RingExtendedSensorDescription(
        key="paid_extended_live_view",
        translation_key="paid_extended_live_view",
        category="other_paid",
        attr_path="settings.other_paid_features.extended_live_view",
    ),
    RingExtendedSensorDescription(
        key="paid_recording_24x7",
        translation_key="paid_recording_24x7",
        category="other_paid",
        attr_path="settings.other_paid_features.recording_24x7",
    ),
    RingExtendedSensorDescription(
        key="paid_natural_language_search",
        translation_key="paid_natural_language_search",
        category="other_paid",
        attr_path="settings.other_paid_features.natural_language_search",
    ),
    RingExtendedSensorDescription(
        key="paid_multicam_live_view",
        translation_key="paid_multicam_live_view",
        category="other_paid",
        attr_path="settings.other_paid_features.multicam_live_view",
    ),
    RingExtendedSensorDescription(
        key="paid_daily_digest",
        translation_key="paid_daily_digest",
        category="other_paid",
        attr_path="settings.other_paid_features.daily_digest",
    ),
    RingExtendedSensorDescription(
        key="paid_package_protection",
        translation_key="paid_package_protection",
        category="other_paid",
        attr_path="settings.other_paid_features.package_protection",
    ),
    RingExtendedSensorDescription(
        key="paid_critical_alerts",
        translation_key="paid_critical_alerts",
        category="other_paid",
        attr_path="settings.other_paid_features.critical_alerts",
    ),
)

# Notification sensors
NOTIFICATION_SENSORS: tuple[RingExtendedSensorDescription, ...] = (
    RingExtendedSensorDescription(
        key="enable_rich_notifications",
        translation_key="enable_rich_notifications",
        category="notifications",
        attr_path="settings.enable_rich_notifications",
    ),
    RingExtendedSensorDescription(
        key="rich_notifications_billing_eligible",
        translation_key="rich_notifications_billing_eligible",
        category="notifications",
        attr_path="settings.rich_notifications_billing_eligible",
    ),
    RingExtendedSensorDescription(
        key="rich_notifications_face_crop_enabled",
        translation_key="rich_notifications_face_crop_enabled",
        category="notifications",
        attr_path="settings.rich_notifications_face_crop_enabled",
    ),
    RingExtendedSensorDescription(
        key="rich_notifications_scene_source",
        translation_key="rich_notifications_scene_source",
        category="notifications",
        attr_path="settings.rich_notifications_scene_source",
    ),
    RingExtendedSensorDescription(
        key="rich_notifications_eligible",
        translation_key="rich_notifications_eligible",
        category="notifications",
        attr_path="features.rich_notifications_eligible",
    ),
)

# Recording & Storage sensors
RECORDING_SENSORS: tuple[RingExtendedSensorDescription, ...] = (
    RingExtendedSensorDescription(
        key="user_specified_recording_ttl",
        translation_key="user_specified_recording_ttl",
        native_unit_of_measurement="days",
        category="recording",
        attr_path="settings.user_specified_recording_ttl",
    ),
    RingExtendedSensorDescription(
        key="lite_24x7_subscribed",
        translation_key="lite_24x7_subscribed",
        category="recording",
        attr_path="settings.lite_24x7.subscribed",
    ),
    RingExtendedSensorDescription(
        key="lite_24x7_enabled",
        translation_key="lite_24x7_enabled",
        category="recording",
        attr_path="settings.lite_24x7.enabled",
    ),
    RingExtendedSensorDescription(
        key="lite_24x7_frequency_secs",
        translation_key="lite_24x7_frequency_secs",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        category="recording",
        attr_path="settings.lite_24x7.frequency_secs",
    ),
    RingExtendedSensorDescription(
        key="lite_24x7_resolution_p",
        translation_key="lite_24x7_resolution_p",
        native_unit_of_measurement="p",
        category="recording",
        attr_path="settings.lite_24x7.resolution_p",
    ),
    RingExtendedSensorDescription(
        key="lite_24x7_footage_ttl",
        translation_key="lite_24x7_footage_ttl",
        native_unit_of_measurement=UnitOfTime.HOURS,
        category="recording",
        attr_path="settings.lite_24x7_footage_ttl",
    ),
    RingExtendedSensorDescription(
        key="offline_motion_enabled",
        translation_key="offline_motion_enabled",
        category="recording",
        attr_path="settings.offline_motion_event_settings.enabled",
    ),
)

# Floodlight sensors
FLOODLIGHT_SENSORS: tuple[RingExtendedSensorDescription, ...] = (
    RingExtendedSensorDescription(
        key="floodlight_on",
        translation_key="floodlight_on",
        category="floodlight",
        attr_path="health.floodlight_on",
    ),
    RingExtendedSensorDescription(
        key="white_led_on",
        translation_key="white_led_on",
        category="floodlight",
        attr_path="health.white_led_on",
    ),
    RingExtendedSensorDescription(
        key="floodlight_duration",
        translation_key="floodlight_duration",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        category="floodlight",
        attr_path="settings.floodlight_settings.duration",
    ),
    RingExtendedSensorDescription(
        key="floodlight_brightness",
        translation_key="floodlight_brightness",
        category="floodlight",
        attr_path="settings.floodlight_settings.brightness",
    ),
    RingExtendedSensorDescription(
        key="floodlight_always_on",
        translation_key="floodlight_always_on",
        category="floodlight",
        attr_path="settings.floodlight_settings.always_on",
    ),
)

# Radar / Bird's Eye View sensors
RADAR_SENSORS: tuple[RingExtendedSensorDescription, ...] = (
    RingExtendedSensorDescription(
        key="birds_eye_view_enabled",
        translation_key="birds_eye_view_enabled",
        category="radar",
        attr_path="settings.radar_settings.birds_eye_view_enabled",
    ),
    RingExtendedSensorDescription(
        key="bez_feature_enabled",
        translation_key="bez_feature_enabled",
        category="radar",
        attr_path="settings.radar_settings.bez_feature_enabled",
    ),
    RingExtendedSensorDescription(
        key="bez_filtering_enabled",
        translation_key="bez_filtering_enabled",
        category="radar",
        attr_path="settings.radar_settings.bez_filtering_enabled",
    ),
    RingExtendedSensorDescription(
        key="installation_height",
        translation_key="installation_height",
        native_unit_of_measurement="m",
        category="radar",
        attr_path="settings.radar_settings.installation_height",
    ),
)

# Local Processing (Sheila) sensors
LOCAL_PROCESSING_SENSORS: tuple[RingExtendedSensorDescription, ...] = (
    RingExtendedSensorDescription(
        key="sheila_cv_processing_enabled",
        translation_key="sheila_cv_processing_enabled",
        category="local_processing",
        attr_path="settings.sheila_settings.cv_processing_enabled",
    ),
    RingExtendedSensorDescription(
        key="sheila_local_storage_enabled",
        translation_key="sheila_local_storage_enabled",
        category="local_processing",
        attr_path="settings.sheila_settings.local_storage_enabled",
    ),
    RingExtendedSensorDescription(
        key="sheila_camera_eligible",
        translation_key="sheila_camera_eligible",
        category="local_processing",
        attr_path="features.sheila_camera_eligible",
    ),
    RingExtendedSensorDescription(
        key="sheila_camera_processing_eligible",
        translation_key="sheila_camera_processing_eligible",
        category="local_processing",
        attr_path="features.sheila_camera_processing_eligible",
    ),
)

# Feature Eligibility sensors
FEATURE_SENSORS: tuple[RingExtendedSensorDescription, ...] = (
    RingExtendedSensorDescription(
        key="cfes_eligible",
        translation_key="cfes_eligible",
        category="features",
        attr_path="features.cfes_eligible",
    ),
    RingExtendedSensorDescription(
        key="motions_enabled",
        translation_key="motions_enabled",
        category="features",
        attr_path="features.motions_enabled",
    ),
    RingExtendedSensorDescription(
        key="show_recordings",
        translation_key="show_recordings",
        category="features",
        attr_path="features.show_recordings",
    ),
    RingExtendedSensorDescription(
        key="show_vod_settings",
        translation_key="show_vod_settings",
        category="features",
        attr_path="features.show_vod_settings",
    ),
    RingExtendedSensorDescription(
        key="recording_mode",
        translation_key="recording_mode",
        category="features",
        attr_path="features.video_recording.recording_mode",
    ),
    RingExtendedSensorDescription(
        key="recording_enabled",
        translation_key="recording_enabled",
        category="features",
        attr_path="features.video_recording.recording_enabled",
    ),
    RingExtendedSensorDescription(
        key="recording_state",
        translation_key="recording_state",
        category="features",
        attr_path="features.video_recording.recording_state",
    ),
    RingExtendedSensorDescription(
        key="recording_24x7_eligible",
        translation_key="recording_24x7_eligible",
        category="features",
        attr_path="features.recording_24x7_eligible",
    ),
    RingExtendedSensorDescription(
        key="dynamic_network_switching_eligible",
        translation_key="dynamic_network_switching_eligible",
        category="features",
        attr_path="features.dynamic_network_switching_eligible",
    ),
)

# Device Status sensors
DEVICE_STATUS_SENSORS: tuple[RingExtendedSensorDescription, ...] = (
    RingExtendedSensorDescription(
        key="night_mode_on",
        translation_key="night_mode_on",
        category="device_status",
        attr_path="health.night_mode_on",
    ),
    RingExtendedSensorDescription(
        key="siren_on",
        translation_key="siren_on",
        category="device_status",
        attr_path="health.siren_on",
    ),
    RingExtendedSensorDescription(
        key="hatch_open",
        translation_key="hatch_open",
        category="device_status",
        attr_path="health.hatch_open",
    ),
    RingExtendedSensorDescription(
        key="stolen",
        translation_key="stolen",
        category="device_status",
        attr_path="stolen",
    ),
    RingExtendedSensorDescription(
        key="owned",
        translation_key="owned",
        category="device_status",
        attr_path="owned",
    ),
    RingExtendedSensorDescription(
        key="subscribed",
        translation_key="subscribed",
        category="device_status",
        attr_path="subscribed",
    ),
    RingExtendedSensorDescription(
        key="is_sidewalk_gateway",
        translation_key="is_sidewalk_gateway",
        category="device_status",
        attr_path="is_sidewalk_gateway",
    ),
    RingExtendedSensorDescription(
        key="device_kind",
        translation_key="device_kind",
        category="device_status",
        attr_path="kind",
    ),
)

# Mapping of categories to their sensor definitions
CATEGORY_SENSORS: dict[str, tuple[RingExtendedSensorDescription, ...]] = {
    "health": HEALTH_SENSORS,
    "power": POWER_SENSORS,
    "firmware": FIRMWARE_SENSORS,
    "video": VIDEO_SENSORS,
    "audio": AUDIO_SENSORS,
    "motion": MOTION_SENSORS,
    "cv_detection": CV_DETECTION_SENSORS + CV_THRESHOLD_SENSORS,
    "cv_paid": CV_PAID_SENSORS,
    "other_paid": OTHER_PAID_SENSORS,
    "notifications": NOTIFICATION_SENSORS,
    "recording": RECORDING_SENSORS,
    "floodlight": FLOODLIGHT_SENSORS,
    "radar": RADAR_SENSORS,
    "local_processing": LOCAL_PROCESSING_SENSORS,
    "features": FEATURE_SENSORS,
    "device_status": DEVICE_STATUS_SENSORS,
}

# All sensors combined
ALL_SENSORS: tuple[RingExtendedSensorDescription, ...] = tuple(
    sensor for sensors in CATEGORY_SENSORS.values() for sensor in sensors
)
