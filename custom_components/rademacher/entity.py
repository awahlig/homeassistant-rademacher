from collections.abc import Mapping
from typing import Any
import asyncio
from contextlib import asynccontextmanager

from homepilot.device import HomePilotDevice

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .state_manager import StateManager


class HomePilotEntity(CoordinatorEntity):
    def __init__(
        self,
        state_manager: StateManager,
        device: HomePilotDevice,
        unique_id,
        name,
        device_class=None,
        entity_category=None,
        icon=None,
    ):
        super().__init__(state_manager.coordinator)
        self._state_manager = state_manager
        self._unique_id = unique_id
        self._name = name
        self._device_name = device.name
        self._device_class = device_class
        self._entity_category = entity_category
        self._icon = icon
        self._did = device.did
        self._model = device.model

    @property
    def state_manager(self):
        return self._state_manager

    @property
    def did(self):
        return self._did

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def name(self):
        return self._name

    @property
    def device_name(self):
        return self._device_name

    @property
    def device_class(self):
        return self._device_class

    @property
    def entity_category(self):
        return self._entity_category

    @property
    def model(self):
        return self._model

    @property
    def sw_version(self):
        return self.coordinator.data[self.did].fw_version

    @property
    def icon(self):
        return self._icon

    @property
    def device_info(self):
        """Information about this entity/device."""
        return {
            "identifiers": {(DOMAIN, self.did)},
            # If desired, the name for the device could be different to the entity
            "name": self.device_name,
            "sw_version": self.coordinator.data[self.did].fw_version,
            "model": self.model,
            "manufacturer": "Rademacher",
        }

    @property
    def available(self):
        device: HomePilotDevice = self.coordinator.data[self.did]
        return device.available

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        device: HomePilotDevice = self.coordinator.data[self.did]
        return getattr(device, "extra_attributes")

    async def async_update_device_state(self):
        """Query the state of this device and update it.
        Should be called after making changes to the device state.
        """
        await self.state_manager.async_update_device_state(self.did)
        self.schedule_update_ha_state()

    @asynccontextmanager
    async def async_state_change_context(self, *, max_wait=5.0):
        """Wrap a state change in this context manager to query and
        update the state after the change.

        Keeps checking for state updates until the state has changed
        compared to the state before the change.
        """
        before = self.state_manager.get_last_state(self.did)
        yield self  # Let the caller perform the state change
        try:
            # Keep checking for state updates, up to max_wait seconds
            async with asyncio.timeout(max_wait):
                await self._async_state_update_check(before)
        except asyncio.TimeoutError:
            pass

    async def _async_state_update_check(self, before):
        delay = 0.05
        while True:
            await self.state_manager.async_update_device_state(self.did)
            after = self.state_manager.get_last_state(self.did)

            if after["statusesMap"] != before["statusesMap"]:
                self.schedule_update_ha_state()
                return

            await asyncio.sleep(delay)
            # Exponential backoff, up to 1 second
            delay = min(delay * 2, 1.0)
