from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re
import dateparser

TZ = ZoneInfo("Asia/Kolkata")
DAYPARTS = {"morning": 9, "noon": 12, "afternoon": 15, "evening": 18, "night": 20, "tonight": 20}


def parse_when(text: str, now: datetime | None = None):
    if not text or not text.strip():
        return None
    now = now or datetime.now(TZ)
    parsed = dateparser.parse(
        text,
        settings={
            "PREFER_DATES_FROM": "future",
            "TIMEZONE": "Asia/Kolkata",
            "RETURN_AS_TIMEZONE_AWARE": True,
            "RELATIVE_BASE": now,
        },
    )
    if not parsed:
        return None
    parsed = parsed.astimezone(TZ)
    has_clock_time = any(token in text.lower() for token in ("am", "pm", ":"))
    if not has_clock_time:
        hour = next((value for word, value in DAYPARTS.items() if word in text.lower()), 10)
        parsed = parsed.replace(hour=hour, minute=0, second=0, microsecond=0)
    if parsed <= now:
        parsed += timedelta(days=1)
    return parsed


def display_when(value: datetime) -> str:
    return value.astimezone(TZ).strftime("%a %d %b, %I:%M %p")
