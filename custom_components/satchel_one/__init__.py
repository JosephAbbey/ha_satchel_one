"""The Satchel One integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant

from . import api
from .const import DOMAIN, CONF_SCHOOL, CONF_STUDENT

PLATFORMS: list[Platform] = [Platform.TODO, Platform.CALENDAR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Satchel One from a config entry."""
    auth = api.AsyncConfigEntryAuth(
        hass,
        school=entry.data[CONF_SCHOOL],
        student=entry.data[CONF_STUDENT],
        access_token=entry.data[CONF_ACCESS_TOKEN],
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = auth

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
