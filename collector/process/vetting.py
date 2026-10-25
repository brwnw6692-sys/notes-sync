"""Decide which discovered candidates join the network, and in what order they are checked."""
from collector.config import CONFIG

_MIN_SAMPLES = 3


def vet_candidate(samples, days_seen: int) -> str:
    """promote / reject / pending, from a candidate's collected sample messages."""
    n = len(samples)
    if n < _MIN_SAMPLES or days_seen < 2:
        return "pending"
    arabic_persian = sum(s["lang"] in ("ar", "fa") for s in samples) / n
    with_place = sum(s["place_hits"] > 0 for s in samples) / n
    original = sum(s["is_original"] for s in samples) / n
    if (arabic_persian >= CONFIG.vet_min_arabic_persian
            and with_place >= CONFIG.vet_min_place_mentions
            and original >= CONFIG.vet_min_original):
        return "promote"
    return "reject"


def rank_candidates(candidates, blind_regions, cap: int):
    """Candidates touching blind spots are vetted first; then fill up to the daily cap."""
    def touches_blind(c):
        return bool(c.get("regions", set()) & blind_regions)
    ordered = sorted(candidates, key=lambda c: not touches_blind(c))
    return ordered[:cap]
