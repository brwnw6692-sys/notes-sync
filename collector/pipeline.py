"""The testable core of one scheduled run: load state -> run_once -> persist, all under the data root."""
from datetime import datetime
from pathlib import Path

from collector.config import CONFIG
from collector.core.orchestrator import run_once
from collector.geo.snapshot import build_snapshot, locate_rows, save_snapshot
from collector.process import discovery_engine as de
from collector.process.source_register import add_source, merge_runtime
from collector.run import process_items
from collector.store import state_store


def _blind_spot_search(cand, key, root, blind, search, now) -> None:
    """Turn the hottest blind cells into Arabic place queries and fold the results in as candidates —
    the map sends scouts to its own gaps. One cell is probed at most once a day."""
    if not search or not blind:
        return
    # Don't keep finding doors we can't walk through: pause search while the backlog is deep.
    pending = sum(1 for c in cand.values() if c["status"] == "pending")
    if pending >= CONFIG.discovery_max_pending:
        return
    from collector.geo.gazetteer import gazetteer_entries
    from collector.geo.grid import cell_id, cell_of
    from collector.geo.reverse import queries_in_cell
    entries = gazetteer_entries()
    half = CONFIG.grid_cell_deg / 2
    log = state_store.load_searches(key, root)
    day = now.date().isoformat()
    done = 0
    for b in sorted(blind, key=lambda b: -b.get("heat", 0)):
        rc = cell_of(b["lat"], b["lon"])
        if rc is None or log.get(cell_id(rc)) == day:
            continue
        queries = queries_in_cell(entries, b["lat"], b["lon"], half)  # Arabic and/or Hebrew
        log[cell_id(rc)] = day
        if queries:
            for q in queries:
                de.register(cand, {h: {q} for h in search(q)}, now)
            done += 1
            if done >= CONFIG.discovery_searches_per_run:
                break
    state_store.save_searches(log, key, root)


def _discover(root, key, fetch, items, sources, now, blind=None, search=None) -> dict:
    """Grow the network: fold in referenced channels and blind-spot search hits, sample a few public
    pages (blind spots first), and auto-enroll any that earn it. Returns {promoted, tracked} metrics."""
    cand = state_store.load_candidates(key, root)
    de.register(cand, de.candidate_regions(items, sources), now)
    _blind_spot_search(cand, key, root, blind or [], search, now)

    covered = {s.get("region") for s in sources if s.get("status", "active") == "active"}
    blind = {r for c in cand.values() for r in c["regions"]} - covered
    for handle in de.due(cand, blind, CONFIG.discovery_per_run, today=now.date().isoformat()):
        res = fetch({"id": handle}, None)
        if not getattr(res, "fetch_ok", False):
            continue
        sampled = process_items(res.items)
        de.record(cand, handle, [{"lang": it.lang, "place_hits": len(it.tags.get("places", [])),
                                   "is_original": it.is_original} for it in sampled], now)

    promos = de.new_promotions(cand)
    if promos:
        registry = state_store.load_sources(key, root)
        for handle, region, lens in promos:
            registry = add_source(registry, handle, region, tier="quiet", discovered=True, lens=lens)
        state_store.save_sources(registry, key, root)
    state_store.save_candidates(cand, key, root)
    return {"promoted": len(promos), "tracked": len(cand)}


def execute_run(root: Path, key: bytes, fetch, now: datetime, budget: int, search=None) -> dict:
    state = state_store.load_state(key, root)
    # The registry (user-managed) is authoritative for WHICH sources to watch;
    # prior run-state supplies each one's cursor and counters.
    registry = state_store.load_sources(key, root)
    if registry:
        state["sources"] = merge_runtime(registry, state.get("sources", []))

    result = run_once(state, fetch, now, budget)

    state_store.save_state(result.new_state, key, root)
    if result.items:
        state_store.save_items(result.items, key, root, now)
    state_store.prune_old_shards(root, now)
    state_store.write_heartbeat(key, root, now, result.metrics)

    # The map reflects everything in the hot tier (last 7 days), not just this run's delta,
    # and re-locates any item that has no coordinates with the current gazetteer.
    recent = state_store.load_recent_items(key, root)
    lens_of = {s["id"]: s.get("lens", "") for s in state["sources"]}
    snapshot = build_snapshot(locate_rows(recent), now, lens_of=lens_of)
    save_snapshot(snapshot, key, root)

    # Mine the whole hot tier for references (most runs fetch nothing new), and send scouts to the
    # map's hottest blind spots via directory search.
    result.metrics.update(_discover(root, key, fetch, recent, state["sources"], now,
                                    blind=snapshot["blind"], search=search))
    return result.metrics
