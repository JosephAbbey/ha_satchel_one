"""Satchel One calendar platform."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.calendar import (
    CalendarEntity,
    CalendarEvent,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .const import (
    DOMAIN,
)
from .api import AsyncConfigEntryAuth
from .coordinator import CalendarUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the satchel one platform."""
    api: AsyncConfigEntryAuth = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            SatchelOneCalendarEntity(
                CalendarUpdateCoordinator(hass, api),
                entry.entry_id,
            )
        ]
    )


class SatchelOneCalendarEntity(
    CoordinatorEntity[CalendarUpdateCoordinator],
    CalendarEntity,
):
    """A calendar event entity."""

    _attr_name = "Timetable"
    _attr_has_entity_name = True
    _attr_supported_features = 0

    def __init__(
        self,
        coordinator: CalendarUpdateCoordinator,
        config_entry_id: str,
    ) -> None:
        """Create the Calendar event device."""
        super().__init__(coordinator)
        self._attr_unique_id = config_entry_id

    def _convert_event(self, event: dict[str, Any]):
        return CalendarEvent(
            uid=event["id"],
            summary=event["classGroup"]["subject"],
            start=datetime.fromisoformat(event["period"]["startDateTime"]),
            end=datetime.fromisoformat(event["period"]["endDateTime"]),
            description=event["classGroup"]["name"]
            + " \n"
            + event["teacher"]["title"]
            + " "
            + event["teacher"]["forename"]
            + " "
            + event["teacher"]["surname"],
            location=event["room"],
        )

    @property
    def extra_state_attributes(self) -> dict[str, bool]:
        """Return the device state attributes."""
        if self.event is None:
            return {}
        if self.event.description is None:
            return {
                "subject": self.event.summary,
                "room": self.event.location,
            }
        parts = self.event.description.split(" \n")
        return {
            "subject": self.event.summary,
            "room": self.event.location,
            "class": parts[0],
            "teacher": parts[1],
        }

    @property
    def offset_reached(self) -> bool:
        """Return whether or not the event offset was reached."""
        return (
            self.coordinator.upcoming is not None and len(self.coordinator.upcoming) > 0
        ) and (
            datetime.fromisoformat(
                self.coordinator.upcoming[0]["period"]["startDateTime"]
            )
            <= datetime.now()
        )

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        if self.coordinator.upcoming is not None and len(self.coordinator.upcoming) > 0:
            return self._convert_event((self.coordinator.upcoming or [])[0])
        else:
            return None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Get all events in a specific time frame."""
        lessons = await self.coordinator.api.list_lessons(start_date, end_date)
        return [self._convert_event(event) for event in lessons]
