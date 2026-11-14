# Regional Mapping

## Supported published regions

The official reference enumerates 14 geographical DNO regions plus England, Scotland and Wales aggregate regions. The GB source excludes Northern Ireland.

| ID | Official short name | Kind |
|---:|---|---|
| 1 | North Scotland | DNO region |
| 2 | South Scotland | DNO region |
| 3 | North West England | DNO region |
| 4 | North East England | DNO region |
| 5 | Yorkshire | DNO region |
| 6 | North Wales | DNO region |
| 7 | South Wales | DNO region |
| 8 | West Midlands | DNO region |
| 9 | East Midlands | DNO region |
| 10 | East England | DNO region |
| 11 | South West England | DNO region |
| 12 | South England | DNO region |
| 13 | London | DNO region |
| 14 | South East England | DNO region |
| 15 | England | Country aggregate |
| 16 | Scotland | Country aggregate |
| 17 | Wales | Country aggregate |

## Live-response discrepancy

A web-retrieved /regional response on 2026-11-14 contained an additional item:

- regionid: 18
- dnoregion: GB
- shortname: GB

The public reference's region list and schema still state IDs 1–17. This item should not be added to the stable region enum solely from one retrieval. Implement dynamic parsing and preserve unknown source metadata. Re-probe the endpoint from the development host before deciding whether ID 18 is a new supported GB aggregate.

## Scottish presentation

- Region 1 = North Scotland DNO region.
- Region 2 = South Scotland DNO region.
- Region 16 = Scotland-wide aggregate.

The Scotland-wide aggregate must not be calculated as an unweighted average of regions 1 and 2. Use the provider's Scotland aggregate endpoint/region 16 for the country-level card. Show regions 1 and 2 separately as DNO-region comparisons. Do not infer a national Scottish average from only these two records unless the provider methodology supports that operation.

## Runtime mapping rules

1. Preserve provider regionid, dnoregion and shortname exactly as returned.
2. Use a reference table for known region meanings but allow unknown IDs.
3. Distinguish DNO regions and aggregate geographies in the UI.
4. Do not label a GB aggregate as England, Scotland or UK.
5. Do not return a national fallback if a postcode fails to resolve.
6. Use postcode-derived region metadata from the provider as authoritative at query time.
7. Track metadata changes rather than overwriting history silently.

## Source

Official API reference: https://carbon-intensity.github.io/api-definitions/#regions
