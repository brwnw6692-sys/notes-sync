from collector.core.contract import Item
from collector.run import process_items
from collector.geo.grid_coverage import grid_coverage, coverage_summary


def _item(src, nid, text):
    return Item.make(src, str(nid), "u", text, "2026-10-25T10:00:00Z")


def test_process_attaches_places_and_a_location():
    items = process_items([_item("a", 1, "قصف في خان يونس")])
    it = items[0]
    assert it.tags["places"] and it.tags["places"][0]["id"] == "khan_yunis"
    assert it.lat == 31.34 and it.lon == 34.30


def test_message_without_a_place_has_no_location():
    it = process_items([_item("a", 1, "اجتماع اقتصادي")])[0]
    assert it.tags["places"] == []
    assert it.lat is None and it.lon is None


def test_processed_items_feed_grid_coverage():
    items = process_items([
        _item("a", 1, "غزة"),
        _item("b", 2, "بيروت"),
    ])
    rows = [{"lat": it.lat, "lon": it.lon, "origin_cluster_id": it.origin_cluster_id,
             "is_original": it.is_original} for it in items if it.lat is not None]
    cov = grid_coverage(rows)
    assert len(cov) == 2  # Gaza and Beirut land in two different cells
    assert coverage_summary(cov)["covered_hot_cells"] >= 1
