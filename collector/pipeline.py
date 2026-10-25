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


def _discover(root, key, fetch, items, sources, now) -> dict:
    """Grow the network: fold in referenced channels, sample a few public pages (blind spots first),
    and auto-enroll any that earn it. Returns {promoted, candidates} for metrics."""
    cand = state_store.load_candidates(key, root)
    de.register(cand, de.candidate_regions(items, sources), now)

    covered = {s.get("region") for s in sources if s.get("status", "active") == "active"}
    blind = {r for c in cand.values() for r in c["regions"]} - covered
    for handle in de.due(cand, blind, CONFIG.discovery_per_run):
        res = fetch({"id": handle}, None)
        if not getattr(res, "fetch_ok", False):
            continue
        sampled = process_items(res.items)
        de.record(cand, handle, [{"lang": it.lang, "place_hits": len(it.tags.get("places", [])),
                                   "is_original": it.is_original} for it in sampled], now)

    promos = de.new_promotions(cand)
    if promos:
        registry = state_store.load_sources(key, root)
        for handle, region in promos:
            registry = add_source(registry, handle, region, tier="quiet", discovered=True)
        state_store.save_sources(registry, key, root)
    state_store.save_candidates(cand, key, root)
    return {"promoted": len(promos), "tracked": len(cand)}


def execute_run(root: Path, key: bytes, fetch, now: datetime, budget: int) -> dict:
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
    save_snapshot(build_snapshot(locate_rows(recent), now), key, root)

    result.metrics.update(_discover(root, key, fetch, result.items, state["sources"], now))
    return result.metrics
