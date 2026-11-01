from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory

from .entity import TalentoEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([
        TalentoInspectButton(entry.runtime_data), TalentoStatusButton(entry.runtime_data.status),
        TalentoAutoButton(entry.runtime_data.status),
    ])


class TalentoInspectButton(TalentoEntity, ButtonEntity):
    _attr_name = "GATT inspecteren"
    _attr_icon = "mdi:bluetooth-connect"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_inspect"

    @property
    def available(self):
        return True

    async def async_press(self):
        await self.coordinator.async_request_refresh()
        if not self.coordinator.last_update_success:
            raise HomeAssistantError("Inspectie mislukt. Controleer bereik, Bluetooth-activering en proxy.")


class TalentoStatusButton(TalentoEntity, ButtonEntity):
    _attr_name = "Kanaal 1 status vernieuwen"
    _attr_icon = "mdi:download-network"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_read_status"

    @property
    def available(self):
        return True

    async def async_press(self):
        await self.coordinator.async_request_refresh()
        if not self.coordinator.last_update_success:
            raise HomeAssistantError(str(self.coordinator.last_exception))


class TalentoAutoButton(TalentoEntity, ButtonEntity):
    _attr_name = "AUTO herstellen"
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_restore_auto"

    @property
    def available(self):
        return True

    async def async_press(self):
        await self.coordinator.async_execute_command("AUTO")
