"""Config flow for Ring Extended integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.ring import DOMAIN as RING_DOMAIN
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import CATEGORY_NAMES, DOMAIN, SENSOR_CATEGORIES

_LOGGER = logging.getLogger(__name__)


class RingExtendedConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ring Extended."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        # Check if Ring integration is configured (check config entries, not hass.data)
        ring_entries = [
            entry for entry in self.hass.config_entries.async_entries()
            if entry.domain == RING_DOMAIN
        ]
        if not ring_entries:
            return self.async_abort(reason="ring_not_configured")

        # Check if already configured
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            categories = user_input.get("categories", [])
            if not categories:
                errors["categories"] = "no_categories_selected"
            else:
                return self.async_create_entry(
                    title="Ring Extended Sensors",
                    data={"categories": categories},
                )

        # Build category options
        category_options = [
            selector.SelectOptionDict(value=cat, label=CATEGORY_NAMES.get(cat, cat))
            for cat in SENSOR_CATEGORIES
        ]

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "categories", default=SENSOR_CATEGORIES
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=category_options,
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return RingExtendedOptionsFlow(config_entry)


class RingExtendedOptionsFlow(OptionsFlow):
    """Handle options flow for Ring Extended."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            categories = user_input.get("categories", [])
            if not categories:
                errors["categories"] = "no_categories_selected"
            else:
                # Update the config entry data
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={"categories": categories},
                )
                return self.async_create_entry(title="", data={})

        # Get current categories
        current_categories = self.config_entry.data.get("categories", SENSOR_CATEGORIES)

        # Build category options
        category_options = [
            selector.SelectOptionDict(value=cat, label=CATEGORY_NAMES.get(cat, cat))
            for cat in SENSOR_CATEGORIES
        ]

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "categories", default=current_categories
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=category_options,
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
            errors=errors,
        )
