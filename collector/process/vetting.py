"""Decide which discovered candidates join the network, in what order, and under which lens.

A source is accepted if it reports Middle East places in a Middle East language — Arabic, Persian, or
Hebrew. Hebrew is not an exception: Israel is a first-class lens, the one non-Arab window on the region.
"""
from collections import Counter

from collector.config import CONFIG

_MIN_SAMPLES = 3
_LENSES = ("ar", "fa", "he")


def candidate_lens(samples) -> str:
    """The dominant Middle East language across a candidate's samples — its reporting lens."""
    counts = Counter(s["lang"] for s in samples if s["lang"] in _LENSES)
    return counts.most_common(1)[0][0] if counts else ""


def vet_candidate(samples, days_seen: int) -> str:
    """promote / reject / pending, from a candidate's collected sample messages."""
    n = len(samples)
    if n < _MIN_SAMPLES or days_seen < 2:
        return "pending"
    relevant = sum(s["lang"] in _LENSES for s in samples) / n
    with_place = sum(s["place_hits"] > 0 for s in samples) / n
    original = sum(s["is_original"] for s in samples) / n
    if (relevant >= CONFIG.vet_min_relevant_lang
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
