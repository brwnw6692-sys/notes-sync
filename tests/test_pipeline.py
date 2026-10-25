from pathlib import Path

from collector.run import process_items
from collector.sources.telegram import parse_page

FIX = Path(__file__).parent / "fixtures"


def test_full_process_chain_on_fixture():
    html = (FIX / "tme_sample.html").read_text(encoding="utf-8")
    items = process_items(parse_page(html, channel="chan_a", cursor=None).items)
    assert len(items) == 2
    assert all(it.text_norm for it in items)
    assert all(it.origin_cluster_id for it in items)
    by_id = {it.native_id: it for it in items}
    assert by_id["1040"].is_original
    assert by_id["1043"].is_original is False  # forwarded


def test_empty_input_is_fine():
    assert process_items([]) == []
