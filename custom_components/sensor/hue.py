"""
Sensor for checking the status of Hue sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.hue_sensors/
"""
import logging
from datetime import timedelta
from datetime import datetime

import requests

from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from homeassistant.const import STATE_UNKNOWN

import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv

DOMAIN = 'hue'
_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=1)

REQUIREMENTS = ['hue-sensors==1.1']


# Validation of the user's configuration of multiway sensors
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional('multiwaysensors'): [{
        vol.Required('name'): cv.string,
        vol.Required('sensorids'): cv.entity_ids
    }]
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Hue sensors."""
    import hue_sensors as hs
    url = hass.data[DOMAIN] + '/sensors'
    data = HueSensorData(url, hs.parse_hue_api_response)
    data.update()
    sensors = []
    for key in data.data.keys():
        sensors.append(HueSensor(key, data))
    _LOGGER.debug("Created regular devices, creating multiwaysensors")

    """Set up the multiway sensors."""
	# TODO: test for existence of multiway conf
    multiwaysensorsconf = config['multiwaysensors']
    for mwsensor in multiwaysensorsconf:
        mwsensorname = mwsensor['name']
        mwsensoridlist = mwsensor['sensorids']
        sensors.append(HueMultiwaySensor(sensors, mwsensor['name'], mwsensor['sensorids']))
    _LOGGER.debug("Created all devices, adding them to Home Assistant")
    add_devices(sensors, True)


class HueSensorData(object):
    """Get the latest sensor data."""

    def __init__(self, url, parse_hue_api_response):
        """Initialize the data object."""
        self.url = url
        self.data = None
        self.parse_hue_api_response = parse_hue_api_response

    # Update only once in scan interval.
    @Throttle(SCAN_INTERVAL)
    def update(self):
        """Get the latest data."""
        response = requests.get(self.url)
        if response.status_code != 200:
            _LOGGER.warning("Invalid response from API")
        else:
            self.data = self.parse_hue_api_response(response.json())

class HueMultiwaySensor(Entity):
    """Class to hold Hue Multiway Sensor basic info."""

    ICON = 'mdi:run-fast'

    def __init__(self, sensors, mwsensorname, mwsensoridlist):
        """Initialize the sensor object."""
        _LOGGER.debug("Init multiwaysensor")
        self._sensors = sensors
        self._sensoridlist = mwsensoridlist
        self._icon = None
        self._name = mwsensorname
        self._state = STATE_UNKNOWN
        self._attributes = {}
        self._attributes['sensorids'] = mwsensoridlist

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

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
        latestupdate = None
        latestsensor = None
        for sensor in self._sensors:
            if sensor.entity_id in self._sensoridlist:
                _LOGGER.debug("Checking sensor: " + sensor.name)
                if 'last updated' in sensor.device_state_attributes.keys():
                    lastupdatearray = sensor.device_state_attributes['last updated']
                    strtime = lastupdatearray[0] + " " + lastupdatearray[1]
                    lastupdated = datetime.strptime(strtime, '%Y-%m-%d %H:%M:%S')
                    if (latestupdate is None) or ((latestupdate is not None and lastupdated > latestupdate)):
                        _LOGGER.debug("Found new latest sensor " + sensor.name)
                        latestupdate = lastupdated
                        latestsensor = sensor
        if latestsensor is not None:
            self._state = latestsensor.state
            self._attributes['last sensor'] = latestsensor.name
            self._attributes['last updated'] = latestsensor.device_state_attributes['last updated']
			

class HueSensor(Entity):
    """Class to hold Hue Sensor basic info."""

    ICON = 'mdi:run-fast'

    def __init__(self, hue_id, data):
        """Initialize the sensor object."""
        self._hue_id = hue_id
        self._data = data    # data is in .data
        self._icon = None
        self._name = self._data.data[self._hue_id]['name']
        self._model = self._data.data[self._hue_id]['model']
        self._state = self._data.data[self._hue_id]['state']
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
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def device_state_attributes(self):
        """Attributes."""
        return self._attributes

    def update(self):
        """Update the sensor."""
        self._data.update()
        self._state = self._data.data[self._hue_id]['state']
        if self._model == 'SML':
            self._icon = 'mdi:run-fast'
            self._attributes['light_level'] = self._data.data[
                self._hue_id]['light_level']
            self._attributes['battery'] = self._data.data[
                self._hue_id]['battery']
            self._attributes['last updated'] = self._data.data[
                self._hue_id]['last_updated']
            self._attributes['lux'] = self._data.data[
                self._hue_id]['lux']
            self._attributes['dark'] = self._data.data[
                self._hue_id]['dark']
            self._attributes['daylight'] = self._data.data[
                self._hue_id]['daylight']
            self._attributes['temperature'] = self._data.data[
                self._hue_id]['temperature']
        elif self._model == 'RWL':
            self._icon = 'mdi:remote'
            self._attributes['last updated'] = self._data.data[
                self._hue_id]['last_updated']
            self._attributes['battery'] = self._data.data[
                self._hue_id]['battery']
        elif self._model == 'ZGP':
            self._icon = 'mdi:remote'
            self._attributes['last updated'] = self._data.data[
                self._hue_id]['last_updated']
        elif self._model == 'Geofence':
            self._icon = 'mdi:cellphone'

