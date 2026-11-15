from math import isfinite

VALID_PROVIDER_INDEXES = {"very low", "low", "moderate", "high", "very high"}


def classify_intensity(value: int | float | None, provider_index: str | None = None) -> str | None:
    """Prefer NESO's index; use explicit application-defined bands only as fallback."""
    if value is None:
        return None
    if not isfinite(float(value)) or value < 0:
        return "invalid"
    if provider_index:
        normalized = provider_index.strip().lower()
        if normalized in VALID_PROVIDER_INDEXES:
            return normalized
    # These display-only bands are not an official NESO classification.
    if value <= 50:
        return "very low"
    if value <= 100:
        return "low"
    if value <= 150:
        return "moderate"
    if value <= 200:
        return "high"
    return "very high"
