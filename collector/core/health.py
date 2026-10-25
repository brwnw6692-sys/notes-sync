"""Per-source health: ok / quiet / limited / broken / dead. "Quiet" is never a failure in disguise."""
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
