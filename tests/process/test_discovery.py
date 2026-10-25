from collector.core.contract import Item
from collector.process.discovery import extract_candidates


def _item(src, text, forwarded_from=None):
    return Item.make(src, "1", "u", text, "2026-10-25T10:00:00Z", forwarded_from=forwarded_from)


def test_forwarded_from_handle_is_a_candidate():
    items = [_item("chan_a", "خبر", forwarded_from="origin_b")]
    assert extract_candidates(items, known={"chan_a"}) == {"origin_b"}


def test_tme_links_in_text_become_candidates():
    items = [_item("chan_a", "تابعونا https://t.me/gaza_now وكذلك t.me/south_leb/42")]
    assert extract_candidates(items, known=set()) == {"gaza_now", "south_leb"}


def test_known_sources_are_not_candidates():
    items = [_item("chan_a", "x", forwarded_from="chan_a")]
    assert extract_candidates(items, known={"chan_a"}) == set()


def test_joinchat_and_private_invite_links_are_ignored():
    items = [_item("chan_a", "ادخل https://t.me/joinchat/AAAA and https://t.me/+AbCdEf")]
    assert extract_candidates(items, known=set()) == set()


def test_handles_are_normalized_to_lowercase_without_at():
    items = [_item("chan_a", "عبر @Gaza_Now", forwarded_from="@Origin_B")]
    assert extract_candidates(items, known=set()) == {"gaza_now", "origin_b"}


def test_non_handle_words_and_short_junk_are_ignored():
    items = [_item("chan_a", "t.me/s t.me/ab")]  # 's' reserved, 'ab' too short
    assert extract_candidates(items, known=set()) == set()
