"""API for Satchel One."""

import logging
from typing import Any, Literal
from datetime import datetime, timedelta
import itertools
import asyncio

from homeassistant.core import HomeAssistant

import requests

from .exceptions import SatchelOneApiError
from .const import API_URL


def headers(access_token):
    """Return headers for Satchel One API requests."""
    return {
        "Accept": "application/smhw.v2021.5+json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }


_LOGGER = logging.getLogger(__name__)

MAX_TASK_RESULTS = 100


def flatten(it):
    """Flatten an iterable."""
    return itertools.chain.from_iterable(it)


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
        school: str,
        student: str,
        access_token: str,
    ) -> None:
        """Initialize Satchel One Auth."""
        self._hass = hass
        self._school = school
        self._student = student
        self._access_token = access_token

    async def get_user_data(self):
        """Get information about the user."""
        result = await self._execute(
            "GET",
            f"/students/{self._student}?include=user_private_info%2Cschool%2Cpackage%2Cpremium_features",
        )
        return result

    async def list_lessons(self, start: datetime, end: datetime):
        """Get this week's lessons."""
        futures = []
        week = start - timedelta(days=start.weekday())
        while week < end:
            futures.append(
                self._execute(
                    "GET",
                    f"/timetable/school/{self._school}/student/{self._student}?requestDate={week.strftime('%Y-%m-%d')}",
                )
            )
            week += timedelta(days=7)
        results = list(await asyncio.gather(*futures))
        flat = list(
            flatten(
                d["lessons"] for d in flatten(r["weeks"][0]["days"] for r in results)
            )
        )
        i = 0
        while i < len(flat) and start > datetime.fromisoformat(
            flat[i]["period"]["endDateTime"]
        ):
            i += 1
        a = i
        while i < len(flat) and end > datetime.fromisoformat(
            flat[i]["period"]["startDateTime"]
        ):
            i += 1
        return flat[a:i]

    async def list_tasks(self) -> list[dict[str, Any]]:
        """Get all Task resources for the task list."""
        result = await self._execute(
            "GET",
            f"/todos?add_dateless=true&from={datetime.now().strftime('%Y-%m-%d')}&to=3000-01-01",
        )
        return result["todos"]

    async def put_task(
        self,
        task_id: str,
        task: dict[str, Any],
    ) -> None:
        """Update a task resource."""
        await self._execute("PUT", f"/todos/{task_id}", json={"todo": task})

    async def _execute(
        self,
        method: (
            Literal["GET"]
            | Literal["POST"]
            | Literal["PUT"]
            | Literal["DELETE"]
            | Literal["OPTIONS"]
            | Literal["PATCH"]
            | Literal["HEAD"]
        ),
        path: str,
        json: Any | None = None,
    ) -> Any:
        try:
            result = await self._hass.async_add_executor_job(
                lambda: requests.request(
                    method,
                    API_URL + path,
                    json=json,
                    headers=headers(self._access_token),
                    timeout=10,
                )
            )
        except requests.ConnectionError as err:
            raise SatchelOneApiError("Could not connect to Satchel One API") from err
        except requests.Timeout as err:
            raise SatchelOneApiError("Timeout connecting to Satchel One API") from err
        r = None
        try:
            r = result.json()
        except requests.JSONDecodeError:
            r = result.text
        if r:
            _raise_if_error(r)
        return r
