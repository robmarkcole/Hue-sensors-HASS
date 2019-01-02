"""
Sensor for checking the status of Hue sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.hue/
"""
import asyncio
import async_timeout
from datetime import timedelta
import logging

import homeassistant.util.dt as dt_util
from homeassistant.const import (
    STATE_HOME,
    STATE_NOT_HOME,
    ATTR_GPS_ACCURACY,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
)
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.components.device_tracker import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORM_SCHEMA,
    DeviceScanner,
)
from homeassistant.util import slugify
from homeassistant.components import hue, zone

__version__ = "1.0.1"

DEPENDENCIES = ["hue"]

_LOGGER = logging.getLogger(__name__)

TYPE_GEOFENCE = "Geofence"
MIN_TIME_BETWEEN_SCANS = timedelta(seconds=60)


async def async_setup_scanner(hass, config, async_see, discovery_info=None):
    interval = config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    scanner = HueDeviceScanner(hass, async_see)
    await scanner.async_start(hass, interval)
    return True


class HueDeviceScanner(DeviceScanner):
    def __init__(self, hass, async_see):
        """Initialize the scanner."""
        self.hass = hass
        self.async_see = async_see

    async def async_start(self, hass, interval):
        """Perform a first update and start polling at the given interval."""
        await self.async_update_info()
        interval = max(interval, MIN_TIME_BETWEEN_SCANS)
        async_track_time_interval(hass, self.async_update_info, interval)

    async def async_see_sensor(self, sensor):
        last_updated = sensor.state.get("lastupdated")
        if not last_updated or last_updated == "none":
            return

        kwargs = dict(
            dev_id=slugify("hue_{}".format(sensor.name)),
            host_name=sensor.name,
            attributes={
                "last_updated": dt_util.as_local(dt_util.parse_datetime(last_updated)),
                "unique_id": sensor.uniqueid,
            },
        )

        if sensor.state.get("presence"):
            kwargs["location_name"] = STATE_HOME
            zone_home = self.hass.states.get(zone.ENTITY_ID_HOME)
            if zone_home:
                kwargs["gps"] = [
                    zone_home.attributes[ATTR_LATITUDE],
                    zone_home.attributes[ATTR_LONGITUDE],
                ]
                kwargs[ATTR_GPS_ACCURACY] = 0
        else:
            kwargs["location_name"] = STATE_NOT_HOME

        _LOGGER.debug(
            "Hue Geofence %s: %s (%s)",
            sensor.name,
            kwargs["location_name"],
            kwargs["attributes"],
        )

        result = await self.async_see(**kwargs)
        return result

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
        sensors = [
            self.async_see_sensor(sensor)
            for api in apis
            for sensor in api.sensors.values()
            if sensor.type == TYPE_GEOFENCE
        ]
        if not sensors:
            return
        await asyncio.wait(sensors)
