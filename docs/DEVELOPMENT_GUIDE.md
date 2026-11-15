# Development Guide

## Current implementation

This repository contains a runnable local application: FastAPI backend, React/TypeScript/Vite frontend, PostgreSQL persistence, Alembic migration, NESO collector worker, and Docker Compose deployment. For Windows 11 setup follow `LOCAL_TESTING_GUIDE.md`.

## Repository principles

- Keep the product independent and branded only as UK Carbon Intelligence.
- Keep provider payload handling separate from public response schemas.
- Use timezone-aware UTC instants in backend/storage; convert to Europe/London in presentation.
- Preserve unknown provider region IDs and optional values. Never map unavailable regional data to GB.
- Do not fabricate chart values or derive intensity from generation mix.
- Keep AI and MCP out of the active product unless separately specified.
- Run backend tests/Ruff and frontend tests/build after code changes.

## Local development

Full stack: copy `.env.example` to `.env`, set the database password, run `docker compose config --quiet`, then `docker compose up --build -d`. Direct frontend development uses `npm ci` and `npm run dev` in `frontend`; direct backend setup uses `pip install -e '.[test]'` in `backend`. The frontend dev server uses the Vite proxy configured in `vite.config.ts`.

## Provider fixtures and testing

Backend tests use mocked HTTPX transport for API behavior, client retry behavior, normalization, classification, and SQLite persistence. Frontend tests use Vitest and Testing Library. Compose is used to check PostgreSQL, migrations, Nginx proxying, and the live worker. Avoid depending on volatile live provider payloads for deterministic unit tests.

## Git

Review status and diffs before committing. Do not publish secrets; `.env` is ignored.
