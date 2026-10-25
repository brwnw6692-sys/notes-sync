import os
from datetime import datetime, timezone

from collector.geo.snapshot import build_snapshot, save_snapshot, load_snapshot
from collector.store.guard import check_tree

NOW = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)
KEY = os.urandom(32)


def _item(lat, lon, cluster, original=True):
    return {"lat": lat, "lon": lon, "origin_cluster_id": cluster, "is_original": original}


def test_snapshot_has_active_cells_with_coords_and_counts():
    snap = build_snapshot([_item(31.50, 34.47, "c1"), _item(31.50, 34.47, "c2")], NOW)
    assert snap["generated_at"] == NOW.isoformat()
    assert snap["active"], "expected at least one active cell"
    cell = snap["active"][0]
    assert {"lat", "lon", "level", "count", "heat"} <= set(cell)
    assert cell["count"] == 2


def test_snapshot_reports_blind_hot_cells_when_uncovered():
    # No items at all -> the hot core is entirely blind
    snap = build_snapshot([], NOW)
    assert snap["blind"], "uncovered hot cells should be reported as blind"
    assert snap["coverage_pct"] == 0


def test_covering_a_hot_area_counts_that_cell_as_covered():
    # One cell out of a region-wide hot core rounds to ~0% coverage, but it IS counted as covered.
    base = build_snapshot([], NOW)["covered_hot_cells"]
    snap = build_snapshot([_item(35.69, 51.39, "c1"), _item(35.70, 51.40, "c2")], NOW)  # Tehran
    assert snap["covered_hot_cells"] == base + 1


def test_snapshot_roundtrips_encrypted_and_passes_guard(tmp_path):
    snap = build_snapshot([_item(31.50, 34.47, "c1")], NOW)
    save_snapshot(snap, KEY, tmp_path)
    assert load_snapshot(KEY, tmp_path)["generated_at"] == NOW.isoformat()
    check_tree(tmp_path)


def test_snapshot_contains_no_place_names():
    import json
    snap = build_snapshot([_item(31.50, 34.47, "c1")], NOW)
    blob = json.dumps(snap)
    for name in ("gaza", "khan", "beirut", "tehran", "غزة"):
        assert name not in blob.lower()
