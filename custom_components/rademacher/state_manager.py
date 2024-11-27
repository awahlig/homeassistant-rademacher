import asyncio
from datetime import timedelta
import logging
import time

from homepilot.api import AuthError
from homepilot.manager import HomePilotManager
from homepilot.device import HomePilotDevice

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator


_LOGGER = logging.getLogger(__name__)


class StateManager:
    """Manages the states of all devices and provides
    ways to update them.
    """

    def __init__(self,
        hass: HomeAssistant,
        manager: HomePilotManager,
        entry_data: dict,
        entry_options: dict
    ):
        self.hass = hass
        self.manager = manager
        self.entry_data = entry_data
        self.entry_options = entry_options
        self.coordinator = None
        self._update_in_progress = False
        self._states = {}

    async def build_update_coordinator(self):
        """Build the update coordinator and do the first refresh."""
        async def update_method():
            await self._async_update_data()
            return self.manager.devices

        self.coordinator = DataUpdateCoordinator(
            self.hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="rademacher",
            update_method=update_method,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=10),
        )

        await self.coordinator.async_config_entry_first_refresh()

    async def _async_update_data(self):
        if self._update_in_progress:
            return

        self._update_in_progress = True
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with asyncio.timeout(10):
                await self._async_update_states_of_all_devices()
        except AuthError as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err
        finally:
            self._update_in_progress = False

    async def _async_apply_device_state(self, did, state, ts):
        if ts < self._states.get(did, { "_ts": 0.0 })["_ts"]:
            # Superseded by a more recent state
            return

        device = self.manager.devices[did]
        state["_ts"] = ts
        self._states[did] = state
        await device.update_state(state, self.manager.api)

    async def _async_update_states_of_all_devices(self):
        ts = time.time()
        try:
            states = await self.manager.api.async_get_devices_state()
            states["-1"] = await self.manager.get_hub_state()
        except AuthError:  # pylint: disable=try-except-raise
            raise
        except:
            for did in self.manager.devices:
                device: HomePilotDevice = self.manager.devices[did]
                device.available = False
            raise

        for did in self.manager.devices:
            if did in states:
                await self._async_apply_device_state(did, states[did], ts)
            else:
                device: HomePilotDevice = self.manager.devices[did]
                device.available = False

    async def async_update_device_state(self, did):
        """Query the state of a single device and apply it."""
        ts = time.time()
        try:
            state = await self.manager.api.async_get_device_state(did)
        except AuthError:  # pylint: disable=try-except-raise
            raise
        except:
            device: HomePilotDevice = self.manager.devices[did]
            device.available = False
            raise
        await self._async_apply_device_state(did, state, ts)

    def get_last_state(self, did, default=None):
        """Get the most recent state of a device."""
        return self._states.get(did, default)
