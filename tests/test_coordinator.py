import asyncio
from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "talento_coordinator_tests"


class FakeCoordinator:
    def __init__(self, hass, logger, **kwargs):
        self.hass = hass
        self.update_interval = kwargs.get("update_interval")
        self.last_update_success = True
        self.data = None

    def async_set_updated_data(self, data):
        self.data = data
        self.last_update_success = True

    def async_set_update_error(self, error):
        self.last_update_success = False

    def async_update_listeners(self):
        pass


modules = {name: ModuleType(name) for name in [
    "homeassistant", "homeassistant.components", "homeassistant.components.bluetooth",
    "homeassistant.const", "homeassistant.core", "homeassistant.exceptions",
    "homeassistant.helpers", "homeassistant.helpers.update_coordinator", "homeassistant.helpers.event",
    "homeassistant.util", "homeassistant.util.dt", "bleak", "bleak.exc", PACKAGE, f"{PACKAGE}.transport",
]}
modules[PACKAGE].__path__ = [str(ROOT / "custom_components/talento_smart_ble")]
modules["homeassistant.components"].bluetooth = modules["homeassistant.components.bluetooth"]
modules["homeassistant.components.bluetooth"].async_ble_device_from_address = Mock(return_value=object())
modules["homeassistant.const"].CONF_ADDRESS = "address"
modules["homeassistant.core"].callback = lambda function: function
modules["homeassistant.exceptions"].HomeAssistantError = RuntimeError
modules["homeassistant.helpers.update_coordinator"].DataUpdateCoordinator = FakeCoordinator
modules["homeassistant.helpers.update_coordinator"].UpdateFailed = RuntimeError
modules["homeassistant.helpers.event"].async_call_later = Mock(return_value=Mock())
modules["homeassistant.util"].dt = modules["homeassistant.util.dt"]
modules["homeassistant.util.dt"].utcnow = lambda: datetime.now(timezone.utc)
modules["bleak.exc"].BleakError = RuntimeError
modules[f"{PACKAGE}.transport"].StatusReadError = type("StatusReadError", (Exception,), {})
modules[f"{PACKAGE}.transport"].async_inspect_device = AsyncMock()
modules[f"{PACKAGE}.transport"].async_read_channel_status = AsyncMock()
with patch.dict(sys.modules, modules):
    specification = importlib.util.spec_from_file_location(
        f"{PACKAGE}.coordinator", ROOT / "custom_components/talento_smart_ble/coordinator.py"
    )
    coordinator_module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(coordinator_module)


class CoordinatorTests(unittest.IsolatedAsyncioTestCase):
    def make_coordinator(self):
        entry = SimpleNamespace(async_on_unload=Mock())
        inspection = SimpleNamespace(address="AA:BB:CC:DD:EE:FF", connection_lock=asyncio.Lock())
        return coordinator_module.TalentoStatusCoordinator(object(), entry, inspection)

    async def test_poll_interval_and_no_initial_measurement(self):
        coordinator = self.make_coordinator()
        self.assertEqual(coordinator.update_interval, timedelta(seconds=30))
        self.assertFalse(coordinator.fresh)
        self.assertEqual(coordinator.freshness_reason, "never_read")

    async def test_refresh_preserves_existing_measurement_while_waiting(self):
        coordinator = self.make_coordinator()
        old = {"raw_hex": "00", "mode": "AUTO", "relay": False, "measured_at": "old"}
        coordinator.async_set_updated_data(old)
        coordinator._measured_monotonic = 100

        async def read(device):
            self.assertEqual(coordinator.data, old)
            self.assertTrue(coordinator.fresh)
            return {"raw_hex": "01", "mode": "AUTO", "relay": True}

        with patch.object(coordinator_module, "monotonic", return_value=130), patch.object(coordinator_module, "async_read_channel_status", read):
            result = await coordinator._async_update_data()
            coordinator.async_set_updated_data(result)
            self.assertTrue(coordinator.fresh)
        self.assertEqual(coordinator.data["raw_hex"], "01")

    async def test_expiry_boundary_and_read_failure(self):
        coordinator = self.make_coordinator()
        coordinator._measured_monotonic = 100
        with patch.object(coordinator_module, "monotonic", return_value=219):
            self.assertTrue(coordinator.fresh)
        with patch.object(coordinator_module, "monotonic", return_value=220):
            self.assertFalse(coordinator.fresh)
            self.assertEqual(coordinator.freshness_reason, "expired")
        coordinator.async_set_update_error(RuntimeError("disconnected"))
        with patch.object(coordinator_module, "monotonic", return_value=110):
            self.assertFalse(coordinator.fresh)
            self.assertEqual(coordinator.freshness_reason, "last_read_failed")

    async def test_wall_clock_changes_do_not_expire_measurement(self):
        coordinator = self.make_coordinator()
        coordinator._measured_monotonic = 100
        with patch.object(coordinator_module, "monotonic", return_value=110), patch.object(coordinator_module.dt_util, "utcnow", return_value=datetime(2099, 1, 1, tzinfo=timezone.utc)):
            self.assertTrue(coordinator.fresh)
            self.assertEqual(coordinator.measurement_age_seconds, 10)
