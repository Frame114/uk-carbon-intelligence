import asyncio
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote

import httpx

from app.core.config import settings
from app.utils.time import format_neso_datetime


class NesoApiError(RuntimeError):
    def __init__(self, message: str, status_code: int = 503) -> None:
        self.status_code = status_code
        super().__init__(message)


class NesoClient:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.client = client or httpx.AsyncClient(
            base_url=settings.neso_api_base_url.rstrip("/"),
            timeout=httpx.Timeout(settings.neso_timeout_seconds, connect=5.0),
            headers={"User-Agent": "UK-Carbon-Intelligence/0.1"},
        )
        self._owns_client = client is None

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    async def request(self, path: str) -> dict:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = await self.client.get(path)
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < 2:
                        retry_after = response.headers.get("Retry-After")
                        delay = min(5.0, 0.5 * (2**attempt))
                        if retry_after:
                            try:
                                delay = min(10.0, max(delay, float(retry_after)))
                            except ValueError:
                                try:
                                    date = parsedate_to_datetime(retry_after)
                                    delay = min(
                                        10.0, max(0.5, (date - datetime.now(UTC)).total_seconds())
                                    )
                                except (TypeError, ValueError, OverflowError):
                                    pass
                        await asyncio.sleep(delay)
                        continue
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict) or "data" not in payload:
                    raise NesoApiError("NESO API returned an invalid response", 502)
                return payload
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code < 500 and exc.response.status_code != 429:
                    raise NesoApiError("NESO API rejected the request", 502) from exc
                last_error = exc
            except (httpx.TimeoutException, httpx.NetworkError, ValueError) as exc:
                last_error = exc
                if attempt < 2:
                    await asyncio.sleep(0.5 * (2**attempt))
        raise NesoApiError("NESO API is temporarily unavailable", 503) from last_error

    async def current(self) -> dict:
        return await self.request("/intensity")

    async def national_forecast(self, start: datetime, horizon_hours: int = 48) -> dict:
        if horizon_hours not in (24, 48):
            raise ValueError("Forecast horizon must be 24 or 48 hours")
        return await self.request(f"/intensity/{format_neso_datetime(start)}/fw{horizon_hours}h")

    async def national_history(self, start: datetime, end: datetime) -> dict:
        return await self.request(
            f"/intensity/{format_neso_datetime(start)}/{format_neso_datetime(end)}"
        )

    async def regional_current(self) -> dict:
        return await self.request("/regional")

    async def regional_forecast(self, start: datetime, horizon_hours: int = 24) -> dict:
        if horizon_hours not in (24, 48):
            raise ValueError("Forecast horizon must be 24 or 48 hours")
        return await self.request(
            f"/regional/intensity/{format_neso_datetime(start)}/fw{horizon_hours}h"
        )

    async def regional_history(self, start: datetime, end: datetime) -> dict:
        return await self.request(
            f"/regional/intensity/{format_neso_datetime(start)}/{format_neso_datetime(end)}"
        )

    async def region_history(self, region_id: int, start: datetime, end: datetime) -> dict:
        return await self.request(
            f"/regional/intensity/{format_neso_datetime(start)}/{format_neso_datetime(end)}/regionid/{region_id}"
        )

    async def postcode_forecast(self, outward_postcode: str, start: datetime | None = None) -> dict:
        start = start or datetime.now(UTC)
        postcode = quote(outward_postcode, safe="")
        return await self.request(
            f"/regional/intensity/{format_neso_datetime(start)}/fw24h/postcode/{postcode}"
        )
