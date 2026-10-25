import pytest

from collector.net.client import FetchResult, PoliteClient


class FakeTransport:
    """Records calls and returns scripted (status, text) or raises."""
    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def __call__(self, url, timeout):
        self.calls.append((url, timeout))
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _client(transport, **kw):
    sleeps = []
    kw.setdefault("budget", 10)
    return PoliteClient(transport, sleep=sleeps.append, **kw), sleeps


def test_successful_fetch_returns_text_and_spends_budget():
    t = FakeTransport([(200, "<html>ok</html>")])
    c, _ = _client(t)
    r = c.get("https://t.me/s/chan_a")
    assert isinstance(r, FetchResult)
    assert r.ok and r.status == 200 and r.text == "<html>ok</html>"
    assert c.remaining_budget == 9


def test_delay_is_applied_between_calls_to_same_host():
    t = FakeTransport([(200, "a"), (200, "b")])
    c, sleeps = _client(t, min_delay=0.5)
    c.get("https://t.me/s/one")
    c.get("https://t.me/s/two")
    assert any(s >= 0.5 for s in sleeps)


def test_429_backs_off_and_retries_then_succeeds():
    t = FakeTransport([(429, ""), (200, "ok")])
    c, sleeps = _client(t, backoff_base_sec=60)
    r = c.get("https://t.me/s/chan")
    assert r.ok and r.text == "ok"
    assert 60 in sleeps  # first backoff step


def test_repeated_429_gives_up_as_limited():
    t = FakeTransport([(429, ""), (429, ""), (429, ""), (429, "")])
    c, _ = _client(t, max_retries=2)
    r = c.get("https://t.me/s/chan")
    assert not r.ok and r.status == 429 and r.error_kind == "rate_limited"


def test_server_error_retries_then_reports_broken():
    t = FakeTransport([(503, ""), (503, ""), (503, "")])
    c, _ = _client(t, max_retries=2)
    r = c.get("https://t.me/s/chan")
    assert not r.ok and r.error_kind == "server_error"


def test_timeout_exception_is_caught_not_raised():
    t = FakeTransport([TimeoutError("slow"), TimeoutError("slow"), TimeoutError("slow")])
    c, _ = _client(t, max_retries=2)
    r = c.get("https://t.me/s/chan")
    assert not r.ok and r.error_kind == "timeout"


def test_budget_exhausted_refuses_without_calling_network():
    t = FakeTransport([(200, "x")])
    c, _ = _client(t, budget=0)
    r = c.get("https://t.me/s/chan")
    assert not r.ok and r.error_kind == "budget" and t.calls == []


def test_404_is_returned_immediately_without_retry():
    t = FakeTransport([(404, "")])
    c, _ = _client(t)
    r = c.get("https://t.me/s/gone")
    assert not r.ok and r.status == 404 and len(t.calls) == 1
