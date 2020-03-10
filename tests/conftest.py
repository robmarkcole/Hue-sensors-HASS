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

from .sensor_samples import MOCK_ZGP, MOCK_ZLLPresence

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


@pytest.fixture
def mock_hass():
    """Mock HA object for tests, including some sensors in hue integration."""
    # mocking raw sensors (aiohue level)
    rwl_sensor = MagicMock(spec=GenericSensor)
    rwl_sensor.raw = deepcopy(MOCK_ZGP)

    sml_sensor = MagicMock(spec=GenericSensor)
    sml_sensor.raw = deepcopy(MOCK_ZLLPresence)

    bridge = MagicMock(spec=Bridge)
    bridge.sensors = {"rwl_1": rwl_sensor, "sml_1": sml_sensor}

    # mocking HueBridge (homeassistant.components.hue level)
    coordinator = MagicMock(spec=DataUpdateCoordinator)
    coordinator.async_request_refresh = MockBridgeUpdater()

    sensor_manager = MagicMock(spec=SensorManager)
    sensor_manager.coordinator = coordinator

    hue_bridge = MagicMock(spec=HueBridge)
    hue_bridge.api = bridge
    hue_bridge.sensor_manager = sensor_manager

    # mocking homeassistant
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {HUE_DOMAIN: {0: hue_bridge}}
    hass.config = MagicMock()
    hass.states = MagicMock()

    return hass


def patch_async_track_time_interval():
    """Mock hass.async_track_time_interval for tests."""
    return patch(
        "custom_components.huesensor.data_manager.async_track_time_interval",
        autospec=True,
    )
