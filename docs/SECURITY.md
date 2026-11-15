# Security notes

- Store credentials in ignored `.env`; `.env.example` contains development placeholders only. Never commit real credentials.
- PostgreSQL is not host-published in Compose. Only the frontend port is exposed; services communicate on a private Compose network.
- Browser API calls use same-origin Nginx proxying. Set `CORS_ORIGINS` explicitly for a separate development origin.
- Provider payloads are validated before normalization; outbound requests have timeouts and bounded retries. API errors avoid returning tracebacks and database details.
- Collection errors store a sanitized exception class. Raw provider metadata is retained with observations; assess retention needs before public release.
- The local stack has no authentication. Do not expose it publicly without deployment-specific access controls, TLS, secret management, backups and security review.
- Review dependency and container updates before release. NESO currently requires no API key for these endpoints.
