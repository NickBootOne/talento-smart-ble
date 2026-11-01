from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant

from .coordinator import TalentoCoordinator, TalentoStatusCoordinator
from .const import NAME
from .program_coordinator import TalentoProgramCoordinator

PLATFORMS = [Platform.BUTTON, Platform.SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    suffix = entry.data[CONF_ADDRESS][-5:]
    if entry.title == f"Talento smart BLE (onderzoek) {suffix}":
        hass.config_entries.async_update_entry(entry, title=f"{NAME} {suffix}")
    coordinator = TalentoCoordinator(hass, entry)
    coordinator.status = TalentoStatusCoordinator(hass, entry, coordinator)
    coordinator.program = TalentoProgramCoordinator(hass, entry, coordinator)
    entry.runtime_data = coordinator
    coordinator.async_set_updated_data({"result": "not_scanned", "services": [], "scanned_at": None})
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
