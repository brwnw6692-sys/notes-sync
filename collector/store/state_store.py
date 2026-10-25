"""Encrypted persistence for the data branch: run state, hot-tier item shards, and the heartbeat."""
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path

from collector.config import CONFIG
from collector.store.crypto import decrypt, encrypt

_STATE = "state.bin"
_SOURCES = "sources.bin"
_HEARTBEAT = "heartbeat.bin"
_SHARDS = "shards"


def default_state() -> dict:
    return {"sources": [], "backlog": [], "run_index": 0, "red_regions": []}


def _write(path: Path, obj, key: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encrypt(json.dumps(obj, ensure_ascii=False).encode(), key))


def _read(path: Path, key: bytes):
    return json.loads(decrypt(path.read_bytes(), key))


def save_state(state: dict, key: bytes, root: Path) -> None:
    _write(Path(root) / _STATE, state, key)


def load_state(key: bytes, root: Path) -> dict:
    path = Path(root) / _STATE
    return _read(path, key) if path.exists() else default_state()


def save_sources(sources, key: bytes, root: Path) -> None:
    _write(Path(root) / _SOURCES, sources, key)


def load_sources(key: bytes, root: Path) -> list:
    path = Path(root) / _SOURCES
    return _read(path, key) if path.exists() else []


def save_items(items, key: bytes, root: Path, now: datetime) -> Path:
    records = [asdict(it) if is_dataclass(it) else it for it in items]
    path = Path(root) / _SHARDS / f"{now.strftime('%Y%m%dT%H%M%S%f')}.bin"
    _write(path, records, key)
    return path


def load_recent_items(key: bytes, root: Path) -> list:
    out = []
    for shard in sorted((Path(root) / _SHARDS).glob("*.bin")):
        out.extend(_read(shard, key))
    return out


def prune_old_shards(root: Path, now: datetime, days: int = CONFIG.hot_items_retention_days) -> int:
    cutoff = now.timestamp() - days * 86400
    removed = 0
    for shard in (Path(root) / _SHARDS).glob("*.bin"):
        stamp = datetime.strptime(shard.stem, "%Y%m%dT%H%M%S%f").replace(tzinfo=timezone.utc)
        if stamp.timestamp() < cutoff:
            shard.unlink()
            removed += 1
    return removed


def write_heartbeat(key: bytes, root: Path, now: datetime, metrics: dict) -> None:
    _write(Path(root) / _HEARTBEAT, {"last_run_at": now.isoformat(), "metrics": metrics}, key)


def read_heartbeat(key: bytes, root: Path) -> dict:
    return _read(Path(root) / _HEARTBEAT, key)
