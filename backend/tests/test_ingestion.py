from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.base import Base
from app.models.entities import CarbonObservation, DataSource, GenerationMixObservation, Region
from app.services.ingestion import _persist_observations


@pytest.mark.asyncio
async def test_observation_upsert_and_generation_mix_deduplication():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    start = datetime(2026, 11, 14, 10, 0, tzinfo=UTC)
    observation = {
        "provider_region_id": 18,
        "region_id": 18,
        "interval_start": start,
        "interval_end": datetime(2026, 11, 14, 10, 30, tzinfo=UTC),
        "value_gco2_kwh": 44,
        "kind": "forecast",
        "provider_index": "very low",
        "retrieved_at": datetime.now(UTC),
        "source_metadata": {"regionid": 18},
    }
    mix = [
        {"provider_region_id": 18, "interval_start": start, "fuel": "wind", "percentage": 70.0},
        {"provider_region_id": 18, "interval_start": start, "fuel": "wind", "percentage": 70.0},
    ]
    async with factory() as session:
        session.add(
            DataSource(
                key="neso-carbon-intensity",
                name="NESO",
                base_url="https://example.test",
                license="CC BY 4.0",
                attribution="NESO",
            )
        )
        session.add(Region(id=18, name="Great Britain", short_name="GB", region_type="national"))
        await session.commit()
        await _persist_observations(session, [observation], mix)
        await session.commit()
        await _persist_observations(session, [observation], mix)
        await session.commit()
        observations = await session.scalar(select(func.count()).select_from(CarbonObservation))
        mixes = await session.scalar(select(func.count()).select_from(GenerationMixObservation))
        assert observations == 1
        assert mixes == 1
    await engine.dispose()


@pytest.mark.asyncio
async def test_region_seed_supports_newly_observed_provider_region():
    from app.services.ingestion import _ensure_regions

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        await _ensure_regions(session, [{"provider_region_id": 18}])
        await session.commit()
        region = await session.get(Region, 18)
        assert region is not None
        assert region.name == "Great Britain"
        assert region.region_type == "national"
    await engine.dispose()
