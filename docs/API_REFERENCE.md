# API reference

The interactive OpenAPI interface is available at `/docs`; the OpenAPI document is `/openapi.json`. In Docker Compose, access both through `http://localhost:8080`.

| Method and path | Purpose |
|---|---|
| `GET /health` | Liveness. |
| `GET /ready` | Readiness and database connectivity. |
| `GET /api/v1/status` | Application and provider status. |
| `GET /api/v1/carbon-intensity/current` | Current GB period with distinct forecast and actual fields. |
| `GET /api/v1/carbon-intensity/forecast?hours=24` | National forecast; `hours` accepts 24 or 48. |
| `GET /api/v1/carbon-intensity/history?start=<ISO>&end=<ISO>&region_id=<id>` | Historical series; region is optional and range is limited to 14 days. |
| `GET /api/v1/regions` | Supported regions and current regional data. |
| `GET /api/v1/regions/{id}` | Region metadata. |
| `GET /api/v1/regions/{id}/current` | Current regional period. |
| `GET /api/v1/regions/{id}/history?start=<ISO>&end=<ISO>` | Historical regional series. |
| `GET /api/v1/postcodes/{postcode}/carbon-intensity` | Regional forecast resolved from full or outward postcode. |
| `GET /api/v1/statistics/summary?start=<ISO>&end=<ISO>` | Separate actual and forecast summary statistics. |
| `GET /api/v1/statistics/regional-comparison?region_ids=1,2&start=<ISO>&end=<ISO>` | Comparison of selected provider regional forecast series. |
| `GET /api/v1/data-sources` | Source attribution, licence and coverage. |
| `GET /api/v1/collection/status` | Latest worker run status. |

Use timezone-aware ISO 8601 timestamps, preferably UTC. Successful data responses contain `data` and retrieval/source metadata. Validation errors return structured 422 details; unsupported regions return 404; unavailable provider/database services return 503. See generated OpenAPI for parameter bounds and response schemas.
