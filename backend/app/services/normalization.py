from datetime import UTC, datetime
from typing import Any

from app.utils.regions import REGIONS
from app.utils.time import parse_utc


class ProviderDataError(ValueError):
    """The provider returned a malformed or unsupported record."""


def _intensity_rows(
    item: dict[str, Any], provider_region_id: int, retrieved_at: datetime
) -> list[dict[str, Any]]:
    try:
        start = parse_utc(item["from"])
        end = parse_utc(item["to"])
        intensity = item["intensity"]
    except (KeyError, TypeError, ValueError) as exc:
        raise ProviderDataError(
            "Provider intensity record is missing valid required fields"
        ) from exc
    if end <= start or not isinstance(intensity, dict):
        raise ProviderDataError("Provider intensity interval is invalid")
    region = REGIONS.get(provider_region_id)
    rows = []
    for field, kind in (("actual", "actual"), ("forecast", "forecast")):
        value = intensity.get(field)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            raise ProviderDataError(f"Provider {field} intensity must be a non-negative number")
        rows.append(
            {
                "provider_region_id": provider_region_id,
                "region_id": region.id if region else None,
                "interval_start": start,
                "interval_end": end,
                "value_gco2_kwh": int(value),
                "kind": kind,
                "provider_index": intensity.get("index"),
                "retrieved_at": retrieved_at,
                "source_metadata": item,
            }
        )
    return rows


def normalize_national(
    payload: dict[str, Any], retrieved_at: datetime | None = None
) -> list[dict[str, Any]]:
    retrieved_at = retrieved_at or datetime.now(UTC)
    try:
        data = payload["data"]
    except (KeyError, TypeError) as exc:
        raise ProviderDataError("Provider response is missing data") from exc
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ProviderDataError("Provider data must be a list or object")
    rows = []
    for item in data:
        if not isinstance(item, dict):
            raise ProviderDataError("Provider data item must be an object")
        rows.extend(_intensity_rows(item, 18, retrieved_at))
    return rows


def normalize_regional(
    payload: dict[str, Any], retrieved_at: datetime | None = None
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Normalize all regional shapes while preserving unsupported provider IDs."""
    retrieved_at = retrieved_at or datetime.now(UTC)
    try:
        frames = payload["data"]
    except (KeyError, TypeError) as exc:
        raise ProviderDataError("Provider response is missing data") from exc
    if isinstance(frames, dict):
        frames = [frames]
    if not isinstance(frames, list):
        raise ProviderDataError("Regional provider data must be a list or object")
    rows: list[dict[str, Any]] = []
    mixes: list[dict[str, Any]] = []
    for frame in frames:
        if not isinstance(frame, dict):
            raise ProviderDataError("Regional frame must be an object")
        if isinstance(frame.get("regions"), list):
            regions = frame["regions"]
            frame_start, frame_end = frame.get("from"), frame.get("to")
        else:
            regions = frame.get("data", [])
            frame_start, frame_end = None, None
            wrapper_id = frame.get("regionid")
            if wrapper_id is not None and isinstance(regions, list):
                regions = [
                    dict(record, regionid=wrapper_id)
                    for record in regions
                    if isinstance(record, dict)
                ]
        if not isinstance(regions, list):
            continue
        for region in regions:
            if not isinstance(region, dict):
                continue
            try:
                region_id = int(region["regionid"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ProviderDataError("Regional item has no valid region ID") from exc
            item = dict(region)
            item.setdefault("from", frame_start)
            item.setdefault("to", frame_end)
            item = {key: value for key, value in item.items() if value is not None}
            normalized = _intensity_rows(item, region_id, retrieved_at)
            rows.extend(normalized)
            forecast = next((record for record in normalized if record["kind"] == "forecast"), None)
            mix = region.get("generationmix")
            if forecast and isinstance(mix, list):
                for component in mix:
                    if not isinstance(component, dict):
                        continue
                    fuel, percentage = component.get("fuel"), component.get("perc")
                    if (
                        not isinstance(fuel, str)
                        or isinstance(percentage, bool)
                        or not isinstance(percentage, (int, float))
                    ):
                        continue
                    if 0 <= percentage <= 100:
                        mixes.append(
                            {
                                "provider_region_id": region_id,
                                "interval_start": forecast["interval_start"],
                                "fuel": fuel,
                                "percentage": float(percentage),
                            }
                        )
    return rows, mixes


def to_period(
    item: dict[str, Any], region_id: int = 18, generationmix: list[dict] | None = None
) -> dict:
    try:
        intensity = item["intensity"]
        return {
            "from": parse_utc(item["from"]),
            "to": parse_utc(item["to"]),
            "region_id": region_id,
            "forecast": intensity.get("forecast"),
            "actual": intensity.get("actual"),
            "index": intensity.get("index"),
            "generation_mix": generationmix or item.get("generationmix", []),
            "provider_metadata": item,
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise ProviderDataError("Provider intensity record is malformed") from exc
