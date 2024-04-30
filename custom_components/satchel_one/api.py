"""API for Satchel One."""

import logging
from typing import Any
from datetime import datetime
import json

from homeassistant.core import HomeAssistant

import requests

from .exceptions import SatchelOneApiError
from .const import API_URL

def headers(access_token):
    return {
      "Accept": "application/smhw.v2021.5+json",
      "Content-Type": "application/json",
      "Authorization": f"Bearer {access_token}",
    }

_LOGGER = logging.getLogger(__name__)

MAX_TASK_RESULTS = 100


def _raise_if_error(result: Any | dict[str, Any]) -> None:
    """Raise a SatchelOneApiError if the response contains an error."""
    if not (isinstance(result, dict) or isinstance(result, list)):
        raise SatchelOneApiError(
            f"Satchel One API replied with unexpected response: {result}"
        )
    if error := result.get("error"):
        if isinstance(error, dict):
            message = error.get("message", "Unknown Error")
            raise SatchelOneApiError(f"Satchel One API response: {message}")
        if isinstance(error, str):
            raise SatchelOneApiError(f"Satchel One API response: {error}")
        raise SatchelOneApiError(f"Satchel One API response: {error}")


class AsyncConfigEntryAuth:
    """Provide Satchel One authentication tied to a config entry."""

    def __init__(
        self,
        hass: HomeAssistant,
        access_token: str,
    ) -> None:
        """Initialize Satchel One Auth."""
        self._hass = hass
        self._access_token = access_token

    async def list_tasks(self) -> list[dict[str, Any]]:
        """Get all Task resources for the task list."""
        result = await self._execute(lambda: requests.get(API_URL + f"/todos?add_dateless=true&from={datetime.now().strftime('%Y-%m-%d')}&to=2024-08-11", headers=headers(self._access_token), timeout=10).json())
        return result["todos"]

    async def put_task(
        self,
        task_id: str,
        task: dict[str, Any],
    ) -> None:
        """Update a task resource."""
        await self._execute(lambda: requests.put(API_URL + f"/todos/{task_id}", headers=headers(self._access_token), data=json.dumps({"todo": task}), timeout=10).text)

    async def _execute(self, request: callable) -> Any:
        try:
            result = await self._hass.async_add_executor_job(request)
        except requests.ConnectionError as err:
            raise SatchelOneApiError(
                "Could not connect to Satchel One API"
            ) from err
        except requests.Timeout as err:
            raise SatchelOneApiError(
                "Timeout connecting to Satchel One API"
            ) from err
        if result:
            _raise_if_error(result)
        return result
