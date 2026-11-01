import asyncio
import logging

from bleak.exc import BleakError

from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.event import async_call_later
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .protocol import encode_command
from .transport import StatusReadError, async_inspect_device, async_read_channel_status

_LOGGER = logging.getLogger(__name__)


class TalentoCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(hass, _LOGGER, name=DOMAIN, config_entry=entry)
        self.address = entry.data[CONF_ADDRESS]
        self.last_attempt = None
        self.failure_reason = None
        self.connection_lock = asyncio.Lock()

    async def _async_update_data(self):
        self.last_attempt = dt_util.utcnow().isoformat()
        device = bluetooth.async_ble_device_from_address(self.hass, self.address, connectable=True)
        if device is None:
            self.failure_reason = "not_seen_by_connectable_adapter"
            raise UpdateFailed("Geen bereikbare Bluetooth-adapter. Activeer Bluetooth op de C15 en probeer opnieuw.")
        try:
            async with self.connection_lock:
                result = await async_inspect_device(device)
        except (BleakError, TimeoutError, OSError) as error:
            self.failure_reason = type(error).__name__
            raise UpdateFailed("GATT-inspectie mislukt. Controleer bereik en sluit de telefoonapp.") from error
        self.failure_reason = None
        return {**result, "scanned_at": dt_util.utcnow().isoformat()}


class TalentoStatusCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, inspection):
        super().__init__(hass, _LOGGER, name=f"{DOMAIN}_status", config_entry=entry)
        self.address = inspection.address
        self.connection_lock = inspection.connection_lock
        self.last_attempt = None
        self.failure = None
        self.last_command = None
        self._cancel_expiry = None
        self.async_set_updated_data({"raw_hex": None, "mode": None, "relay": None, "measured_at": None})
        entry.async_on_unload(self.cancel_expiry)

    @callback
    def cancel_expiry(self):
        if self._cancel_expiry is not None:
            self._cancel_expiry()
            self._cancel_expiry = None

    @callback
    def expire(self, now):
        self._cancel_expiry = None
        self.async_update_listeners()

    @property
    def fresh(self):
        measured_at = self.data.get("measured_at")
        return bool(
            self.last_update_success and measured_at is not None
            and (dt_util.utcnow() - dt_util.parse_datetime(measured_at)).total_seconds() < 120
        )

    async def _async_update_data(self):
        self.last_attempt = dt_util.utcnow().isoformat()
        self.cancel_expiry()
        self.async_set_updated_data({"raw_hex": None, "mode": None, "relay": None, "measured_at": None})
        async with self.connection_lock:
            device = bluetooth.async_ble_device_from_address(self.hass, self.address, connectable=True)
            if device is None:
                self.failure = {"stage": "lookup", "reason": "not_seen_by_connectable_adapter"}
                raise UpdateFailed("C15 niet bereikbaar. Activeer Bluetooth en controleer de proxy.")
            try:
                result = await async_read_channel_status(device)
            except StatusReadError as error:
                self.failure = {"stage": error.stage, "reason": error.reason, "raw_hex": error.raw_hex}
                raise UpdateFailed(
                    f"Statusleestest mislukt bij {error.stage} ({error.reason}). "
                    "Mogelijk is authenticatie nodig; er is geen PIN-handshake uitgevoerd. Download de diagnostiek."
                ) from error
        self.failure = None
        self._cancel_expiry = async_call_later(self.hass, 121, self.expire)
        return {**result, "measured_at": dt_util.utcnow().isoformat()}

    async def async_execute_command(self, command):
        encode_command(command)
        async with self.connection_lock:
            self.cancel_expiry()
            self.last_attempt = dt_util.utcnow().isoformat()
            self.last_command = {"requested": command, "at": self.last_attempt, "outcome": "pending"}
            self.async_set_updated_data({"raw_hex": None, "mode": None, "relay": None, "measured_at": None})
            device = bluetooth.async_ble_device_from_address(self.hass, self.address, connectable=True)
            if device is None:
                self.failure = {"stage": "lookup", "reason": "not_seen_by_connectable_adapter", "command_may_have_applied": False}
                self.last_command["outcome"] = "not_sent"
                error = UpdateFailed("C15 niet bereikbaar. Activeer Bluetooth en controleer de proxy.")
                self.async_set_update_error(error)
                raise HomeAssistantError(str(error))
            try:
                result = await async_read_channel_status(device, command=command)
            except StatusReadError as error:
                self.failure = {
                    "stage": error.stage, "reason": error.reason, "raw_hex": error.raw_hex,
                    "command_may_have_applied": error.command_may_have_applied,
                }
                self.last_command["outcome"] = "unconfirmed" if error.command_may_have_applied else "not_sent"
                failure = UpdateFailed(
                    f"Opdracht {command} niet bevestigd bij {error.stage} ({error.reason}). "
                    "De relaisstand is onbekend; lees opnieuw of controleer de C15. Er wordt niet automatisch opnieuw geschakeld."
                )
                self.async_set_update_error(failure)
                raise HomeAssistantError(str(failure)) from error
            except asyncio.CancelledError:
                self.last_command["outcome"] = "cancelled_unknown"
                self.async_set_update_error(UpdateFailed("Schakelactie afgebroken; werkelijke toestand onbekend."))
                raise
            self.failure = None
            self.last_command["outcome"] = "confirmed"
            self.async_set_updated_data({**result, "measured_at": dt_util.utcnow().isoformat()})
            self._cancel_expiry = async_call_later(self.hass, 121, self.expire)
