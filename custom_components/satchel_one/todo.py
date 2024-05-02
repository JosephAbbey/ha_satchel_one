"""Satchel One todo platform."""

from __future__ import annotations

from datetime import datetime
from typing import cast

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import AsyncConfigEntryAuth
from .const import DOMAIN
from .coordinator import TaskUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Satchel One todo platform."""
    api: AsyncConfigEntryAuth = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            SatchelOneTodoListEntity(
                TaskUpdateCoordinator(hass, api),
                entry.entry_id,
            )
        ],
        True,
    )


class SatchelOneTodoListEntity(
    CoordinatorEntity[TaskUpdateCoordinator], TodoListEntity
):
    """A To-do List representation of the Shopping List."""

    _attr_name = "Homework"
    _attr_has_entity_name = True
    _attr_supported_features = TodoListEntityFeature.UPDATE_TODO_ITEM

    def __init__(
        self,
        coordinator: TaskUpdateCoordinator,
        config_entry_id: str,
    ) -> None:
        """Initialize LocalTodoListEntity."""
        super().__init__(coordinator)
        self._attr_unique_id = config_entry_id

    @property
    def todo_items(self) -> list[TodoItem] | None:
        """Get the current set of To-do items."""
        if self.coordinator.data is None:
            return None
        return sorted([
          TodoItem(
            uid=str(item["id"]),
            due=datetime.fromisoformat(item["due_on"]).date(),
            status=TodoItemStatus.COMPLETED if item["completed"] else TodoItemStatus.NEEDS_ACTION,
            summary=item["class_task_title"],
            description=f"{item['class_task_type']} - {item['subject']} - {item['teacher_name']} - {item['class_task_description']}",
          ) for item in self.coordinator.data], key=lambda x: x.due)

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update a To-do item."""
        uid: str = cast(str, item.uid)
        await self.coordinator.api.put_task(
            uid,
            task={
                "completed": item.status == TodoItemStatus.COMPLETED
            }
        )
        await self.coordinator.async_refresh()
