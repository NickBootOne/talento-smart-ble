import logging

from bleak.exc import BleakError

from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .transport import async_inspect_device

_LOGGER = logging.getLogger(__name__)


class TalentoCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(hass, _LOGGER, name=DOMAIN, config_entry=entry)
        self.address = entry.data[CONF_ADDRESS]
        self.last_attempt = None
        self.failure_reason = None

    async def _async_update_data(self):
        self.last_attempt = dt_util.utcnow().isoformat()
        device = bluetooth.async_ble_device_from_address(self.hass, self.address, connectable=True)
        if device is None:
            self.failure_reason = "not_seen_by_connectable_adapter"
            raise UpdateFailed("Geen bereikbare Bluetooth-adapter. Activeer Bluetooth op de C15 en probeer opnieuw.")
        try:
            result = await async_inspect_device(device)
        except (BleakError, TimeoutError, OSError) as error:
            self.failure_reason = type(error).__name__
            raise UpdateFailed("GATT-inspectie mislukt. Controleer bereik en sluit de telefoonapp.") from error
        self.failure_reason = None
        return {**result, "scanned_at": dt_util.utcnow().isoformat()}
