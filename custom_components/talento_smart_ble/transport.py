import asyncio
import logging

from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from .const import CHANNEL_SELECT, CHANNEL_STATE, CONFIG_SERVICE
from .protocol import decode_status

_LOGGER = logging.getLogger(__name__)


class StatusReadError(Exception):
    def __init__(self, stage, reason, raw_hex=None):
        super().__init__(reason)
        self.stage = stage
        self.reason = reason
        self.raw_hex = raw_hex


async def async_read_channel_status(device):
    client = None
    stage = "connect"
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
                return decode_status(payload)
            except ValueError as error:
                raise StatusReadError(stage, str(error), payload[:16].hex()) from error
    except StatusReadError:
        raise
    except Exception as error:
        raise StatusReadError(stage, type(error).__name__) from error
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
