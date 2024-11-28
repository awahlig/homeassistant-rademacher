"""Platform for Rademacher Bridge."""
import logging

from homepilot.cover import HomePilotCover
from homepilot.device import HomePilotDevice
from homepilot.hub import HomePilotHub
from homepilot.switch import HomePilotSwitch

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.const import CONF_EXCLUDE
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import HomePilotEntity
from .state_manager import StateManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup of entities for switch platform."""
    state_manager: StateManager = hass.data[DOMAIN][config_entry.entry_id]
    manager = state_manager.manager
    exclude_devices: list[str] = state_manager.entry_options[CONF_EXCLUDE]
    new_entities = []
    for did in manager.devices:
        if did not in exclude_devices:
            device: HomePilotDevice = manager.devices[did]
            if isinstance(device, HomePilotHub):
                _LOGGER.info("Found Led Switch for Device ID: %s", device.did)
                new_entities.append(HomePilotLedSwitchEntity(state_manager, device))
                new_entities.append(HomePilotAutoUpdaeSwitchEntity(state_manager, device))
            if isinstance(device, HomePilotSwitch):
                _LOGGER.info("Found Switch for Device ID: %s", device.did)
                new_entities.append(HomePilotSwitchEntity(state_manager, device))
            if isinstance(device, HomePilotCover):
                cover: HomePilotCover = device
                if cover.has_ventilation_position_config:
                    _LOGGER.info("Found Ventilation Position Config Switch for Device ID: %s", device.did)
                    new_entities.append(HomePilotVentilationSwitchEntity(state_manager, device))
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class HomePilotSwitchEntity(HomePilotEntity, SwitchEntity):
    """This class represents all Switches supported."""

    def __init__(
        self, state_manager: StateManager, device: HomePilotDevice
    ) -> None:
        super().__init__(
            state_manager,
            device,
            unique_id=device.uid,
            name=device.name,
            device_class=SwitchDeviceClass.SWITCH.value,
        )

    @property
    def is_on(self):
        return self.coordinator.data[self.did].is_on

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        device: HomePilotSwitch = self.coordinator.data[self.did]
        await device.async_turn_on()
        await self.async_update_device_state()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        device: HomePilotSwitch = self.coordinator.data[self.did]
        await device.async_turn_off()
        await self.async_update_device_state()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()


class HomePilotLedSwitchEntity(HomePilotEntity, SwitchEntity):
    """This class represents the Led Switch which controls the LEDs on the hub."""

    def __init__(
        self, state_manager: StateManager, device: HomePilotDevice
    ) -> None:
        super().__init__(
            state_manager,
            device,
            unique_id=f"{device.uid}_led_status",
            name=f"{device.name} LED Status",
            device_class=SwitchDeviceClass.SWITCH.value,
            entity_category=EntityCategory.CONFIG,
        )

    @property
    def is_on(self):
        device: HomePilotHub = self.coordinator.data[self.did]
        return device.led_status

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        device: HomePilotHub = self.coordinator.data[self.did]
        await device.async_turn_led_on()
        await self.async_update_device_state()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        device: HomePilotHub = self.coordinator.data[self.did]
        await device.async_turn_led_off()
        await self.async_update_device_state()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()

class HomePilotAutoUpdaeSwitchEntity(HomePilotEntity, SwitchEntity):
    """This class represents the Led Switch which controls the LEDs on the hub."""

    def __init__(
        self, state_manager: StateManager, device: HomePilotDevice
    ) -> None:
        super().__init__(
            state_manager,
            device,
            unique_id=f"{device.uid}_auto_update",
            name=f"{device.name} Auto Update",
            device_class=SwitchDeviceClass.SWITCH.value,
            entity_category=EntityCategory.CONFIG,
        )

    @property
    def is_on(self):
        device: HomePilotHub = self.coordinator.data[self.did]
        return device.auto_update

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        device: HomePilotHub = self.coordinator.data[self.did]
        await device.async_set_auto_update_on()
        await self.async_update_device_state()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        device: HomePilotHub = self.coordinator.data[self.did]
        await device.async_set_auto_update_off()
        await self.async_update_device_state()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()

class HomePilotVentilationSwitchEntity(HomePilotEntity, SwitchEntity):
    """This class represents the Switch which controls Ventilation Position Mode."""

    def __init__(
        self, state_manager: StateManager, device: HomePilotDevice
    ) -> None:
        super().__init__(
            state_manager,
            device,
            unique_id=f"{device.uid}_ventilation_position_mode",
            name=f"{device.name} Ventilation Position Mode",
            device_class=SwitchDeviceClass.SWITCH.value,
            entity_category=EntityCategory.CONFIG,
        )

    @property
    def is_on(self):
        device: HomePilotCover = self.coordinator.data[self.did]
        return device.ventilation_position_mode

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        device: HomePilotCover = self.coordinator.data[self.did]
        await device.async_set_ventilation_position_mode(True)
        await self.async_update_device_state()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        device: HomePilotCover = self.coordinator.data[self.did]
        await device.async_set_ventilation_position_mode(False)
        await self.async_update_device_state()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()
