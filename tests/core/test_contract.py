from collector.core.contract import Item, CollectResult


def test_item_id_is_stable_hash_of_source_and_native_id():
    a = Item.make(source_id="s1", native_id="42", url="u", text_raw="t", posted_at="2026-10-25T10:00:00Z")
    b = Item.make(source_id="s1", native_id="42", url="u", text_raw="t", posted_at="2026-10-25T10:00:00Z")
    assert a.id == b.id and len(a.id) == 64


def test_item_id_differs_per_source():
    a = Item.make(source_id="s1", native_id="42", url="u", text_raw="t", posted_at="")
    b = Item.make(source_id="s2", native_id="42", url="u", text_raw="t", posted_at="")
    assert a.id != b.id


def test_collect_result_defaults_are_safe():
    r = CollectResult()
    assert r.items == [] and r.fetch_ok is False and r.structure_ok is False
