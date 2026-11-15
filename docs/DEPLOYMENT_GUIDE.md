# Deployment guide

The supported deployment here is local Docker Compose. Windows 11 instructions are in `../LOCAL_TESTING_GUIDE.md`.

1. Copy `.env.example` to `.env`; configure a local PostgreSQL password and matching URL-encoded `DATABASE_URL` credentials.
2. Run `docker compose config --quiet` to validate environment interpolation.
3. Run `docker compose up --build -d` and wait for database, backend and frontend health checks.
4. Open `http://localhost:8080`; verify `/ready` and `/api/v1/collection/status`.
5. Use `docker compose logs -f` to inspect service output.

The database uses a named persistent volume. The frontend Nginx service proxies API requests over the private Compose network. `PORT` changes the host port. `docker compose down` keeps database data; `docker compose down -v` deletes it. This local stack is not hardened for public production. Public deployment requires TLS, managed secrets, backups, access controls and monitoring.
