from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class Metadata(BaseModel):
    source: dict[str, str]
    retrieved_at: datetime
    timezone: str = "UTC"
    stale: bool = False


class Period(BaseModel):
    model_config = ConfigDict(extra="allow")

    from_: datetime
    to: datetime
    region_id: int
    region_name: str
    region_type: str
    forecast: int | None = None
    actual: int | None = None
    index: str | None = None
    forecast_classification: str | None = None
    actual_classification: str | None = None
    generation_mix: list[dict[str, Any]] = []


class DataEnvelope(BaseModel):
    data: list[dict[str, Any]]
    metadata: dict[str, Any]
