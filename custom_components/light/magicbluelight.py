"""
This component provides light support for the Magicblue bluetooth bulbs.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.magicblue/
"""
import logging

import voluptuous as vol
from homeassistant.util import Throttle
from datetime import timedelta

# Import the device class from the component that you want to support
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ATTR_RGB_COLOR, ATTR_HS_COLOR, SUPPORT_COLOR,
    SUPPORT_BRIGHTNESS, Light, PLATFORM_SCHEMA)

import homeassistant.helpers.config_validation as cv
import homeassistant.util.color as color_util

# Home Assistant depends on 3rd party packages for API specific code.
REQUIREMENTS = ['magicblue==0.6.0']

CONF_NAME = 'name'
CONF_ADDRESS = 'address'
CONF_VERSION = 'version'

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_ADDRESS): cv.string,
    vol.Optional(CONF_VERSION, default=9): cv.positive_int
})

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the MagicBlue platform."""
    from magicblue import MagicBlue

    # Assign configuration variables. The configuration check
    # takes care they are present.
    bulb_name = config.get(CONF_NAME)
    bulb_mac_address = config.get(CONF_ADDRESS)
    bulb_version = config.get(CONF_VERSION)

    bulb = MagicBlue(bulb_mac_address, bulb_version)

    # Add devices
    add_devices([MagicBlueLight(bulb, bulb_name)])


class MagicBlueLight(Light):
    """Representation of an MagicBlue Light."""

    def __init__(self, light, name):
        """Initialize an MagicBlueLight."""
        self._light = light
        self._name = name
        self._state = False
        self._rgb = (255, 255, 255)
        self._brightness = 255

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def rgb_color(self):
        """Return the RBG color value."""
        return self._rgb

    @property
    def brightness(self):
        """Return the brightness of the light (integer 1-255)."""
        return self._brightness

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state

    @property
    def supported_features(self):
        """Return the supported features."""
        return SUPPORT_BRIGHTNESS | SUPPORT_COLOR

    @Throttle(timedelta(seconds=1))
    def turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        if not self._light.test_connection():
            try:
                self._light.connect()
            except Exception as err:  # pylint: disable=broad-except
                error_message = 'Connection failed for magicblue %s: %s'
                _LOGGER.error(error_message, self._name, err)
                return

        if not self._state:
            self._light.turn_on()

        if ATTR_HS_COLOR in kwargs:
            brightness = (100.0 * self._brightness) / 255.0
            hue = kwargs[ATTR_HS_COLOR][0]
            sat = kwargs[ATTR_HS_COLOR][1]
            self._rgb = color_util.color_hsv_to_RGB(hue, sat, brightness)
            self._light.set_color(self._rgb)

        elif ATTR_RGB_COLOR in kwargs:
            self._rgb = kwargs[ATTR_RGB_COLOR]
            self._brightness = 255
            self._light.set_color(self._rgb)

        elif ATTR_BRIGHTNESS in kwargs:
            self._rgb = (255, 255, 255)
            self._brightness = kwargs[ATTR_BRIGHTNESS]
            self._light.turn_on(self._brightness / 255)

        self._state = True

    @Throttle(timedelta(seconds=1))
    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        if not self._light.test_connection():
            try:
                self._light.connect()
            except Exception as err:  # pylint: disable=broad-except
                error_message = 'Connection failed for magicblue %s: %s'
                _LOGGER.error(error_message, self._name, err)
                return

        self._light.turn_off()
        self._state = False

    def update(self):
        _LOGGER.warn('light update is taking place')
        if not self._light.test_connection():
            try:
                self._light.connect()
            except Exception as err:  # pylint: disable=broad-except
                error_message = 'Connection failed for magicblue %s: %s'
                _LOGGER.error(error_message, self._name, err)
                return
        info = self._light.get_device_info()
        _LOGGER.warn('light info ', info)
        _LOGGER.warn('brightness ', info.brightness)
        _LOGGER.warn('r ', info.r)
        self._brightness = info.brightness
        self._rgb = (info.r, info.g, info.b)

