# Local testing on Windows 11

Requirements: Docker Desktop running with Linux containers, Git, and PowerShell. Clone/open the repository, then:

```powershell
Set-Location 'J:\10 Software Projects\uk-carbon-intelligence'
Copy-Item .env.example .env
notepad .env
```

Set `POSTGRES_PASSWORD` to a private local password. Set `DATABASE_URL` to `postgresql+asyncpg://carbon:<URL-encoded-password>@db:5432/carbon_intelligence` using the same password. The service hostname must remain `db`. Keep `.env` private; it is git-ignored.

```powershell
docker compose config --quiet
docker compose up --build -d
docker compose ps
```

Wait for database, backend, and frontend health checks to pass. On first run Docker downloads and builds images; this can take several minutes. The backend container applies Alembic migrations before starting. The worker then contacts NESO and stores current/forecast observations.

## Local addresses

- Dashboard: http://localhost:8080
- Interactive API documentation: http://localhost:8080/docs
- Liveness: `Invoke-RestMethod http://localhost:8080/health` returns `ok`.
- Readiness/database: `Invoke-RestMethod http://localhost:8080/ready` returns `status=ready` and database `ok`.
- Current data: `Invoke-RestMethod http://localhost:8080/api/v1/carbon-intensity/current` returns provider timestamps, actual and forecast values, and attribution metadata.
- Collection: `Invoke-RestMethod http://localhost:8080/api/v1/collection/status` should report `success` after the first collector cycle.

Try the dashboard current overview, regional explorer, postcode lookup, history filters, CSV download, and regional comparison. Intensity data covers Great Britain (England, Scotland, Wales); Northern Ireland is outside provider coverage. Missing intervals are not represented as zero. Actual estimates and forecasts remain separate.

## Operations

```powershell
docker compose logs -f
docker compose logs --tail 100 worker
docker compose up -d --build
docker compose down
```

`docker compose down` preserves collected data. To change the host port, set `PORT=8081` in `.env`, recreate services, and use http://localhost:8081. To intentionally erase local data, `docker compose down -v` deletes the database volume.

## Troubleshooting

- Docker commands fail: start Docker Desktop; `docker info` should show a server version and Linux engine.
- Compose reports a missing password: check `.env`, `POSTGRES_PASSWORD`, and matching URL-encoded credentials in `DATABASE_URL`; rerun `docker compose config --quiet`.
- A container is unhealthy: inspect `docker compose ps` and `docker compose logs --tail 150 backend db worker frontend`.
- NESO requests fail: confirm internet access and inspect worker logs. Provider outages/rate limits can delay collection; values are not fabricated.
- Port is occupied: set a free `PORT` in `.env`, recreate, and open that port.

## Developer checks

```powershell
Set-Location backend
python -m pip install -e '.[test]'
pytest -q
ruff check app tests alembic
Set-Location ..\frontend
npm ci
npm test -- --run
npm run build
```

Unit tests use mocked NESO responses and SQLite. Use Compose to verify PostgreSQL, migrations, proxy connectivity, and the live collector.
