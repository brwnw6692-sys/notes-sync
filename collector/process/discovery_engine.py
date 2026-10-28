"""The active discovery loop: grow the network by sampling the channels our sources reference.

Pure and testable — the network fetch and the encrypted store live at the edge (pipeline/live). Here we
only: fold new references into a candidate store, choose who to sample next (blind spots first), record
each sample over time, and read off the candidates that have earned a place in the registry.
"""
from collector.config import CONFIG
from collector.process.affiliation import classify_affiliation, dominant_affiliation
from collector.process.discovery import _field, extract_candidates
from collector.process.vetting import candidate_lens, rank_candidates, vet_candidate


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


def due(cand_state: dict, blind_regions, cap: int, today: str) -> list:
    """Pending handles to sample this run. Rotate: never-sampled and least-recently-sampled first,
    each sampled at most once a day, so a big backlog is worked through fairly instead of starving
    behind the same few front-runners."""
    blind = set(blind_regions)
    pend = [(h, c) for h, c in cand_state.items()
            if c["status"] == "pending" and c.get("last_sampled") != today]
    # key: never-sampled ("") first, then oldest last_sampled, then blind-touch as a tiebreak
    pend.sort(key=lambda hc: (hc[1].get("last_sampled") or "",
                              not (set(hc[1]["regions"]) & blind)))
    return [h for h, _ in pend[:cap]]


def record(cand_state: dict, handle: str, samples, now, texts=()) -> str:
    """Fold sampled messages into a candidate, count distinct days seen, tally the actor markers in its
    text, then vet. Returns the verdict; on promotion sets the lens and (if clear) the affiliation."""
    c = cand_state[handle]
    day = _day(now)
    c["last_sampled"] = day
    if day not in c["days"]:
        c["days"].append(day)
    c["samples"] = (c["samples"] + list(samples))[-CONFIG.discovery_sample_keep:]
    tally = c.setdefault("affil_tally", {})
    for t in texts:
        a = classify_affiliation(t)
        if a:
            tally[a] = tally.get(a, 0) + 1
    verdict = vet_candidate(c["samples"], days_seen=len(c["days"]))
    if verdict == "promote":
        c["status"] = "promoted"
        c["lens"] = candidate_lens(c["samples"])        # ar / fa / he — the reporting window
        c["affiliation"] = dominant_affiliation(tally)  # actor orientation, or '' when unclear
    elif verdict == "reject":
        c["status"] = "rejected"
    return verdict


def new_promotions(cand_state: dict) -> list:
    """Promoted candidates not yet added; marks them added. Returns [(handle, region, lens, affiliation)]."""
    out = []
    for handle, c in cand_state.items():
        if c["status"] == "promoted" and not c.get("added"):
            c["added"] = True
            region = c["regions"][0] if c["regions"] else CONFIG.discovery_default_region
            out.append((handle, region, c.get("lens", ""), c.get("affiliation", "")))
    return out
