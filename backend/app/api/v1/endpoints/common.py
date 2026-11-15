from datetime import UTC, datetime, timedelta

from fastapi import HTTPException


def period_floor(now: datetime | None = None) -> datetime:
    now = now or datetime.now(UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    minute = 30 * (now.minute // 30)
    return now.astimezone(UTC).replace(minute=minute, second=0, microsecond=0)


def resolve_range(
    start: datetime | None, end: datetime | None, max_days: int = 14
) -> tuple[datetime, datetime]:
    end = end or datetime.now(UTC)
    start = start or end - timedelta(hours=24)
    if start.tzinfo is None or end.tzinfo is None:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "timezone_required",
                "message": "Use timezone-aware ISO-8601 timestamps.",
            },
        )
    start, end = start.astimezone(UTC), end.astimezone(UTC)
    if end <= start:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_range", "message": "End must be later than start."},
        )
    if end - start > timedelta(days=max_days):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "range_too_large",
                "message": f"The requested range cannot exceed {max_days} days.",
            },
        )
    return start, end


def error_response(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}
