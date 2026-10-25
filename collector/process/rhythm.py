"""Per-channel posting rhythm: a smoothed 24-hour activity profile (UTC)."""
from datetime import datetime, timezone

from collector.config import CONFIG

_KERNEL = (0.25, 0.5, 0.25)  # previous hour, this hour, next hour (wraps at midnight)
_EPS = 1e-9


def build_profile(timestamps) -> list | None:
    """Share of posts per UTC hour, smoothed. None when there isn't enough history to judge."""
    counts = [0] * 24
    n = 0
    for raw in timestamps:
        try:
            ts = datetime.fromisoformat((raw or "").replace("Z", "+00:00"))
        except ValueError:
            continue
        if ts.tzinfo is not None:
            ts = ts.astimezone(timezone.utc)
        counts[ts.hour] += 1
        n += 1
    if n < CONFIG.rhythm_min_posts:
        return None
    raw_share = [c / n for c in counts]
    return [_KERNEL[0] * raw_share[(h - 1) % 24] + _KERNEL[1] * raw_share[h] + _KERNEL[2] * raw_share[(h + 1) % 24]
            for h in range(24)]


def is_active_hour(profile, hour: int) -> bool:
    if profile is None:
        return False
    return profile[hour % 24] + _EPS >= CONFIG.rhythm_active_ratio / 24
