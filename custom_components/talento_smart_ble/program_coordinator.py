from homeassistant.components import bluetooth
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .coordinator import _LOGGER
from .transport import StatusReadError, async_read_program


class TalentoProgramCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, inspection):
        super().__init__(hass, _LOGGER, name="talento_smart_ble_program", config_entry=entry)
        self.address = inspection.address
        self.connection_lock = inspection.connection_lock
        self.failure = None
        self.async_set_updated_data(None)

    async def _async_update_data(self):
        async with self.connection_lock:
            device = bluetooth.async_ble_device_from_address(self.hass, self.address, connectable=True)
            if device is None:
                self.failure = {"stage": "lookup", "reason": "not_seen_by_connectable_adapter"}
                raise UpdateFailed("C15 unreachable for schedule retrieval.")
            try:
                result = await async_read_program(device)
            except StatusReadError as error:
                self.failure = {"stage": error.stage, "reason": error.reason, "packets_received": getattr(error, "packets_received", 0)}
                raise UpdateFailed(f"Schedule retrieval failed at {error.stage} ({error.reason}). Download diagnostics.") from error
        self.failure = None
        return {**result, "read_at": dt_util.utcnow().isoformat()}
