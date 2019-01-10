"""
This component provides light support for the Magicblue bluetooth bulbs.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.magicblue/
"""
import asyncio
import logging

import voluptuous as vol
from homeassistant.util import Throttle
from datetime import timedelta
from functools import partial

# Import the device class from the component that you want to support
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ATTR_RGB_COLOR, ATTR_HS_COLOR, SUPPORT_COLOR,
    SUPPORT_BRIGHTNESS, SUPPORT_WHITE_VALUE, ATTR_WHITE_VALUE, Light, PLATFORM_SCHEMA)

import homeassistant.helpers.config_validation as cv
import homeassistant.util.color as color_util

# Home Assistant depends on 3rd party packages for API specific code.
REQUIREMENTS = ['magicblue==0.6.0']

CONF_NAME = 'name'
CONF_ADDRESS = 'address'
CONF_VERSION = 'version'

MODE_WHITE = 'white'
MODE_COLOR = 'color'

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_ADDRESS): cv.string,
    vol.Optional(CONF_VERSION, default=9): cv.positive_int
})

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the MagicBlue platform."""
    from magicblue import MagicBlue

    # Assign configuration variables. The configuration check
    # takes care they are present.
    bulb_name = config.get(CONF_NAME)
    bulb_mac_address = config.get(CONF_ADDRESS)
    bulb_version = config.get(CONF_VERSION)

    bulb = MagicBlue(bulb_mac_address, bulb_version)

    # Add devices
    async_add_entities([MagicBlueLight(bulb, bulb_name)], update_before_add=True)


class MagicBlueLight(Light):
    """Representation of an MagicBlue Light."""

    def __init__(self, light, name):
        """Initialize an MagicBlueLight."""
        self._light = light
        self._name = name
        self._state = False
        self._rgb = (255, 255, 255)
        self._brightness = 255
        self._white_value = 255
        self._mode = MODE_WHITE

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def rgb_color(self):
        """Return the RBG color value."""
        return self._rgb

    @property
    def hs_color(self):
        """Return the HS color value."""
        (hue, sat, val) = color_util.color_RGB_to_hsv(*self._rgb)
        return (hue, sat)

    @property
    def brightness(self):
        """Return the brightness of the light (integer 1-255)."""
        return self._brightness

    @property
    def white_value(self):
        """Return the white value of the light (integer 1-255)."""
        return self._white_value

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state

    @property
    def supported_features(self):
        """Return the supported features."""
        return SUPPORT_BRIGHTNESS | SUPPORT_COLOR | SUPPORT_WHITE_VALUE

    #@Throttle(timedelta(seconds=1))
    async def async_turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        try:
            connected = await self.hass.async_add_job(self._light.test_connection)
            if not connected: 
                connection = await self.hass.async_add_job(self._light.connect)
        except Exception as err:  # pylint: disable=broad-except
            error_message = 'Connection failed for magicblue %s: %s'
            _LOGGER.error(error_message, self._name, err)
            return

        if not self._state:
            await self.hass.async_add_job(self._light.turn_on)

        if ATTR_HS_COLOR in kwargs:
            self._mode = MODE_COLOR
            brightness_pct = (100.0 * self._brightness) / 255.0
            hue = kwargs[ATTR_HS_COLOR][0]
            sat = kwargs[ATTR_HS_COLOR][1]
            self._rgb = color_util.color_hsv_to_RGB(hue, sat, brightness_pct)
            self._white_value = 0
            self._light.set_color(self._rgb)
            await self.hass.async_add_job(partial(self._light.set_color, self._rgb))
            _LOGGER.debug('setting color to %s', self._rgb)

        elif ATTR_RGB_COLOR in kwargs:
            self._mode = MODE_COLOR
            normalised_rgb = kwargs[ATTR_RGB_COLOR]
            brightness_fraction = self._brightness / 255.0
            self._rgb = tuple( c / brightness_fraction for c in normalised_rgb)
            self._white_value = 0
            #(h, s, v) = color_util.color_RGB_to_hsv(*self._rgb)
            #self._brightness = v * 255 / 100
            await self.hass.async_add_job(partial(self._light.set_color, self._rgb))
            _LOGGER.debug('setting color to %s', self._rgb)

        elif ATTR_WHITE_VALUE in kwargs:
            self._mode = MODE_WHITE
            self._rgb = (0, 0, 0)
            self._white_value = kwargs[ATTR_WHITE_VALUE]
            self._brightness = kwargs[ATTR_WHITE_VALUE]
            self._light.turn_on(self._brightness / 255)
            await self.hass.async_add_job(partial(self._light.turn_on, self._brightness / 255))
            _LOGGER.debug('setting brightness to %s', self._brightness)

        elif ATTR_BRIGHTNESS in kwargs:
            # if we are in white mode, just 
            if (self._mode == MODE_WHITE):
                self._white_value = kwargs[ATTR_BRIGHTNESS]
                self._brightness = kwargs[ATTR_BRIGHTNESS]
                await self.hass.async_add_job(partial(self._light.turn_on, self._brightness / 255))
                _LOGGER.debug('setting brightness to %s', self._brightness)
            else:
                brightness_pct = (100.0 * kwargs[ATTR_BRIGHTNESS]) / 255.0
                (hue, sat, val) = color_util.color_RGB_to_hsv(*self._rgb)
                self._rgb = color_util.color_hsv_to_RGB(hue, sat, brightness_pct)
                self._brightness = kwargs[ATTR_BRIGHTNESS]
                await self.hass.async_add_job(partial(self._light.set_color, self._rgb))
                _LOGGER.debug('setting color to %s', self._rgb)

        self._state = True

    #@Throttle(timedelta(seconds=1))
    async def async_turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        try:
            connected = await self.hass.async_add_job(self._light.test_connection)
            if not connected: 
                connection = await self.hass.async_add_job(self._light.connect)
        except Exception as err:  # pylint: disable=broad-except
            error_message = 'Connection failed for magicblue %s: %s'
            _LOGGER.error(error_message, self._name, err)
            return

        await self.hass.async_add_job(self._light.turn_off)
        self._state = False

    async def async_update(self):
        try:
            connected = await self.hass.async_add_job(self._light.test_connection)
            if not connected: 
                connection = await self.hass.async_add_job(self._light.connect)
        except Exception as err:  # pylint: disable=broad-except
            error_message = 'Connection failed for magicblue %s: %s'
            _LOGGER.error(error_message, self._name, err)
            return
        info = await self.hass.async_add_job(self._light.get_device_info)
        _LOGGER.debug('light info %s', info)
        self._white_value = info['brightness']
        self._rgb = (info['r'], info['g'], info['b'])
        self._state = info['on']
        if (self._state):
            if( self._white_value > 0):
                self._mode = MODE_WHITE
                self._brightness = self._white_value
            else:
                self._mode = MODE_COLOR
                (h, s, v) = color_util.color_RGB_to_hsv(*self._rgb)
                self._brightness = v * 255 / 100

                _LOGGER.debug('got rgb of %s', self._rgb)
                _LOGGER.debug('calculated brightness as %s', self._brightness)
