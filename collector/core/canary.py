"""System-level sight check. Canaries are always-active public sources; if they go dark, we are blind."""
from datetime import datetime

from collector.config import CONFIG

_FAILING_STATES = {"broken", "limited", "dead"}


def canary_failing(canary: dict, now: datetime) -> bool:
    if canary.get("state") in _FAILING_STATES:
        return True
    raw = canary.get("last_post_at") or ""
    try:
        last = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return True
    return (now - last).total_seconds() > CONFIG.canary_max_silence_hours * 3600


def system_sight(canaries: list, now: datetime) -> dict:
    """healthy / degraded / blind / unknown. When we can't trust our sight, silence is not a signal."""
    total = len(canaries)
    if total == 0:
        return {"sight": "unknown", "suppress_silence_signals": True, "failing": 0, "total": 0}
    failing = sum(canary_failing(c, now) for c in canaries)
    if failing / total >= CONFIG.canary_blind_fraction:
        sight = "blind"
    elif failing:
        sight = "degraded"
    else:
        sight = "healthy"
    return {"sight": sight, "suppress_silence_signals": sight == "blind",
            "failing": failing, "total": total}
