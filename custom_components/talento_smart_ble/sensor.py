from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.entity import EntityCategory

from .entity import TalentoEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([
        TalentoInspectionSensor(entry.runtime_data),
        TalentoStatusSensor(entry.runtime_data.status, "raw_hex", "Ruwe kanaalstatus"),
        TalentoStatusSensor(entry.runtime_data.status, "mode", "Modus"),
        TalentoStatusSensor(entry.runtime_data.status, "relay", "Relaisstatus"),
        TalentoProgramSensor(entry.runtime_data.program),
    ])


class TalentoInspectionSensor(TalentoEntity, SensorEntity):
    _attr_translation_key = "inspection"
    _attr_icon = "mdi:list-status"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_inspection"

    @property
    def native_value(self):
        return self.coordinator.data["result"]

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        return {
            "scanned_at": data["scanned_at"],
            "service_count": len(data["services"]),
            "relay_control_supported": True,
        }


class TalentoStatusSensor(TalentoEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, key, name):
        super().__init__(coordinator)
        self.key = key
        self._attr_translation_key = key
        if key == "relay":
            self._attr_device_class = SensorDeviceClass.ENUM
            self._attr_options = ["aan", "uit"]
        self._attr_unique_id = f"{coordinator.address}_status_{key}"

    @property
    def available(self):
        return self.coordinator.fresh and self.coordinator.data.get(self.key) is not None

    @property
    def native_value(self):
        value = self.coordinator.data.get(self.key)
        return ("aan" if value else "uit") if self.key == "relay" and value is not None else value

    @property
    def extra_state_attributes(self):
        return {
            "measured_at": self.coordinator.data.get("measured_at"),
            "channel": 1,
            "expires_after_seconds": 120,
        }


class TalentoProgramSensor(TalentoEntity, SensorEntity):
    _attr_translation_key = "program"
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_program"

    @property
    def available(self):
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        count = self.coordinator.data["program_count"]
        return f"{count} program" if count == 1 else f"{count} programs"

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if data is None:
            return {}
        return {
            "talento_program_overview": True,
            **{key: data[key] for key in ["read_at", "program_count", "rule_count", "packet_count", "overview", "overview_truncated", "program_summaries", "program_summaries_truncated", "display_rows", "display_rule_count", "display_truncated", "duplicate_rule_count", "complete"]},
        }
