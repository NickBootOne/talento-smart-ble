from homeassistant.components.switch import SwitchEntity

from .entity import TalentoEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([TalentoRelaySwitch(entry.runtime_data.status)])


class TalentoRelaySwitch(TalentoEntity, SwitchEntity):
    _attr_name = "Relais (FIX-bediening)"
    _attr_icon = "mdi:electric-switch"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_relay_fix"

    @property
    def available(self):
        return self.coordinator.fresh and self.coordinator.data.get("relay") is not None

    @property
    def is_on(self):
        return self.coordinator.data.get("relay")

    @property
    def extra_state_attributes(self):
        return {
            "mode": self.coordinator.data.get("mode"),
            "measured_at": self.coordinator.data.get("measured_at"),
            "control_mode": "FIX",
            "expires_after_seconds": 120,
        }

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_execute_command("FIX_ON")

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_execute_command("FIX_OFF")
