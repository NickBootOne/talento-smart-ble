import asyncio
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "talento_transport_tests"
package = ModuleType(PACKAGE)
package.__path__ = [str(ROOT / "custom_components/talento_smart_ble")]
sys.modules[PACKAGE] = package
connector = ModuleType("bleak_retry_connector")
connector.BleakClientWithServiceCache = object
connector.establish_connection = AsyncMock()
with patch.dict(sys.modules, {"bleak_retry_connector": connector}):
    specification = importlib.util.spec_from_file_location(
        f"{PACKAGE}.transport", ROOT / "custom_components/talento_smart_ble/transport.py"
    )
    transport = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(transport)


def make_client(service_uuid=None):
    service = SimpleNamespace(
        uuid=service_uuid or transport.CONFIG_SERVICE.upper(),
        characteristics=[
            SimpleNamespace(uuid=transport.CHANNEL_SELECT.upper(), properties=["write"]),
            SimpleNamespace(uuid=transport.CHANNEL_STATE.upper(), properties=["write", "read"]),
        ],
    )
    return SimpleNamespace(
        services=[service], disconnect=AsyncMock(),
        read_gatt_char=AsyncMock(side_effect=AssertionError("Unexpected read")),
        write_gatt_char=AsyncMock(side_effect=AssertionError("Unexpected write")),
    )


class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_metadata_only_and_disconnect(self):
        client = make_client()
        device = object()
        with patch.object(transport, "establish_connection", AsyncMock(return_value=client)) as connect:
            result = await transport.async_inspect_device(device)
        self.assertEqual(result["result"], "expected_uuids_found")
        self.assertIs(connect.call_args.args[1], device)
        self.assertEqual(result["services"][0]["characteristics"][1]["properties"], ["read", "write"])
        client.disconnect.assert_awaited_once()
        client.read_gatt_char.assert_not_called()
        client.write_gatt_char.assert_not_called()

    async def test_expected_characteristics_in_wrong_service_are_rejected(self):
        client = make_client("00001800-0000-1000-8000-00805f9b34fb")
        with patch.object(transport, "establish_connection", AsyncMock(return_value=client)):
            result = await transport.async_inspect_device(object())
        self.assertEqual(result["result"], "expected_uuids_missing")
        client.disconnect.assert_awaited_once()

    async def test_disconnect_on_metadata_failure(self):
        client = make_client()
        client.services = None
        with patch.object(transport, "establish_connection", AsyncMock(return_value=client)):
            with self.assertRaises(TypeError):
                await transport.async_inspect_device(object())
        client.disconnect.assert_awaited_once()

    async def test_connection_failure_is_propagated(self):
        with patch.object(transport, "establish_connection", AsyncMock(side_effect=TimeoutError)):
            with self.assertRaises(TimeoutError):
                await transport.async_inspect_device(object())

    async def test_cancellation_disconnects_and_propagates(self):
        class CancelledServices:
            def __iter__(self):
                raise asyncio.CancelledError

        client = make_client()
        client.services = CancelledServices()
        with patch.object(transport, "establish_connection", AsyncMock(return_value=client)):
            with self.assertRaises(asyncio.CancelledError):
                await transport.async_inspect_device(object())
        client.disconnect.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
