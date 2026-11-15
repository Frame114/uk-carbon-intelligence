import re

_FULL_POSTCODE = re.compile(r"^([A-Z]{1,2}\d[A-Z\d]?)\s*\d[A-Z]{2}$")
_OUTWARD_POSTCODE = re.compile(r"^(?:[A-Z]{1,2}\d[A-Z\d]?|GIR)$", re.IGNORECASE)


def normalize_outward_postcode(postcode: str) -> str:
    normalized = re.sub(r"\s+", "", postcode).upper()
    if normalized == "GIR0AA":
        return "GIR"
    if _OUTWARD_POSTCODE.fullmatch(normalized):
        return normalized
    match = _FULL_POSTCODE.fullmatch(normalized)
    if match:
        return match.group(1)
    raise ValueError("Enter a valid UK full postcode or outward postcode")
