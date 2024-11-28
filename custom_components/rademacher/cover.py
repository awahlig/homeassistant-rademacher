"""Platform for Rademacher Bridge."""
import logging
from typing import Any

from homepilot.cover import CoverType, HomePilotCover
from homepilot.device import HomePilotDevice

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.const import CONF_EXCLUDE

from .const import DOMAIN
from .entity import HomePilotEntity
from .state_manager import StateManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup of entities for cover platform."""
    state_manager: StateManager = hass.data[DOMAIN][config_entry.entry_id]
    manager = state_manager.manager
    exclude_devices: list[str] = state_manager.entry_options[CONF_EXCLUDE]
    new_entities = []
    for did in manager.devices:
        if did not in exclude_devices:
            device: HomePilotDevice = manager.devices[did]
            if isinstance(device, HomePilotCover):
                _LOGGER.info("Found Cover for Device ID: %s", device.did)
                new_entities.append(HomePilotCoverEntity(state_manager, device))
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class HomePilotCoverEntity(HomePilotEntity, CoverEntity):
    """This class represents the Cover entity."""

    def __init__(
        self, state_manager: StateManager, cover: HomePilotCover
    ) -> None:
        super().__init__(
            state_manager,
            cover,
            unique_id=cover.uid,
            name=cover.name,
            device_class=CoverDeviceClass.SHUTTER.value
            if cover.cover_type == CoverType.SHUTTER.value
            else CoverDeviceClass.GARAGE.value,
        )
        self._supported_features = (
            CoverEntityFeature.STOP | CoverEntityFeature.CLOSE | CoverEntityFeature.OPEN
        )
        if cover.can_set_position:
            self._supported_features |= CoverEntityFeature.SET_POSITION
        if cover.has_tilt:
            self._supported_features |= (
                CoverEntityFeature.OPEN_TILT
                | CoverEntityFeature.CLOSE_TILT
                | CoverEntityFeature.STOP_TILT
            )
        if cover.can_set_tilt_position:
            self._supported_features |= CoverEntityFeature.SET_TILT_POSITION

    @property
    def supported_features(self):
        return self._supported_features

    @property
    def current_cover_position(self):
        device: HomePilotCover = self.coordinator.data[self.did]
        return device.cover_position

    @property
    def current_cover_tilt_position(self):
        device: HomePilotCover = self.coordinator.data[self.did]
        return device.cover_tilt_position

    @property
    def is_closing(self):
        device: HomePilotCover = self.coordinator.data[self.did]
        return device.is_closing

    @property
    def is_opening(self):
        device: HomePilotCover = self.coordinator.data[self.did]
        return device.is_opening

    @property
    def is_closed(self):
        device: HomePilotCover = self.coordinator.data[self.did]
        return device.is_closed

    async def async_open_cover(self, **kwargs: Any) -> None:
        device: HomePilotCover = self.coordinator.data[self.did]
        await device.async_open_cover()
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        device: HomePilotCover = self.coordinator.data[self.did]
        await device.async_close_cover()
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        device: HomePilotCover = self.coordinator.data[self.did]
        await device.async_set_cover_position(kwargs[ATTR_POSITION])
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        device: HomePilotCover = self.coordinator.data[self.did]
        await device.async_stop_cover()
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_open_cover_tilt(self, **kwargs: Any) -> None:
        device: HomePilotCover = self.coordinator.data[self.did]
        await device.async_open_cover_tilt()
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_close_cover_tilt(self, **kwargs: Any) -> None:
        device: HomePilotCover = self.coordinator.data[self.did]
        await device.async_close_cover_tilt()
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_set_cover_tilt_position(self, **kwargs: Any) -> None:
        device: HomePilotCover = self.coordinator.data[self.did]
        await device.async_set_cover_tilt_position(kwargs[ATTR_TILT_POSITION])
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_stop_cover_tilt(self, **kwargs: Any) -> None:
        device: HomePilotCover = self.coordinator.data[self.did]
        await device.async_stop_cover_tilt()
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()
