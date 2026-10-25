"""Which sources are polled this run: backlog, then red regions, then hot, then the quiet slice."""
import hashlib

from collector.config import CONFIG


def _offset(source_id: str, slots: int) -> int:
    # Stable per source, so quiet sources spread evenly across the hour.
    return int(hashlib.blake2b(source_id.encode(), digest_size=4).hexdigest(), 16) % slots


def plan_run(sources, run_index: int, minutes: int, red_regions, budget: int,
             backlog=(), active_now=frozenset()):
    """Returns (selected, overflow_ids). Overflow should be passed as backlog next run.

    active_now: ids of quiet-tier sources currently inside their learned rhythm window.
    """
    active = {s["id"]: s for s in sources if s.get("status", "active") == "active"}
    slots = max(1, CONFIG.quiet_every_min // minutes)

    red = [s for s in active.values() if s["region"] in red_regions]
    hot = [s for s in active.values() if s["tier"] == "hot"]
    in_rhythm = [s for s in active.values() if s["id"] in active_now]
    quiet = [s for s in active.values()
             if s["tier"] != "hot" and _offset(s["id"], slots) == run_index % slots]

    ordered, seen = [], set()
    for s in [active[i] for i in backlog if i in active] + red + hot + in_rhythm + quiet:
        if s["id"] not in seen:
            seen.add(s["id"])
            ordered.append(s)
    return ordered[:budget], [s["id"] for s in ordered[budget:]]
