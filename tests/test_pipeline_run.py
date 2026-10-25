import os
from datetime import datetime, timezone

from collector.core.contract import CollectResult, Cursor, Item
from collector.pipeline import execute_run
from collector.store.guard import check_tree
from collector.store.state_store import load_state, load_recent_items, read_heartbeat

KEY = os.urandom(32)
NOW = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)


def _state(ids):
    return {"sources": [{"id": i, "tier": "hot", "region": "x", "status": "active",
                         "canary": False, "cursor": {"last_native_id": 0}} for i in ids],
            "backlog": [], "run_index": 0, "red_regions": []}


def _fetch(script):
    def fetch(source, cursor):
        return script.get(source["id"], CollectResult(fetch_ok=True, structure_ok=True,
                                                     new_cursor=cursor or Cursor()))
    return fetch


def test_run_persists_state_items_and_heartbeat(tmp_path):
    from collector.store.state_store import save_state
    save_state(_state(["a"]), KEY, tmp_path)
    fetch = _fetch({"a": CollectResult(items=[Item.make("a", "5", "u", "انفجار", NOW.isoformat())],
                                       new_cursor=Cursor(last_native_id=5),
                                       fetch_ok=True, structure_ok=True)})
    metrics = execute_run(tmp_path, KEY, fetch, NOW, budget=10)

    saved = load_state(KEY, tmp_path)
    assert saved["run_index"] == 1
    assert saved["sources"][0]["cursor"]["last_native_id"] == 5
    assert len(load_recent_items(KEY, tmp_path)) == 1
    assert read_heartbeat(KEY, tmp_path)["last_run_at"] == NOW.isoformat()
    assert metrics["items"] == 1


def test_run_output_passes_the_guard(tmp_path):
    from collector.store.state_store import save_state
    save_state(_state(["a"]), KEY, tmp_path)
    execute_run(tmp_path, KEY, _fetch({}), NOW, budget=10)
    check_tree(tmp_path)


def test_run_with_no_prior_state_starts_from_default(tmp_path):
    metrics = execute_run(tmp_path, KEY, _fetch({}), NOW, budget=10)
    assert metrics["fetched"] == 0
    assert load_state(KEY, tmp_path)["run_index"] == 1
