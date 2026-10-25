"""The active discovery loop: grow the network by sampling the channels our sources reference.

Pure and testable — the network fetch and the encrypted store live at the edge (pipeline/live). Here we
only: fold new references into a candidate store, choose who to sample next (blind spots first), record
each sample over time, and read off the candidates that have earned a place in the registry.
"""
from collector.config import CONFIG
from collector.process.discovery import _field, extract_candidates
from collector.process.vetting import rank_candidates, vet_candidate


def _day(now) -> str:
    return now.date().isoformat()


def candidate_regions(items, sources) -> dict:
    """{handle: {regions}} for referenced channels we don't already follow; a candidate inherits
    the region of the source that referenced it, so blind-spot steering has something to go on."""
    region_of = {s["id"]: s.get("region", "") for s in sources}
    known = set(region_of)
    out: dict = {}
    for it in items:
        for h in extract_candidates([it], known):
            out.setdefault(h, set()).add(region_of.get(_field(it, "source_id"), ""))
    return out


def register(cand_state: dict, cand_regions: dict, now) -> dict:
    """Fold newly-referenced handles into the store and refresh region hints. Mutates and returns it."""
    day = _day(now)
    for handle, regions in cand_regions.items():
        regions = {r for r in regions if r}
        c = cand_state.get(handle)
        if c is None:
            cand_state[handle] = {"first_seen": day, "days": [], "samples": [],
                                  "regions": sorted(regions), "status": "pending"}
        elif c["status"] == "pending":
            c["regions"] = sorted(set(c["regions"]) | regions)
    return cand_state


def due(cand_state: dict, blind_regions, cap: int) -> list:
    """Pending handles to sample this run — blind-spot ones first, capped."""
    pend = [{"handle": h, "regions": set(c["regions"])}
            for h, c in cand_state.items() if c["status"] == "pending"]
    return [c["handle"] for c in rank_candidates(pend, set(blind_regions), cap)]


def record(cand_state: dict, handle: str, samples, now) -> str:
    """Fold sampled messages into a candidate, count distinct days seen, then vet. Returns the verdict."""
    c = cand_state[handle]
    day = _day(now)
    if day not in c["days"]:
        c["days"].append(day)
    c["samples"] = (c["samples"] + list(samples))[-CONFIG.discovery_sample_keep:]
    verdict = vet_candidate(c["samples"], days_seen=len(c["days"]))
    if verdict == "promote":
        c["status"] = "promoted"
    elif verdict == "reject":
        c["status"] = "rejected"
    return verdict


def new_promotions(cand_state: dict) -> list:
    """Promoted candidates not yet added to the registry; marks them added. Returns [(handle, region)]."""
    out = []
    for handle, c in cand_state.items():
        if c["status"] == "promoted" and not c.get("added"):
            c["added"] = True
            out.append((handle, c["regions"][0] if c["regions"] else CONFIG.discovery_default_region))
    return out
