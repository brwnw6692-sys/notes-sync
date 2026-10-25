"""End to end: a followed source references a good Arabic channel, and discovery enrolls it by itself."""
import os
from datetime import datetime, timezone

from collector.core.contract import CollectResult, Cursor, Item
from collector.pipeline import execute_run
from collector.store.state_store import load_sources, save_sources

KEY = os.urandom(32)
D1 = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)
D2 = datetime(2026, 10, 26, 12, 0, tzinfo=timezone.utc)


def _seed():
    return [{"id": "chan_a", "region": "arab_world", "tier": "hot", "status": "active", "canary": False}]


def _fetch(source, cursor):
    sid = source["id"]
    if sid == "chan_a":
        # our seed forwards a referenced channel we don't yet follow
        it = Item.make("chan_a", "9", "u", "عاجل", D1.isoformat(), forwarded_from="origin_b")
        return CollectResult(items=[it], new_cursor=Cursor(last_native_id=9),
                             fetch_ok=True, structure_ok=True)
    if sid == "origin_b":
        # the candidate's public page: Arabic, names places, varied (original) reporting
        texts = ["قصف في دمشق", "اشتباكات في بيروت", "غارة على الموصل", "انفجار في بغداد"]
        items = [Item.make("origin_b", str(i), "u", t, D1.isoformat()) for i, t in enumerate(texts)]
        return CollectResult(items=items, new_cursor=Cursor(last_native_id=4),
                             fetch_ok=True, structure_ok=True)
    return CollectResult(items=[], new_cursor=cursor or Cursor(), fetch_ok=True, structure_ok=True)


def test_a_referenced_arabic_channel_is_discovered_and_enrolled(tmp_path):
    save_sources(_seed(), KEY, tmp_path)
    m1 = execute_run(tmp_path, KEY, _fetch, D1, budget=10)   # discover + sample (day 1)
    assert "origin_b" not in {s["id"] for s in load_sources(KEY, tmp_path)}  # 2-day probation
    assert m1["tracked"] >= 1

    m2 = execute_run(tmp_path, KEY, _fetch, D2, budget=10)   # sample again (day 2) -> promote
    reg = {s["id"]: s for s in load_sources(KEY, tmp_path)}
    assert "origin_b" in reg, "a good referenced channel should enroll itself"
    assert reg["origin_b"]["discovered"] is True
    assert m2["promoted"] == 1


def test_the_user_seed_is_never_overwritten_by_discovery(tmp_path):
    save_sources(_seed(), KEY, tmp_path)
    execute_run(tmp_path, KEY, _fetch, D1, budget=10)
    execute_run(tmp_path, KEY, _fetch, D2, budget=10)
    chan_a = next(s for s in load_sources(KEY, tmp_path) if s["id"] == "chan_a")
    assert "discovered" not in chan_a and chan_a["tier"] == "hot"


def test_blind_spot_search_adds_scouted_channels_as_candidates(tmp_path):
    """A hot blind cell becomes an Arabic query; the search hits join the candidate pool."""
    save_sources(_seed(), KEY, tmp_path)
    queries = []

    def _search(q):
        queries.append(q)
        return ["scout_chan_" + str(len(queries))]

    execute_run(tmp_path, KEY, _fetch, D1, budget=10, search=_search)
    from collector.store.state_store import load_candidates
    cand = load_candidates(KEY, tmp_path)
    assert queries, "the map should have sent at least one scout to a blind spot"
    assert any(h.startswith("scout_chan_") for h in cand), "scouted channels should be tracked"
