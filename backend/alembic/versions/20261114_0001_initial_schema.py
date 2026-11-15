"""Create initial carbon intelligence schema.

Revision ID: 20261114_0001
Revises:
Create Date: 2026-11-14
"""

import sqlalchemy as sa

from alembic import op

revision = "20261114_0001"
down_revision = None
branch_labels = None
depends_on = None


REGIONS = [
    (1, "North Scotland", "North Scotland", "dno"),
    (2, "South Scotland", "South Scotland", "dno"),
    (3, "North West England", "North West England", "dno"),
    (4, "North East England", "North East England", "dno"),
    (5, "Yorkshire", "Yorkshire", "dno"),
    (6, "North Wales & Merseyside", "North Wales & Merseyside", "dno"),
    (7, "South Wales", "South Wales", "dno"),
    (8, "West Midlands", "West Midlands", "dno"),
    (9, "East Midlands", "East Midlands", "dno"),
    (10, "East England", "East England", "dno"),
    (11, "South West England", "South West England", "dno"),
    (12, "South England", "South England", "dno"),
    (13, "London", "London", "dno"),
    (14, "South East England", "South East England", "dno"),
    (15, "England", "England", "country"),
    (16, "Scotland", "Scotland", "country"),
    (17, "Wales", "Wales", "country"),
    (18, "Great Britain", "GB", "national"),
]


def upgrade() -> None:
    op.create_table(
        "data_sources",
        sa.Column("key", sa.String(length=80), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("base_url", sa.String(length=500), nullable=False),
        sa.Column("license", sa.String(length=80), nullable=False),
        sa.Column("attribution", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "regions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("short_name", sa.String(length=100), nullable=False),
        sa.Column("region_type", sa.String(length=24), nullable=False),
        sa.Column("provider_name", sa.String(length=200), nullable=True),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "carbon_observations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "source_key",
            sa.String(length=80),
            sa.ForeignKey("data_sources.key", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("provider_region_id", sa.Integer(), nullable=False),
        sa.Column(
            "region_id",
            sa.Integer(),
            sa.ForeignKey("regions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("interval_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("interval_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value_gco2_kwh", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=12), nullable=False),
        sa.Column("provider_index", sa.String(length=20), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("kind IN ('actual', 'forecast')", name="ck_observation_kind"),
        sa.CheckConstraint("value_gco2_kwh >= 0", name="ck_observation_nonnegative"),
        sa.UniqueConstraint(
            "source_key",
            "provider_region_id",
            "interval_start",
            "kind",
            name="uq_observation_source_region_period_kind",
        ),
    )
    op.create_index(
        "ix_observations_region_start", "carbon_observations", ["region_id", "interval_start"]
    )
    op.create_index("ix_observations_start_kind", "carbon_observations", ["interval_start", "kind"])
    op.create_table(
        "generation_mix_observations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "observation_id",
            sa.Integer(),
            sa.ForeignKey("carbon_observations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fuel", sa.String(length=40), nullable=False),
        sa.Column("percentage", sa.Float(), nullable=False),
        sa.CheckConstraint(
            "percentage >= 0 AND percentage <= 100", name="ck_generation_mix_percentage"
        ),
        sa.UniqueConstraint("observation_id", "fuel", name="uq_generation_mix_observation_fuel"),
    )
    op.create_table(
        "collection_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "source_key",
            sa.String(length=80),
            sa.ForeignKey("data_sources.key", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("records_received", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_written", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_collection_runs_started", "collection_runs", ["started_at"])
    op.bulk_insert(
        sa.table(
            "data_sources",
            sa.column("key", sa.String),
            sa.column("name", sa.String),
            sa.column("base_url", sa.String),
            sa.column("license", sa.String),
            sa.column("attribution", sa.String),
        ),
        [
            {
                "key": "neso-carbon-intensity",
                "name": "NESO Carbon Intensity API",
                "base_url": "https://api.carbonintensity.org.uk",
                "license": "CC BY 4.0",
                "attribution": (
                    "Data source: National Energy System Operator (NESO) Carbon Intensity API."
                ),
            }
        ],
    )
    op.bulk_insert(
        sa.table(
            "regions",
            sa.column("id", sa.Integer),
            sa.column("name", sa.String),
            sa.column("short_name", sa.String),
            sa.column("region_type", sa.String),
        ),
        [
            {"id": item[0], "name": item[1], "short_name": item[2], "region_type": item[3]}
            for item in REGIONS
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_collection_runs_started", table_name="collection_runs")
    op.drop_table("collection_runs")
    op.drop_table("generation_mix_observations")
    op.drop_index("ix_observations_start_kind", table_name="carbon_observations")
    op.drop_index("ix_observations_region_start", table_name="carbon_observations")
    op.drop_table("carbon_observations")
    op.drop_table("regions")
    op.drop_table("data_sources")
