from fastapi import APIRouter

from app.api.v1.endpoints import carbon_intensity, data_management, regions, statistics, system

router = APIRouter(prefix="/api/v1")
router.include_router(carbon_intensity.router)
router.include_router(regions.router)
router.include_router(statistics.router)
router.include_router(data_management.router)
router.include_router(system.v1_router)
