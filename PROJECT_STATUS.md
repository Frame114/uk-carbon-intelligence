# Project Status — UK Carbon Intelligence

**Current milestone:** 1 — Research and project foundation  
**Last updated:** 2026-11-14  
**Repository directory:** `uk-carbon-intelligence/`

## Completed in this workspace

- Confirmed the official API describes its data as Great Britain (GB), not the whole UK.
- Reviewed the official API reference and current terms of use.
- Probed the public national intensity, generation mix, factors and regional endpoints through the web retrieval environment.
- Confirmed outward-postcode lookup and UTC half-hour data semantics in the API reference.
- Identified documented historical query limits: 14 days for national intensity range queries; 30 days for statistics; block statistics use a 1–24 hour integer block.
- Identified a discrepancy requiring defensive implementation: official documentation enumerates region IDs 1–17, while one live /regional response returned an additional regionid: 18, shortname: GB item.
- Created the initial architecture and research documents.
- Created a standalone source-tree scaffold.

## Not yet completed

- No application backend, frontend, database or ingestion code has been implemented.
- No OpenRouter or MCP implementation exists.
- No Dockerfiles or Docker Compose deployment have been implemented.
- No automated application tests have been written or run.
- No GitHub remote repository has been created or configured.

## Environment limitations

- Git is installed in the workspace.
- Python 3.13.5 and Node.js 22.16.0 are available.
- Docker and Docker Compose are not installed in this workspace, so Docker verification cannot be performed here.
- Direct curl requests from this workspace failed because DNS resolution for api.carbonintensity.org.uk is unavailable. API endpoint observations in the research document came from web retrieval, not local runtime requests.
- No user repository or existing uk-carbon-intelligence directory was mounted when work began. This scaffold was created at /mnt/data/uk-carbon-intelligence and does not modify another project.

## Verification labels

| Capability | Status |
|---|---|
| Official documentation reviewed | Complete for initial research |
| API JSON examples retrieved | Web-retrieved sample responses |
| Direct API call from this container | Blocked by DNS/network environment |
| Backend implementation | Not started |
| Backend tests | Not started |
| Frontend implementation | Not started |
| Docker build/startup | Not verified; Docker unavailable |
| GitHub publication | Not performed |
