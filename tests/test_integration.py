"""The huesensors tests."""
import logging
from datetime import timedelta

from homeassistant.components.hue import DOMAIN as HUE_DOMAIN

from custom_components.huesensor import DOMAIN
from custom_components.huesensor.data_manager import HueSensorData
from custom_components.huesensor.binary_sensor import (
    async_setup_platform as async_setup_binary_sensor,
)

from .conftest import (
    add_sensor_data_to_bridge,
    DEV_ID_SENSOR_1,
    entity_test_added_to_hass,
    patch_async_track_time_interval,
)


async def test_integration(mock_hass_2_bridges, caplog):
    """Test setup with yaml config for remotes and binary sensors."""
    mock_hass = mock_hass_2_bridges
    entity_counter = []
    config_bs = {"platform": DOMAIN, "scan_interval": timedelta(seconds=2)}

    data_coord_b1 = mock_hass.data[HUE_DOMAIN][0].sensor_manager.coordinator
    data_coord_b2 = mock_hass.data[HUE_DOMAIN][1].sensor_manager.coordinator

    def _add_entity_counter(*_args):
        entity_counter.append(1)

    with caplog.at_level(logging.DEBUG):
        with patch_async_track_time_interval():

            # add to HA
            await entity_test_added_to_hass(data_manager, bin_sensor)
            assert len(data_manager.sensors) == 4
            assert len(caplog.messages) == 7

            # # Change the state on bridge and call update
            # hue_bridge = mock_hass.data[HUE_DOMAIN][1].api
            # r1_data_st = hue_bridge.sensors["ZGPSwitch_1_0"].raw["state"]
            # r1_data_st["buttonevent"] = 16
            # r1_data_st["lastupdated"] = "2019-06-22T14:43:55"
            # hue_bridge.sensors["ZGPSwitch_1_0"].raw["state"] = r1_data_st

            # assert data_coord_b1.async_request_refresh.call_count == 2
            # assert data_coord_b2.async_request_refresh.call_count == 2

            # await data_manager.async_update_from_bridges()
            # assert remote.state == "2_click"
            # assert len(caplog.messages) == 8

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


async def test_add_new_device(mock_hass, caplog):
    """Test behavior when a new device is discovered."""
    entity_counter = []
    config_remote = {"platform": DOMAIN, "scan_interval": timedelta(seconds=3)}

    data_coord_b1 = mock_hass.data[HUE_DOMAIN][0].sensor_manager.coordinator

    def _add_entity_counter(*_args):
        entity_counter.append(1)

    with caplog.at_level(logging.DEBUG):
        with patch_async_track_time_interval():
            # setup remotes
            await async_setup_remote(mock_hass, config_remote, _add_entity_counter)
            assert sum(entity_counter) == 1

            assert DOMAIN in mock_hass.data
            data_manager = mock_hass.data[DOMAIN]
            assert isinstance(data_manager, HueSensorData)
            assert len(data_manager.data) == 1
            assert len(data_manager.registered_entities) == 1

            # Check bridge updates
            assert data_coord_b1.async_request_refresh.call_count == 1
            assert len(data_manager.sensors) == 0

            # add to HA
            for device in data_manager.registered_entities.values():
                await entity_test_added_to_hass(data_manager, device)
            assert len(data_manager.sensors) == 1
            assert len(caplog.messages) == 2

            # Add a new device to bridge data and call update
            new_remote_id = f"{MOCK_RWL['type']}_0_0"
            hue_bridge = mock_hass.data[HUE_DOMAIN][0].api
            add_sensor_data_to_bridge(hue_bridge, new_remote_id, MOCK_RWL)
            await data_manager.async_update_from_bridges()

            # Check bridge updates
            assert data_coord_b1.async_request_refresh.call_count == 2
            assert len(data_manager.registered_entities) == 2
            assert len(data_manager.sensors) == 1
            assert len(caplog.messages) == 3
            assert sum(entity_counter) == 2
            assert DEV_ID_REMOTE_2 in data_manager.registered_entities
            new_remote = data_manager.registered_entities[DEV_ID_REMOTE_2]
            assert new_remote.state == "4_click_up"

            # new device changes state
            remote_data_st = hue_bridge.sensors[new_remote_id].raw["state"]
            remote_data_st["buttonevent"] = 3002
            remote_data_st["lastupdated"] = "2019-12-28T21:58:03"
            hue_bridge.sensors[new_remote_id].raw["state"] = remote_data_st
            assert new_remote.state == "4_click_up"

            # new update comes, but new remote is not added yet
            await data_manager.async_update_from_bridges()
            assert data_coord_b1.async_request_refresh.call_count == 3
            assert sum(entity_counter) == 2
            assert len(data_manager.sensors) == 1
            assert new_remote.state == "3_click_up"
            assert len(caplog.messages) == 4

            # now it is
            await entity_test_added_to_hass(data_manager, new_remote)
            assert len(data_manager.sensors) == 2
            assert len(caplog.messages) == 5

            await data_manager.async_update_from_bridges()
            assert data_coord_b1.async_request_refresh.call_count == 4
            assert len(data_manager.sensors) == 2

            # Remove entities from hass
            for i, device in enumerate(data_manager.sensors.copy().values()):
                await device.async_will_remove_from_hass()
            assert len(data_manager.sensors) == 0
            assert len(data_manager.registered_entities) == 0
            assert data_coord_b1.async_request_refresh.call_count == 4
            assert len(caplog.messages) == 8
