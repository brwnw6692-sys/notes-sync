from datetime import datetime, timezone

from collector.core.contract import CollectResult, Cursor, Item
from collector.core.orchestrator import run_once

NOW = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)


def _src(id_, tier="hot", region="x", status="active", canary=False, last_native_id=0, nf=0):
    return {"id": id_, "tier": tier, "region": region, "status": status, "canary": canary,
            "cursor": {"last_native_id": last_native_id}, "consecutive_404": nf,
            "last_post_at": NOW.isoformat()}


def _item(src, nid, text, forwarded_from=None):
    return Item.make(src, str(nid), "u", text, NOW.isoformat(), forwarded_from=forwarded_from)


def _result(items, **kw):
    kw.setdefault("fetch_ok", True)
    kw.setdefault("structure_ok", True)
    cur = Cursor(last_native_id=max((int(i.native_id) for i in items), default=0))
    return CollectResult(items=items, new_cursor=cur, **kw)


def _fetcher(script):
    """script: {source_id: CollectResult}. Records which sources were fetched."""
    fetched = []

    def fetch(source, cursor):
        fetched.append(source["id"])
        return script.get(source["id"], CollectResult(fetch_ok=True, structure_ok=True,
                                                      new_cursor=cursor or Cursor()))
    fetch.fetched = fetched
    return fetch


def test_due_sources_are_fetched_and_quiet_ones_are_not():
    state = {"sources": [_src("hot1", tier="hot"), _src("q1", tier="quiet")],
             "run_index": 1, "red_regions": []}
    fetch = _fetcher({"hot1": _result([_item("hot1", 10, "خبر")])})
    run_once(state, fetch, NOW, budget=10)
    assert "hot1" in fetch.fetched and "q1" not in fetch.fetched


def test_items_from_fetched_sources_are_normalized_and_clustered():
    state = {"sources": [_src("a"), _src("b")], "run_index": 1, "red_regions": []}
    same = "انفجار كبير في المدينة الليلة وسماع دوي في عدة احياء"
    fetch = _fetcher({"a": _result([_item("a", 5, same)]),
                      "b": _result([_item("b", 7, same + " عاجل")])})
    res = run_once(state, fetch, NOW, budget=10)
    assert all(it.text_norm for it in res.items)
    clusters = {it.origin_cluster_id for it in res.items}
    assert len(clusters) == 1  # the two near-identical messages share one origin


def test_health_recorded_and_cursor_advances():
    state = {"sources": [_src("a", last_native_id=4)], "run_index": 1, "red_regions": []}
    fetch = _fetcher({"a": _result([_item("a", 5, "خبر")])})
    res = run_once(state, fetch, NOW, budget=10)
    assert res.health["a"] == "ok"
    new_a = next(s for s in res.new_state["sources"] if s["id"] == "a")
    assert new_a["cursor"]["last_native_id"] == 5


def test_a_broken_source_does_not_stop_the_others():
    state = {"sources": [_src("bad"), _src("good")], "run_index": 1, "red_regions": []}
    fetch = _fetcher({"bad": CollectResult(fetch_ok=False, structure_ok=False, error_kind="x"),
                      "good": _result([_item("good", 3, "خبر من غزة")])})
    res = run_once(state, fetch, NOW, budget=10)
    assert res.health["bad"] == "broken" and res.health["good"] == "ok"
    assert any(it.source_id == "good" for it in res.items)


def test_discovery_candidates_are_collected_from_items():
    state = {"sources": [_src("a")], "run_index": 1, "red_regions": []}
    fetch = _fetcher({"a": _result([_item("a", 1, "x", forwarded_from="origin_b")])})
    res = run_once(state, fetch, NOW, budget=10)
    assert "origin_b" in res.metrics_candidates


def test_canary_blind_suppresses_silence_signals():
    # two canaries, both broken -> blind
    state = {"sources": [_src("c1", canary=True), _src("c2", canary=True)],
             "run_index": 1, "red_regions": []}
    fetch = _fetcher({"c1": CollectResult(fetch_ok=False, structure_ok=False, error_kind="x"),
                      "c2": CollectResult(fetch_ok=False, structure_ok=False, error_kind="x")})
    res = run_once(state, fetch, NOW, budget=10)
    assert res.sight["sight"] == "blind"
    assert res.silence_suppressed is True


def test_budget_overflow_becomes_backlog_for_next_run():
    state = {"sources": [_src("h1"), _src("h2"), _src("h3")], "run_index": 1, "red_regions": []}
    fetch = _fetcher({})
    res = run_once(state, fetch, NOW, budget=2)
    assert len(fetch.fetched) == 2
    assert len(res.new_state["backlog"]) == 1


def test_metrics_are_numbers_only():
    state = {"sources": [_src("a")], "run_index": 1, "red_regions": []}
    res = run_once(state, _fetcher({"a": _result([_item("a", 1, "خبر")])}), NOW, budget=10)
    assert all(isinstance(v, int) for v in res.metrics.values())
