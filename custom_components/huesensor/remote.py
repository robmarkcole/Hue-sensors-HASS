"""
Hue remotes.
"""
import asyncio
import async_timeout
import logging
import threading
from datetime import timedelta
import voluptuous as vol

from homeassistant.components.remote import (
    PLATFORM_SCHEMA,
    RemoteDevice,
)
from homeassistant.core import callback
from homeassistant.helpers.entity import (
    Entity,
    ToggleEntity,
)
from homeassistant.const import STATE_OFF

from homeassistant.helpers.event import async_track_time_interval

DEPENDENCIES = ["hue"]


_LOGGER = logging.getLogger(__name__)

DEFAULT_SCAN_INTERVAL = timedelta(seconds=0.1)
TYPE_GEOFENCE = "Geofence"
HASS_BUTTON_EVENT = "huesensor.button_event"
ICONS = {
    "RWL": "mdi:remote",
    "ROM": "mdi:remote",
    "ZGP": "mdi:remote",
    "FOH": "mdi:light-switch",
    "Z3-": "mdi:light-switch",
}
ATTRS = {
    "RWL": ["last_updated", "last_button_event", "battery", "on", "reachable"],
    "ROM": ["last_updated", "last_button_event", "battery", "on", "reachable"],
    "ZGP": ["last_updated", "last_button_event"],
    "FOH": ["last_updated", "last_button_event"],
    "Z3-": [
        "last_updated",
        "last_button_event",
        "battery",
        "on",
        "reachable",
        "dial_state",
        "dial_position",
        "software_update",
    ],
}


def parse_hue_api_response(sensors):
    """Take in the Hue API json response."""
    data_dict = {}  # The list of sensors, referenced by their hue_id.

    # Loop over all keys (1,2 etc) to identify sensors and get data.
    for sensor in sensors:
        modelid = sensor["modelid"][0:3]
        if modelid in ["RWL", "ROM"]:
            _key = modelid + "_" + sensor["uniqueid"][:-5]
            if modelid == "RWL" or modelid == "ROM":
                data_dict[_key] = parse_rwl(sensor)

        elif modelid in ["FOH", "ZGP"]:  # New Model ID
            # needed for uniqueness
            _key = modelid + "_" + sensor["uniqueid"][-14:-3]
            if modelid == "FOH":
                data_dict[_key] = parse_foh(sensor)
            elif modelid == "ZGP":
                data_dict[_key] = parse_zgp(sensor)

        elif (
            modelid == "Z3-"
        ):  # Newest Model ID / Lutron Aurora / Hue Bridge treats it as two sensors, I wanted them combined
            if sensor["type"] == "ZLLRelativeRotary":  # Rotary Dial
                _key = (
                    modelid + "_" + sensor["uniqueid"][:-5]
                )  # Rotary key is substring of button
                key_value = parse_z3_rotary(sensor)
            else:  # sensor["type"] == "ZLLSwitch"
                _key = modelid + "_" + sensor["uniqueid"]
                key_value = parse_z3_switch(sensor)

            # Combine parsed data
            if _key in data_dict:
                data_dict[_key].update(key_value)
            else:
                data_dict[_key] = key_value

    return data_dict


def parse_zgp(response):
    """Parse the json response for a ZGPSWITCH Hue Tap."""
    TAP_BUTTONS = {34: "1_click", 16: "2_click", 17: "3_click", 18: "4_click"}
    press = response["state"]["buttonevent"]
    if press is None or press not in TAP_BUTTONS:
        button = "No data"
    else:
        button = TAP_BUTTONS[press]

    data = {
        "model": "ZGP",
        "name": response["name"],
        "state": button,
        "last_button_event": button,
        "last_updated": response["state"]["lastupdated"].split("T"),
    }
    return data


def parse_rwl(response):
    """Parse the json response for a RWL Hue remote."""

    """
        I know it should be _released not _up
        but _hold_up is too good to miss isn't it
    """
    responsecodes = {"0": "_click", "1": "_hold",
                     "2": "_click_up", "3": "_hold_up"}

    button = None
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
        "last_button_event": button,
        "last_updated": response["state"]["lastupdated"].split("T"),
    }
    return data


def parse_foh(response):
    """Parse the JSON response for a FOHSWITCH (type still = ZGPSwitch)"""
    FOH_BUTTONS = {
        16: "left_upper_press",
        20: "left_upper_release",
        17: "left_lower_press",
        21: "left_lower_release",
        18: "right_lower_press",
        22: "right_lower_release",
        19: "right_upper_press",
        23: "right_upper_release",
        100: "double_upper_press",
        101: "double_upper_release",
        98: "double_lower_press",
        99: "double_lower_release",
    }

    press = response["state"]["buttonevent"]
    if press is None or press not in FOH_BUTTONS:
        button = "No data"
    else:
        button = FOH_BUTTONS[press]

    data = {
        "model": "FOH",
        "name": response["name"],
        "state": button,
        "last_button_event": button,
        "last_updated": response["state"]["lastupdated"].split("T"),
    }
    return data


def parse_z3_rotary(response):
    """Parse the json response for a Lutron Aurora Rotary Event."""

    Z3_DIAL = {1: "begin", 2: "end"}

    turn = response["state"]["rotaryevent"]
    dial_position = response["state"]["expectedrotation"]
    if turn is None or turn not in Z3_DIAL:
        dial = "No data"
    else:
        dial = Z3_DIAL[turn]

    data = {
        "model": "Z3-",
        "name": response["name"],
        "dial_state": dial,
        "dial_position": dial_position,
        "software_update": response["swupdate"]["state"],
        "battery": response["config"]["battery"],
        "on": response["config"]["on"],
        "reachable": response["config"]["reachable"],
        "last_updated": response["state"]["lastupdated"].split("T"),
    }
    return data


def parse_z3_switch(response):
    """Parse the json response for a Lutron Aurora."""

    Z3_BUTTON = {
        1000: "initial_press",
        1001: "repeat",
        1002: "short_release",
        1003: "long_release",
    }

    press = response["state"]["buttonevent"]
    if press is None or press not in Z3_BUTTON:
        button = "No data"
    else:
        button = Z3_BUTTON[press]

    data = {"last_button_event": button, "state": button}
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
    data = HueRemoteData(hass, async_add_entities)
    await data.async_update_info()

    # start polling for updates on the bridge at the default scan interval
    remove_listener = async_track_time_interval(
        hass, data.async_update_info, DEFAULT_SCAN_INTERVAL)

    # register service to change the polling interval
    # TODO: The whole polling should be moved one level up at integration level
    @callback
    def set_polling_interval(service):
        """Adjust the polling interval on the bridge."""
        nonlocal remove_listener
        remove_listener()
        interval = service.data["interval"]
        remove_listener = async_track_time_interval(
            hass, data.async_update_info, timedelta(seconds=interval))

    hass.services.async_register(
        "huesensor",
        "set_polling_interval",
        set_polling_interval,
        schema=vol.Schema({
            vol.Required("interval", default=0.1): vol.Coerce(float)}))


class HueRemoteData(object):
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
            sensor.raw
            for sensor in bridge.api.sensors.values()
            if sensor.type != TYPE_GEOFENCE
        )

        new_sensors = data.keys() - self.data.keys()
        updated_sensors = []
        for key, new in data.items():
            old = self.data.get(key)
            if not old or old == new:
                continue
            if (
                old["last_updated"] == new["last_updated"]
                and old["state"] == new["state"]
            ):
                continue
            updated_sensors.append(key)
        self.data.update(data)

        new_entities = {
            entity_id: HueRemote(entity_id, self) for entity_id in new_sensors
        }
        if new_entities:
            _LOGGER.debug("Created %s", ", ".join(new_entities.keys()))
            self.sensors.update(new_entities)
            self.async_add_entities(new_entities.values(), True)
        for entity_id in updated_sensors:
            # schedule state update on the hass entity
            self.sensors[entity_id].async_schedule_update_ha_state()
            # Fire event on the hass event bus
            self.hass.bus.async_fire(
                HASS_BUTTON_EVENT,
                {
                    "hue_id": self.sensors[entity_id].unique_id,
                    "entity_id": self.sensors[entity_id].entity_id,
                    "button_event": self.data[entity_id]["state"]
                }
            )

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


class HueRemote(RemoteDevice):
    """Class to hold Hue Remote basic info."""

    ICON = "mdi:remote"

    def __init__(self, hue_id, data):
        """Initialize the remote object."""
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
    def state(self):
        """Return the state of the sensor."""
        data = self._data.get(self._hue_id)
        return data["state"]

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        data = self._data.get(self._hue_id)
        if data:
            icon = ICONS.get(data["model"])
            if icon:
                return icon
        return self.ICON

    @property
    def device_state_attributes(self):
        """Attributes."""
        data = self._data.get(self._hue_id)
        if data:
            return {key: data.get(key) for key in ATTRS.get(data["model"], [])}

    @property
    def force_update(self):
        """Force update."""
        return True

    def turn_on(self, **kwargs):
        """Do nothing."""

    def turn_off(self, **kwargs):
        """Do nothing."""
