from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import TalentoCoordinator, TalentoStatusCoordinator

PLATFORMS = [Platform.BUTTON, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = TalentoCoordinator(hass, entry)
    coordinator.status = TalentoStatusCoordinator(hass, entry, coordinator)
    entry.runtime_data = coordinator
    coordinator.async_set_updated_data({"result": "not_scanned", "services": [], "scanned_at": None})
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
