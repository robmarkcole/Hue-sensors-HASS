"""The huesensors component."""
import asyncio
from datetime import timedelta
import logging
from typing import AsyncIterable, Tuple

from homeassistant.components.hue import DOMAIN as HUE_DOMAIN, HueBridge
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_time_interval

from .hue_api_response import (
    BINARY_SENSOR_MODELS,
    ENTITY_ATTRS,
    parse_hue_api_response,
    REMOTE_MODELS,
)

_LOGGER = logging.getLogger(__name__)

_KNOWN_MODEL_IDS = tuple(BINARY_SENSOR_MODELS + REMOTE_MODELS)

# Scan interval for remotes and binary sensors is set to < 1s
# just to ~ensure that an update is called for each HA tick,
# as using an exact 1s misses some of the ticks
DEFAULT_SCAN_INTERVAL = timedelta(seconds=0.5)


async def async_get_bridges(hass) -> AsyncIterable[HueBridge]:
    """Retrieve Hue bridges from loaded official Hue integration."""
    for entry in hass.data[HUE_DOMAIN].values():
        if isinstance(entry, HueBridge) and entry.api:
            yield entry


class HueSensorData:
    """Sensor data handler for this custom integration."""

    def __init__(self, hass):
        """Initialize the data object."""
        self.hass = hass
        self.lock = asyncio.Lock()
        self.data = {}
        self.sensors = {}
        self.available = False
        self._scan_interval = None
        self._update_listener = None

    async def _iter_data(self) -> AsyncIterable[Tuple[bool, str, str, dict]]:
        async for bridge in async_get_bridges(self.hass):
            await bridge.sensor_manager.coordinator.async_request_refresh()
            data = parse_hue_api_response(
                sensor.raw
                for sensor in bridge.api.sensors.values()
                if sensor.raw["modelid"].startswith(_KNOWN_MODEL_IDS)
            )
            for dev_id, dev_data in data.items():
                updated = False
                dev_model = dev_data["model"]
                if dev_model == "SML":
                    dev_data["changed"] = True
                old = self.data.get(dev_id)
                if not old:
                    updated = True
                    self.data[dev_id] = dev_data
                elif old != dev_data:
                    updated = True
                    if (
                        old["last_updated"] == dev_data["last_updated"]
                        and old["state"] == dev_data["state"]
                    ):
                        if dev_model == "SML":
                            dev_data["changed"] = False
                        updated = False
                    self.data[dev_id].update(dev_data)

                yield updated, dev_data["model"], dev_id, dev_data

    async def async_start_scheduler(self):
        """Schedule data polling with current scan_interval."""
        async with self.lock:
            if self.available:
                return

            if self._update_listener is not None:
                _LOGGER.info(f"Cancelling old time tracker")
                self._update_listener()
            self._update_listener = async_track_time_interval(
                self.hass, self.async_update_from_bridges, self._scan_interval,
            )
            self.available = True

    async def async_stop_scheduler(self):
        """Cancel data polling with current scan_interval."""
        async with self.lock:
            if not self.available and self._update_listener is None:
                _LOGGER.debug(f"Already stopped")
                return

            if self._update_listener is not None:
                self._update_listener()
                self._update_listener = None

            self.available = False
        _LOGGER.debug(f"Stopped polling with {self._scan_interval}")

    async def async_add_platform_entities(
        self, entity_cls, platform_models, async_add_entities, scan_interval,
    ):
        """Add sensor entities from platform setups."""
        new_entities = []
        async for updated, model, dev_id, dev_data in self._iter_data():
            if model in platform_models and dev_id not in self.sensors:
                platform_entity = entity_cls(dev_id, self)
                self.sensors[dev_id] = platform_entity
                new_entities.append(platform_entity)

        if new_entities:
            async_add_entities(new_entities, True)

            if self._scan_interval is None:
                self._scan_interval = scan_interval
                _LOGGER.info(
                    "Configure a scan_interval of %.2f s for %s devices",
                    scan_interval.total_seconds(),
                    entity_cls.__name__,
                )
            elif scan_interval < self._scan_interval:
                _LOGGER.info(
                    "Re-Configure a scan_interval of %.2f s for %s devices"
                    " (before it was %.2f s)",
                    scan_interval.total_seconds(),
                    entity_cls.__name__,
                    self._scan_interval.total_seconds(),
                )
                await self.async_stop_scheduler()
                self._scan_interval = scan_interval

    async def async_update_from_bridges(self, now=None):
        """Request data from bridges and update sensors data."""
        async for updated, _model, dev_id, _dev_data in self._iter_data():
            if updated:
                try:
                    self.sensors[dev_id].async_write_ha_state()
                    _LOGGER.debug(
                        "%s (%s): updated with state=%s",
                        self.sensors[dev_id].entity_id,
                        dev_id,
                        self.sensors[dev_id].state,
                    )
                except KeyError as exc:  # pragma: no cover
                    _LOGGER.error(
                        "Unknown %s, not in %s", exc, self.sensors.keys()
                    )


class HueSensorBaseDevice(Entity):
    """Common class to handle custom HueSensor entities."""

    def __init__(self, hue_id, data_manager: HueSensorData):
        """Initialize the hue object."""
        self._hue_id = hue_id
        self._data_manager = data_manager

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        # TODO use bridge.sensor_manager.coordinator.async_add_listener
        # self.bridge.sensor_manager.coordinator.async_add_listener(
        #     self.async_write_ha_state
        # )
        await self._data_manager.async_start_scheduler()
        _LOGGER.debug(
            "Setup complete for %s:%s", self.__class__.__name__, self._hue_id
        )

    async def async_will_remove_from_hass(self):
        """When entity will be removed from hass."""
        # self.bridge.sensor_manager.coordinator.async_remove_listener(
        #     self.async_write_ha_state
        # )
        _LOGGER.debug("%s: Removing entity from HA", self.entity_id)
        self._data_manager.sensors.pop(self._hue_id)

        if self._data_manager.sensors:
            return

        await self._data_manager.async_stop_scheduler()

    @property
    def sensor_data(self) -> dict:
        """Access to parsed sensor data."""
        return self._data_manager.data.get(self._hue_id)

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def name(self):
        """Return the name of the remote."""
        return self.sensor_data["name"]

    @property
    def unique_id(self):
        """Return the ID of this Hue remote."""
        return self._hue_id

    @property
    def device_state_attributes(self):
        """Attributes."""
        return {
            key: self.sensor_data.get(key)
            for key in ENTITY_ATTRS.get(self.sensor_data["model"], ())
        }
