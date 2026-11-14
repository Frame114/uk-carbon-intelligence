# Architecture — UK Carbon Intelligence

## 1. Architecture goals

- Remain a standalone application with no runtime dependency on unrelated repositories or services.
- Separate NESO's external provider contract from UK Carbon Intelligence's internal API and domain model.
- Preserve source timestamps, provenance and forecast/actual distinctions.
- Make optional AI and MCP integrations removable without affecting core data access.
- Keep local deployment reproducible through Docker Compose.
- Avoid infrastructure that does not solve a demonstrated problem.

## 2. Logical topology

```text
Browser
  |
  v
React + TypeScript frontend
  |
  | same-origin /api proxy in deployment
  v
FastAPI application --------------------> OpenRouter (optional)
  |                                          |
  | domain services                          | evidence-bound request
  |                                          |
  +----> NESO API client --------------------+
  |          |
  |          v
  |      NESO Carbon Intensity API
  |
  +----> PostgreSQL <------ ingestion worker
  |                          |
  |                          +----> NESO API client
  |
  +----> MCP server (optional process/profile)
             |
             +----> shared application services
```

## 3. Deployable services

| Service | Responsibility | Initial decision |
|---|---|---|
| frontend | Serve the compiled React application and proxy /api to backend | Nginx or equivalent static server in production image |
| backend | REST API, validation, domain services, NESO integration | FastAPI |
| worker | Scheduled provider retrieval, normalisation and persistence | Same backend image with a distinct command; one active scheduler initially |
| db | Durable normalized records, jobs and metadata | PostgreSQL |
| mcp | Optional MCP transport exposing the same services | Separate optional process/profile |

Redis is not part of the initial architecture. PostgreSQL and database unique constraints are sufficient for the first ingestion worker and idempotency model. Revisit a queue/cache only if measured load or concurrent-job complexity demonstrates a need.

## 4. Backend module boundaries

```text
backend/app/
  api/v1/endpoints/     HTTP route handlers only
  clients/              External NESO and OpenRouter clients
  schemas/              Provider and API DTO schemas
  models/               SQLAlchemy persistence models
  repositories/         Database queries and upserts
  services/             Domain rules and orchestration
  ingestion/             Scheduled jobs and ingestion workflows
  ai/                   Optional grounded analysis
  mcp/                  MCP tool adapters
  core/                 Settings, logging, errors, security
  utils/                Date/time and shared helpers
```

Routes call services. Services coordinate clients and repositories. The frontend and MCP layer must never call NESO directly; they use the internal API or shared backend services. This prevents duplicated provider logic.

## 5. Provider adapter boundary

The NESO client owns:

- endpoint path construction and URL encoding;
- request timeout policy;
- response status/error handling;
- provider payload parsing;
- bounded retries and rate-limit behaviour;
- provider-specific schema compatibility.

The normalisation layer converts provider payloads to internal domain objects. It must tolerate unknown fields and region IDs, nullable values, endpoint shape differences, and future provider extensions. Keep raw payload samples only for diagnostics and reproducibility, not as the UI's primary contract.

## 6. Domain and data model proposal

### Region

- provider region ID (not assumed to be constrained to 1–17);
- canonical short name;
- provider DNO/descriptor;
- region kind: dno, country_aggregate, gb_aggregate, or unknown;
- effective/observed metadata and active flag.

### IntensityObservation

- region scope (GB, country or regional ID);
- interval start/end as UTC timestamptz;
- nullable forecast value;
- nullable estimated actual value;
- nullable provider classification index;
- source endpoint and fetched-at timestamp;
- optional raw payload JSONB / payload digest.

Unique key should represent (scope, interval_start, interval_end) unless contract tests show a separate provider revision dimension is required. Repeated ingestions should update null/forecast values when provider actuals become available, not duplicate the interval.

### GenerationMixObservation

- scope and interval;
- fuel name as provider string;
- percentage contribution;
- fetched-at timestamp and source endpoint.

Use one row per fuel and interval with unique constraint (scope, interval_start, interval_end, fuel).

### IngestionJob

- job type, target scope/range;
- started/finished timestamps;
- status and attempt count;
- records created/updated;
- error category/message (sanitised);
- provider response metadata where useful.

### DataSourceMetadata

- provider name/base URL;
- latest successful fetch per dataset;
- freshness threshold;
- terms/licence reference;
- contract version or last schema observation.

Final schema must follow actual fixtures and migrations; this is a proposal, not an already implemented database.

## 7. API design

Expose a versioned internal contract under /api/v1. Candidate route groups:

- /carbon-intensity/current
- /carbon-intensity/forecast
- /carbon-intensity/history
- /regions and /regions/{region_id}
- /scotland
- /postcode/{outward_postcode}
- /generation
- /statistics
- /factors
- /health and /health/ready

Internal DTOs should explicitly include source, scope, from, to, forecast, actual, index, fetched_at and freshness as applicable. Do not make users infer whether a displayed value is forecast or estimated actual.

## 8. Ingestion design

Initial approach:

1. Schedule a small set of jobs around the provider's half-hour data cadence.
2. Fetch national current data, national forecasts, the single regional dataset, and national generation mix.
3. Normalize and validate records.
4. Upsert observations using stable unique keys.
5. Persist job outcome and last-success metadata.
6. Apply freshness checks before displaying stale values.

Use the regional aggregate endpoint once per cadence rather than N per-region requests. Do not poll every page/widget. Start with a 30-minute cadence and a short cache for interactive requests; adjust only from observed freshness and provider guidance. Use database advisory locking or another simple single-worker guard to avoid duplicate schedulers.

Historical range retrieval should be user-triggered or controlled backfill, chunked to provider limits, with progress and rate-limited calls.

## 9. Data integrity and scientific boundaries

- Store UTC instants, display using Europe/London.
- Keep actual and forecast separate; do not overwrite forecast with actual, or vice versa.
- Do not calculate carbon-intensity from fuel percentages using a simplified weighted average.
- Keep renewable and low-carbon totals separate; nuclear is low-carbon but not renewable.
- Do not misclassify imports or other without a documented policy.
- Preserve the official intensity index from the provider rather than rebuilding thresholds from memory.
- Treat regional generation mix as estimated regional consumption mix where the official methodology says that is how regional values are derived; label it carefully.

## 10. Optional AI

The backend gathers relevant normalized observations and prepares an evidence object containing scope, period, units, actual/forecast markers, freshness and source. OpenRouter receives only that evidence and a bounded task prompt. If the key is missing or the call fails, the rest of the app continues normally. AI output is explanatory text, not the source of truth.

## 11. Optional MCP

MCP tool adapters reuse domain services, enforce time/range/result limits and return structured output with source timestamps. Keep the MCP process optional and independently startable. No MCP tool should duplicate provider calculations or bypass app data validation.

## 12. Observability and failure handling

- Structured logs with request/job correlation IDs.
- Separate liveness and readiness checks.
- /health/ready checks database connectivity; provider availability should be represented as a separate dependency/freshness status, not make the whole app unhealthy.
- Metrics or status records for fetch age, failures, duration and rows updated.
- Stale-data UI warning when a dataset exceeds its freshness threshold.
- Bounded retries and no retry loop for 4xx validation failures.

## 13. Security and release considerations

- Secrets only via environment variables.
- PostgreSQL on the private Compose network, no public port by default.
- Restrictive CORS in production; same-origin frontend proxy preferred.
- Validate all date, region and postcode inputs.
- Use SQLAlchemy parameterized queries.
- Keep OpenRouter disabled by default.
- Present an independent-source disclaimer and attribution; do not use NESO branding without written permission.
- Do not present the app as an official NESO replacement or endorsed product.
