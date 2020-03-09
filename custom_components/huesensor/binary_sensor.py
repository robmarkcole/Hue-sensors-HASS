"""Binary sensor for Hue motion sensors."""
import logging

from homeassistant.components.binary_sensor import BinarySensorDevice
from homeassistant.components.sensor import PLATFORM_SCHEMA  # noqa: F401
from homeassistant.const import CONF_SCAN_INTERVAL, STATE_ON

from . import DOMAIN
from .data_manager import (
    DEFAULT_SCAN_INTERVAL,
    HueSensorBaseDevice,
    HueSensorData,
)
from .hue_api_response import BINARY_SENSOR_MODELS

_LOGGER = logging.getLogger(__name__)

TYPE_GEOFENCE = "Geofence"
DEVICE_CLASSES = {"SML": "motion"}


async def async_setup_platform(
    hass, config, async_add_entities, discovery_info=None
):
    """Initialise Hue Bridge connection."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = HueSensorData(hass)

    await hass.data[DOMAIN].async_add_platform_entities(
        HueBinarySensor,
        BINARY_SENSOR_MODELS,
        async_add_entities,
        config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )


class HueBinarySensor(HueSensorBaseDevice, BinarySensorDevice):
    """Class to hold Hue Binary Sensor basic info."""

    @property
    def is_on(self):
        """Return the state of the sensor."""
        data = self.sensor_data
        if data and data["model"] == "SML" and data["changed"]:
            return data["state"] == STATE_ON
        return False

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return DEVICE_CLASSES.get(self.sensor_data["model"])
