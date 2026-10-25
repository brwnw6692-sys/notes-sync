"""The user-managed source registry: which channels we watch. Separate from machine run-state."""
import re

_HANDLE = re.compile(r"^[A-Za-z]\w{4,31}$")  # Telegram public handle rule
_RUNTIME_FIELDS = ("cursor", "consecutive_404", "last_post_at")


def _norm(handle: str) -> str:
    return handle.lstrip("@").lower()


def add_source(sources, handle, region, tier="quiet", canary=False, discovered=False):
    """Add or update a source. Idempotent by normalized handle. Returns a new list.
    discovered=True marks a channel the discovery engine found, so it is distinguishable from
    the user's own seeds — and a re-add never clobbers a handle the user already curates."""
    sid = _norm(handle)
    if not _HANDLE.match(sid):
        raise ValueError(f"invalid channel handle: {handle!r}")
    existing = next((s for s in sources if s["id"] == sid), None)
    if existing is not None and discovered:
        return [dict(s) for s in sources]        # never overwrite a curated source with a discovery
    entry = {"id": sid, "region": region, "tier": tier, "status": "active", "canary": bool(canary)}
    if discovered:
        entry["discovered"] = True
    out = [dict(s) for s in sources if s["id"] != sid]
    out.append(entry)
    return out


def remove_source(sources, handle):
    sid = _norm(handle)
    return [dict(s) for s in sources if s["id"] != sid]


def merge_runtime(registry, prior_state_sources):
    """Overlay saved per-source runtime (cursor, counters) onto the registry, keyed by id."""
    by_id = {s["id"]: s for s in prior_state_sources}
    merged = []
    for reg in registry:
        prev = by_id.get(reg["id"], {})
        row = dict(reg)
        row["cursor"] = prev.get("cursor", {"last_native_id": 0})
        row["consecutive_404"] = prev.get("consecutive_404", 0)
        if "last_post_at" in prev:
            row["last_post_at"] = prev["last_post_at"]
        merged.append(row)
    return merged
