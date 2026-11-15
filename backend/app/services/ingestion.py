import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.clients.neso import NesoClient
from app.core.config import settings
from app.models.entities import (
    CarbonObservation,
    CollectionRun,
    DataSource,
    GenerationMixObservation,
)
from app.models.entities import (
    Region as RegionModel,
)
from app.services.normalization import normalize_national, normalize_regional
from app.utils.regions import get_region
from app.utils.time import parse_utc

logger = logging.getLogger(__name__)
SOURCE_KEY = "neso-carbon-intensity"
SOURCE_NAME = "NESO Carbon Intensity API"


async def _ensure_source(session: AsyncSession) -> None:
    source = await session.get(DataSource, SOURCE_KEY)
    if source is None:
        session.add(
            DataSource(
                key=SOURCE_KEY,
                name=SOURCE_NAME,
                base_url=settings.neso_api_base_url,
                license="CC BY 4.0",
                attribution=(
                    "Data source: National Energy System Operator (NESO) Carbon Intensity API."
                ),
            )
        )
        await session.flush()


async def _upsert(
    session: AsyncSession, model, rows: list[dict], unique: list[str], update_fields: list[str]
) -> None:
    if not rows:
        return
    # PostgreSQL rejects a multi-row ON CONFLICT statement when duplicate keys
    # occur in that statement. Provider feeds overlap at the current interval.
    rows = list({tuple(row[key] for key in unique): row for row in rows}.values())
    dialect = session.bind.dialect.name if session.bind is not None else ""
    if dialect == "postgresql":
        statement = pg_insert(model).values(rows)
        statement = statement.on_conflict_do_update(
            index_elements=unique,
            set_={field: getattr(statement.excluded, field) for field in update_fields},
        )
        await session.execute(statement)
    elif dialect == "sqlite":
        statement = sqlite_insert(model).values(rows)
        statement = statement.on_conflict_do_update(
            index_elements=unique,
            set_={field: getattr(statement.excluded, field) for field in update_fields},
        )
        await session.execute(statement)
    else:
        for row in rows:
            await session.merge(model(**row))


async def _ensure_regions(session: AsyncSession, observations: list[dict]) -> None:
    provider_ids = {row["provider_region_id"] for row in observations}
    existing = (
        set(
            (
                await session.scalars(
                    select(RegionModel.id).where(RegionModel.id.in_(provider_ids))
                )
            ).all()
        )
        if provider_ids
        else set()
    )
    rows = []
    for provider_id in provider_ids - existing:
        region = get_region(provider_id)
        rows.append(
            {
                "id": region.id,
                "name": region.name,
                "short_name": region.short_name,
                "region_type": region.type,
                "provider_name": region.short_name,
            }
        )
    await _upsert(
        session, RegionModel, rows, ["id"], ["name", "short_name", "region_type", "provider_name"]
    )


async def _persist_observations(
    session: AsyncSession, observations: list[dict], mixes: list[dict]
) -> int:
    records = [dict(row, source_key=SOURCE_KEY) for row in observations]
    records = list(
        {
            (
                row["source_key"],
                row["provider_region_id"],
                row["interval_start"],
                row["kind"],
            ): row
            for row in records
        }.values()
    )
    previous_count = await session.scalar(select(func.count()).select_from(CarbonObservation))
    await _upsert(
        session,
        CarbonObservation,
        records,
        ["source_key", "provider_region_id", "interval_start", "kind"],
        [
            "region_id",
            "interval_end",
            "value_gco2_kwh",
            "provider_index",
            "retrieved_at",
            "source_metadata",
        ],
    )
    if mixes:
        region_ids = {item["provider_region_id"] for item in mixes}
        starts = {item["interval_start"] for item in mixes}
        result = await session.execute(
            select(CarbonObservation).where(
                CarbonObservation.source_key == SOURCE_KEY,
                CarbonObservation.kind == "forecast",
                CarbonObservation.provider_region_id.in_(region_ids),
                CarbonObservation.interval_start.in_(starts),
            )
        )
        lookup = {
            (item.provider_region_id, parse_utc(item.interval_start)): item.id
            for item in result.scalars().all()
        }
        observation_ids = set(lookup.values())
        if observation_ids:
            await session.execute(
                delete(GenerationMixObservation).where(
                    GenerationMixObservation.observation_id.in_(observation_ids)
                )
            )
        deduplicated = {
            (item["provider_region_id"], item["interval_start"], item["fuel"]): item
            for item in mixes
        }
        mix_records = [
            {
                "observation_id": lookup[(item["provider_region_id"], item["interval_start"])],
                "fuel": item["fuel"],
                "percentage": item["percentage"],
            }
            for item in deduplicated.values()
            if (item["provider_region_id"], item["interval_start"]) in lookup
        ]
        if mix_records:
            await session.execute(GenerationMixObservation.__table__.insert().values(mix_records))
    current_count = await session.scalar(select(func.count()).select_from(CarbonObservation))
    # Count records actually added to the archive; conflict updates refresh old rows.
    return max(0, int(current_count or 0) - int(previous_count or 0))


async def collect_once(
    session_factory: async_sessionmaker[AsyncSession], client: NesoClient
) -> dict:
    started = datetime.now(UTC)
    async with session_factory() as session:
        await _ensure_source(session)
        run = CollectionRun(source_key=SOURCE_KEY, started_at=started, status="running")
        session.add(run)
        await session.commit()
        run_id = run.id
    try:
        current, national, regional_current, regional_future = await asyncio.gather(
            client.current(),
            client.national_forecast(started, 48),
            client.regional_current(),
            client.regional_forecast(started, 24),
        )
        retrieved_at = datetime.now(UTC)
        national_rows = normalize_national(current, retrieved_at) + normalize_national(
            national, retrieved_at
        )
        regional_rows, regional_mix = normalize_regional(regional_current, retrieved_at)
        future_rows, future_mix = normalize_regional(regional_future, retrieved_at)
        observations = national_rows + regional_rows + future_rows
        mixes = regional_mix + future_mix
        async with session_factory() as session:
            await _ensure_source(session)
            await _ensure_regions(session, observations)
            written = await _persist_observations(session, observations, mixes)
            run = await session.get(CollectionRun, run_id)
            run.status = "success"
            run.finished_at = datetime.now(UTC)
            run.records_received = len(observations)
            run.records_written = written
            run.metadata_json = {"generation_mix_rows": len(mixes), "endpoints": 4}
            await session.commit()
        return {
            "status": "success",
            "records_received": len(observations),
            "records_written": written,
        }
    except Exception as exc:
        logger.exception("NESO collection run failed")
        async with session_factory() as session:
            run = await session.get(CollectionRun, run_id)
            if run:
                run.status = "failed"
                run.finished_at = datetime.now(UTC)
                run.error_summary = type(exc).__name__
                await session.commit()
        return {"status": "failed", "error": str(exc)}


async def run_collector(
    session_factory: async_sessionmaker[AsyncSession], client: NesoClient
) -> None:
    logger.info(
        "Starting NESO collection loop; interval=%s seconds", settings.collection_interval_seconds
    )
    while True:
        await collect_once(session_factory, client)
        await asyncio.sleep(settings.collection_interval_seconds)
