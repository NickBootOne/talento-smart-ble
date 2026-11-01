import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "custom_components/talento_smart_ble/protocol.py"
specification = importlib.util.spec_from_file_location("talento_protocol", path)
protocol = importlib.util.module_from_spec(specification)
specification.loader.exec_module(protocol)


class ProtocolTests(unittest.TestCase):
    def test_exact_apk_write_payloads(self):
        self.assertEqual(protocol.encode_command("AUTO"), b"\x00")
        self.assertEqual(protocol.encode_command("FIX_ON"), b"\x01")
        self.assertEqual(protocol.encode_command("FIX_OFF"), b"\x02")
        for command in ["OVR", "", "ON", "REBOOT"]:
            with self.assertRaises(ValueError):
                protocol.encode_command(command)

    def test_readback_is_not_the_write_encoding(self):
        self.assertFalse(protocol.command_confirmed("FIX_ON", protocol.decode_status(b"\x01")))
        self.assertTrue(protocol.command_confirmed("FIX_ON", protocol.decode_status(b"\x02")))
        self.assertTrue(protocol.command_confirmed("FIX_OFF", protocol.decode_status(b"\x03")))
        self.assertFalse(protocol.command_confirmed("AUTO", protocol.decode_status(b"\x08")))

    def test_six_unambiguous_apk_return_values(self):
        expected = [("AUTO", False), ("AUTO", True), ("FIX_ON", True), ("FIX_OFF", False), ("OVR", True), ("OVR", False)]
        for value, (mode, relay) in enumerate(expected):
            with self.subTest(value=value):
                result = protocol.decode_status(bytes([value]))
                self.assertEqual(result, {"raw_hex": f"{value:02x}", "mode": mode, "relay": relay})

    def test_other_bytes_preserved_but_not_interpreted(self):
        for value in range(6, 256):
            result = protocol.decode_status(bytes([value]))
            self.assertEqual(result["raw_hex"], f"{value:02x}")
            self.assertIsNone(result["mode"])
            self.assertIsNone(result["relay"])

    def test_empty_or_multiple_bytes_rejected(self):
        for payload in [b"", b"\x00\x01"]:
            with self.assertRaises(ValueError):
                protocol.decode_status(payload)
