from datetime import UTC, datetime

import pytest

from app.services.normalization import ProviderDataError, normalize_national, normalize_regional
from app.utils.postcode import normalize_outward_postcode
from app.utils.regions import get_region
from app.utils.time import parse_utc


def test_national_actual_and_forecast_are_separate_and_zero_is_retained():
    payload = {
        "data": [
            {
                "from": "2026-11-14T10:00Z",
                "to": "2026-11-14T10:30Z",
                "intensity": {"actual": 0, "forecast": 42, "index": "very low"},
            }
        ]
    }
    rows = normalize_national(payload, datetime(2026, 11, 14, 10, 35, tzinfo=UTC))
    assert [(row["kind"], row["value_gco2_kwh"]) for row in rows] == [
        ("actual", 0),
        ("forecast", 42),
    ]
    assert rows[0]["provider_region_id"] == 18
    assert rows[0]["interval_start"].tzinfo == UTC


def test_optional_actual_does_not_become_zero():
    payload = {
        "data": [
            {
                "from": "2026-11-14T10:00Z",
                "to": "2026-11-14T10:30Z",
                "intensity": {"actual": None, "forecast": 17, "index": "very low"},
            }
        ]
    }
    rows = normalize_national(payload)
    assert len(rows) == 1
    assert rows[0]["kind"] == "forecast"
    assert rows[0]["value_gco2_kwh"] == 17


def test_missing_data_and_negative_values_are_rejected():
    with pytest.raises(ProviderDataError):
        normalize_national({"unexpected": []})
    with pytest.raises(ProviderDataError):
        normalize_national(
            {
                "data": [
                    {
                        "from": "2026-11-14T10:00Z",
                        "to": "2026-11-14T10:30Z",
                        "intensity": {"forecast": -1},
                    }
                ]
            }
        )


def test_regional_mapping_preserves_documented_and_unknown_ids():
    payload = {
        "data": [
            {
                "from": "2026-11-14T10:00Z",
                "to": "2026-11-14T10:30Z",
                "regions": [
                    {
                        "regionid": 18,
                        "shortname": "GB",
                        "intensity": {"forecast": 66, "index": "low"},
                        "generationmix": [{"fuel": "wind", "perc": 55}],
                    },
                    {
                        "regionid": 27,
                        "shortname": "New region",
                        "intensity": {"forecast": 12, "index": "very low"},
                    },
                ],
            }
        ]
    }
    observations, mix = normalize_regional(payload)
    assert [row["provider_region_id"] for row in observations] == [18, 27]
    assert observations[0]["region_id"] == 18
    assert observations[1]["region_id"] is None
    assert observations[1]["source_metadata"]["shortname"] == "New region"
    assert mix == [
        {
            "provider_region_id": 18,
            "interval_start": datetime(2026, 11, 14, 10, 0, tzinfo=UTC),
            "fuel": "wind",
            "percentage": 55.0,
        }
    ]
    assert get_region(27).type == "unknown"


def test_postcode_normalization_accepts_full_and_outward_codes():
    assert normalize_outward_postcode("sw1a 1aa") == "SW1A"
    assert normalize_outward_postcode("RG10") == "RG10"
    assert normalize_outward_postcode("GIR 0AA") == "GIR"
    with pytest.raises(ValueError):
        normalize_outward_postcode("not a postcode")


def test_utc_parser_normalizes_offsets_and_naive_timestamps():
    assert parse_utc("2026-11-14T10:00:00+01:00") == datetime(2026, 11, 14, 9, 0, tzinfo=UTC)
    assert parse_utc("2026-11-14T10:00:00") == datetime(2026, 11, 14, 10, 0, tzinfo=UTC)
