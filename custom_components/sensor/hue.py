"""
Sensor for checking the status of Hue sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.hue/
"""
import logging
from datetime import timedelta

import requests
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_IP_ADDRESS, CONF_TOKEN)
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

__version__ = '0.7'

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=0.1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_IP_ADDRESS): cv.string,
    vol.Required(CONF_TOKEN): cv.string,
})


def parse_hue_api_response(response):
    """Take in the Hue API json response."""
    data_dict = {}    # The list of sensors, referenced by their hue_id.

    # Loop over all keys (1,2 etc) to identify sensors and get data.
    for key in response.keys():
        sensor = response[key]
        modelid = sensor['modelid'][0:3]
        if modelid in ['RWL', 'SML', 'ZGP']:
            _key = modelid + '_' + sensor['uniqueid'][:-5]

            if modelid == 'RWL':
                data_dict[_key] = parse_rwl(sensor)
            elif modelid == 'ZGP':
                data_dict[_key] = parse_zgp(sensor)
            elif modelid == 'SML':
                if _key not in data_dict.keys():
                    data_dict[_key] = parse_sml(sensor)
                else:
                    data_dict[_key].update(parse_sml(sensor))

        elif sensor['modelid'] == 'HA_GEOFENCE':
            data_dict['Geofence'] = parse_geofence(sensor)
    return data_dict


def parse_sml(response):
    """Parse the json for a SML Hue motion sensor and return the data."""
    if response['type'] == "ZLLLightLevel":
        lightlevel = response['state']['lightlevel']
        if lightlevel is not None:
            lx = round(float(10**((lightlevel-1)/10000)), 2)
            dark = response['state']['dark']
            daylight = response['state']['daylight']
            data = {'light_level': lightlevel,
                    'lx': lx,
                    'dark': dark,
                    'daylight': daylight, }
        else:
            data = {'light_level': 'No light level data'}

    elif response['type'] == "ZLLTemperature":
        if response['state']['temperature'] is not None:
            data = {'temperature': response['state']['temperature']/100.0}
        else:
            data = {'temperature': 'No temperature data'}

    elif response['type'] == "ZLLPresence":
        name_raw = response['name']
        arr = name_raw.split()
        arr.insert(-1, 'motion')
        name = ' '.join(arr)
        hue_state = response['state']['presence']
        if hue_state is True:
            state = 'on'
        else:
            state = 'off'

        data = {'model': 'SML',
                'name': name,
                'state': state,
                'battery': response['config']['battery'],
                'on': response['config']['on'],
                'reachable': response['config']['reachable'],
                'last_updated': response['state']['lastupdated'].split('T')}
    return data


def parse_zgp(response):
    """Parse the json response for a ZGPSWITCH Hue Tap."""
    TAP_BUTTONS = {34: '1_click', 16: '2_click', 17: '3_click', 18: '4_click'}
    press = response['state']['buttonevent']
    if press is None:
        button = 'No data'
    else:
        button = TAP_BUTTONS[press]

    data = {'model': 'ZGP',
            'name': response['name'],
            'state': button,
            'last_updated': response['state']['lastupdated'].split('T')}
    return data


def parse_rwl(response):
    """Parse the json response for a RWL Hue remote."""

    """
        I know it should be _released not _up
        but _hold_up is too good to miss isn't it
    """
    responsecodes = {
        '0' : "_click",
        '1' : "_hold",
        '2' : "_click_up",
        '3' : "_hold_up"
    }


    button = ""
    if response['state']['buttonevent']:
        press = str(response['state']['buttonevent'])
        button = str(press)[0] + responsecodes[press[-1]]

    data = {'model': 'RWL',
            'name': response['name'],
            'state': button,
            'battery': response['config']['battery'],
            'on': response['config']['on'],
            'reachable': response['config']['reachable'],
            'last_updated': response['state']['lastupdated'].split('T')}
    return data


def parse_geofence(response):
    """Parse the json response for a GEOFENCE and return the data."""
    hue_state = response['state']['presence']
    if hue_state is True:
        state = 'on'
    else:
        state = 'off'
    data = {'name': response['name'],
            'model': 'Geofence',
            'state': state}
    return data


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Hue sensors."""
    try:
        data = HueSensorData(parse_hue_api_response, config)
        data.update()
        sensors = []
        for key in data.data.keys():
            sensors.append(HueSensor(key, data))
        add_devices(sensors, True)
    except:
        _LOGGER.warning("Cannot setup Hue sensors, check your config")


class HueSensorData(object):
    """Get the latest sensor data."""

    def __init__(self, parse_hue_api_response, config):
        """Initialize the data object."""
        self.url = self._build_url(config)
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

    def _build_url(self, config):
        ip_address = config.get(CONF_IP_ADDRESS)
        token = config.get(CONF_TOKEN)

        return "http://" + ip_address + "/api/" + token + "/sensors"


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
        try:
            if self._model == 'SML':
                self._icon = 'mdi:run-fast'
                self._attributes['light_level'] = self._data.data[
                    self._hue_id]['light_level']
                self._attributes['battery'] = self._data.data[
                    self._hue_id]['battery']
                self._attributes['last_updated'] = self._data.data[
                    self._hue_id]['last_updated']
                self._attributes['lx'] = self._data.data[
                    self._hue_id]['lx']
                self._attributes['dark'] = self._data.data[
                    self._hue_id]['dark']
                self._attributes['daylight'] = self._data.data[
                    self._hue_id]['daylight']
                self._attributes['temperature'] = self._data.data[
                    self._hue_id]['temperature']
                self._attributes['on'] = self._data.data[
                    self._hue_id]['on']
                self._attributes['reachable'] = self._data.data[
                    self._hue_id]['reachable']
            elif self._model == 'RWL':
                self._icon = 'mdi:remote'
                self._attributes['last_updated'] = self._data.data[
                    self._hue_id]['last_updated']
                self._attributes['battery'] = self._data.data[
                    self._hue_id]['battery']
                self._attributes['on'] = self._data.data[
                    self._hue_id]['on']
                self._attributes['reachable'] = self._data.data[
                    self._hue_id]['reachable']
            elif self._model == 'ZGP':
                self._icon = 'mdi:remote'
                self._attributes['last_updated'] = self._data.data[
                    self._hue_id]['last_updated']
            elif self._model == 'Geofence':
                self._icon = 'mdi:cellphone'
        except:
            _LOGGER.error("Error updating Hue sensors")
