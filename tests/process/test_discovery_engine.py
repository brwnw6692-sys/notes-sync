from datetime import datetime, timezone

from collector.core.contract import Item
from collector.process import discovery_engine as de

D1 = datetime(2026, 10, 25, tzinfo=timezone.utc)
D2 = datetime(2026, 10, 26, tzinfo=timezone.utc)


def _item(src, text, fwd=None):
    return Item.make(src, "1", "u", text, "2026-10-25T10:00:00Z", forwarded_from=fwd)


def _sources():
    return [{"id": "chan_a", "region": "arab_world"}]


def _samples(n, **kw):
    kw = {"lang": "ar", "place_hits": 1, "is_original": True, **kw}
    return [dict(kw) for _ in range(n)]


def test_candidate_inherits_the_referring_sources_region():
    cr = de.candidate_regions([_item("chan_a", "x", fwd="origin_b")], _sources())
    assert cr == {"origin_b": {"arab_world"}}


def test_register_adds_unknown_handles_as_pending():
    state = {}
    de.register(state, {"origin_b": {"arab_world"}}, D1)
    assert state["origin_b"]["status"] == "pending"
    assert state["origin_b"]["regions"] == ["arab_world"]


def test_due_puts_blind_spot_candidates_first():
    state = {}
    de.register(state, {"a": {"covered"}, "b": {"gaza"}}, D1)
    order = de.due(state, blind_regions={"gaza"}, cap=5)
    assert order[0] == "b"


def test_a_good_candidate_promotes_after_two_days():
    state = {}
    de.register(state, {"origin_b": {"arab_world"}}, D1)
    assert de.record(state, "origin_b", _samples(5), D1) == "pending"   # one day only
    assert de.record(state, "origin_b", _samples(5), D2) == "promote"   # second day -> earns it
    assert state["origin_b"]["status"] == "promoted"


def test_wrong_language_candidate_is_rejected_not_promoted():
    state = {}
    de.register(state, {"heb_chan": {"israel"}}, D1)
    de.record(state, "heb_chan", _samples(6, lang="he"), D1)
    assert de.record(state, "heb_chan", _samples(6, lang="he"), D2) == "reject"
    assert state["heb_chan"]["status"] == "rejected"


def test_new_promotions_are_reported_once():
    state = {}
    de.register(state, {"origin_b": {"arab_world"}}, D1)
    de.record(state, "origin_b", _samples(5), D1)
    de.record(state, "origin_b", _samples(5), D2)
    assert de.new_promotions(state) == [("origin_b", "arab_world")]
    assert de.new_promotions(state) == []   # already added, not reported again
