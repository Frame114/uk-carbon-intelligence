import asyncio
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.dependencies import get_neso_client
from app.api.v1.endpoints.common import resolve_range
from app.clients.neso import NesoApiError, NesoClient
from app.services.normalization import ProviderDataError
from app.services.presentation import clip_periods, metadata, national_periods, regional_periods
from app.utils.regions import get_region

router = APIRouter(prefix="/statistics", tags=["Statistics"])


def describe(values: list[int]) -> dict:
    if not values:
        return {"count": 0, "average": None, "minimum": None, "maximum": None}
    return {
        "count": len(values),
        "average": round(sum(values) / len(values), 2),
        "minimum": min(values),
        "maximum": max(values),
    }


@router.get("/summary", summary="Summarize GB intensity for a time range")
async def summary(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    client: NesoClient = Depends(get_neso_client),
):
    start, end = resolve_range(start, end)
    try:
        payload = await client.national_history(start, end)
        periods = clip_periods(national_periods(payload), start, end)
        actuals = [item["actual"] for item in periods if item["actual"] is not None]
        forecasts = [item["forecast"] for item in periods if item["forecast"] is not None]
        return {
            "data": {
                "region_id": 18,
                "region_name": "Great Britain",
                "from": start,
                "to": end,
                "actual": describe(actuals),
                "forecast": describe(forecasts),
                "method": (
                    "Arithmetic summary of provider observations within the requested UTC range; "
                    "actual and forecast are kept separate."
                ),
            },
            "metadata": metadata(),
        }
    except (NesoApiError, ProviderDataError) as exc:
        raise HTTPException(
            status_code=503, detail={"code": "provider_unavailable", "message": str(exc)}
        ) from exc


@router.get("/regional-comparison", summary="Compare regional provider forecasts")
async def regional_comparison(
    region_ids: list[int] = Query(default=[1, 2, 16, 18], min_length=2, max_length=6),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    client: NesoClient = Depends(get_neso_client),
):
    if len(set(region_ids)) != len(region_ids):
        raise HTTPException(
            status_code=422,
            detail={"code": "duplicate_region", "message": "region_ids must be unique."},
        )
    start, end = resolve_range(start or datetime.now(UTC) - timedelta(hours=24), end)
    try:
        history_payload, current_payload = await asyncio.gather(
            client.regional_history(start, end),
            client.regional_current(),
        )
        periods = clip_periods(regional_periods(history_payload), start, end)
        current_by_region = {item["region_id"]: item for item in regional_periods(current_payload)}
        output = []
        for region_id in region_ids:
            selected = sorted(
                (
                    item
                    for item in periods
                    if item["region_id"] == region_id and item["forecast"] is not None
                ),
                key=lambda item: item["from"],
            )
            values = [item["forecast"] for item in selected]
            current = current_by_region.get(region_id)
            last_in_range = selected[-1] if selected else None
            summary = describe(values)
            summary.update(
                {
                    "region_id": region_id,
                    "region_name": (current or last_in_range)["region_name"]
                    if current or last_in_range
                    else get_region(region_id).name,
                    "current_forecast": current["forecast"] if current else None,
                    "trend_change": values[-1] - values[0] if len(values) > 1 else None,
                }
            )
            output.append(summary)
        return {
            "data": output,
            "metadata": {
                **metadata(),
                "comparison_basis": (
                    "Provider regional forecasts only; no unweighted regional average is used."
                ),
                "from": start,
                "to": end,
            },
        }
    except (NesoApiError, ProviderDataError, ValueError) as exc:
        raise HTTPException(
            status_code=503, detail={"code": "provider_unavailable", "message": str(exc)}
        ) from exc
