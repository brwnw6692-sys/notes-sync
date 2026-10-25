"""The testable core of one scheduled run: load state -> run_once -> persist, all under the data root."""
from datetime import datetime
from pathlib import Path

from collector.core.orchestrator import run_once
from collector.store import state_store


def execute_run(root: Path, key: bytes, fetch, now: datetime, budget: int) -> dict:
    state = state_store.load_state(key, root)
    result = run_once(state, fetch, now, budget)

    state_store.save_state(result.new_state, key, root)
    if result.items:
        state_store.save_items(result.items, key, root, now)
    state_store.prune_old_shards(root, now)
    state_store.write_heartbeat(key, root, now, result.metrics)
    return result.metrics
