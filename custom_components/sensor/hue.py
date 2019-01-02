"""
Sensor for checking the status of Hue sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.hue/
"""
import asyncio
import async_timeout
import logging
from datetime import timedelta

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from homeassistant.components import hue
from homeassistant.helpers.event import async_track_time_interval

from ..device_tracker.hue import TYPE_GEOFENCE

DEPENDENCIES = ["hue"]

__version__ = "1.0.1"

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=0.1)


def parse_hue_api_response(sensors):
    """Take in the Hue API json response."""
    data_dict = {}  # The list of sensors, referenced by their hue_id.

    # Loop over all keys (1,2 etc) to identify sensors and get data.
    for sensor in sensors:
        modelid = sensor["modelid"][0:3]
        if modelid in ["RWL", "SML", "ZGP"]:
            _key = modelid + "_" + sensor["uniqueid"][:-5]
            if modelid == "RWL":
                data_dict[_key] = parse_rwl(sensor)
            elif modelid == "ZGP":
                data_dict[_key] = parse_zgp(sensor)
            elif modelid == "SML":
                if _key not in data_dict:
                    data_dict[_key] = parse_sml(sensor)
                else:
                    data_dict[_key].update(parse_sml(sensor))

    return data_dict


def parse_sml(response):
    """Parse the json for a SML Hue motion sensor and return the data."""
    if response["type"] == "ZLLLightLevel":
        lightlevel = response["state"]["lightlevel"]
        if lightlevel is not None:
            lx = round(float(10 ** ((lightlevel - 1) / 10000)), 2)
            dark = response["state"]["dark"]
            daylight = response["state"]["daylight"]
            data = {
                "light_level": lightlevel,
                "lx": lx,
                "dark": dark,
                "daylight": daylight,
            }
        else:
            data = {
                "light_level": "No light level data",
                "lx": None,
                "dark": None,
                "daylight": None,
            }

    elif response["type"] == "ZLLTemperature":
        if response["state"]["temperature"] is not None:
            data = {"temperature": response["state"]["temperature"] / 100.0}
        else:
            data = {"temperature": "No temperature data"}

    elif response["type"] == "ZLLPresence":
        name_raw = response["name"]
        arr = name_raw.split()
        arr.insert(-1, "motion")
        name = " ".join(arr)
        hue_state = response["state"]["presence"]
        if hue_state is True:
            state = "on"
        else:
            state = "off"

        data = {
            "model": "SML",
            "name": name,
            "state": state,
            "battery": response["config"]["battery"],
            "on": response["config"]["on"],
            "reachable": response["config"]["reachable"],
            "last_updated": response["state"]["lastupdated"].split("T"),
        }
    return data


def parse_zgp(response):
    """Parse the json response for a ZGPSWITCH Hue Tap."""
    TAP_BUTTONS = {34: "1_click", 16: "2_click", 17: "3_click", 18: "4_click"}
    press = response["state"]["buttonevent"]
    if press is None:
        button = "No data"
    else:
        button = TAP_BUTTONS[press]

    data = {
        "model": "ZGP",
        "name": response["name"],
        "state": button,
        "last_updated": response["state"]["lastupdated"].split("T"),
    }
    return data


def parse_rwl(response):
    """Parse the json response for a RWL Hue remote."""

    """
        I know it should be _released not _up
        but _hold_up is too good to miss isn't it
    """
    responsecodes = {"0": "_click", "1": "_hold", "2": "_click_up", "3": "_hold_up"}

    button = ""
    if response["state"]["buttonevent"]:
        press = str(response["state"]["buttonevent"])
        button = str(press)[0] + responsecodes[press[-1]]

    data = {
        "model": "RWL",
        "name": response["name"],
        "state": button,
        "battery": response["config"]["battery"],
        "on": response["config"]["on"],
        "reachable": response["config"]["reachable"],
        "last_updated": response["state"]["lastupdated"].split("T"),
    }
    return data


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Hue sensors."""
    data = HueSensorData(hass, async_add_entities)
    await data.async_update_info()
    async_track_time_interval(hass, data.async_update_info, SCAN_INTERVAL)


class HueSensorData(object):
    """Get the latest sensor data."""

    def __init__(self, hass, async_add_entities):
        """Initialize the data object."""
        self.hass = hass
        self.data = {}
        self.async_add_entities = async_add_entities

    async def async_update_info(self, now=None):
        """Get the bridge info."""
        apis = []

        for entry in self.hass.data[hue.DOMAIN].values():
            try:
                if entry.api is not None:
                    apis.append(entry.api)
            except:
                pass
        if not apis:
            return
        with async_timeout.timeout(10):
            await asyncio.wait([api.sensors.update() for api in apis])
        raw_sensors = (
            sensor.raw
            for api in apis
            for sensor in api.sensors.values()
            if sensor.type != TYPE_GEOFENCE
        )
        data = parse_hue_api_response(raw_sensors)
        _LOGGER.debug("hue_api_response %s", data)
        new_entities = data.keys() - self.data.keys()
        self.data = data
        self.async_add_entities(HueSensor(key, self) for key in new_entities)


class HueSensor(Entity):
    """Class to hold Hue Sensor basic info."""

    ICON = "mdi:run-fast"

    def __init__(self, hue_id, data):
        """Initialize the sensor object."""
        self._hue_id = hue_id
        self._data = data  # data is in .data
        self._icon = None
        self._name = self._data.data[self._hue_id]["name"]
        self._model = self._data.data[self._hue_id]["model"]
        self._state = self._data.data[self._hue_id]["state"]
        self._attributes = {}

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def available(self):
        """Return if the sensor is available."""
        return self._hue_id in self._data.data

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def device_state_attributes(self):
        """Attributes."""
        return self._attributes

    def update(self):
        """Update the sensor."""
        data = self._data.data.get(self._hue_id)
        if not data:
            return
        self._state = data["state"]
        try:
            if self._model == "SML":
                self._icon = "mdi:run-fast"
                self._attributes["light_level"] = data["light_level"]
                self._attributes["battery"] = data["battery"]
                self._attributes["last_updated"] = data["last_updated"]
                self._attributes["lx"] = data["lx"]
                self._attributes["dark"] = data["dark"]
                self._attributes["daylight"] = data["daylight"]
                self._attributes["temperature"] = data["temperature"]
                self._attributes["on"] = data["on"]
                self._attributes["reachable"] = data["reachable"]
            elif self._model == "RWL":
                self._icon = "mdi:remote"
                self._attributes["last_updated"] = data["last_updated"]
                self._attributes["battery"] = data["battery"]
                self._attributes["on"] = data["on"]
                self._attributes["reachable"] = data["reachable"]
            elif self._model == "ZGP":
                self._icon = "mdi:remote"
                self._attributes["last_updated"] = data["last_updated"]
        except:
            _LOGGER.exception("Error updating Hue sensors")
