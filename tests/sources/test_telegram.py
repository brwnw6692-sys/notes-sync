from pathlib import Path

from collector.core.contract import Cursor
from collector.sources.telegram import parse_page

FIX = Path(__file__).parent.parent / "fixtures"


def _read(name):
    return (FIX / name).read_text(encoding="utf-8")


def test_parses_messages_and_detects_internal_gap():
    res = parse_page(_read("tme_sample.html"), channel="chan_a", cursor=None)
    assert res.fetch_ok and res.structure_ok
    assert [it.native_id for it in res.items] == ["1040", "1043"]
    assert res.gaps_detected == 2  # 1041 and 1042 are missing
    assert res.new_cursor.last_native_id == 1043


def test_extracts_text_time_and_url():
    it = parse_page(_read("tme_sample.html"), channel="chan_a", cursor=None).items[0]
    assert it.text_raw == "انفجار في المدينة"
    assert it.posted_at == "2026-10-25T10:00:00+00:00"
    assert it.url == "https://t.me/chan_a/1040"


def test_forward_records_origin_handle_not_display_name():
    items = parse_page(_read("tme_sample.html"), channel="chan_a", cursor=None).items
    assert items[0].forwarded_from is None
    assert items[1].forwarded_from == "origin_b"


def test_cursor_skips_already_seen_and_counts_gap_from_cursor():
    res = parse_page(_read("tme_sample.html"), channel="chan_a", cursor=Cursor(last_native_id=1038))
    assert [it.native_id for it in res.items] == ["1040", "1043"]
    assert res.gaps_detected == 1 + 2  # 1039, then 1041-1042


def test_nothing_new_since_cursor_is_empty_not_broken():
    res = parse_page(_read("tme_sample.html"), channel="chan_a", cursor=Cursor(last_native_id=1043))
    assert res.structure_ok and res.items == []
    assert res.new_cursor.last_native_id == 1043


def test_empty_channel_page_is_valid_structure():
    res = parse_page(_read("tme_empty_channel.html"), channel="chan_c", cursor=None)
    assert res.structure_ok and res.items == []


def test_unknown_structure_is_broken_not_quiet():
    res = parse_page("<html><body>nope</body></html>", channel="chan_a", cursor=None)
    assert res.fetch_ok and res.structure_ok is False and res.items == []
