"""Coordinator for fetching data from Satchel One API."""

import asyncio
import datetime
import logging
from typing import Any, Final
from collections.abc import Iterable

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import AsyncConfigEntryAuth

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL: Final = datetime.timedelta(minutes=5)
TIMEOUT = 10


class TaskUpdateCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Coordinator for fetching Satchel One for a Task List form the API."""

    def __init__(
        self, hass: HomeAssistant, api: AsyncConfigEntryAuth
    ) -> None:
        """Initialize TaskUpdateCoordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Satchel One",
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Fetch tasks from API endpoint."""
        async with asyncio.timeout(TIMEOUT):
            return await self.api.list_tasks()

class CalendarUpdateCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Coordinator for fetching Satchel One for a Lessons List form the API."""

    def __init__(
        self, hass: HomeAssistant, api: AsyncConfigEntryAuth
    ) -> None:
        """Initialize TaskUpdateCoordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Satchel One",
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Fetch lessons from API endpoint."""
        async with asyncio.timeout(TIMEOUT):
            return await self.api.list_lessons(datetime.datetime.now(), datetime.datetime.now())

    @property
    def upcoming(self) -> Iterable[dict[str, Any]] | None:
        """Return the next upcoming event if any."""
        return self.data
