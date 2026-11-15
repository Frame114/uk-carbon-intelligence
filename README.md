# UK Carbon Intelligence

Independent GB electricity carbon intensity dashboard powered by National Energy System Operator (NESO) provider data. The source covers Great Britain (England, Scotland and Wales), not Northern Ireland.

## Status

The repository contains a local runnable app: FastAPI API, React/TypeScript dashboard, PostgreSQL schema and migration, NESO background collector, and Docker Compose. See [PROJECT_STATUS.md](PROJECT_STATUS.md) for current verification evidence and outstanding checks.

## Run on Windows 11

Follow [LOCAL_TESTING_GUIDE.md](LOCAL_TESTING_GUIDE.md). Copy `.env.example` to `.env`, configure a local database password, and run `docker compose up --build -d`. Dashboard: http://localhost:8080. Swagger API docs: http://localhost:8080/docs.

## Data constraints

Actual estimates and forecasts are separate. Values are not reconstructed from fuel mix. Missing intervals remain missing. All source periods are UTC and displayed in Europe/London. Postcodes resolve to regional provider data, not property-level readings. NESO attribution and independent-product limitations are described in [docs/API_RESEARCH.md](docs/API_RESEARCH.md) and [docs/DATA_METHODOLOGY.md](docs/DATA_METHODOLOGY.md).

## Project docs

Architecture, methodology, regional mapping, API reference, schema, ingestion, security, deployment, and testing guides are in `docs/`. OpenAPI is available at `/openapi.json`.
