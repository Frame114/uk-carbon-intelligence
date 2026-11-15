from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_database_session
from app.core.config import settings
from app.services.presentation import SOURCE

root_router = APIRouter(tags=["System"])
v1_router = APIRouter(tags=["System"])


@root_router.get("/health", summary="Process liveness")
async def health():
    return {"status": "ok", "timestamp": datetime.now(UTC)}


@root_router.get("/ready", summary="Database readiness")
async def ready(session: AsyncSession = Depends(get_database_session)):
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "database_unavailable", "message": "Database is not ready."},
        ) from exc
    return {"status": "ready", "dependencies": {"database": "ok"}, "timestamp": datetime.now(UTC)}


@v1_router.get("/status", summary="Application service status")
async def status(request: Request):
    return {
        "data": {
            "application": settings.app_name,
            "version": settings.app_version,
            "status": "ok",
            "provider": SOURCE,
            "collection_interval_seconds": settings.collection_interval_seconds,
            "scheduler_enabled_in_api": settings.scheduler_enabled,
            "openapi": str(request.base_url).rstrip("/") + "/openapi.json",
        },
        "timestamp": datetime.now(UTC),
    }
