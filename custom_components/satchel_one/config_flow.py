"""Config flow for Satchel One."""


import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.helpers import selector

from .api import AsyncConfigEntryAuth
from .const import DOMAIN
from .exceptions import SatchelOneApiError

_LOGGER = logging.getLogger(__name__)

class SatchelOneConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Satchel One."""
    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                await self._test_credentials(
                    user_input[CONF_ACCESS_TOKEN],
                )
            except SatchelOneApiError as exception:
                _LOGGER.warning(exception)
                _errors["base"] = "api"
            else:
                return self.async_create_entry(
                    title="Satchel One",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ACCESS_TOKEN): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        ),
                    ),
                }
            ),
            errors=_errors,
        )

    async def _test_credentials(self, access_token: str) -> None:
        """Validate credentials."""
        client = AsyncConfigEntryAuth(
            self.hass,
            access_token=access_token,
        )
        await client.list_tasks()
