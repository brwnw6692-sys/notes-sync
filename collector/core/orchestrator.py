"""One full run, wired from parts: schedule -> fetch (isolated) -> health -> process -> discover -> sight.

Pure: it takes the current state and an injected `fetch(source, cursor) -> CollectResult`, and returns
results, the next state, and numbers-only metrics. No network, no disk here, so the whole run is tested.
"""
from dataclasses import dataclass, field
from datetime import datetime

from collector.core.canary import system_sight
from collector.core.health import classify
from collector.core.scheduler import plan_run
from collector.process.discovery import extract_candidates
from collector.run import process_items


@dataclass
class RunResult:
    items: list = field(default_factory=list)
    new_state: dict = field(default_factory=dict)
    health: dict = field(default_factory=dict)          # source_id -> state
    sight: dict = field(default_factory=dict)
    silence_suppressed: bool = False
    metrics_candidates: set = field(default_factory=set)
    metrics: dict = field(default_factory=dict)


def _cursor(source):
    from collector.core.contract import Cursor
    return Cursor(last_native_id=source.get("cursor", {}).get("last_native_id", 0))


def run_once(state: dict, fetch, now: datetime, budget: int) -> RunResult:
    sources = state["sources"]
    by_id = {s["id"]: s for s in sources}
    red = set(state.get("red_regions", []))

    due, overflow = plan_run(sources, run_index=state.get("run_index", 0), minutes=10,
                             red_regions=red, budget=budget, backlog=state.get("backlog", []))
    # Canaries are the heartbeat: always polled so we can judge our own sight.
    due_ids = {s["id"] for s in due}
    for s in sources:
        if s.get("canary") and s["status"] == "active" and s["id"] not in due_ids:
            due.append(s)
            due_ids.add(s["id"])

    items, health, candidates = [], {}, set()
    new_by_id = {sid: dict(s) for sid, s in by_id.items()}

    for source in due:
        result = _fetch_isolated(fetch, source, _cursor(source))
        state_name = classify(result, prior_not_found=source.get("consecutive_404", 0))
        health[source["id"]] = state_name

        ns = new_by_id[source["id"]]
        ns["consecutive_404"] = source.get("consecutive_404", 0) + 1 if result.http_status == 404 else 0
        if result.new_cursor is not None:
            ns["cursor"] = {"last_native_id": result.new_cursor.last_native_id}
        items.extend(result.items)

    items = process_items(items)
    candidates = extract_candidates(items, known=set(by_id))

    canaries = [{"state": health.get(s["id"], "quiet"), "last_post_at": s.get("last_post_at", "")}
                for s in sources if s.get("canary") and s["status"] == "active"]
    sight = system_sight(canaries, now)

    new_state = dict(state)
    new_state["sources"] = list(new_by_id.values())
    new_state["backlog"] = overflow
    new_state["run_index"] = state.get("run_index", 0) + 1

    metrics = {"fetched": len(due), "items": len(items), "candidates": len(candidates)}
    for st in ("ok", "quiet", "limited", "broken", "dead"):
        metrics[st] = sum(v == st for v in health.values())

    return RunResult(items=items, new_state=new_state, health=health, sight=sight,
                     silence_suppressed=sight["suppress_silence_signals"],
                     metrics_candidates=candidates, metrics=metrics)


def _fetch_isolated(fetch, source, cursor):
    """A single source can never take the run down with it."""
    from collector.core.contract import CollectResult
    try:
        return fetch(source, cursor)
    except Exception:
        return CollectResult(fetch_ok=False, structure_ok=False, error_kind="adapter_crash",
                             new_cursor=cursor)
