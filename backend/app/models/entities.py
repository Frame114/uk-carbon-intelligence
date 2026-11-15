from datetime import datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    license: Mapped[str] = mapped_column(String(80), nullable=False)
    attribution: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    short_name: Mapped[str] = mapped_column(String(100), nullable=False)
    region_type: Mapped[str] = mapped_column(String(24), nullable=False, default="unknown")
    provider_name: Mapped[str | None] = mapped_column(String(200))
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class CarbonObservation(Base):
    __tablename__ = "carbon_observations"
    __table_args__ = (
        UniqueConstraint(
            "source_key",
            "provider_region_id",
            "interval_start",
            "kind",
            name="uq_observation_source_region_period_kind",
        ),
        CheckConstraint("kind IN ('actual', 'forecast')", name="ck_observation_kind"),
        CheckConstraint("value_gco2_kwh >= 0", name="ck_observation_nonnegative"),
        Index("ix_observations_region_start", "region_id", "interval_start"),
        Index("ix_observations_start_kind", "interval_start", "kind"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_key: Mapped[str] = mapped_column(
        ForeignKey("data_sources.key", ondelete="RESTRICT"), nullable=False
    )
    provider_region_id: Mapped[int] = mapped_column(Integer, nullable=False)
    region_id: Mapped[int | None] = mapped_column(ForeignKey("regions.id", ondelete="SET NULL"))
    interval_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    interval_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    value_gco2_kwh: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(String(12), nullable=False)
    provider_index: Mapped[str | None] = mapped_column(String(20))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    generation_mix: Mapped[list["GenerationMixObservation"]] = relationship(
        back_populates="observation", cascade="all, delete-orphan"
    )


class GenerationMixObservation(Base):
    __tablename__ = "generation_mix_observations"
    __table_args__ = (
        UniqueConstraint("observation_id", "fuel", name="uq_generation_mix_observation_fuel"),
        CheckConstraint(
            "percentage >= 0 AND percentage <= 100", name="ck_generation_mix_percentage"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    observation_id: Mapped[int] = mapped_column(
        ForeignKey("carbon_observations.id", ondelete="CASCADE"), nullable=False
    )
    fuel: Mapped[str] = mapped_column(String(40), nullable=False)
    percentage: Mapped[float] = mapped_column(Float, nullable=False)
    observation: Mapped[CarbonObservation] = relationship(back_populates="generation_mix")


class CollectionRun(Base):
    __tablename__ = "collection_runs"
    __table_args__ = (Index("ix_collection_runs_started", "started_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_key: Mapped[str] = mapped_column(
        ForeignKey("data_sources.key", ondelete="RESTRICT"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    records_received: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_written: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_summary: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
