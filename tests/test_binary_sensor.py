"""Tests for binary_sensor.py."""
import logging
from datetime import timedelta

import pytest

from custom_components.huesensor import DOMAIN
from custom_components.huesensor.binary_sensor import (
    async_setup_platform,
    HueBinarySensor,
)
from custom_components.huesensor.data_manager import HueSensorData
from custom_components.huesensor.hue_api_response import (
    parse_hue_api_response,
    parse_sml,
)

from .conftest import (
    DEV_ID_REMOTE_1,
    DEV_ID_SENSOR_1,
    patch_async_track_time_interval,
)
from .sensor_samples import (
    MOCK_ZLLLightlevel,
    MOCK_ZLLPresence,
    MOCK_ZLLTemperature,
    PARSED_ZLLLightlevel,
    PARSED_ZLLPresence,
    PARSED_ZLLTemperature,
)


@pytest.mark.parametrize(
    "raw_response, sensor_key, parsed_response, parser_func",
    (
        (
            MOCK_ZLLPresence,
            "SML_00:17:88:01:02:00:af:28-02",
            PARSED_ZLLPresence,
            parse_sml,
        ),
        (
            MOCK_ZLLLightlevel,
            "SML_00:17:88:01:02:00:af:28-02",
            PARSED_ZLLLightlevel,
            parse_sml,
        ),
        (
            MOCK_ZLLTemperature,
            "SML_00:17:88:01:02:00:af:28-02",
            PARSED_ZLLTemperature,
            parse_sml,
        ),
    ),
)
def test_parse_sensor_raw_data(
    raw_response, sensor_key, parsed_response, parser_func, caplog
):
    """Test data parsers for known sensors."""
    assert parser_func(raw_response) == parsed_response
    with caplog.at_level(level=logging.WARNING):
        assert parse_hue_api_response([raw_response]) == {
            sensor_key: parsed_response
        }
        assert len(caplog.messages) == 0


async def test_platform_binary_sensor_setup(mock_hass, caplog):
    """Test platform setup for binary sensors."""
    with caplog.at_level(logging.DEBUG):
        with patch_async_track_time_interval():
            await async_setup_platform(
                mock_hass,
                {
                    "platform": "huesensor",
                    "scan_interval": timedelta(seconds=2),
                },
                lambda *x: logging.warning("Added sensor entity: %s", x[0]),
            )
            assert DOMAIN in mock_hass.data
            data_manager = mock_hass.data[DOMAIN]
            assert isinstance(data_manager, HueSensorData)
            assert data_manager._scan_interval == timedelta(seconds=2)
            assert len(data_manager.data) == 2
            assert DEV_ID_REMOTE_1 in data_manager.data
            assert DEV_ID_SENSOR_1 in data_manager.data

            assert len(data_manager.data) == 2
            assert len(data_manager.sensors) == 1

            assert DEV_ID_SENSOR_1 in data_manager.sensors
            bin_sensor = data_manager.sensors[DEV_ID_SENSOR_1]
            assert isinstance(bin_sensor, HueBinarySensor)
            assert bin_sensor.device_class == "motion"
            assert not bin_sensor.is_on
            assert bin_sensor.state == "off"
            assert not bin_sensor.should_poll
            assert "light_level" in bin_sensor.device_state_attributes
            assert bin_sensor.unique_id == DEV_ID_SENSOR_1

            await bin_sensor.async_added_to_hass()
            await bin_sensor.async_will_remove_from_hass()
