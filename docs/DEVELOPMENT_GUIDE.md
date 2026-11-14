# Development Guide

## Current state

This repository is currently a research and architecture scaffold. It is not yet runnable. Follow ROADMAP.md in order; do not add frontend or backend feature code until the provider fixtures and schema decisions for Milestone 2 are ready.

## Repository principles

- Keep this project independent and branded only as UK Carbon Intelligence.
- Do not change unrelated folders or repositories.
- Keep provider client models separate from internal API models.
- Write tests with each service/normalizer.
- Use UTC-aware datetime values everywhere in the backend.
- Preserve unknown provider values; do not reject new fields/region IDs without investigation.
- Never silently replace unavailable regional data with GB values.
- Never fabricate data for charts.
- Keep optional AI and MCP disabled unless explicitly configured.

## Local developer requirements (planned)

Docker Desktop and Docker Compose will be the primary way to run the full application. Direct backend/frontend development can use Python and Node toolchains, but should not be required for an end user.

The eventual Windows startup guide will use:

```powershell
git clone <repository-url>
cd uk-carbon-intelligence
Copy-Item .env.example .env
docker compose up --build
```

These commands are not yet executable because Docker configuration and services have not been implemented.

## Provider contract fixture strategy

- Save small, sanitized example payloads for national current, national historical, forecast, regional, regional-by-ID, postcode, factors and generation mix.
- Keep observation timestamps and fetch times separate.
- Add fixture coverage for optional actual, missing generationmix, unexpected region IDs, null values and error responses.
- Re-run a live contract check from a network-enabled dev machine when the provider contract changes.
- Do not persist live personal postcode inputs in logs; postcode lookup only needs to store an outward code if product functionality requires it.

## Git policy

Review diffs before commits. No commit, push, repository publication or deployment should occur without explicit user approval.
