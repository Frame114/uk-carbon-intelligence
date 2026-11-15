from datetime import UTC, datetime

from app.services.classification import classify_intensity
from app.services.normalization import ProviderDataError, to_period
from app.utils.regions import get_region
from app.utils.time import parse_utc

SOURCE = {
    "provider": "National Energy System Operator (NESO)",
    "name": "NESO Carbon Intensity API",
    "url": "https://api.carbonintensity.org.uk",
    "license": "CC BY 4.0",
}


def metadata(stale: bool = False) -> dict:
    return {
        "source": SOURCE,
        "retrieved_at": datetime.now(UTC),
        "timezone": "UTC",
        "stale": stale,
    }


def present_period(item: dict, region_id: int = 18) -> dict:
    normalized = to_period(item, region_id=region_id)
    region = get_region(region_id)
    forecast = normalized["forecast"]
    actual = normalized["actual"]
    return {
        "from": normalized["from"],
        "to": normalized["to"],
        "region_id": region_id,
        "region_name": region.name,
        "region_type": region.type,
        "forecast": forecast,
        "actual": actual,
        "index": normalized["index"],
        "forecast_classification": classify_intensity(forecast, normalized["index"]),
        "actual_classification": classify_intensity(actual),
        "generation_mix": normalized["generation_mix"],
    }


def national_periods(payload: dict, region_id: int = 18) -> list[dict]:
    data = payload.get("data")
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ProviderDataError("NESO response data is not a list or object")
    return [present_period(item, region_id) for item in data if isinstance(item, dict)]


def regional_periods(payload: dict) -> list[dict]:
    frames = payload.get("data")
    if isinstance(frames, dict):
        frames = [frames]
    if not isinstance(frames, list):
        raise ProviderDataError("NESO regional response data is not a list or object")
    result: list[dict] = []
    for frame in frames:
        if not isinstance(frame, dict):
            continue
        if isinstance(frame.get("regions"), list):
            for region_item in frame["regions"]:
                if not isinstance(region_item, dict):
                    continue
                region_id = int(region_item.get("regionid", -1))
                item = dict(region_item)
                item["from"] = frame.get("from")
                item["to"] = frame.get("to")
                result.append(_present_regional_item(item, region_id))
        elif frame.get("regionid") is not None and isinstance(frame.get("data"), list):
            region_id = int(frame["regionid"])
            for record in frame["data"]:
                if isinstance(record, dict):
                    item = dict(record)
                    item.setdefault("regionid", region_id)
                    result.append(_present_regional_item(item, region_id))
        elif frame.get("regionid") is not None and isinstance(frame.get("intensity"), dict):
            region_id = int(frame["regionid"])
            result.append(_present_regional_item(frame, region_id))
    return result


def _present_regional_item(item: dict, region_id: int) -> dict:
    result = present_period(item, region_id)
    result["region_name"] = item.get("shortname") or get_region(region_id).name
    result["region_type"] = get_region(region_id).type
    result["provider_region_name"] = item.get("dnoregion")
    result["generation_mix"] = item.get("generationmix", [])
    result["postcode"] = item.get("postcode")
    return result


def clip_periods(periods: list[dict], start: datetime, end: datetime) -> list[dict]:
    start, end = parse_utc(start), parse_utc(end)
    return [
        period
        for period in periods
        if parse_utc(period["from"]) >= start and parse_utc(period["from"]) < end
    ]
