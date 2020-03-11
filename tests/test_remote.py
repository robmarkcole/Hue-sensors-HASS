"""Tests for remote.py."""
import logging
from datetime import timedelta

import pytest

from custom_components.huesensor import DOMAIN
from custom_components.huesensor.data_manager import HueSensorData
from custom_components.huesensor.hue_api_response import (
    parse_hue_api_response,
    parse_rwl,
    parse_zgp,
    parse_z3_rotary,
)
from custom_components.huesensor.remote import async_setup_platform, HueRemote

from .conftest import (
    DEV_ID_REMOTE_1,
    DEV_ID_SENSOR_1,
    entity_test_added_to_hass,
    patch_async_track_time_interval,
)
from .sensor_samples import (
    MOCK_RWL,
    MOCK_ZGP,
    MOCK_Z3_ROTARY,
    PARSED_RWL,
    PARSED_ZGP,
    PARSED_Z3_ROTARY,
)


@pytest.mark.parametrize(
    "raw_response, sensor_key, parsed_response, parser_func",
    (
        (MOCK_ZGP, "ZGP_00:44:23:08", PARSED_ZGP, parse_zgp),
        (MOCK_RWL, "RWL_00:17:88:01:10:3e:3a:dc-02", PARSED_RWL, parse_rwl),
        (
            MOCK_Z3_ROTARY,
            "Z3-_ff:ff:00:0f:e7:fd:ba:b7-01-fc00",
            PARSED_Z3_ROTARY,
            parse_z3_rotary,
        ),
    ),
)
def test_parse_remote_raw_data(
    raw_response, sensor_key, parsed_response, parser_func, caplog
):
    """Test data parsers for known remotes and check behavior for unknown."""
    assert parser_func(raw_response) == parsed_response
    unknown_sensor_data = {"modelid": "new_one", "uniqueid": "ff:00:11:22"}
    assert parse_hue_api_response(
        [raw_response, unknown_sensor_data, raw_response]
    ) == {sensor_key: parsed_response}
    assert len(caplog.messages) == 0


async def test_platform_remote_setup(mock_hass, caplog):
    """Test platform setup for remotes."""
    with caplog.at_level(logging.DEBUG):
        with patch_async_track_time_interval():
            await async_setup_platform(
                mock_hass,
                {
                    "platform": "huesensor",
                    "scan_interval": timedelta(seconds=3),
                },
                lambda *x: logging.warning("Added remote entity: %s", x[0]),
            )

            assert DOMAIN in mock_hass.data
            data_manager = mock_hass.data[DOMAIN]
            assert isinstance(data_manager, HueSensorData)
            assert len(data_manager.registered_entities) == 1
            assert data_manager._scan_interval == timedelta(seconds=3)
            assert len(data_manager.data) == 1
            assert DEV_ID_REMOTE_1 in data_manager.data
            assert DEV_ID_SENSOR_1 not in data_manager.data

            assert len(data_manager.sensors) == 0
            assert len(data_manager.registered_entities) == 1
            remote = data_manager.registered_entities[DEV_ID_REMOTE_1]
            assert not remote.hass

            await entity_test_added_to_hass(data_manager, remote)
            # await remote.async_added_to_hass()
            assert len(data_manager.sensors) == 1
            assert DEV_ID_REMOTE_1 in data_manager.sensors

            assert isinstance(remote, HueRemote)
            assert remote.hass
            assert remote.force_update
            assert remote.state == "3_click"
            assert remote.icon == "mdi:remote"
            assert not remote.should_poll
            assert "last_updated" in remote.device_state_attributes
            assert remote.unique_id == DEV_ID_REMOTE_1

            await remote.async_will_remove_from_hass()
            assert len(data_manager.sensors) == 0
            assert len(data_manager.registered_entities) == 0
            assert not data_manager.available
