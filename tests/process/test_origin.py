from collector.config import CONFIG
from collector.core.contract import Item
from collector.process.origin import simhash, hamming, cluster_items


def _item(src, text, ts, **kw):
    return Item.make(src, "1", "u", text, ts, text_norm=text, **kw)


BASE = "انفجار كبير في المدينة الليلة وسماع دوي في عدة احياء"


def test_hamming_zero_for_equal():
    assert hamming(simhash("abc def"), simhash("abc def")) == 0


def test_near_identical_text_clusters_and_earliest_is_original():
    a = _item("s1", BASE, "2026-10-25T10:00:00Z")
    b = _item("s2", BASE + " عاجل", "2026-10-25T10:05:00Z")
    out = cluster_items([b, a], hamming_max=CONFIG.simhash_hamming_max, window_hours=6)
    by_src = {it.source_id: it for it in out}
    assert by_src["s1"].origin_cluster_id == by_src["s2"].origin_cluster_id
    assert by_src["s1"].is_original and not by_src["s2"].is_original


def test_unrelated_texts_do_not_cluster():
    a = _item("s1", BASE, "2026-10-25T10:00:00Z")
    b = _item("s2", "اجتماع وزراء الخارجية في القاهرة لبحث الملف الاقتصادي", "2026-10-25T10:05:00Z")
    out = cluster_items([a, b], hamming_max=CONFIG.simhash_hamming_max, window_hours=6)
    assert out[0].origin_cluster_id != out[1].origin_cluster_id
    assert out[0].is_original and out[1].is_original


def test_same_text_outside_window_is_a_new_origin():
    a = _item("s1", BASE, "2026-10-25T10:00:00Z")
    b = _item("s2", BASE, "2026-10-25T20:00:00Z")
    out = cluster_items([a, b], hamming_max=CONFIG.simhash_hamming_max, window_hours=6)
    assert out[0].origin_cluster_id != out[1].origin_cluster_id


def test_forwarded_item_is_never_original():
    a = _item("s1", "نص فريد تماما عن موضوع اخر", "2026-10-25T10:00:00Z", forwarded_from="origin_chan")
    out = cluster_items([a], hamming_max=CONFIG.simhash_hamming_max, window_hours=6)
    assert out[0].is_original is False


def test_missing_timestamp_does_not_crash():
    a = _item("s1", BASE, "")
    out = cluster_items([a], hamming_max=CONFIG.simhash_hamming_max, window_hours=6)
    assert out[0].origin_cluster_id == a.id
