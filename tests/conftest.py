"""Pytest fixtures for huesensors tests."""
from copy import deepcopy
from unittest.mock import MagicMock, patch

from aiohue import Bridge
from aiohue.sensors import GenericSensor
from homeassistant.core import HomeAssistant
from homeassistant.components.hue import DOMAIN as HUE_DOMAIN, HueBridge
from homeassistant.components.hue.sensor_base import SensorManager
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import pytest

from .sensor_samples import (
    MOCK_ZGP,
    MOCK_ZLLPresence,
    MOCK_RWL,
    MOCK_Z3_ROTARY,
)

DEV_ID_REMOTE_1 = "ZGP_00:44:23:08"
DEV_ID_SENSOR_1 = "SML_00:17:88:01:02:00:af:28-02"


class MockBridgeUpdater:
    """
    Call counter for the hue data coordinator.

    Used to mock and count bridge updates done with
    `await bridge.sensor_manager.coordinator.async_request_refresh()`.
    """

    _counter: int = 0

    def __await__(self):
        """Dumb await."""
        yield

    def __call__(self, *args, **kwargs):
        """Call just returns self, increasing counter."""
        self._counter += 1
        return self

    @property
    def call_count(self) -> int:
        """Return call counter."""
        return self._counter


def _mock_hue_sensor(raw_data: dict):
    hue_sensor = MagicMock(spec=GenericSensor)
    hue_sensor.raw = deepcopy(raw_data)
    return hue_sensor


def _mock_hue_bridges(bridges):
    # mocking HueBridge at homeassistant.components.hue level
    hue_bridges = {}
    for i, bridge in enumerate(bridges):
        coordinator = MagicMock(spec=DataUpdateCoordinator)
        coordinator.async_request_refresh = MockBridgeUpdater()

        sensor_manager = MagicMock(spec=SensorManager)
        sensor_manager.coordinator = coordinator

        hue_bridge = MagicMock(spec=HueBridge)
        hue_bridge.api = bridge
        hue_bridge.sensor_manager = sensor_manager

        hue_bridges[i] = hue_bridge

    return hue_bridges


@pytest.fixture
def mock_hass():
    """Mock HA object for tests, including some sensors in hue integration."""
    bridge = MagicMock(spec=Bridge)
    bridge.sensors = {
        "rwl_1": _mock_hue_sensor(MOCK_ZGP),
        "sml_1": _mock_hue_sensor(MOCK_ZLLPresence),
    }

    # mocking homeassistant
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {HUE_DOMAIN: _mock_hue_bridges([bridge])}

    return hass


@pytest.fixture
def mock_hass_double_bridge():
    """Mock HA object for tests, with some sensors in 2 bridges."""
    bridge1 = MagicMock(spec=Bridge)
    bridge1.sensors = {
        "rwl_1": _mock_hue_sensor(MOCK_ZGP),
        "z3_2": _mock_hue_sensor(MOCK_Z3_ROTARY),
    }

    bridge2 = MagicMock(spec=Bridge)
    bridge2.sensors = {
        "rwl_2": _mock_hue_sensor(MOCK_RWL),
        "sml_1": _mock_hue_sensor(MOCK_ZLLPresence),
    }

    # mocking homeassistant
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {HUE_DOMAIN: _mock_hue_bridges([bridge1, bridge2])}
    hass.config = MagicMock()
    hass.states = MagicMock()

    return hass


def patch_async_track_time_interval():
    """Mock hass.async_track_time_interval for tests."""
    return patch(
        "custom_components.huesensor.data_manager.async_track_time_interval",
        autospec=True,
    )
