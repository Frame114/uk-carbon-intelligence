from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.dependencies import get_neso_client
from app.api.v1.endpoints.common import period_floor, resolve_range
from app.clients.neso import NesoApiError, NesoClient
from app.services.normalization import ProviderDataError
from app.services.presentation import clip_periods, metadata, regional_periods
from app.utils.postcode import normalize_outward_postcode
from app.utils.regions import REGIONS, get_region

router = APIRouter(tags=["Regions and postcodes"])


@router.get("/regions", summary="List supported regions with current intensity")
async def list_regions(client: NesoClient = Depends(get_neso_client)):
    try:
        periods = regional_periods(await client.regional_current())
        latest_by_region = {}
        for period in periods:
            latest_by_region[period["region_id"]] = period
        data = []
        for region_id, region in REGIONS.items():
            snapshot = latest_by_region.get(region_id)
            data.append(
                {
                    **region.as_dict(),
                    "current": snapshot,
                    "available": snapshot is not None,
                }
            )
        # Keep provider regions visible without treating unknown IDs as known geography.
        for region_id, snapshot in latest_by_region.items():
            if region_id not in REGIONS:
                data.append(
                    {
                        **get_region(region_id).as_dict(),
                        "current": snapshot,
                        "available": True,
                    }
                )
        return {"data": data, "metadata": metadata()}
    except (NesoApiError, ProviderDataError, ValueError) as exc:
        raise HTTPException(
            status_code=503, detail={"code": "provider_unavailable", "message": str(exc)}
        ) from exc


@router.get("/regions/{region_id}", summary="Get a supported region")
async def get_region_detail(region_id: int):
    region = REGIONS.get(region_id)
    if region is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "region_not_found",
                "message": f"Region {region_id} is not in the supported region catalogue.",
            },
        )
    return {"data": region.as_dict(), "metadata": metadata()}


@router.get("/regions/{region_id}/current", summary="Get current intensity for one region")
async def region_current(region_id: int, client: NesoClient = Depends(get_neso_client)):
    try:
        periods = regional_periods(await client.regional_current())
        matches = [item for item in periods if item["region_id"] == region_id]
        if not matches:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "region_data_unavailable",
                    "message": f"No current NESO data is available for region {region_id}.",
                },
            )
        return {"data": matches[:1], "metadata": metadata()}
    except (NesoApiError, ProviderDataError, ValueError) as exc:
        raise HTTPException(
            status_code=503, detail={"code": "provider_unavailable", "message": str(exc)}
        ) from exc


@router.get("/regions/{region_id}/history", summary="Get historical intensity for one region")
async def region_history(
    region_id: int,
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    client: NesoClient = Depends(get_neso_client),
):
    start, end = resolve_range(start, end)
    try:
        payload = await client.region_history(region_id, start, end)
        periods = clip_periods(regional_periods(payload), start, end)
        return {"data": periods, "metadata": metadata()}
    except (NesoApiError, ProviderDataError, ValueError) as exc:
        raise HTTPException(
            status_code=503, detail={"code": "provider_unavailable", "message": str(exc)}
        ) from exc


@router.get(
    "/postcodes/{postcode}/carbon-intensity",
    summary="Resolve an outward postcode to regional forecast",
)
async def postcode_intensity(postcode: str, client: NesoClient = Depends(get_neso_client)):
    try:
        outward = normalize_outward_postcode(postcode)
    except ValueError as exc:
        raise HTTPException(
            status_code=422, detail={"code": "invalid_postcode", "message": str(exc)}
        ) from exc
    try:
        payload = await client.postcode_forecast(outward, period_floor())
        periods = regional_periods(payload)
        return {
            "data": periods,
            "metadata": {
                **metadata(),
                "postcode": outward,
                "geography_note": "Regional data only; this is not a property-level measurement.",
            },
        }
    except (NesoApiError, ProviderDataError, ValueError) as exc:
        raise HTTPException(
            status_code=503, detail={"code": "provider_unavailable", "message": str(exc)}
        ) from exc
