"""
Sensor for checking the status of Hue sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.hue_sensors/
"""
import json
import logging
from datetime import timedelta

import requests

from homeassistant.const import (CONF_FILENAME)
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)
PHUE_CONFIG_FILE = 'phue.conf'
SCAN_INTERVAL = timedelta(seconds=1)

REQUIREMENTS = ['https://github.com/robmarkcole/Hue-sensors/archive/'
                'v0.3.zip'
                '#hue_sensors==v0.3']


def load_conf(filepath):
    """Return the URL for API requests."""
    with open(filepath, 'r') as file_path:
        data = json.load(file_path)
        ip_add = next(data.keys().__iter__())
        username = data[ip_add]['username']
        url = 'http://' + ip_add + '/api/' + username + '/sensors'
    return url


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the sensor."""
    from hue_sensors import parse_hue_api_response
    filename = config.get(CONF_FILENAME, PHUE_CONFIG_FILE)  # returns the IP
    filepath = hass.config.path(filename)
    url = load_conf(filepath)
    data = HueSensorData(url, parse_hue_api_response)
    data.update()
    sensors = []
    for key in data.data.keys():
        sensors.append(HueSensor(key, data))
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


class HueSensor(Entity):
    """Class to hold Hue Sensor basic info."""

    ICON = 'mdi:run-fast'

    def __init__(self, hue_id, data):
        """Initialize the sensor object."""
        self._hue_id = hue_id
        self._data = data    # data is in .data
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
        return self.ICON

    @property
    def device_state_attributes(self):
        """Only motion sensors have attributes currently, but could extend."""
        return self._attributes

    def update(self):
        """Update the sensor."""
        self._data.update()
        self._state = self._data.data[self._hue_id]['state']
        if self._model == 'SML001':
            self._attributes['light_level'] = self._data.data[
                self._hue_id]['light_level']
            self._attributes['temperature'] = self._data.data[
                self._hue_id]['temperature']
        elif self._model in ['RWL021', 'ZGPSWITCH']:
            self.ICON = 'mdi:remote'
            self._attributes['last updated'] = self._data.data[
                self._hue_id]['last_updated']
        elif self._model == 'Geofence':
            self.ICON = 'mdi:cellphone'
