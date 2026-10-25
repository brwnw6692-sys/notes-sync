"""Per-source health: ok / quiet / limited / broken / dead. "Quiet" is never a failure in disguise."""
from datetime import datetime, timedelta, timezone

from collector.config import CONFIG


def classify(result, prior_not_found: int = 0) -> str:
    """prior_not_found: consecutive 404s already recorded for this source."""
    if result.http_status == 429:
        return "limited"
    if result.http_status == 404:
        if prior_not_found + 1 >= CONFIG.dead_after_consecutive_fails:
            return "dead"
        return "broken"
    if not result.fetch_ok or not result.structure_ok:
        return "broken"
    if result.error_kind == "partial":
        return "limited"
    return "ok" if result.items else "quiet"


def abnormal_silence(median_gap_sec: float, silent_sec: float,
                     factor: int = CONFIG.silence_factor,
                     floor_hours: int = CONFIG.silence_floor_hours) -> bool:
    """A signal for detection, not a fault: a usually chatty source has gone unusually quiet."""
    if median_gap_sec <= 0 or silent_sec < floor_hours * 3600:
        return False
    return silent_sec >= median_gap_sec * factor


def expected_posts(profile, posts_per_day: float, start: datetime, end: datetime) -> float:
    """Posts the channel's rhythm predicts between start and end (partial hours count proportionally)."""
    total = 0.0
    t = start.astimezone(timezone.utc) if start.tzinfo else start   # profile hours are UTC
    end = end.astimezone(timezone.utc) if end.tzinfo else end
    while t < end:
        hour_end = t.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        step_end = min(hour_end, end)
        fraction = (step_end - t).total_seconds() / 3600
        total += fraction * profile[t.hour] * posts_per_day
        t = step_end
    return total


def silence_signal(profile, posts_per_day: float, median_gap_sec: float,
                   silent_since: datetime, now: datetime) -> bool:
    """Unusual silence, judged against what this channel normally posts at these hours.

    Falls back to the median-gap rule when the channel has no rhythm profile yet.
    """
    silent_sec = (now - silent_since).total_seconds()
    if silent_sec < CONFIG.silence_floor_hours * 3600:
        return False
    if profile is None:
        return abnormal_silence(median_gap_sec, silent_sec)
    return expected_posts(profile, posts_per_day, silent_since, now) >= CONFIG.silence_min_expected_posts
