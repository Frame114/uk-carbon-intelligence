# UK Carbon Intelligence

An independent, Docker-first electricity carbon-intelligence application built around the National Energy System Operator (NESO) Carbon Intensity API for **Great Britain**.

> **Geographic scope:** the source API covers Great Britain (England, Scotland and Wales). It does not provide Northern Ireland coverage. The product must make this limitation clear wherever it describes its coverage.

## Project status

**Milestone 1 — Research and project foundation.** The initial API research, architecture decisions and repository skeleton are being established. Application services, database migrations, frontend screens and Docker deployment have not yet been implemented or verified.

See [PROJECT_STATUS.md](PROJECT_STATUS.md), [ROADMAP.md](ROADMAP.md) and [docs/API_RESEARCH.md](docs/API_RESEARCH.md).

## Data source

- NESO Carbon Intensity API: https://api.carbonintensity.org.uk
- API documentation: https://carbon-intensity.github.io/api-definitions/
- Official information and methodology: https://carbonintensity.org.uk/

The API is currently described by NESO as free to use under its terms and CC BY 4.0 licence. The terms also impose restrictions, including restrictions on misleading endorsement, substantial replacement of NESO's core user experience, and use of NESO marks without written approval. Review [docs/API_RESEARCH.md](docs/API_RESEARCH.md) before release.

## Planned architecture

- Backend: FastAPI, Pydantic v2, SQLAlchemy 2, Alembic and httpx.
- Database: PostgreSQL.
- Frontend: React, TypeScript, Vite, Tailwind CSS and Recharts.
- Ingestion: a separate lightweight worker process; no Redis unless a later, evidenced requirement justifies it.
- Optional integrations: OpenRouter-based analysis and an MCP server.
- Runtime: Docker Compose.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Running the project

There is no runnable application yet. Docker Compose, application dependencies and deployment instructions will be added in later milestones. Do not treat this research scaffold as a working release.

## Independence and attribution

UK Carbon Intelligence is an independent project and is not an NESO product. It must not use NESO logos or word marks without prior written approval. It must attribute the data source and link to the official API and source website.
