import httpx
import pytest

from app.clients.neso import NesoApiError, NesoClient


@pytest.mark.asyncio
async def test_client_retries_rate_limit_then_accepts_valid_json(monkeypatch):
    calls = 0
    delays = []

    async def sleep(delay):
        delays.append(delay)

    async def handler(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, json={"error": "slow down"})
        return httpx.Response(200, json={"data": []})

    monkeypatch.setattr("app.clients.neso.asyncio.sleep", sleep)
    client = NesoClient(
        httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://api.test")
    )
    try:
        assert await client.request("/intensity") == {"data": []}
        assert calls == 2
        assert delays == [0.5]
    finally:
        await client.client.aclose()


@pytest.mark.asyncio
async def test_client_does_not_retry_bad_request(monkeypatch):
    calls = 0

    async def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(400, json={"error": "bad request"})

    async def no_sleep(_):
        raise AssertionError("4xx responses must not be retried")

    monkeypatch.setattr("app.clients.neso.asyncio.sleep", no_sleep)
    client = NesoClient(
        httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://api.test")
    )
    try:
        with pytest.raises(NesoApiError) as error:
            await client.request("/invalid")
        assert error.value.status_code == 502
        assert calls == 1
    finally:
        await client.client.aclose()
