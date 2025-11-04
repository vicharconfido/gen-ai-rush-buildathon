from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional

import httpx

from ..config import Settings


class RetellAPIError(RuntimeError):
    """Raised when the Retell API returns an unexpected response."""


@dataclass
class MonthlyUsageRequest:
    year: int
    month: int
    team_id: Optional[str] = None

    @property
    def start_date(self) -> date:
        return date(self.year, self.month, 1)

    @property
    def end_date(self) -> date:
        last_day = calendar.monthrange(self.year, self.month)[1]
        return date(self.year, self.month, last_day)


class RetellClient:
    """Simple async client for interacting with the Retell usage API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._default_api_key = settings.retell_api_key
        self._client = httpx.AsyncClient(
            base_url=str(settings.retell_base_url),
            headers={"Content-Type": "application/json"},
            timeout=settings.request_timeout_seconds,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def get_monthly_usage(
        self, request: MonthlyUsageRequest, *, api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {
            "granularity": "month",
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
        }
        if request.team_id:
            params["team_id"] = request.team_id

        key = api_key or self._default_api_key
        if not key:
            raise RetellAPIError("A Retell API key is required to fetch usage data.")

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

        response = await self._client.get("/usage", params=params, headers=headers)
        if response.status_code != httpx.codes.OK:
            raise RetellAPIError(
                f"Retell API returned status {response.status_code}: {response.text}"
            )

        payload = response.json()
        if "data" not in payload:
            raise RetellAPIError("Unexpected response format: missing 'data' key")

        return payload
