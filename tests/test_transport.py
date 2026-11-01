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
    async def test_each_command_is_written_once_and_confirmed_by_readback(self):
        for command, payload, reply in [("FIX_ON", b"\x01", b"\x02"), ("FIX_OFF", b"\x02", b"\x03"), ("AUTO", b"\x00", b"\x01")]:
            with self.subTest(command=command):
                client = make_client()
                events = []
                replies = iter([b"\x00", reply])

                async def write(characteristic, value, response):
                    events.append(("write", characteristic.uuid.lower(), value, response))

                async def read(characteristic):
                    events.append(("read", characteristic.uuid.lower()))
                    return next(replies)

                async def wait(seconds):
                    events.append(("wait", seconds))

                client.write_gatt_char = AsyncMock(side_effect=write)
                client.read_gatt_char = AsyncMock(side_effect=read)
                with patch.object(transport, "establish_connection", AsyncMock(return_value=client)), patch.object(transport.asyncio, "sleep", wait):
                    result = await transport.async_read_channel_status(object(), command=command)
                self.assertEqual(events, [
                    ("write", transport.CHANNEL_SELECT, b"\x01", True), ("wait", 1),
                    ("read", transport.CHANNEL_STATE),
                    ("write", transport.CHANNEL_STATE, payload, True), ("wait", 1),
                    ("write", transport.CHANNEL_SELECT, b"\x01", True), ("wait", 1),
                    ("read", transport.CHANNEL_STATE),
                ])
                self.assertEqual(result["mode"], command)
                client.disconnect.assert_awaited_once()

    async def test_unconfirmed_command_does_not_retry(self):
        client = make_client()
        client.write_gatt_char = AsyncMock()
        client.read_gatt_char = AsyncMock(side_effect=[b"\x00", b"\x00"])
        with patch.object(transport, "establish_connection", AsyncMock(return_value=client)), patch.object(transport.asyncio, "sleep", AsyncMock()):
            with self.assertRaises(transport.StatusReadError) as caught:
                await transport.async_read_channel_status(object(), command="FIX_ON")
        self.assertEqual(caught.exception.reason, "command_not_confirmed")
        self.assertTrue(caught.exception.command_may_have_applied)
        self.assertEqual(caught.exception.raw_hex, "00")
        self.assertEqual(client.write_gatt_char.await_count, 3)
        client.disconnect.assert_awaited_once()

    async def test_write_timeout_is_not_retried_or_claimed_successful(self):
        client = make_client()
        client.write_gatt_char = AsyncMock(side_effect=[None, TimeoutError])
        client.read_gatt_char = AsyncMock(return_value=b"\x00")
        with patch.object(transport, "establish_connection", AsyncMock(return_value=client)), patch.object(transport.asyncio, "sleep", AsyncMock()):
            with self.assertRaises(transport.StatusReadError) as caught:
                await transport.async_read_channel_status(object(), command="FIX_ON")
        self.assertEqual(caught.exception.stage, "write_command")
        self.assertTrue(caught.exception.command_may_have_applied)
        self.assertEqual(client.write_gatt_char.await_count, 2)
        client.disconnect.assert_awaited_once()

    async def test_unknown_initial_status_blocks_relay_command(self):
        client = make_client()
        client.write_gatt_char = AsyncMock()
        client.read_gatt_char = AsyncMock(return_value=b"\x08")
        with patch.object(transport, "establish_connection", AsyncMock(return_value=client)), patch.object(transport.asyncio, "sleep", AsyncMock()):
            with self.assertRaises(transport.StatusReadError) as caught:
                await transport.async_read_channel_status(object(), command="FIX_ON")
        self.assertFalse(caught.exception.command_may_have_applied)
        self.assertEqual(caught.exception.reason, "unknown_initial_status")
        self.assertEqual(client.write_gatt_char.await_count, 1)

    async def test_unsupported_override_is_rejected_before_connecting(self):
        with patch.object(transport, "establish_connection", AsyncMock()) as connect:
            with self.assertRaises(ValueError):
                await transport.async_read_channel_status(object(), command="OVR")
        connect.assert_not_called()

    async def test_readonly_status_blocks_relay_command(self):
        client = make_client()
        client.services[0].characteristics[1].properties = ["read"]
        client.write_gatt_char = AsyncMock()
        client.read_gatt_char = AsyncMock(return_value=b"\x00")
        with patch.object(transport, "establish_connection", AsyncMock(return_value=client)), patch.object(transport.asyncio, "sleep", AsyncMock()):
            with self.assertRaises(transport.StatusReadError) as caught:
                await transport.async_read_channel_status(object(), command="AUTO")
        self.assertFalse(caught.exception.command_may_have_applied)
        self.assertEqual(client.write_gatt_char.await_count, 1)

    async def test_status_selects_only_channel_one_then_reads(self):
        client = make_client()
        client.write_gatt_char = AsyncMock()
        client.read_gatt_char = AsyncMock(return_value=b"\x02")
        events = []
        client.write_gatt_char.side_effect = lambda *args, **kwargs: events.append("select")
        client.read_gatt_char.side_effect = lambda *args: events.append("read") or b"\x02"

        async def wait(seconds):
            self.assertEqual(seconds, 1)
            events.append("wait")

        with patch.object(transport, "establish_connection", AsyncMock(return_value=client)), patch.object(transport.asyncio, "sleep", wait):
            result = await transport.async_read_channel_status(object())
        self.assertEqual(events, ["select", "wait", "read"])
        self.assertEqual(result, {"raw_hex": "02", "mode": "FIX_ON", "relay": True})
        selected = client.services[0].characteristics[0]
        state = client.services[0].characteristics[1]
        client.write_gatt_char.assert_awaited_once_with(selected, b"\x01", response=True)
        client.read_gatt_char.assert_awaited_once_with(state)
        client.disconnect.assert_awaited_once()

    async def test_status_permission_failure_stops_without_reading(self):
        client = make_client()
        client.write_gatt_char = AsyncMock(side_effect=PermissionError)
        with patch.object(transport, "establish_connection", AsyncMock(return_value=client)):
            with self.assertRaises(transport.StatusReadError) as caught:
                await transport.async_read_channel_status(object())
        self.assertEqual(caught.exception.stage, "select_channel_1")
        self.assertEqual(caught.exception.reason, "PermissionError")
        client.read_gatt_char.assert_not_called()
        client.disconnect.assert_awaited_once()

    async def test_status_invalid_length_is_not_decoded(self):
        client = make_client()
        client.write_gatt_char = AsyncMock()
        client.read_gatt_char = AsyncMock(return_value=b"\x01\x02")
        with patch.object(transport, "establish_connection", AsyncMock(return_value=client)), patch.object(transport.asyncio, "sleep", AsyncMock()):
            with self.assertRaises(transport.StatusReadError) as caught:
                await transport.async_read_channel_status(object())
        self.assertEqual(caught.exception.stage, "decode_status")
        self.assertEqual(caught.exception.raw_hex, "0102")
        client.disconnect.assert_awaited_once()

    async def test_status_wrong_service_never_writes(self):
        client = make_client("00001800-0000-1000-8000-00805f9b34fb")
        with patch.object(transport, "establish_connection", AsyncMock(return_value=client)):
            with self.assertRaises(transport.StatusReadError):
                await transport.async_read_channel_status(object())
        client.write_gatt_char.assert_not_called()
        client.disconnect.assert_awaited_once()

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
