import pytest

from collector.process.source_register import add_source, remove_source, merge_runtime


def test_add_normalizes_handle_and_sets_defaults():
    out = add_source([], "@Gaza_Now", region="gaza", tier="quiet", canary=False)
    assert len(out) == 1
    s = out[0]
    assert s["id"] == "gaza_now" and s["region"] == "gaza"
    assert s["tier"] == "quiet" and s["status"] == "active" and s["canary"] is False


def test_add_is_idempotent_and_updates_fields():
    out = add_source([], "chan1", region="x", tier="quiet", canary=False)
    out = add_source(out, "chan1", region="y", tier="hot", canary=True)
    assert len(out) == 1
    assert out[0]["region"] == "y" and out[0]["tier"] == "hot" and out[0]["canary"] is True


def test_remove_deletes_by_normalized_handle():
    out = add_source([], "Chan_One", region="x", tier="quiet", canary=False)
    out = remove_source(out, "@chan_one")
    assert out == []


def test_remove_unknown_is_a_no_op():
    out = add_source([], "alpha", region="x", tier="quiet", canary=False)
    assert remove_source(out, "nope_nope") == out


def test_invalid_handle_is_rejected():
    with pytest.raises(ValueError):
        add_source([], "ab", region="x", tier="quiet", canary=False)  # too short


def test_merge_runtime_carries_cursor_and_counters_by_id():
    registry = [{"id": "a", "region": "x", "tier": "quiet", "status": "active", "canary": False}]
    prior = [{"id": "a", "cursor": {"last_native_id": 99}, "consecutive_404": 2,
              "last_post_at": "2026-10-25T10:00:00Z"}]
    merged = merge_runtime(registry, prior)
    assert merged[0]["cursor"] == {"last_native_id": 99}
    assert merged[0]["consecutive_404"] == 2
    assert merged[0]["region"] == "x"  # registry fields preserved


def test_merge_runtime_defaults_for_new_source():
    registry = [{"id": "new", "region": "x", "tier": "quiet", "status": "active", "canary": False}]
    merged = merge_runtime(registry, [])
    assert merged[0]["cursor"] == {"last_native_id": 0}
    assert merged[0]["consecutive_404"] == 0
