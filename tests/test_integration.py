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


async def test_integration(mock_hass_2_bridges, caplog):
    """Test setup with yaml config for remotes and binary sensors."""
    mock_hass = mock_hass_2_bridges
    entity_counter = []
    config_remote = {"platform": DOMAIN, "scan_interval": timedelta(seconds=3)}
    config_bs = {"platform": DOMAIN, "scan_interval": timedelta(seconds=2)}

    data_coord_b1 = mock_hass.data[HUE_DOMAIN][0].sensor_manager.coordinator
    data_coord_b2 = mock_hass.data[HUE_DOMAIN][1].sensor_manager.coordinator

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
            assert len(data_manager.data) == 4

            # Check bridge updates
            assert data_coord_b1.async_request_refresh.call_count == 1
            assert data_coord_b2.async_request_refresh.call_count == 1

            assert len(data_manager.sensors) == 3
            assert DEV_ID_REMOTE_1 in data_manager.sensors
            remote = data_manager.sensors[DEV_ID_REMOTE_1]
            assert remote.state == "3_click"
            assert remote.icon == "mdi:remote"

            # add to HA
            for i, device in enumerate(data_manager.sensors.values()):
                await device.async_added_to_hass()
                device.hass = mock_hass
                device.entity_id = f"remote.test_{i + 1}"

            assert len(caplog.messages) == 4

            await async_setup_binary_sensor(
                mock_hass, config_bs, _add_entity_counter
            )
            assert sum(entity_counter) == 2
            assert len(data_manager.sensors) == 4

            # Check bridge updates
            assert data_coord_b1.async_request_refresh.call_count == 2
            assert data_coord_b2.async_request_refresh.call_count == 2
            assert len(caplog.messages) == 6
            assert DEV_ID_SENSOR_1 in data_manager.sensors
            bin_sensor = data_manager.sensors[DEV_ID_SENSOR_1]

            # add to HA
            await bin_sensor.async_added_to_hass()
            bin_sensor.hass = mock_hass
            bin_sensor.entity_id = "binary_sensor.test1"
            assert len(caplog.messages) == 7

            # Change the state on bridge and call update
            hue_bridge = mock_hass.data[HUE_DOMAIN][1]
            r1_data_st = hue_bridge.api.sensors["ZGPSwitch_1_0"].raw["state"]
            r1_data_st["buttonevent"] = 16
            r1_data_st["lastupdated"] = "2019-06-22T14:43:55"
            hue_bridge.api.sensors["ZGPSwitch_1_0"].raw["state"] = r1_data_st

            assert data_coord_b1.async_request_refresh.call_count == 2
            assert data_coord_b2.async_request_refresh.call_count == 2

            await data_manager.async_update_from_bridges()
            assert remote.state == "2_click"
            assert len(caplog.messages) == 8

            assert data_coord_b1.async_request_refresh.call_count == 3
            assert data_coord_b2.async_request_refresh.call_count == 3

            # Test scheduler: extra calls do nothing
            await data_manager.async_start_scheduler()
            # Test scheduler: forced re-schedule cancels current listener
            data_manager.available = False
            await data_manager.async_start_scheduler()
            assert len(caplog.messages) == 9

            # Remove entities from hass
            for i, device in enumerate(data_manager.sensors.copy().values()):
                await device.async_will_remove_from_hass()
            assert i == 3

            assert len(caplog.messages) == 14

            # Test scheduler: extra stops do nothing
            await data_manager.async_stop_scheduler()

            assert data_coord_b1.async_request_refresh.call_count == 3
            assert data_coord_b2.async_request_refresh.call_count == 3

        assert len(caplog.messages) == 15
