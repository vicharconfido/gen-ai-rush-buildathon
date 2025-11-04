from __future__ import annotations

from typing import Dict, Optional

from .retell_client import MonthlyUsageRequest, RetellClient


class UsageService:
    """Higher level abstraction to work with Retell usage data."""

    def __init__(self, client: RetellClient) -> None:
        self._client = client

    async def get_monthly_usage(
        self,
        *,
        year: int,
        month: int,
        team_id: Optional[str] = None,
        api_key_override: Optional[str] = None,
    ) -> Dict[str, object]:
        request = MonthlyUsageRequest(year=year, month=month, team_id=team_id)
        payload = await self._client.get_monthly_usage(
            request, api_key=api_key_override
        )
        return payload
