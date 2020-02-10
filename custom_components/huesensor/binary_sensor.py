"""
Binary sensor for Hue motion sensors.
"""
import asyncio
import async_timeout
import logging
import threading
from datetime import timedelta

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.components.binary_sensor import BinarySensorDevice
from homeassistant.helpers.event import async_track_time_interval

DEPENDENCIES = ["hue"]

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=0.1)
TYPE_GEOFENCE = "Geofence"

DEVICE_CLASSES = {"SML": "motion","PHD": "light"}

ATTRS = {
    "SML": [
        "light_level",
        "battery",
        "last_updated",
        "lx",
        "dark",
        "daylight",
        "temperature",
        "on",
        "reachable",
        "sensitivity",
        "threshold_dark",
        "threshold_offset"
    ],
    "PHD": [
        "on",
        "configured",
        "sunrise_offset",
        "sunset_offset",
        "name",
        "type",
        "modelid",
        "swversion",
        "daylight",
        "last_updated",
    ]

}


def parse_hue_api_response(bridgeid, sensors):
    """Take in the Hue API json response."""
    data_dict = {}  # The list of sensors, referenced by their hue_id.

    # Loop over all keys (1,2 etc) to identify sensors and get data.
    for sensor in sensors:
        modelid = sensor["modelid"][0:3]
        if modelid == "SML":
            _key = modelid + "_" + sensor["uniqueid"][:-5]
            if _key not in data_dict:
                data_dict[_key] = parse_sml(sensor)
            else:
                data_dict[_key].update(parse_sml(sensor))

        elif modelid == "PHD":
            _key = modelid + "_" + bridgeid
            if _key not in data_dict:
                data_dict[_key] = parse_phd(sensor)
            else:
                data_dict[_key].update(parse_phd(sensor))
    return data_dict


def parse_sml(response):
    """Parse the json for a SML Hue motion sensor and return the data."""
    if response["type"] == "ZLLLightLevel":
        lightlevel = response["state"]["lightlevel"]
        tholddark = response["config"]["tholddark"]
        tholdoffset = response["config"]["tholdoffset"]
        if lightlevel is not None:
            lx = round(float(10 ** ((lightlevel - 1) / 10000)), 2)
            dark = response["state"]["dark"]
            daylight = response["state"]["daylight"]
            data = {
                "light_level": lightlevel,
                "lx": lx,
                "dark": dark,
                "daylight": daylight,
                "threshold_dark": tholddark,
                "threshold_offset": tholdoffset
            }
        else:
            data = {
                "light_level": "No light level data",
                "lx": None,
                "dark": None,
                "daylight": None,
                "threshold_dark": None,
                "threshold_offset": None
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
            state = STATE_ON
        else:
            state = STATE_OFF

        data = {
            "model": "SML",
            "name": name,
            "state": state,
            "battery": response["config"]["battery"],
            "on": response["config"]["on"],
            "reachable": response["config"]["reachable"],
            "sensitivity": response["config"]["sensitivity"],
            "last_updated": response["state"]["lastupdated"].split("T"),
        }
    return data

def parse_phd(response):
    """Parse the json for a PHD Daylight sensor and return the data."""
    if response["type"] == "Daylight":
        daylight = response["state"]["daylight"]
        name_raw = response["name"]
        name = "Hue " + name_raw

        if daylight is True:
            state = STATE_ON
        else:
            state = STATE_OFF
        if daylight is not None:
            data = {
                "model": "PHD",
                "state": state,
                "on": response["config"]["on"],
                "configured": response["config"]["configured"],
                "sunrise_offset": response["config"]["sunriseoffset"],
                "sunset_offset": response["config"]["sunsetoffset"],
                "name": name,
                "type": response["type"],
                "modelid": response["modelid"],
                "swversion": response["swversion"],
                "daylight": daylight,
                "last_updated": response["state"]["lastupdated"].split("T")
            }
        else:
            data = {
                "model": "PHD",
                "state": "No Daylight data",
                "on": None,
                "configured": None,
                "sunrise_offset": None,
                "sunset_offset": None,
                "name": None,
                "type": None,
                "modelid": None,
                "swversion": None,
                "daylight": "No Daylight data",
                "last_updated": None
            }

    return data


def get_bridges(hass):
    from homeassistant.components import hue
    from homeassistant.components.hue.bridge import HueBridge

    return [
        entry
        for entry in hass.data[hue.DOMAIN].values()
        if isinstance(entry, HueBridge) and entry.api
    ]


async def update_api(api):
    import aiohue

    try:
        with async_timeout.timeout(10):
            await api.update()
    except (asyncio.TimeoutError, aiohue.AiohueException) as err:
        _LOGGER.debug("Failed to fetch sensors: %s", err)
        return False
    return True


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Initialise Hue Bridge connection."""
    data = HueSensorData(hass, async_add_entities)
    await data.async_update_info()
    async_track_time_interval(hass, data.async_update_info, SCAN_INTERVAL)


class HueSensorData(object):
    """Get the latest sensor data."""

    def __init__(self, hass, async_add_entities):
        """Initialize the data object."""
        self.hass = hass
        self.lock = threading.Lock()
        self.data = {}
        self.sensors = {}
        self.async_add_entities = async_add_entities

    async def update_bridge(self, bridge):
        available = await update_api(bridge.api.sensors)
        if not available:
            return

        data = parse_hue_api_response(
            bridge.api.id, (sensor.raw
            for sensor in bridge.api.sensors.values()
            if sensor.type != TYPE_GEOFENCE)
        )

        new_sensors = data.keys() - self.data.keys()
        updated_sensors = []
        for key, new in data.items():
            new["changed"] = True
            old = self.data.get(key)
            if not old or old == new:
                continue
            updated_sensors.append(key)
            if (
                old["last_updated"] == new["last_updated"]
                and old["state"] == new["state"]
            ):
                new["changed"] = False
        self.data.update(data)

        new_entities = {
            entity_id: HueSensor(entity_id, self) for entity_id in new_sensors
        }
        if new_entities:
            _LOGGER.debug("Created %s", ", ".join(new_entities.keys()))
            self.sensors.update(new_entities)
            self.async_add_entities(new_entities.values(), True)
        for entity_id in updated_sensors:
            self.sensors[entity_id].async_schedule_update_ha_state()

    async def async_update_info(self, now=None):
        """Get the bridge info."""
        locked = self.lock.acquire(False)
        if not locked:
            return
        try:
            bridges = get_bridges(self.hass)
            if not bridges:
                if now:
                    # periodic task
                    await asyncio.sleep(5)
                return
            await asyncio.wait(
                [self.update_bridge(bridge) for bridge in bridges], loop=self.hass.loop
            )
        finally:
            self.lock.release()


class HueSensor(BinarySensorDevice):
    """Class to hold Hue Sensor basic info."""

    def __init__(self, hue_id, data):
        """Initialize the sensor object."""
        self._hue_id = hue_id
        self._data = data.data  # data is in .data

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def name(self):
        """Return the name of the sensor."""
        data = self._data.get(self._hue_id)
        if data:
            return data["name"]

    @property
    def unique_id(self):
        """Return the ID of this Hue sensor."""
        return self._hue_id

    @property
    def is_on(self):
        """Return the state of the sensor."""
        data = self._data.get(self._hue_id)
        if data and data["model"] in ["SML","PHD"] and data["changed"]:
            return data["state"] == STATE_ON
        return False

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        data = self._data.get(self._hue_id)
        if data:
            device_class = DEVICE_CLASSES.get(data["model"])
            if device_class:
                return device_class

    @property
    def device_state_attributes(self):
        """Attributes."""
        data = self._data.get(self._hue_id)
        if data:
            return {key: data.get(key) for key in ATTRS.get(data["model"], [])}
