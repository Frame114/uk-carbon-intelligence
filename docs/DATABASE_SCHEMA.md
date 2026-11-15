# Database schema

Models are in `backend/app/models/entities.py`; migration `20261114_0001` creates the initial schema. Compose starts PostgreSQL 17 and runs `alembic upgrade head` before starting FastAPI.

| Table | Role |
|---|---|
| `data_sources` | Provider name, URL, licence and attribution. |
| `regions` | Provider-region metadata keyed by region ID. IDs 1–18 are represented. |
| `carbon_observations` | UTC interval, provider region, value in gCO2/kWh, actual/forecast kind, provider index, fetch time and source payload. Unique by source, provider region, interval start and kind. |
| `generation_mix_observations` | Provider fuel and percentage linked to an observation; percentage constrained to 0–100 and unique per fuel/observation. |
| `collection_runs` | Worker start/end, status, received/written counts, error class and run metadata. |

Source foreign keys retain attribution lineage. Mix records cascade with observation deletion. Observation conflicts refresh existing period data rather than duplicate records. PostgreSQL is persisted in Compose volume `postgres_data`; `docker compose down` preserves it, while `docker compose down -v` removes it.
