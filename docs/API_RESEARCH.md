# NESO Carbon Intensity API Research

**Research date:** 2026-11-14  
**Provider:** National Energy System Operator (NESO)  
**Base URL:** https://api.carbonintensity.org.uk  
**Documentation:** https://carbon-intensity.github.io/api-definitions/

## 1. Executive findings

1. The API covers **Great Britain** (England, Scotland and Wales), not the whole UK. Northern Ireland is not covered. Never label GB-only measurements as UK-wide.
2. Data is half-hourly and timestamps are UTC (+00:00). Store UTC instants and convert to Europe/London only for presentation.
3. Intensity responses can expose separate forecast, actual and index fields. Treat them as optional; do not merge forecast and actual or replace null with zero.
4. Postcode lookup accepts an outward postcode only (for example G1, ML1, EH1). It returns a regional estimate, not a property-level measurement.
5. NESO documentation enumerates region IDs 1–17. Live `/regional` responses observed during implementation include region ID 18 with short name GB; the application treats it as the GB aggregate and preserves the provider payload. Recheck this mapping against current official documentation before external publication.
6. National /intensity/{from}/{to} requests are limited to 14 days. National statistics ranges are limited to 30 days; block statistics accept 1–24 hours.
7. The API reference documents fw24h and fw48h forecast endpoints. Public website material mentions 96+ hours. Do not assume the REST API supports 96 hours until verified.
8. Documented read operations do not require authentication. NESO says the API is currently free but rate-limited and may block high-volume clients. No numeric quota was found in the reviewed reference.
9. Terms identify CC BY 4.0 but include additional restrictions. Do not imply NESO endorsement, use logos/word marks without written approval, or create a substantial replacement for NESO's core user experience.

## 2. Official resources

- API: https://api.carbonintensity.org.uk
- Definitions: https://carbon-intensity.github.io/api-definitions/
- Public information: https://carbonintensity.org.uk/
- Terms: https://github.com/carbon-intensity/terms
- Methodology: https://github.com/carbon-intensity/methodology
- National methodology: https://www.neso.energy/data-portal/national-carbon-intensity-forecast/national_carbon_intensity_forecast_methodology
- Regional methodology: https://www.neso.energy/data-portal/regional-carbon-intensity-forecast/regional_carbon_intensity_forecast_methodology

## 3. Endpoint inventory

### National intensity

| Endpoint | Purpose |
|---|---|
| GET /intensity | Current half-hour period |
| GET /intensity/date | Current UTC date series |
| GET /intensity/date/{date} | Specified date (YYYY-MM-DD) |
| GET /intensity/date/{date}/{period} | Specific settlement period (1–48) |
| GET /intensity/factors | Fuel emission factors |
| GET /intensity/{from} | Specific half-hour period |
| GET /intensity/{from}/fw24h | Forward 24 hours |
| GET /intensity/{from}/fw48h | Forward 48 hours |
| GET /intensity/{from}/pt24h | Previous 24 hours |
| GET /intensity/{from}/{to} | Arbitrary range; max 14 days |

### National statistics

- GET /intensity/stats/{from}/{to}: summary statistics, max 30-day range.
- GET /intensity/stats/{from}/{to}/{block}: block summary; block is integer 1–24 hours; max 30-day range.
- Statistics may summarise actual data for past periods and forecast data for future periods. Identify which is being summarised.

### Generation mix

- GET /generation: current generation mix (documented as beta).
- GET /generation/{from}/pt24h: previous 24 hours.
- GET /generation/{from}/{to}: specified range; contract-test range behaviour before large backfills.
- generationmix is a list of {fuel, perc}; perc is percentage contribution, not MW or MWh.

### Regional current data

- GET /regional
- GET /regional/england
- GET /regional/scotland
- GET /regional/wales
- GET /regional/postcode/{postcode}
- GET /regional/regionid/{regionid}

Regional responses may include regionid, dnoregion, shortname, intensity and generationmix.

### Regional time series

Documented patterns include /regional/intensity/{from}/fw24h, fw48h and pt24h, with optional /postcode/{postcode} or /regionid/{regionid} suffixes, plus /regional/intensity/{from}/{to} and its postcode/regionid variants. The reviewed regional arbitrary-range section does not state a maximum range. Apply a conservative local limit until directly verified.

## 4. Response contract observations

National current example shape:

```json
{
  "data": [{
    "from": "2026-11-14T14:30Z",
    "to": "2026-11-14T15:00Z",
    "intensity": {
      "forecast": 107,
      "actual": 116,
      "index": "moderate"
    }
  }]
}
```

The actual value is described as an estimated actual carbon intensity from metered generation, not a direct CO2 meter reading.

Generation responses may wrap a single object or time series differently from intensity responses. Model endpoint-specific payloads rather than assuming one universal data shape.

A live regional response contained a time bucket with from, to and a regions array. Region items contained numeric ID, DNO name, short name, intensity and generation mix. The observed response included ID 18 / GB although the published list ends at 17.

Parser requirements:
- accept unknown region IDs without crashing;
- retain raw source metadata for diagnosis;
- distinguish DNO regions from country/GB aggregates;
- do not treat ID 18 as stable until independently re-probed.

Treat forecast, actual, index, generationmix, postcode and metadata as nullable/optional where appropriate.

## 5. Published region mapping

| ID | Short name | Interpretation |
|---:|---|---|
| 1 | North Scotland | DNO |
| 2 | South Scotland | DNO |
| 3 | North West England | DNO |
| 4 | North East England | DNO |
| 5 | Yorkshire | DNO |
| 6 | North Wales | DNO |
| 7 | South Wales | DNO |
| 8 | West Midlands | DNO |
| 9 | East Midlands | DNO |
| 10 | East England | DNO |
| 11 | South West England | DNO |
| 12 | South England | DNO |
| 13 | London | DNO |
| 14 | South East England | DNO |
| 15 | England | Country aggregate |
| 16 | Scotland | Country aggregate |
| 17 | Wales | Country aggregate |

Prefer API-returned metadata backed by a stable reference table. See REGIONAL_MAPPING.md. Region 16 is the Scotland-wide aggregate; do not compute it as an unweighted average of regions 1 and 2.

## 6. Time model

- All returned times are UTC (+00:00).
- Periods are half-hourly; from is the interval start and to the next boundary.
- Date paths use YYYY-MM-DD; period lookup is documented as 1–48.
- Persist timezone-aware UTC timestamps (PostgreSQL TIMESTAMPTZ).
- Use Europe/London for display and user date selection only.
- DST transition days can have 23 or 25 local clock hours. UTC instants remain unambiguous; test DST conversion accordingly.

## 7. Forecast horizon discrepancy

The API reference documents fw24h and fw48h and describes forecasts up to two days ahead. Public information mentions 96+ hours, while another description labels a display -24hrs to +48hrs.

Implement fw24h/fw48h first. Do not advertise a 96-hour REST forecast until a supported route is documented and live-tested. Treat horizon as a provider capability, not a hard-coded promise.

## 8. History limitations

- National intensity arbitrary range: maximum 14 days per request.
- National statistics: maximum 30 days.
- Statistics block: 1–24 integer hours.
- Website CSV downloads reportedly have a 30-day limit and cannot cross years; do not assume this website UI limit is identical to API limits.
- Contract-test exact UTC date handling and regional range limits.

Chunk national backfills into at most 14-day requests. Use statistics endpoints for summaries, but calculate reproducible analytics from stored normalized observations when precise filtering is required.

## 9. Carbon intensity and generation methodology

The measure is gCO2/kWh. NESO's public description accounts for large metered power stations, interconnector imports, transmission/distribution losses, national demand and embedded wind/solar. Regional estimates use a reduced GB network model and power-flow calculations to attribute emissions to electricity consumed in each region.

The public methodology describes half-hourly regional demand and generation-by-fuel forecasts, supervised ML regression ensembles, 30-minute updates and short-term nowcasting, plus network-flow modelling. The displayed actual remains an estimate, not a complete lifecycle emissions score or a direct measurement at each property.

Generation rules:
- Renewable and low-carbon are distinct; nuclear may be low-carbon but is not renewable.
- Imports remain separate because intensity varies by origin.
- Do not silently classify biomass or other as zero-carbon/renewable.
- Do not derive provider intensity from a simplistic weighted average of fuel shares and generic factors.
- Percentages are not MW, MWh or intensity values.

## 10. Authentication, rate limits and attribution

- Documented read endpoints do not require authentication.
- Terms say the API is currently free and rate-limited; high-volume applications may be blocked.
- No numeric quota was found in the reviewed docs.
- Use a single regional request per cadence where possible, persist results, cache reads, avoid per-widget polling and apply bounded 429 backoff.
- Terms identify CC BY 4.0 but also restrict substantial replacement of NESO's core experience, false endorsement, resale/sublicensing of API access and unauthorised use of NESO marks/logos.
- Attribute: “Data source: National Energy System Operator (NESO) Carbon Intensity API”, link to the official source and state that this is an independent project. Review live terms before external release.

## 11. HTTP resilience

Anticipate timeouts, connection failures, malformed JSON, HTTP 429 and 5xx responses.

Client requirements:
- asynchronous httpx client with explicit connect/read/write/pool timeouts;
- one shared connection pool per process;
- bounded retries only for transient failures (timeouts, 5xx, 429);
- respect Retry-After where present;
- exponential backoff with jitter and a hard maximum;
- no retries for validation errors (400) or unknown routes (404);
- structured logs without secrets;
- last-successful-fetch timestamp and freshness evaluation;
- limited raw payload diagnostics with retention controls.

## 12. Verified facts and unresolved questions

Verified from reviewed official docs/site:
- GB scope; public national and regional endpoint families;
- no authentication for public read operations;
- outward postcode only; UTC half-hour periods;
- national range limit 14 days; statistics range 30 days and blocks 1–24 hours;
- official index labels: very low, low, moderate, high, very high;
- API currently free, rate-limited and subject to change;
- CC BY 4.0 identified in API docs/terms.

Requires repeatable local verification:
- why a regional response contained ID 18 (GB) while docs list 1–17;
- synchronization of Scotland and regional endpoints;
- exact freshness guarantees and numeric quota;
- historical depth for each endpoint;
- regional arbitrary-range maximum;
- any REST forecast horizon beyond 48 hours;
- authoritative classification thresholds;
- biomass and other fuel treatment.

## 13. Sources

1. https://api.carbonintensity.org.uk/
2. https://carbon-intensity.github.io/api-definitions/
3. https://carbonintensity.org.uk/
4. https://github.com/carbon-intensity/terms
5. https://github.com/carbon-intensity/methodology
6. https://www.neso.energy/data-portal/national-carbon-intensity-forecast/national_carbon_intensity_forecast_methodology
7. https://www.neso.energy/data-portal/regional-carbon-intensity-forecast/regional_carbon_intensity_forecast_methodology
