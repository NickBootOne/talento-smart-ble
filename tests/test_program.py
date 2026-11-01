import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

import test_transport as transport_tests

source = Path(__file__).resolve().parents[1] / "custom_components/talento_smart_ble/program.py"
specification = importlib.util.spec_from_file_location("program_decoder", source)
program = importlib.util.module_from_spec(specification)
specification.loader.exec_module(program)
transport = transport_tests.transport


def header(identifier=1, name=b"Werkdagen"):
    packet = bytearray(14)
    packet[0] = identifier >> 8
    packet[1] = identifier & 255
    packet[2:2 + len(name)] = name
    return bytes(packet)


def rule(identifier=1, action=16):
    packet = bytearray(14)
    packet[0] = 8 | (identifier >> 8)
    packet[1] = identifier & 255
    packet[2] = action
    packet[3] = 1
    packet[5] = 62
    packet[6:8] = bytes([8, 30])
    return bytes(packet)


class ProgramDecoderTests(unittest.TestCase):
    def test_weekday_on_and_off_rules(self):
        result = program.decode_program([header(), rule(), rule(action=8)])
        self.assertTrue(result["complete"])
        self.assertEqual(result["program_count"], 1)
        self.assertEqual(result["rule_count"], 2)
        self.assertEqual(result["programs"][0]["name"], "Werkdagen")
        command = result["programs"][0]["rules"][0]
        self.assertEqual(command["time"], "08:30:00")
        self.assertEqual(command["weekdays"], ["ma", "di", "wo", "do", "vr"])
        self.assertEqual(command["channels"], [1])
        self.assertEqual(command["action"], "AAN")
        self.assertEqual(result["programs"][0]["rules"][1]["action"], "UIT")

    def test_out_of_order_packets_and_nine_bit_identifier(self):
        result = program.decode_program([rule(300), header(300)])
        self.assertTrue(result["complete"])
        self.assertEqual(result["programs"][0]["id"], 300)
        self.assertEqual(result["rule_count"], 1)

    def test_unknown_rule_and_orphan_are_reported(self):
        for packets in [[header(), rule(action=0)], [rule()]]:
            result = program.decode_program(packets)
            self.assertFalse(result["complete"])
            self.assertTrue(result["warnings"])
            self.assertEqual(result["raw_packets"], [packet.hex() for packet in packets])

    def test_date_range_with_wildcard_year(self):
        packet = bytearray(14)
        packet[0:8] = bytes([4, 1, 255, 6, 1, 255, 8, 31])
        result = program.decode_program([header(), bytes(packet)])
        dates = result["programs"][0]["date_ranges"][0]
        self.assertEqual(dates["start"], {"year": None, "month": 6, "day": 1})
        self.assertEqual(dates["end"]["day"], 31)

    def test_empty_program_and_duplicate_header(self):
        self.assertEqual(program.decode_program([])["program_count"], 0)
        with self.assertRaises(ValueError):
            program.decode_program([header(), header()])
        with self.assertRaises(ValueError):
            program.decode_program([b"\x00"])

    def test_astro_is_not_a_guessed_clock_time(self):
        packet = bytearray(rule(action=16 | 64))
        packet[4] = 251
        result = program.decode_program([header(), bytes(packet)])
        command = result["programs"][0]["rules"][0]
        self.assertNotIn("time", command)
        self.assertEqual(command["time_type"], "ZONSOPKOMST")
        self.assertEqual(command["offset_raw"], -5)


def client_for(values):
    characteristics = [
        SimpleNamespace(uuid=program.DIRECTION, properties=["write"]),
        SimpleNamespace(uuid=program.PACKAGE_COUNT, properties=["read"]),
        SimpleNamespace(uuid=program.CONTENT, properties=["read"]),
    ]
    return SimpleNamespace(
        services=[SimpleNamespace(uuid=program.MEMORY_SERVICE, characteristics=characteristics)],
        write_gatt_char=AsyncMock(), read_gatt_char=AsyncMock(side_effect=values), disconnect=AsyncMock(),
    )


class ProgramTransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_only_read_direction_is_written_and_exact_count_read(self):
        client = client_for([b"\x02\x00", header(), rule()])
        with patch.object(transport, "establish_connection", AsyncMock(return_value=client)), patch.object(transport.asyncio, "sleep", AsyncMock()) as wait:
            result = await transport.async_read_program(object())
        client.write_gatt_char.assert_awaited_once_with(client.services[0].characteristics[0], b"\x00", response=True)
        wait.assert_awaited_once_with(0.5)
        self.assertEqual(client.read_gatt_char.await_count, 3)
        self.assertEqual(result["packet_count"], 2)
        self.assertEqual(result["rule_count"], 1)
        client.disconnect.assert_awaited_once()

    async def test_zero_count_does_not_read_content(self):
        client = client_for([b"\x00\x00"])
        with patch.object(transport, "establish_connection", AsyncMock(return_value=client)), patch.object(transport.asyncio, "sleep", AsyncMock()):
            result = await transport.async_read_program(object())
        self.assertEqual(result["program_count"], 0)
        self.assertEqual(client.read_gatt_char.await_count, 1)

    async def test_count_length_and_safety_limit(self):
        for count in [b"\x01", b"\xff\xff"]:
            client = client_for([count])
            with patch.object(transport, "establish_connection", AsyncMock(return_value=client)), patch.object(transport.asyncio, "sleep", AsyncMock()):
                with self.assertRaises(transport.StatusReadError):
                    await transport.async_read_program(object())
            self.assertEqual(client.read_gatt_char.await_count, 1)
            client.disconnect.assert_awaited_once()

    async def test_midstream_failure_does_not_retry_or_publish_partial_transfer(self):
        client = client_for([b"\x02\x00", header(), TimeoutError()])
        with patch.object(transport, "establish_connection", AsyncMock(return_value=client)), patch.object(transport.asyncio, "sleep", AsyncMock()):
            with self.assertRaises(transport.StatusReadError) as caught:
                await transport.async_read_program(object())
        self.assertEqual(caught.exception.packets_received, 1)
        self.assertEqual(caught.exception.stage, "read_program_packet_2")
        self.assertEqual(client.write_gatt_char.await_count, 1)
        client.disconnect.assert_awaited_once()
