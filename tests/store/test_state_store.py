import os
from datetime import datetime, timedelta, timezone

from collector.core.contract import Item
from collector.store.guard import check_tree
from collector.store.state_store import (default_state, load_state, load_recent_items,
                                        prune_old_shards, save_items, save_state,
                                        write_heartbeat, read_heartbeat)

KEY = os.urandom(32)
NOW = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)


def test_missing_state_returns_default(tmp_path):
    st = load_state(KEY, tmp_path)
    assert st == default_state()


def test_state_roundtrips_encrypted(tmp_path):
    state = {"sources": [{"id": "a", "cursor": {"last_native_id": 42}}],
             "backlog": ["b"], "run_index": 7, "red_regions": ["leb"]}
    save_state(state, KEY, tmp_path)
    assert load_state(KEY, tmp_path) == state


def test_state_file_is_encrypted(tmp_path):
    save_state(default_state(), KEY, tmp_path)
    blob = (tmp_path / "state.bin").read_bytes()
    assert b"sources" not in blob and b"last_native_id" not in blob


def test_items_roundtrip_in_a_shard(tmp_path):
    items = [Item.make("chan_a", "1", "u", "انفجار", NOW.isoformat())]
    save_items(items, KEY, tmp_path, NOW)
    loaded = load_recent_items(KEY, tmp_path)
    assert len(loaded) == 1 and loaded[0]["source_id"] == "chan_a"


def test_old_shards_are_pruned_beyond_seven_days(tmp_path):
    save_items([Item.make("a", "1", "u", "x", "")], KEY, tmp_path, NOW - timedelta(days=9))
    save_items([Item.make("b", "2", "u", "y", "")], KEY, tmp_path, NOW - timedelta(days=1))
    prune_old_shards(tmp_path, NOW, days=7)
    sources = {i["source_id"] for i in load_recent_items(KEY, tmp_path)}
    assert sources == {"b"}


def test_heartbeat_roundtrips(tmp_path):
    write_heartbeat(KEY, tmp_path, NOW, {"ok": 10, "broken": 1})
    hb = read_heartbeat(KEY, tmp_path)
    assert hb["last_run_at"] == NOW.isoformat() and hb["metrics"] == {"ok": 10, "broken": 1}


def test_everything_written_passes_the_guard(tmp_path):
    save_state(default_state(), KEY, tmp_path)
    save_items([Item.make("a", "1", "u", "x", NOW.isoformat())], KEY, tmp_path, NOW)
    write_heartbeat(KEY, tmp_path, NOW, {"ok": 1})
    check_tree(tmp_path)
