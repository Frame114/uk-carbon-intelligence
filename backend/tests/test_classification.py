import math

import pytest

from app.services.classification import classify_intensity


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, "very low"),
        (50, "very low"),
        (50.1, "low"),
        (100, "low"),
        (100.1, "moderate"),
        (150, "moderate"),
        (150.1, "high"),
        (200, "high"),
        (200.1, "very high"),
    ],
)
def test_application_defined_fallback_boundaries(value, expected):
    assert classify_intensity(value) == expected


def test_provider_index_takes_precedence_over_presentation_fallback():
    assert classify_intensity(40, "high") == "high"


@pytest.mark.parametrize("value", [None, -1, math.nan, math.inf, -math.inf])
def test_missing_and_invalid_values_are_safe(value):
    expected = None if value is None else "invalid"
    assert classify_intensity(value) == expected


def test_unknown_provider_index_uses_documented_fallback():
    assert classify_intensity(88, "future-provider-index") == "low"
