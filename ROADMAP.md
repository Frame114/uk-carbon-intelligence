# Roadmap — UK Carbon Intelligence

## Milestone 1 — Research and project foundation

- [x] Review the official NESO API reference and terms.
- [x] Confirm initial geographical scope, timestamp semantics and documented request limits.
- [x] Record live/documentation discrepancies for later contract tests.
- [x] Establish the standalone project tree and initial architecture.
- [ ] Complete a repeatable local API contract probe when network access is available.
- [ ] Finalise the provider contract fixtures and region mapping after repeat verification.

## Milestone 2 — Backend and provider integration

- [ ] Implement a typed asynchronous NESO client.
- [ ] Create provider response schemas that allow optional/null fields and unknown future fields.
- [ ] Normalise national, regional, postcode and generation responses into internal domain objects.
- [ ] Implement versioned REST endpoints and health checks.
- [ ] Add unit tests for parsing, errors, timestamps and region handling.

## Milestone 3 — Database and ingestion

- [ ] Implement PostgreSQL models and Alembic migrations.
- [ ] Implement idempotent repositories and upserts.
- [ ] Add a single lightweight ingestion worker and job history.
- [ ] Apply bounded retries, request pacing, freshness checks and recovery behaviour.
- [ ] Add database and ingestion integration tests.

## Milestone 4 — Frontend dashboard

- [ ] Build the application shell and navigation.
- [ ] Implement overview, forecast, history, regions, Scotland, postcode and generation views.
- [ ] Add genuine data visualisations, freshness indicators and error/empty states.
- [ ] Test UI behaviour and API integration.

## Milestone 5 — Optional AI and MCP

- [ ] Add evidence-grounded OpenRouter analysis behind an explicit feature flag.
- [ ] Add MCP tools that reuse backend services.
- [ ] Test unavailable AI credentials, MCP schemas, structured outputs and failure handling.

## Milestone 6 — Docker integration

- [ ] Add backend, frontend, worker and PostgreSQL containers.
- [ ] Add health checks, database readiness and migrations.
- [ ] Validate persistence and restart behaviour.
- [ ] Document Windows 11 / Docker Desktop setup.

## Milestone 7 — Quality assurance

- [ ] Run backend, frontend, integration and MCP tests.
- [ ] Produce actual coverage reports; target at least 85% meaningful backend coverage.
- [ ] Complete security, dependency and failure-scenario checks.

## Milestone 8 — Documentation and release preparation

- [ ] Complete operational and technical documentation.
- [ ] Add GitHub Actions CI.
- [ ] Review repository cleanliness and attribution.
- [ ] Prepare release notes and a verification matrix.

No milestone should be marked complete solely because files were generated. Completion requires the relevant tests and verification evidence.
