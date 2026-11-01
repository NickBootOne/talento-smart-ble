from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory

from .entity import TalentoEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([
        TalentoInspectButton(entry.runtime_data), TalentoStatusButton(entry.runtime_data.status),
        TalentoAutoButton(entry.runtime_data.status),
        TalentoProgramButton(entry.runtime_data.program),
    ])


class TalentoInspectButton(TalentoEntity, ButtonEntity):
    _attr_translation_key = "inspect"
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
            raise HomeAssistantError("Inspection failed. Check range, Bluetooth activation and proxy availability.")


class TalentoStatusButton(TalentoEntity, ButtonEntity):
    _attr_translation_key = "read_status"
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
    _attr_translation_key = "restore_auto"
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_restore_auto"

    @property
    def available(self):
        return True

    async def async_press(self):
        await self.coordinator.async_execute_command("AUTO")


class TalentoProgramButton(TalentoEntity, ButtonEntity):
    _attr_translation_key = "read_program"
    _attr_icon = "mdi:calendar-arrow-down"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_read_program"

    @property
    def available(self):
        return True

    async def async_press(self):
        await self.coordinator.async_request_refresh()
        if not self.coordinator.last_update_success:
            raise HomeAssistantError(str(self.coordinator.last_exception))
