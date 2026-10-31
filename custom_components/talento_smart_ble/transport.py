import asyncio
import logging

from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from .const import CHANNEL_SELECT, CHANNEL_STATE, CONFIG_SERVICE

_LOGGER = logging.getLogger(__name__)


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
