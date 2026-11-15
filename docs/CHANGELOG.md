# Changelog

## Unreleased — local application build

- Implemented FastAPI routes and NESO client for current intensity, forecast, history, regions, postcode, summary statistics and regional comparison.
- Added SQLAlchemy storage, Alembic migration, region/source metadata and scheduled ingestion worker.
- Added React dashboard with live data, regional explorer, history, comparisons, postcode lookup and CSV export.
- Added Docker Compose services, persistent PostgreSQL, health checks, Nginx proxy and Windows local testing guide.
- Added automated backend/frontend tests and technical documentation.
- Fixed duplicate period keys in bulk upsert and ensured region persistence before observations.
