from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.dependencies import get_neso_client
from app.api.v1.endpoints.common import period_floor, resolve_range
from app.clients.neso import NesoApiError, NesoClient
from app.services.normalization import ProviderDataError
from app.services.presentation import clip_periods, metadata, national_periods, regional_periods

router = APIRouter(prefix="/carbon-intensity", tags=["Carbon intensity"])


@router.get("/current", summary="Get current GB carbon intensity")
async def current(client: NesoClient = Depends(get_neso_client)):
    try:
        payload = await client.current()
        periods = national_periods(payload)
        if not periods:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "no_current_data",
                    "message": "NESO returned no current intensity.",
                },
            )
        return {"data": periods[:1], "metadata": metadata()}
    except (NesoApiError, ProviderDataError) as exc:
        raise HTTPException(
            status_code=503, detail={"code": "provider_unavailable", "message": str(exc)}
        ) from exc


@router.get("/forecast", summary="Get national carbon intensity forecast")
async def forecast(
    hours: int = Query(
        default=24,
        ge=24,
        le=48,
        description="Forecast horizon in hours; supported values are 24 or 48.",
    ),
    client: NesoClient = Depends(get_neso_client),
):
    if hours not in (24, 48):
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_horizon", "message": "hours must be 24 or 48."},
        )
    start = period_floor()
    try:
        payload = await client.national_forecast(start, hours)
        periods = clip_periods(national_periods(payload), start, start + timedelta(hours=hours))
        return {"data": periods, "metadata": metadata()}
    except (NesoApiError, ProviderDataError) as exc:
        raise HTTPException(
            status_code=503, detail={"code": "provider_unavailable", "message": str(exc)}
        ) from exc


@router.get("/history", summary="Get national or regional historical intensity")
async def history(
    start: datetime | None = Query(default=None, description="Inclusive UTC start time."),
    end: datetime | None = Query(default=None, description="Exclusive UTC end time."),
    region_id: int | None = Query(default=None, ge=1, description="Optional NESO region ID."),
    client: NesoClient = Depends(get_neso_client),
):
    start, end = resolve_range(start, end)
    try:
        if region_id is None:
            payload = await client.national_history(start, end)
            periods = national_periods(payload)
        else:
            payload = await client.region_history(region_id, start, end)
            periods = regional_periods(payload)
        return {"data": clip_periods(periods, start, end), "metadata": metadata()}
    except (NesoApiError, ProviderDataError) as exc:
        raise HTTPException(
            status_code=503, detail={"code": "provider_unavailable", "message": str(exc)}
        ) from exc
