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

DOMAIN = 'hue_bridge'


def load_conf(filepath):
    """Return the URL for API requests."""
    with open(filepath, 'r') as file_path:
        data = json.load(file_path)
        ip_add = next(data.keys().__iter__())
        username = data[ip_add]['username']
        url = 'http://' + ip_add + '/api/' + username + '/sensors'
    return url


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Tube sensor."""
    filename = config.get(CONF_FILENAME, PHUE_CONFIG_FILE)  # returns the IP
    filepath = hass.config.path(filename)
    url = load_conf(filepath)
    hass.data[DOMAIN] = url
    _LOGGER.warning("URL is {}".format(url))
