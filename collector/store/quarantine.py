"""Encrypted snapshots of pages whose structure changed, so a parser fix can start from the real page."""
import hashlib
import hmac
import json
from datetime import datetime
from pathlib import Path

from collector.config import CONFIG
from collector.store.crypto import decrypt, encrypt

_DIR = "q"
_MAX_PER_SOURCE = CONFIG.quarantine_max_per_source
_MAX_TOTAL = CONFIG.quarantine_max_total


def _tag(source_id: str, key: bytes) -> str:
    # Keyed, so nobody without the key can test candidate channel names against file names.
    return hmac.new(key, source_id.encode(), hashlib.sha256).hexdigest()[:12]


def _stamp(path: Path) -> str:
    return path.stem.split("-", 1)[1]


def save_broken_page(html: str, source_id: str, key: bytes, root: Path, now: datetime) -> Path:
    qdir = Path(root) / _DIR
    qdir.mkdir(parents=True, exist_ok=True)
    tag = _tag(source_id, key)
    path = qdir / f"{tag}-{now.strftime('%Y%m%dT%H%M%S%f')}.bin"
    record = {"source_id": source_id, "captured_at": now.isoformat(), "html": html}
    path.write_bytes(encrypt(json.dumps(record, ensure_ascii=False).encode(), key))

    mine = sorted(qdir.glob(f"{tag}-*.bin"), key=_stamp)
    for old in mine[:-_MAX_PER_SOURCE]:
        old.unlink()
    everything = sorted(qdir.glob("*.bin"), key=_stamp)
    for old in everything[:-_MAX_TOTAL]:
        old.unlink()
    return path


def load_quarantined(path: Path, key: bytes) -> dict:
    return json.loads(decrypt(Path(path).read_bytes(), key))
