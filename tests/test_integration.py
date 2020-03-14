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

_NEW_ZLLPresence = {
    "state": {"presence": False, "lastupdated": "2020-02-28T07:28:08"},
    "swupdate": {"state": "noupdates", "lastinstall": "2019-05-06T13:14:45"},
    "config": {
        "on": True,
        "battery": 100,
        "reachable": True,
        "alert": "lselect",
        "sensitivity": 1,
        "sensitivitymax": 2,
        "ledindication": False,
        "usertest": False,
        "pending": [],
    },
    "name": "Kitchen sensor",
    "type": "ZLLPresence",
    "modelid": "SML001",
    "manufacturername": "Philips",
    "productname": "Hue motion sensor",
    "swversion": "6.1.1.27575",
    "uniqueid": "00:aa:bb:cc:dd:ee:ff:28-01-0406",
    "capabilities": {"certified": True, "primary": True},
}
DEV_ID_NEW_SENSOR = "SML_00:aa:bb:cc:dd:ee:ff:28-01"


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
            # setup binary sensor
            await async_setup_binary_sensor(
                mock_hass, config_bs, _add_entity_counter
            )
            assert sum(entity_counter) == 1

            assert DOMAIN in mock_hass.data
            data_manager = mock_hass.data[DOMAIN]
            assert isinstance(data_manager, HueSensorData)
            assert len(data_manager.data) == 1
            assert len(data_manager.registered_entities) == 1

            # Check bridge updates
            assert data_coord_b1.async_request_refresh.call_count == 1
            assert data_coord_b2.async_request_refresh.call_count == 1

            assert len(data_manager.sensors) == 0
            assert DEV_ID_SENSOR_1 in data_manager.registered_entities
            bin_sensor = data_manager.registered_entities[DEV_ID_SENSOR_1]
            assert bin_sensor.state == "off"
            assert bin_sensor.device_state_attributes["temperature"] == 17.44
            assert bin_sensor.device_state_attributes["light_level"] == 0
            assert bin_sensor.device_state_attributes["battery"] == 58
            assert bin_sensor.device_state_attributes["on"]

            # add to HA
            for device in data_manager.registered_entities.values():
                await entity_test_added_to_hass(data_manager, device)
            assert len(data_manager.sensors) == 1
            assert len(caplog.messages) == 2

            # Change the presence state on bridge and call update
            hue_bridge = mock_hass.data[HUE_DOMAIN][0].api
            bs_data_st = hue_bridge.sensors["ZLLPresence_0_0"].raw["state"]
            bs_data_st["presence"] = True
            bs_data_st["lastupdated"] = "2020-02-06T07:29:08"
            hue_bridge.sensors["ZLLPresence_0_0"].raw["state"] = bs_data_st

            assert data_coord_b1.async_request_refresh.call_count == 1
            assert data_coord_b2.async_request_refresh.call_count == 1

            await data_manager.async_update_from_bridges()
            assert bin_sensor.state == "on"
            assert data_coord_b1.async_request_refresh.call_count == 2
            assert data_coord_b2.async_request_refresh.call_count == 2
            assert len(caplog.messages) == 3

            # Change the temperature state on bridge and call update
            temp_data_st = hue_bridge.sensors["ZLLTemperature_0_2"].raw[
                "state"
            ]
            temp_data_st["temperature"] = 1845
            hue_bridge.sensors["ZLLTemperature_0_2"].raw[
                "state"
            ] = temp_data_st
            await data_manager.async_update_from_bridges()
            assert bin_sensor.device_state_attributes["temperature"] == 18.45
            assert data_coord_b1.async_request_refresh.call_count == 3
            assert data_coord_b2.async_request_refresh.call_count == 3

            # Mimic the strange SML logic around the "changed" attribute
            # that sets state to off *if* state & lastupdated don't change
            # but any other thing does (like the temperature)
            assert bin_sensor.state == "off"
            assert len(caplog.messages) == 3

            # Change the lastupdated and check again
            bs_data_st["lastupdated"] = "2020-02-06T07:29:09"
            await data_manager.async_update_from_bridges()
            assert bin_sensor.device_state_attributes["temperature"] == 18.45
            assert data_coord_b1.async_request_refresh.call_count == 4
            assert data_coord_b2.async_request_refresh.call_count == 4
            assert bin_sensor.state == "on"
            assert len(caplog.messages) == 4

            # Add a new device to 2nd bridge data and call update
            new_id = "ZLLPresence_1_0"
            hue_bridge_2 = mock_hass.data[HUE_DOMAIN][1].api
            add_sensor_data_to_bridge(hue_bridge_2, new_id, _NEW_ZLLPresence)
            await data_manager.async_update_from_bridges()
            assert data_coord_b1.async_request_refresh.call_count == 5
            assert data_coord_b2.async_request_refresh.call_count == 5
            assert len(data_manager.registered_entities) == 2
            assert len(data_manager.sensors) == 1
            assert len(caplog.messages) == 5
            assert sum(entity_counter) == 2
            assert DEV_ID_NEW_SENSOR in data_manager.registered_entities
            new_binsensor = data_manager.registered_entities[DEV_ID_NEW_SENSOR]
            assert new_binsensor.state == "off"

            # new device changes state
            new_sensor_st = hue_bridge_2.sensors[new_id].raw["state"]
            new_sensor_st["presence"] = True
            new_sensor_st["lastupdated"] = "2020-02-28T07:28:09"
            hue_bridge_2.sensors[new_id].raw["state"] = new_sensor_st

            # new update comes, but new sensor is not added yet
            await data_manager.async_update_from_bridges()
            assert data_coord_b1.async_request_refresh.call_count == 6
            assert data_coord_b2.async_request_refresh.call_count == 6
            assert len(data_manager.sensors) == 1
            assert len(caplog.messages) == 6
            assert new_binsensor.state == "on"

            # now it is added to HA
            await entity_test_added_to_hass(data_manager, new_binsensor)
            assert len(data_manager.sensors) == 2
            assert len(caplog.messages) == 7

            # Test scheduler: extra calls do nothing
            await data_manager.async_start_scheduler()
            # Test scheduler: forced re-schedule cancels current listener
            data_manager.available = False
            await data_manager.async_start_scheduler()
            assert len(caplog.messages) == 8

            # Remove entities from hass
            for i, device in enumerate(data_manager.sensors.copy().values()):
                await device.async_will_remove_from_hass()
            assert i == 1

            # Test scheduler: extra stops do nothing
            await data_manager.async_stop_scheduler()

            assert data_coord_b1.async_request_refresh.call_count == 6
            assert data_coord_b2.async_request_refresh.call_count == 6

        assert len(caplog.messages) == 12
