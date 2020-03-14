"""The huesensors component."""
import asyncio
from datetime import timedelta
import logging
from typing import AsyncIterable, Set, Tuple

from homeassistant.components.hue import DOMAIN as HUE_DOMAIN, HueBridge
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_time_interval

from .hue_api_response import (
    BINARY_SENSOR_MODELS,
    ENTITY_ATTRS,
    parse_hue_api_response,
)

_LOGGER = logging.getLogger(__name__)

# Scan interval for binary sensors is set to < 1s
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
        self.registered_entities = {}
        self.available = False
        self._scan_interval = None
        self._update_listener = None

        # delayed setup and discovery with platform + model filter
        self._registered_models: Set[str] = set()
        self._registered_platforms = {}

    async def _iter_data(
        self, models_filter: Tuple[str] = BINARY_SENSOR_MODELS
    ) -> AsyncIterable[Tuple[bool, str, str, dict]]:
        async for bridge in async_get_bridges(self.hass):
            await bridge.sensor_manager.coordinator.async_request_refresh()
            data = parse_hue_api_response(
                sensor.raw
                for sensor in bridge.api.sensors.values()
                if sensor.raw["modelid"].startswith(models_filter)
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

    def _register_new_entity(self, dev_id, model, new_entities_to_add):
        """Register a new Entity and add it in platform queue for HA setup."""
        # Create platform entity and register the device
        entity_cls, async_add_entities = self._registered_platforms[model]
        platform_entity = entity_cls(dev_id, self)
        self.registered_entities[dev_id] = platform_entity

        # Add entity to platform queue to add it to HA
        if async_add_entities not in new_entities_to_add:
            new_entities_to_add[async_add_entities] = [entity_cls, []]
        new_entities_to_add[async_add_entities][1].append(platform_entity)

    async def _add_new_entities(self, new_entities, scan_interval=None):
        """Call HA add_entities for each platform with its discovered items."""
        for func_add_entities, (entity_cls, entities) in new_entities.items():
            func_add_entities(entities, True)

            if scan_interval is None:
                continue

            if self._scan_interval is None:
                self._scan_interval = scan_interval
                _LOGGER.info(
                    "Configure a scan_interval of %.2f s for %s devices",
                    scan_interval.total_seconds(),
                    entity_cls.__name__,
                )

    async def async_add_platform_entities(
        self, entity_cls, platform_models, func_add_entities, scan_interval,
    ):
        """Add sensor entities from platform setups."""
        for model in platform_models:
            self._registered_platforms[model] = (entity_cls, func_add_entities)
            self._registered_models.add(model)

        new_entities_to_add = {}
        async for is_new, model, dev_id, _ in self._iter_data(platform_models):
            if is_new and dev_id not in self.registered_entities:
                self._register_new_entity(dev_id, model, new_entities_to_add)

        await self._add_new_entities(new_entities_to_add, scan_interval)

    async def async_update_from_bridges(self, now=None):
        """Request data from bridges and update sensors data."""
        new_entities_to_add = {}
        async for updated, model, dev_id, _dev_data in self._iter_data(
            tuple(self._registered_models)
        ):
            if updated and dev_id not in self.registered_entities:
                # Discovery of newly added devices
                _LOGGER.warning(
                    "New device discovered %s:%s. Adding it now", model, dev_id
                )
                self._register_new_entity(dev_id, model, new_entities_to_add)
            elif updated and dev_id not in self.sensors:
                # device is registered, but it is not added to hass yet ¿?
                _LOGGER.warning(
                    "Device %s:%s registered but not added yet", model, dev_id
                )
            elif updated:
                self.sensors[dev_id].async_write_ha_state()
                _LOGGER.debug(
                    "%s (%s): updated with state=%s",
                    self.sensors[dev_id].entity_id,
                    dev_id,
                    self.sensors[dev_id].state,
                )
        await self._add_new_entities(new_entities_to_add)


class HueSensorBaseDevice(Entity):
    """Common class to handle custom HueSensor entities."""

    def __init__(self, hue_id, data_manager: HueSensorData):
        """Initialize the hue object."""
        self._hue_id = hue_id
        self._data_manager = data_manager

    async def async_added_to_hass(self):
        """Register sensor when entity is added to hass and start updating."""
        self._data_manager.sensors[self.unique_id] = self
        await self._data_manager.async_start_scheduler()
        _LOGGER.debug(
            "Setup complete for %s:%s", self.__class__.__name__, self.unique_id
        )

    async def async_will_remove_from_hass(self):
        """When entity will be removed from hass."""
        _LOGGER.debug("%s: Removing entity from HA", self.entity_id)
        self._data_manager.sensors.pop(self.unique_id)
        self._data_manager.registered_entities.pop(self.unique_id)

        if self._data_manager.sensors:
            return

        await self._data_manager.async_stop_scheduler()

    @property
    def sensor_data(self) -> dict:
        """Access to parsed sensor data."""
        return self._data_manager.data.get(self.unique_id)

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
