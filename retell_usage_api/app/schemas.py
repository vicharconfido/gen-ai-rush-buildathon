from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, constr, validator


class UsageMetric(BaseModel):
    period_start: date = Field(..., description="First day of the month covered by the data")
    period_end: date = Field(..., description="Last day of the month covered by the data")
    value: float = Field(..., description="Primary usage metric reported by Retell")
    raw: Dict[str, Any] = Field(
        default_factory=dict,
        description="Full payload returned by Retell for this period",
    )


class MonthlyUsageResponse(BaseModel):
    month: str = Field(..., description="ISO formatted month, e.g. 2024-05")
    metrics: List[UsageMetric] = Field(
        default_factory=list, description="Usage metrics reported for the month"
    )
    source_payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Complete raw response received from Retell",
    )


class MonthlyUsageQuery(BaseModel):
    month: constr(regex=r"^\d{4}-\d{2}$") = Field(
        ..., description="Target month formatted as YYYY-MM"
    )
    retell_api_key: str = Field(..., min_length=1, description="Retell API key")
    team_id: Optional[str] = Field(
        default=None, description="Optional Retell team identifier"
    )

    @validator("month")
    def _validate_month(cls, value: str) -> str:
        year, month = value.split("-")
        year_int = int(year)
        month_int = int(month)
        if not (2000 <= year_int <= 3000):
            raise ValueError("Year must be between 2000 and 3000")
        if not (1 <= month_int <= 12):
            raise ValueError("Month must be between 01 and 12")
        return value
