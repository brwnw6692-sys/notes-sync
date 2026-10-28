from datetime import datetime, timezone, timedelta
from collector.geo.snapshot import build_snapshot

NOW = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)


def _item(lat, lon, cid, hours_ago):
    ts = (NOW - timedelta(hours=hours_ago)).isoformat()
    return {"lat": lat, "lon": lon, "origin_cluster_id": cid, "is_original": True, "posted_at": ts}


def test_recent_window_separates_now_from_the_backdrop():
    # two independent reports in the same cell: one fresh, one old
    items = [_item(33.51, 36.29, "c1", 3), _item(33.51, 36.29, "c2", 200)]
    cell = build_snapshot(items, NOW)["active"][0]
    assert cell["count"] == 2        # both counted over the 7-day tier
    assert cell["recent"] == 1       # only the fresh one is "happening now"


def test_unparseable_or_missing_timestamp_is_not_recent():
    items = [{"lat": 33.51, "lon": 36.29, "origin_cluster_id": "c1", "is_original": True, "posted_at": ""}]
    cell = build_snapshot(items, NOW)["active"][0]
    assert cell["count"] == 1 and cell["recent"] == 0
