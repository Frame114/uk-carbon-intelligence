from datetime import UTC, datetime, timedelta

import httpx
import pytest

from app.api.v1.dependencies import get_neso_client
from app.main import app


class FakeNesoClient:
    def __init__(self):
        current = datetime.now(UTC)
        self.now = current.replace(minute=30 * (current.minute // 30), second=0, microsecond=0)

    def record(self, start, region_id=18, value=75):
        return {
            "from": start.isoformat().replace("+00:00", "Z"),
            "to": (start + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
            "intensity": {"actual": value, "forecast": value + 4, "index": "low"},
        }

    async def current(self):
        return {"data": [self.record(self.now)]}

    async def national_forecast(self, start, horizon_hours=24):
        return {
            "data": [
                self.record(start - timedelta(minutes=30)),
                self.record(start),
                self.record(start + timedelta(minutes=30)),
            ]
        }

    async def national_history(self, start, end):
        return {
            "data": [
                self.record(start - timedelta(minutes=30)),
                self.record(start),
                self.record(start + timedelta(minutes=30)),
            ]
        }

    def region_frame(self, region_id, start, value=75):
        return {
            "regionid": region_id,
            "shortname": "GB" if region_id == 18 else "London",
            "intensity": {"forecast": value, "index": "low"},
            "generationmix": [{"fuel": "wind", "perc": 60}],
            "from": start.isoformat().replace("+00:00", "Z"),
            "to": (start + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
        }

    async def regional_current(self):
        start = self.now
        return {
            "data": [
                {
                    "from": start.isoformat().replace("+00:00", "Z"),
                    "to": (start + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
                    "regions": [
                        self.region_frame(18, start),
                        self.region_frame(19, start, 55),
                        self.region_frame(13, start, 100),
                    ],
                }
            ]
        }

    async def regional_forecast(self, start, horizon_hours=24):
        past = self.region_frame(13, start - timedelta(minutes=30))
        future = self.region_frame(13, start)
        return {"data": [{"regionid": 13, "shortname": "London", "data": [past, future]}]}

    async def regional_history(self, start, end):
        return {
            "data": [
                {
                    "from": start.isoformat().replace("+00:00", "Z"),
                    "to": (start + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
                    "regions": [self.region_frame(18, start), self.region_frame(13, start, 100)],
                }
            ]
        }

    async def region_history(self, region_id, start, end):
        return {
            "data": [
                {
                    "regionid": region_id,
                    "shortname": "London",
                    "data": [self.region_frame(region_id, start)],
                }
            ]
        }

    async def postcode_forecast(self, outward_postcode, start=None):
        item = self.region_frame(13, start or self.now, 102)
        item["postcode"] = outward_postcode
        return {
            "data": [
                {
                    "regionid": 13,
                    "shortname": "London",
                    "postcode": outward_postcode,
                    "data": [item],
                }
            ]
        }


@pytest.fixture
def fake_client():
    client = FakeNesoClient()
    app.dependency_overrides[get_neso_client] = lambda: client
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def api_client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_system_routes_and_openapi(api_client):
    assert (await api_client.get("/health")).json()["status"] == "ok"
    assert (await api_client.get("/api/v1/status")).json()["data"]["provider"][
        "name"
    ] == "NESO Carbon Intensity API"
    paths = (await api_client.get("/openapi.json")).json()["paths"]
    assert "/api/v1/carbon-intensity/current" in paths
    assert "/api/v1/regions/{region_id}/history" in paths


@pytest.mark.asyncio
async def test_current_and_forecast_keep_actual_and_forecast_distinct(api_client, fake_client):
    current = (await api_client.get("/api/v1/carbon-intensity/current")).json()["data"][0]
    assert current["actual"] == 75
    assert current["forecast"] == 79
    future = (await api_client.get("/api/v1/carbon-intensity/forecast?hours=24")).json()["data"]
    assert len(future) == 2
    assert all(
        datetime.fromisoformat(item["from"].replace("Z", "+00:00")) >= fake_client.now
        for item in future
    )
    assert fake_client


@pytest.mark.asyncio
async def test_history_applies_fourteen_day_limit_and_clips_boundary_data(api_client, fake_client):
    start, end = fake_client.now, fake_client.now + timedelta(hours=1)
    result = await api_client.get(
        "/api/v1/carbon-intensity/history",
        params={"start": start.isoformat(), "end": end.isoformat()},
    )
    assert result.status_code == 200
    assert len(result.json()["data"]) == 2
    too_far = await api_client.get(
        "/api/v1/carbon-intensity/history",
        params={"start": start.isoformat(), "end": (start + timedelta(days=15)).isoformat()},
    )
    assert too_far.status_code == 422
    assert too_far.json()["error"]["code"] == "range_too_large"


@pytest.mark.asyncio
async def test_regions_include_live_unknown_ids_and_gracefully_404_unknown_detail(
    api_client, fake_client
):
    result = await api_client.get("/api/v1/regions")
    assert result.status_code == 200
    unknown = next(item for item in result.json()["data"] if item["id"] == 19)
    assert unknown["type"] == "unknown"
    assert unknown["current"]["region_name"] == "London"
    assert (await api_client.get("/api/v1/regions/999")).status_code == 404


@pytest.mark.asyncio
async def test_postcode_full_value_normalizes_and_invalid_input_is_structured(
    api_client, fake_client
):
    result = await api_client.get("/api/v1/postcodes/SW1A%201AA/carbon-intensity")
    assert result.status_code == 200
    assert result.json()["metadata"]["postcode"] == "SW1A"
    assert result.json()["data"][0]["region_id"] == 13
    invalid = await api_client.get("/api/v1/postcodes/nonsense/carbon-intensity")
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "invalid_postcode"


@pytest.mark.asyncio
async def test_regional_comparison_uses_provider_periods_not_regional_mean(api_client, fake_client):
    now = datetime.now(UTC).replace(second=0, microsecond=0)
    result = await api_client.get(
        "/api/v1/statistics/regional-comparison",
        params=[
            ("region_ids", "13"),
            ("region_ids", "18"),
            ("start", now.isoformat()),
            ("end", (now + timedelta(hours=1)).isoformat()),
        ],
    )
    assert result.status_code == 200
    comparison = result.json()["data"]
    assert {item["region_id"] for item in comparison} == {13, 18}
    assert comparison[0]["average"] == 100
    assert "no unweighted regional average" in result.json()["metadata"]["comparison_basis"].lower()
