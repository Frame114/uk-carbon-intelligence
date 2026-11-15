# Test strategy and latest evidence

## Test layers

- **Backend unit tests:** intensity classification thresholds; response normalization, missing values, unknown regions, postcode normalization, and UTC behavior.
- **Backend client/API tests:** mocked NESO transport including bounded 429 retry; API route schemas, 14-day range bounds, period clipping, regional behavior, and structured errors.
- **Persistence tests:** SQLite schema, observation upsert behavior, and generation-mix deduplication. PostgreSQL behavior is separately checked through Compose.
- **Frontend tests:** initial loading/current data, provider/backend error state, region selection, history, and formatting including zero/missing values and DST.
- **Build/lint:** TypeScript/Vite production build and Ruff checks/format.
- **Runtime smoke:** Compose health, Alembic revision, live API, frontend reverse proxy, and worker collection status.

## Recorded results

At the latest full pass: backend 31 tests passed; frontend 6 tests passed; frontend production build succeeded; Ruff lint passed after formatting corrections; Compose config parsed; PostgreSQL/backend/frontend were healthy; `/health`, `/ready`, and current intensity returned successfully. Latest collector reported success. The SQLite persistence test does not replace verification on a clean PostgreSQL volume.

Re-run exact commands in `LOCAL_TESTING_GUIDE.md` after changes. Live provider calls depend on NESO availability and are smoke checks, not deterministic tests.
