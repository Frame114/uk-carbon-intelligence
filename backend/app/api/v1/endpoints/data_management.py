from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_database_session
from app.models.entities import CollectionRun
from app.services.presentation import SOURCE, metadata

router = APIRouter(tags=["Data management"])


@router.get("/data-sources", summary="List current data providers")
async def data_sources():
    return {
        "data": [
            {
                "key": "neso-carbon-intensity",
                "name": SOURCE["name"],
                "provider": SOURCE["provider"],
                "base_url": SOURCE["url"],
                "license": SOURCE["license"],
                "coverage": (
                    "Great Britain (England, Scotland and Wales); Northern Ireland is not covered."
                ),
                "attribution": (
                    "Data source: National Energy System Operator (NESO) Carbon Intensity API."
                ),
            }
        ],
        "metadata": metadata(),
    }


@router.get("/collection/status", summary="Get latest scheduled collection result")
async def collection_status(session: AsyncSession = Depends(get_database_session)):
    result = await session.execute(
        select(CollectionRun).order_by(desc(CollectionRun.started_at)).limit(1)
    )
    run = result.scalar_one_or_none()
    if run is None:
        data = {
            "status": "never_run",
            "last_started_at": None,
            "last_finished_at": None,
            "records_received": 0,
            "records_written": 0,
        }
    else:
        data = {
            "status": run.status,
            "last_started_at": run.started_at,
            "last_finished_at": run.finished_at,
            "records_received": run.records_received,
            "records_written": run.records_written,
            "error": run.error_summary,
        }
    return {"data": data, "metadata": metadata()}
