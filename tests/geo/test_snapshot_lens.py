from datetime import datetime, timezone, timedelta
from collector.geo.snapshot import build_snapshot

NOW = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)


def _item(cid, src, hours_ago=2):
    ts = (NOW - timedelta(hours=hours_ago)).isoformat()
    return {"lat": 33.51, "lon": 36.29, "origin_cluster_id": cid, "is_original": True,
            "posted_at": ts, "source_id": src}


def test_active_cell_breaks_recent_activity_down_by_lens():
    items = [_item("c1", "arab_a"), _item("c2", "arab_b"), _item("c3", "isr_a")]
    lens_of = {"arab_a": "ar", "arab_b": "ar", "isr_a": "he"}
    cell = build_snapshot(items, NOW, lens_of=lens_of)["active"][0]
    assert cell["recent"] == 3
    assert cell["lenses"] == {"ar": 2, "he": 1}      # who is reporting from here, right now


def test_old_reports_do_not_count_toward_the_lens_breakdown():
    items = [_item("c1", "arab_a", hours_ago=200)]
    cell = build_snapshot(items, NOW, lens_of={"arab_a": "ar"})["active"][0]
    assert cell["lenses"] == {}
