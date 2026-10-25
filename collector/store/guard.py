"""Last line of defense: nothing that is not encrypted may ever be pushed."""
import math
import sys
from pathlib import Path

from collector.store.crypto import HEADER, KEY_HEADER

_MIN_ENTROPY = 7.5      # bits/byte; AES-GCM output is ~7.95 on a 4 KB file
_KEY_LEN = 4 + 16 + 12 + 32 + 16  # header + salt + nonce + key + GCM tag
_MIN_KEY_ENTROPY = 5.0  # 76 random bytes give ~5.9; ASCII text gives ~3-4


def _entropy(data: bytes) -> float:
    if not data:
        return 0.0
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    n = len(data)
    return -sum((c / n) * math.log2(c / n) for c in freq if c)


def is_encrypted(path: Path) -> bool:
    data = Path(path).read_bytes()
    if data[:4] == KEY_HEADER:
        return len(data) == _KEY_LEN and _entropy(data[4:]) > _MIN_KEY_ENTROPY
    if data[:4] == HEADER:
        return _entropy(data[16:]) > _MIN_ENTROPY
    return False


def check_tree(root: Path) -> None:
    files = [p for p in Path(root).rglob("*") if p.is_file() and ".git" not in p.parts]
    bad = [p for p in files if not is_encrypted(p)]
    if bad:
        # Count only: file names themselves could leak in public logs.
        print(f"GUARD: {len(bad)} non-encrypted file(s) blocked", file=sys.stderr)
        raise SystemExit(1)
