import os

from collector.addsource import apply_change
from collector.store.guard import check_tree
from collector.store.state_store import load_sources

KEY = os.urandom(32)


def test_add_writes_encrypted_source(tmp_path):
    apply_change(tmp_path, KEY, "add", handle="gaza_now", region="gaza", tier="quiet", canary=False)
    sources = load_sources(KEY, tmp_path)
    assert len(sources) == 1 and sources[0]["id"] == "gaza_now"
    check_tree(tmp_path)


def test_add_then_remove(tmp_path):
    apply_change(tmp_path, KEY, "add", handle="chan_one", region="x", tier="quiet", canary=False)
    apply_change(tmp_path, KEY, "remove", handle="chan_one")
    assert load_sources(KEY, tmp_path) == []


def test_list_returns_sources(tmp_path):
    apply_change(tmp_path, KEY, "add", handle="chan_one", region="x", tier="hot", canary=True)
    listed = apply_change(tmp_path, KEY, "list")
    assert listed[0]["id"] == "chan_one" and listed[0]["canary"] is True


def test_add_is_idempotent_across_calls(tmp_path):
    apply_change(tmp_path, KEY, "add", handle="chan_one", region="x", tier="quiet", canary=False)
    apply_change(tmp_path, KEY, "add", handle="chan_one", region="y", tier="hot", canary=False)
    sources = load_sources(KEY, tmp_path)
    assert len(sources) == 1 and sources[0]["region"] == "y"
