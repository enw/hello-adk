import os
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def get_datetime(timezone: str = "") -> dict:
    """Get the current date, weekday, and time.

    Call this before answering anything about today, now, a date, a weekday,
    or scheduling; never guess the current date.

    Args:
        timezone: IANA zone name such as America/New_York. Empty means the
            server's configured default (APP_TIMEZONE, else UTC).
    """
    zone_name = timezone.strip() or os.environ.get("APP_TIMEZONE", "") or "UTC"
    try:
        now = datetime.now(ZoneInfo(zone_name))
    except (ZoneInfoNotFoundError, ValueError):
        return {"error": f"Unknown timezone {zone_name!r}; use an IANA name such as America/New_York."}
    return {
        "date": now.strftime("%Y-%m-%d"),
        "weekday": now.strftime("%A"),
        "time": now.strftime("%H:%M:%S"),
        "timezone": zone_name,
        "iso": now.isoformat(timespec="seconds"),
        "unix": int(now.timestamp()),
    }
