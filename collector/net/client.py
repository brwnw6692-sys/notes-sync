"""A polite HTTP client: paced, backs off when asked to slow down, and bounded by a per-run budget.

The network itself is injected as `transport(url, timeout) -> (status, text)`, so all of this
logic is tested offline against a fake, including the rate-limited and server-error paths.
"""
import time
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass
class FetchResult:
    ok: bool
    status: int = 0
    text: str = ""
    error_kind: str = ""   # rate_limited / server_error / timeout / budget / network


class PoliteClient:
    def __init__(self, transport, *, budget: int, min_delay: float = 0.5,
                 timeout: float = 20.0, max_retries: int = 3,
                 backoff_base_sec: float = 60.0, sleep=time.sleep):
        self._transport = transport
        self.remaining_budget = budget
        self._min_delay = min_delay
        self._timeout = timeout
        self._max_retries = max_retries
        self._backoff = backoff_base_sec
        self._sleep = sleep
        self._last_seen = {}  # host -> monotonic time of last request

    def _pace(self, url: str) -> None:
        host = urlsplit(url).netloc
        last = self._last_seen.get(host)
        now = time.monotonic()
        if last is not None:
            wait = self._min_delay - (now - last)
            if wait > 0:
                self._sleep(wait)
        self._last_seen[host] = time.monotonic()

    def get(self, url: str) -> FetchResult:
        if self.remaining_budget <= 0:
            return FetchResult(False, error_kind="budget")
        self.remaining_budget -= 1

        for attempt in range(self._max_retries + 1):
            self._pace(url)
            try:
                status, text = self._transport(url, self._timeout)
            except TimeoutError:
                last = FetchResult(False, error_kind="timeout")
            except Exception:
                last = FetchResult(False, error_kind="network")
            else:
                if status == 200:
                    return FetchResult(True, status=status, text=text)
                if status == 404:
                    return FetchResult(False, status=404)
                if status == 429:
                    last = FetchResult(False, status=429, error_kind="rate_limited")
                elif 500 <= status < 600:
                    last = FetchResult(False, status=status, error_kind="server_error")
                else:
                    return FetchResult(False, status=status, error_kind="http")
            if attempt < self._max_retries:
                self._sleep(self._backoff * (2 ** attempt))
        return last
