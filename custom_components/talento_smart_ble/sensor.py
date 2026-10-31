from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import EntityCategory

from .entity import TalentoEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([TalentoInspectionSensor(entry.runtime_data)])


class TalentoInspectionSensor(TalentoEntity, SensorEntity):
    _attr_name = "Laatste GATT-inspectie"
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
            "relay_control_supported": False,
        }
