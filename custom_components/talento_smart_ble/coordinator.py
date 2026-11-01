import asyncio
import logging
from datetime import timedelta
from time import monotonic

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
            raise UpdateFailed("No reachable Bluetooth adapter. Enable Bluetooth on the C15 and try again.")
        try:
            async with self.connection_lock:
                result = await async_inspect_device(device)
        except (BleakError, TimeoutError, OSError) as error:
            self.failure_reason = type(error).__name__
            raise UpdateFailed("GATT inspection failed. Check range and close the phone app.") from error
        self.failure_reason = None
        return {**result, "scanned_at": dt_util.utcnow().isoformat()}


class TalentoStatusCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, inspection):
        super().__init__(hass, _LOGGER, name=f"{DOMAIN}_status", config_entry=entry, update_interval=timedelta(seconds=30))
        self.address = inspection.address
        self.connection_lock = inspection.connection_lock
        self.last_attempt = None
        self.failure = None
        self.last_command = None
        self._cancel_expiry = None
        self._measured_monotonic = None
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
    def measurement_age_seconds(self):
        if self._measured_monotonic is None:
            return None
        return max(0, monotonic() - self._measured_monotonic)

    @property
    def freshness_reason(self):
        if not self.last_update_success:
            return "last_read_failed"
        age = self.measurement_age_seconds
        if age is None:
            return "never_read"
        return "fresh" if age < 120 else "expired"

    @property
    def fresh(self):
        return self.freshness_reason == "fresh"

    async def _async_update_data(self):
        self.last_attempt = dt_util.utcnow().isoformat()
        async with self.connection_lock:
            device = bluetooth.async_ble_device_from_address(self.hass, self.address, connectable=True)
            if device is None:
                self.failure = {"stage": "lookup", "reason": "not_seen_by_connectable_adapter"}
                raise UpdateFailed("C15 unreachable. Enable Bluetooth and check the proxy.")
            try:
                result = await async_read_channel_status(device)
            except StatusReadError as error:
                self.failure = {"stage": error.stage, "reason": error.reason, "raw_hex": error.raw_hex}
                raise UpdateFailed(
                    f"Status read failed at {error.stage} ({error.reason}). "
                    "Authentication may be required; no PIN handshake was performed. Download diagnostics."
                ) from error
        self.failure = None
        self.cancel_expiry()
        self._measured_monotonic = monotonic()
        self._cancel_expiry = async_call_later(self.hass, 121, self.expire)
        return {**result, "measured_at": dt_util.utcnow().isoformat()}

    async def async_execute_command(self, command):
        encode_command(command)
        async with self.connection_lock:
            self.cancel_expiry()
            self.last_attempt = dt_util.utcnow().isoformat()
            self.last_command = {"requested": command, "at": self.last_attempt, "outcome": "pending"}
            self._measured_monotonic = None
            self.async_set_updated_data({"raw_hex": None, "mode": None, "relay": None, "measured_at": None})
            device = bluetooth.async_ble_device_from_address(self.hass, self.address, connectable=True)
            if device is None:
                self.failure = {"stage": "lookup", "reason": "not_seen_by_connectable_adapter", "command_may_have_applied": False}
                self.last_command["outcome"] = "not_sent"
                error = UpdateFailed("C15 unreachable. Enable Bluetooth and check the proxy.")
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
                    f"Command {command} was not confirmed at {error.stage} ({error.reason}). "
                    "The relay state is unknown; refresh status or check the C15. Switching commands are not retried automatically."
                )
                self.async_set_update_error(failure)
                raise HomeAssistantError(str(failure)) from error
            except asyncio.CancelledError:
                self.last_command["outcome"] = "cancelled_unknown"
                self.async_set_update_error(UpdateFailed("Switching cancelled; actual state unknown."))
                raise
            self.failure = None
            self.last_command["outcome"] = "confirmed"
            self._measured_monotonic = monotonic()
            self.async_set_updated_data({**result, "measured_at": dt_util.utcnow().isoformat()})
            self._cancel_expiry = async_call_later(self.hass, 121, self.expire)
