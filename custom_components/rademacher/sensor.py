"""Platform for Rademacher Bridge."""
from enum import Enum
import logging

from homepilot.device import HomePilotDevice
from homepilot.sensor import ContactState, HomePilotSensor
from homepilot.thermostat import HomePilotThermostat

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    CONF_EXCLUDE,
    CONF_SENSOR_TYPE,
    DEGREE,
    LIGHT_LUX,
    PERCENTAGE,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import HomePilotEntity
from .state_manager import StateManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup of entities for sensor platform."""
    state_manager: StateManager = hass.data[DOMAIN][config_entry.entry_id]
    manager = state_manager.manager
    exclude_devices: list[str] = state_manager.entry_options[CONF_EXCLUDE]
    ternary_contact_sensors: list[str] = state_manager.entry_options[CONF_SENSOR_TYPE]
    new_entities = []
    for did in manager.devices:
        if did not in exclude_devices:
            device: HomePilotDevice = manager.devices[did]
            if isinstance(device, HomePilotSensor):
                if device.has_temperature:
                    _LOGGER.info(
                        "Found Temperature Sensor for Device ID: %s", device.did
                    )
                    new_entities.append(
                        HomePilotSensorEntity(
                            state_manager=state_manager,
                            device=device,
                            id_suffix="temp",
                            name_suffix="Temperature",
                            value_attr="temperature_value",
                            device_class=SensorDeviceClass.TEMPERATURE.value,
                            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                        )
                    )
                if device.has_target_temperature:
                    _LOGGER.info(
                        "Found Target Temperature Sensor for Device ID: %s", device.did
                    )
                    new_entities.append(
                        HomePilotSensorEntity(
                            state_manager=state_manager,
                            device=device,
                            id_suffix="target_temp",
                            name_suffix="Target Temperature",
                            value_attr="target_temperature_value",
                            device_class=SensorDeviceClass.TEMPERATURE.value,
                            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                        )
                    )
                if device.has_wind_speed:
                    _LOGGER.info(
                        "Found Wind Speed Sensor for Device ID: %s", device.did
                    )
                    new_entities.append(
                        HomePilotSensorEntity(
                            state_manager=state_manager,
                            device=device,
                            id_suffix="wind_speed",
                            name_suffix="Wind Speed",
                            value_attr="wind_speed_value",
                            native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
                            icon="mdi:weather-windy",
                        )
                    )
                if device.has_brightness:
                    _LOGGER.info(
                        "Found Brightness Sensor for Device ID: %s", device.did
                    )
                    new_entities.append(
                        HomePilotSensorEntity(
                            state_manager=state_manager,
                            device=device,
                            id_suffix="brightness",
                            name_suffix="Brightness",
                            value_attr="brightness_value",
                            device_class=SensorDeviceClass.ILLUMINANCE.value,
                            native_unit_of_measurement=LIGHT_LUX,
                        )
                    )
                if device.has_sun_height:
                    _LOGGER.info(
                        "Found Sun Height Sensor for Device ID: %s", device.did
                    )
                    new_entities.append(
                        HomePilotSensorEntity(
                            state_manager=state_manager,
                            device=device,
                            id_suffix="sun_height",
                            name_suffix="Sun Height",
                            value_attr="sun_height_value",
                            native_unit_of_measurement=DEGREE,
                            icon="mdi:weather-sunset-up",
                        )
                    )
                if device.has_sun_direction:
                    _LOGGER.info(
                        "Found Sun Direction Sensor for Device ID: %s", device.did
                    )
                    new_entities.append(
                        HomePilotSensorEntity(
                            state_manager=state_manager,
                            device=device,
                            id_suffix="sun_direction",
                            name_suffix="Sun Direction",
                            value_attr="sun_direction_value",
                            native_unit_of_measurement=DEGREE,
                            icon="mdi:sun-compass",
                        )
                    )
                if device.has_contact_state and device.did in ternary_contact_sensors:
                    _LOGGER.info("Found Contact Sensor for Device ID: %s", device.did)
                    new_entities.append(
                        HomePilotSensorEntity(
                            state_manager=state_manager,
                            device=device,
                            device_class=SensorDeviceClass.ENUM.value,
                            id_suffix="contact_state",
                            name_suffix="Contact State",
                            value_attr="contact_state_value",
                            state_class=None,
                            icon_template=lambda val: "mdi:square-outline"
                            if val == ContactState.OPEN
                            else (
                                "mdi:network-strength-outline"
                                if val == ContactState.TILTED
                                else "mdi:square"
                            ),
                            options=["Open", "Tilted", "Closed"]
                        )
                    )
            if isinstance(device, (HomePilotSensor, HomePilotThermostat)):
                if device.has_battery_level:
                    _LOGGER.info(
                        "Found Battery Level Sensor for Device ID: %s", device.did
                    )
                    new_entities.append(
                        HomePilotSensorEntity(
                            state_manager=state_manager,
                            device=device,
                            id_suffix="battery_level",
                            name_suffix="Battery Level",
                            value_attr="battery_level_value",
                            device_class=SensorDeviceClass.BATTERY,
                            native_unit_of_measurement=PERCENTAGE,
                            entity_category=EntityCategory.DIAGNOSTIC,
                        )
                    )
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class HomePilotSensorEntity(HomePilotEntity, SensorEntity):
    """This class represents all Sensors supported."""

    def __init__(
        self,
        state_manager: StateManager,
        device: HomePilotSensor,
        id_suffix,
        name_suffix,
        value_attr,
        device_class=None,
        native_unit_of_measurement=None,
        icon=None,
        icon_template=None,
        entity_category=None,
        options=None,
        state_class=SensorStateClass.MEASUREMENT
    ) -> None:
        super().__init__(
            state_manager,
            device,
            unique_id=f"{device.uid}_f{id_suffix}",
            name=f"{device.name} {name_suffix}",
            device_class=device_class,
            icon=icon,
            entity_category=entity_category,
        )
        self._value_attr = value_attr
        self._icon_template = icon_template
        self._attr_native_unit_of_measurement = native_unit_of_measurement
        self._attr_options = options
        self._attr_state_class = state_class

    @property
    def value_attr(self):
        """This property stores which attribute contains the is_on value on
        the HomePilotDevice supporting class.
        """
        return self._value_attr

    @property
    def native_value(self):
        value = getattr(self.coordinator.data[self.did], self.value_attr)
        return value.name.capitalize() if isinstance(value, Enum) else value

    @property
    def icon(self):
        if self._icon_template is not None:
            return self._icon_template(
                getattr(self.coordinator.data[self.did], self.value_attr)
            )
        return super().icon
