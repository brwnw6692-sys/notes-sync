"""Parsing and locating the 32-byte data key. The raw value never needs to be logged."""
import base64
import binascii
import os
from pathlib import Path

_LOCAL = Path(".secrets/DATA_KEY.txt")


def parse_key(raw: str) -> bytes | None:
    """A 32-byte key from base64 text, tolerating whitespace and url-safe alphabets. None if invalid."""
    cleaned = "".join((raw or "").split())
    if not cleaned:
        return None
    for decoder in (base64.b64decode, base64.urlsafe_b64decode):
        try:
            candidate = decoder(cleaned)
        except (binascii.Error, ValueError):
            continue
        if len(candidate) == 32:
            return candidate
    return None


def load_key(root: Path | None = None) -> bytes | None:
    """Prefer the DATA_KEY env var (CI); fall back to the local .secrets file (developer machine)."""
    env = os.environ.get("DATA_KEY")
    if env:
        return parse_key(env)
    local = (Path(root) / _LOCAL) if root else _LOCAL
    if local.exists():
        return parse_key(local.read_text(encoding="utf-8"))
    return None
