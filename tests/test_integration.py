"""The huesensors tests."""
import logging
from datetime import timedelta

from homeassistant.components.hue import DOMAIN as HUE_DOMAIN

from custom_components.huesensor import DOMAIN
from custom_components.huesensor.data_manager import HueSensorData
from custom_components.huesensor.remote import (
    async_setup_platform as async_setup_remote,
)
from custom_components.huesensor.binary_sensor import (
    async_setup_platform as async_setup_binary_sensor,
)

from .conftest import (
    DEV_ID_REMOTE_1,
    DEV_ID_SENSOR_1,
    patch_async_track_time_interval,
)


async def test_integration(mock_hass, caplog):
    """Test setup with yaml config for remotes and binary sensors."""
    entity_counter = []
    config_remote = {"platform": DOMAIN, "scan_interval": timedelta(seconds=3)}
    config_bs = {"platform": DOMAIN, "scan_interval": timedelta(seconds=2)}

    def _add_entity_counter(*_args):
        entity_counter.append(1)

    with caplog.at_level(logging.DEBUG):
        with patch_async_track_time_interval():
            # setup remotes
            await async_setup_remote(
                mock_hass, config_remote, _add_entity_counter
            )
            assert sum(entity_counter) == 1

            assert DOMAIN in mock_hass.data
            data_manager = mock_hass.data[DOMAIN]
            assert isinstance(data_manager, HueSensorData)
            assert len(data_manager.data) == 2

            # Check bridge updates
            assert (
                mock_hass.data[HUE_DOMAIN][
                    0
                ].sensor_manager.coordinator.async_request_refresh.call_count
                == 1
            )

            assert len(data_manager.sensors) == 1
            assert DEV_ID_REMOTE_1 in data_manager.sensors
            remote = data_manager.sensors[DEV_ID_REMOTE_1]
            assert remote.state == "3_click"
            assert remote.icon == "mdi:remote"

            # add to HA
            await remote.async_added_to_hass()
            remote.hass = mock_hass
            remote.entity_id = "remote.test1"
            assert len(caplog.messages) == 2

            await async_setup_binary_sensor(
                mock_hass, config_bs, _add_entity_counter
            )
            assert sum(entity_counter) == 2
            assert len(data_manager.sensors) == 2

            # Check bridge updates
            assert (
                mock_hass.data[HUE_DOMAIN][
                    0
                ].sensor_manager.coordinator.async_request_refresh.call_count
                == 2
            )
            assert len(caplog.messages) == 4
            assert DEV_ID_SENSOR_1 in data_manager.sensors
            bin_sensor = data_manager.sensors[DEV_ID_SENSOR_1]

            # add to HA
            await bin_sensor.async_added_to_hass()
            bin_sensor.hass = mock_hass
            bin_sensor.entity_id = "binary_sensor.test1"
            assert len(caplog.messages) == 5

            # Change the state on bridge and call update
            hue_bridge = mock_hass.data[HUE_DOMAIN][0]
            r1_data_st = hue_bridge.api.sensors["rwl_1"].raw["state"]
            r1_data_st["buttonevent"] = 16
            r1_data_st["lastupdated"] = "2019-06-22T14:43:55"
            hue_bridge.api.sensors["rwl_1"].raw["state"] = r1_data_st

            await data_manager.async_update_from_bridges()
            assert remote.state == "2_click"
            assert len(caplog.messages) == 6

            # Test scheduler: extra calls do nothing
            await data_manager.async_start_scheduler()
            # Test scheduler: forced re-schedule cancels current listener
            data_manager.available = False
            await data_manager.async_start_scheduler()
            assert len(caplog.messages) == 7

            # Remove entities from hass
            await bin_sensor.async_will_remove_from_hass()
            await remote.async_will_remove_from_hass()
            assert len(caplog.messages) == 10

            # Test scheduler: extra stops do nothing
            await data_manager.async_stop_scheduler()

        assert len(caplog.messages) == 11
