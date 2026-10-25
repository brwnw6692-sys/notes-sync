"""The live entry point run by GitHub Actions. Thin edge: env key, real network, then the guard.

Usage: python -m collector.live <data_dir>
Only numbers reach stdout. Actions logs are public, so no source names or content are printed.
"""
import base64
import binascii
import sys
from pathlib import Path

from collector.config import CONFIG
from collector.core.contract import Cursor
from collector.net.client import PoliteClient
from collector.net.http import make_transport
from collector.pipeline import execute_run
from collector.sources.telegram_fetch import fetch_channel
from collector.store.guard import check_tree


def load_data_key() -> bytes:
    import os
    # A pasted secret can pick up whitespace anywhere (a wrapped textarea adds a newline mid-value),
    # so drop all whitespace, then accept either standard or url-safe base64.
    raw = "".join(os.environ.get("DATA_KEY", "").split())
    if not raw:
        print("DATA_KEY missing", file=sys.stderr)
        raise SystemExit(2)
    key = None
    for decoder in (base64.b64decode, base64.urlsafe_b64decode):
        try:
            candidate = decoder(raw)
        except (binascii.Error, ValueError):
            continue
        if len(candidate) == 32:
            key = candidate
            break
    if key is None:
        print("DATA_KEY not a valid 32-byte base64 key", file=sys.stderr)
        raise SystemExit(2)
    return key


def _make_fetch(client):
    def fetch(source, cursor: Cursor | None):
        return fetch_channel(client, source["id"], cursor)
    return fetch


def main(argv=None) -> int:
    from datetime import datetime, timezone
    argv = argv or sys.argv[1:]
    root = Path(argv[0]) if argv else Path("data_work")
    key = load_data_key()

    client = PoliteClient(make_transport(), budget=CONFIG.telegram_req_budget,
                          min_delay=CONFIG.domain_delay_sec[1])
    now = datetime.now(timezone.utc)
    metrics = execute_run(root, key, _make_fetch(client), now, budget=CONFIG.telegram_req_budget)

    check_tree(root)  # refuse to leave any non-encrypted file for the push
    print("run: " + " ".join(f"{k}={metrics[k]}" for k in sorted(metrics)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
