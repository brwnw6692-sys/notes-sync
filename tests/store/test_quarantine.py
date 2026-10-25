import os
from datetime import datetime, timedelta, timezone

from collector.store.guard import check_tree, is_encrypted
from collector.store.quarantine import load_quarantined, save_broken_page

KEY = os.urandom(32)
T0 = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)


def test_saved_page_is_encrypted_and_roundtrips(tmp_path):
    p = save_broken_page("<html>new layout</html>", "chan_a", KEY, tmp_path, T0)
    assert is_encrypted(p)
    rec = load_quarantined(p, KEY)
    assert rec == {"source_id": "chan_a", "captured_at": T0.isoformat(), "html": "<html>new layout</html>"}


def test_filename_does_not_reveal_source(tmp_path):
    p = save_broken_page("<html/>", "chan_secret_name", KEY, tmp_path, T0)
    assert "chan" not in p.name and "secret" not in p.name


def test_filename_differs_with_a_different_key(tmp_path):
    a = save_broken_page("<html/>", "chan_a", KEY, tmp_path / "a", T0)
    b = save_broken_page("<html/>", "chan_a", os.urandom(32), tmp_path / "b", T0)
    assert a.name.split("-")[0] != b.name.split("-")[0]


def test_keeps_only_newest_three_per_source(tmp_path):
    for i in range(5):
        save_broken_page(f"<html>{i}</html>", "chan_a", KEY, tmp_path, T0 + timedelta(minutes=i))
    kept = sorted(load_quarantined(p, KEY)["html"] for p in tmp_path.rglob("*.bin"))
    assert kept == ["<html>2</html>", "<html>3</html>", "<html>4</html>"]


def test_total_cap_drops_oldest_across_sources(tmp_path, monkeypatch):
    from collector.store import quarantine
    monkeypatch.setattr(quarantine, "_MAX_TOTAL", 4)
    for i in range(6):
        save_broken_page("<html/>", f"chan_{i}", KEY, tmp_path, T0 + timedelta(minutes=i))
    sources = sorted(load_quarantined(p, KEY)["source_id"] for p in tmp_path.rglob("*.bin"))
    assert sources == ["chan_2", "chan_3", "chan_4", "chan_5"]


def test_quarantine_dir_passes_the_guard(tmp_path):
    save_broken_page("<html/>", "chan_a", KEY, tmp_path, T0)
    check_tree(tmp_path)
