import asyncio
import logging

from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from .const import CHANNEL_SELECT, CHANNEL_STATE, CONFIG_SERVICE
from .protocol import command_confirmed, decode_status, encode_command

_LOGGER = logging.getLogger(__name__)


class StatusReadError(Exception):
    def __init__(self, stage, reason, raw_hex=None):
        super().__init__(reason)
        self.stage = stage
        self.reason = reason
        self.raw_hex = raw_hex
        self.command_may_have_applied = False


async def async_read_channel_status(device, command=None):
    command_payload = encode_command(command) if command is not None else None
    client = None
    stage = "connect"
    command_attempted = False
    try:
        async with asyncio.timeout(45):
            client = await establish_connection(
                BleakClientWithServiceCache, device, "Talento smart status test", max_attempts=2,
            )
            stage = "check_characteristics"
            config = next((service for service in client.services if service.uuid.lower() == CONFIG_SERVICE), None)
            characteristics = {item.uuid.lower(): item for item in config.characteristics} if config else {}
            select = characteristics.get(CHANNEL_SELECT)
            state = characteristics.get(CHANNEL_STATE)
            if select is None or state is None or "read" not in state.properties:
                raise StatusReadError(stage, "missing_status_characteristics")
            if "write" not in select.properties and "write-without-response" not in select.properties:
                raise StatusReadError(stage, "channel_select_not_writable")
            stage = "select_channel_1"
            await client.write_gatt_char(select, b"\x01", response="write" in select.properties)
            stage = "wait_for_channel"
            await asyncio.sleep(1)
            stage = "read_status"
            payload = bytes(await client.read_gatt_char(state))
            stage = "decode_status"
            try:
                measurement = decode_status(payload)
            except ValueError as error:
                raise StatusReadError(stage, str(error), payload[:16].hex()) from error
            if command is None:
                return measurement
            if measurement["relay"] is None or measurement["mode"] is None:
                raise StatusReadError(stage, "unknown_initial_status", measurement["raw_hex"])
            if "write" not in state.properties:
                raise StatusReadError("check_write_permission", "status_write_with_response_required")
            stage = "write_command"
            command_attempted = True
            await client.write_gatt_char(state, command_payload, response=True)
            stage = "wait_after_command"
            await asyncio.sleep(1)
            stage = "reselect_channel_1"
            await client.write_gatt_char(select, b"\x01", response="write" in select.properties)
            await asyncio.sleep(1)
            stage = "readback_command"
            payload = bytes(await client.read_gatt_char(state))
            try:
                measurement = decode_status(payload)
            except ValueError as error:
                raise StatusReadError(stage, str(error), payload[:16].hex()) from error
            if not command_confirmed(command, measurement):
                raise StatusReadError(stage, "command_not_confirmed", measurement["raw_hex"])
            return measurement
    except StatusReadError as error:
        error.command_may_have_applied = command_attempted
        raise
    except Exception as error:
        failure = StatusReadError(stage, type(error).__name__)
        failure.command_may_have_applied = command_attempted
        raise failure from error
    finally:
        if client is not None:
            try:
                async with asyncio.timeout(10):
                    await client.disconnect()
            except Exception:
                _LOGGER.warning("Status test disconnect did not complete")


async def async_inspect_device(device):
    client = None
    try:
        async with asyncio.timeout(45):
            client = await establish_connection(
                BleakClientWithServiceCache, device, "Talento smart GATT inspection",
                max_attempts=2,
            )
            services = [
                {
                    "uuid": service.uuid.lower(),
                    "characteristics": [
                        {
                            "uuid": characteristic.uuid.lower(),
                            "properties": sorted(characteristic.properties),
                        }
                        for characteristic in service.characteristics
                    ],
                }
                for service in client.services
            ]
            config = next((service for service in services if service["uuid"] == CONFIG_SERVICE), None)
            characteristics = {item["uuid"] for item in config["characteristics"]} if config else set()
            found = {CHANNEL_SELECT, CHANNEL_STATE}.issubset(characteristics)
            return {
                "result": "expected_uuids_found" if found else "expected_uuids_missing",
                "services": services,
            }
    finally:
        if client is not None:
            try:
                async with asyncio.timeout(10):
                    await client.disconnect()
            except Exception:
                _LOGGER.warning("GATT inspection disconnect did not complete")
