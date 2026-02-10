from __future__ import annotations

from datetime import datetime, time


SESSION_WINDOWS = {
    "asia": (time(0, 0), time(6, 0)),
    "london": (time(7, 0), time(10, 0)),
    "new_york": (time(12, 0), time(16, 0)),
}


def current_session(now: datetime) -> str:
    for name, (start, end) in SESSION_WINDOWS.items():
        if start <= now.time() <= end:
            return name
    return "off_session"


def in_kill_zone(now: datetime) -> bool:
    return current_session(now) in {"london", "new_york"}
