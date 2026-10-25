import os
from datetime import datetime, timezone

from collector.core.contract import CollectResult, Cursor, Item
from collector.pipeline import execute_run
from collector.geo.snapshot import load_snapshot, locate_rows
from collector.store.state_store import save_sources

KEY = os.urandom(32)
NOW = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)


def _src():
    return [{"id": "a", "region": "x", "tier": "hot", "status": "active", "canary": False}]


def _fetch_then_empty(items):
    calls = {"n": 0}

    def fetch(source, cursor):
        calls["n"] += 1
        if calls["n"] == 1:
            return CollectResult(items=items, new_cursor=Cursor(last_native_id=9),
                                 fetch_ok=True, structure_ok=True)
        return CollectResult(items=[], new_cursor=cursor or Cursor(), fetch_ok=True, structure_ok=True)
    return fetch


def test_map_keeps_showing_activity_after_an_empty_run(tmp_path):
    save_sources(_src(), KEY, tmp_path)
    msg = Item.make("a", "9", "u", "قصف في دمشق", NOW.isoformat())
    fetch = _fetch_then_empty([msg])
    execute_run(tmp_path, KEY, fetch, NOW, budget=10)       # collects 1 located message
    first = load_snapshot(KEY, tmp_path)
    execute_run(tmp_path, KEY, fetch, NOW, budget=10)       # fetches nothing new
    second = load_snapshot(KEY, tmp_path)
    assert first["active"], "first run should produce an active cell"
    assert second["active"], "map must still show activity after an empty run"


def test_locate_rows_heals_items_stored_without_coords():
    rows = locate_rows([{"text_raw": "انفجار في بغداد", "lat": None, "lon": None,
                         "origin_cluster_id": "c1", "is_original": True}])
    assert rows[0]["lat"] is not None and rows[0]["lon"] is not None
