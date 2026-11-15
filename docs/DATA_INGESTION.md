# Data ingestion

`python -m app.worker` runs a separate collection loop, every 1800 seconds by default (`COLLECTION_INTERVAL_SECONDS`). Each cycle requests national current, national 48-hour forecast, regional current and regional 24-hour forecast from NESO. The async HTTP client applies a request timeout and bounded retries for transient and rate-limit responses.

Normalization validates interval timestamps and order, preserves UTC periods and distinct actual/forecast values, and rejects invalid negative intensity. Provider region IDs and source metadata are retained. Region rows are ensured before observation writes. Generation mix is saved as descriptive source data only; it never derives intensity.

Each run is recorded as running then success or failed. `records_received` counts normalized provider rows; `records_written` counts newly inserted archive rows, excluding conflicts that update existing rows. Failure status records a sanitized exception class; diagnostics are available in worker logs. Missing provider periods are not filled. Dashboard data/history routes currently call NESO directly; the worker archive supports persistence and collection status.
