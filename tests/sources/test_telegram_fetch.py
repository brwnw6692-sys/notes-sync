from pathlib import Path

from collector.core.contract import Cursor
from collector.sources.telegram_fetch import channel_url, fetch_channel

FIX = Path(__file__).parent.parent / "fixtures"
SAMPLE = (FIX / "tme_sample.html").read_text(encoding="utf-8")


class OneShot:
    def __init__(self, result):
        self._result = result
        self.urls = []

    def get(self, url):
        self.urls.append(url)
        return self._result


class _R:
    def __init__(self, ok, status=200, text="", error_kind=""):
        self.ok, self.status, self.text, self.error_kind = ok, status, text, error_kind


def test_channel_url_uses_web_preview():
    assert channel_url("gaza_now", None) == "https://t.me/s/gaza_now"


def test_channel_url_pages_backwards_from_cursor_to_fill_gaps():
    assert channel_url("gaza_now", Cursor(last_native_id=1040)) == "https://t.me/s/gaza_now?before=1041"


def test_fetch_ok_parses_items():
    client = OneShot(_R(True, text=SAMPLE))
    res = fetch_channel(client, "chan_a", cursor=None)
    assert res.fetch_ok and res.structure_ok
    assert [it.native_id for it in res.items] == ["1040", "1043"]
    assert client.urls == ["https://t.me/s/chan_a"]


def test_rate_limited_fetch_becomes_limited_result_not_broken():
    res = fetch_channel(OneShot(_R(False, status=429, error_kind="rate_limited")), "chan_a", cursor=None)
    assert res.fetch_ok is False and res.http_status == 429 and res.error_kind == "rate_limited"
    assert res.items == []


def test_404_fetch_is_marked_for_dead_check():
    res = fetch_channel(OneShot(_R(False, status=404, error_kind="")), "chan_a", cursor=None)
    assert res.http_status == 404 and res.items == []


def test_server_error_is_broken_fetch():
    res = fetch_channel(OneShot(_R(False, status=503, error_kind="server_error")), "chan_a", cursor=None)
    assert res.fetch_ok is False and res.error_kind == "server_error"
