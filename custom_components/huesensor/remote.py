"""Hue remotes."""
import logging

from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.components.remote import (  # noqa: F401
    PLATFORM_SCHEMA,
    RemoteDevice,
)

from . import DOMAIN
from .data_manager import (
    DEFAULT_SCAN_INTERVAL,
    HueSensorBaseDevice,
    HueSensorData,
)
from .hue_api_response import REMOTE_MODELS

_LOGGER = logging.getLogger(__name__)

REMOTE_ICONS = {
    "RWL": "mdi:remote",
    "ROM": "mdi:remote",
    "ZGP": "mdi:remote",
    "FOH": "mdi:light-switch",
    "Z3-": "mdi:light-switch",
}


async def async_setup_platform(
    hass, config, async_add_entities, discovery_info=None
):
    """Initialise Hue Bridge connection."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = HueSensorData(hass)

    await hass.data[DOMAIN].async_add_platform_entities(
        HueRemote,
        REMOTE_MODELS,
        async_add_entities,
        config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )


class HueRemote(HueSensorBaseDevice, RemoteDevice):
    """Class to hold Hue Remote basic info."""

    @property
    def state(self):
        """Return the state of the remote."""
        return self.sensor_data["state"]

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        data = self.sensor_data
        if data:
            icon = REMOTE_ICONS.get(data["model"])
            if icon:
                return icon
        return "mdi:remote"  # pragma: no cover

    @property
    def force_update(self):
        """Force update."""
        return True

    def turn_on(self, **kwargs):
        """Do nothing."""

    def turn_off(self, **kwargs):
        """Do nothing."""
