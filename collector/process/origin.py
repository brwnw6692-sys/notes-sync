"""Who said it first: forward chains plus SimHash near-duplicate clustering."""
import hashlib
from datetime import datetime

_SHINGLE = 4


def _shingles(text: str):
    t = " ".join(text.split())
    if len(t) <= _SHINGLE:
        return [t] if t else []
    return [t[i:i + _SHINGLE] for i in range(len(t) - _SHINGLE + 1)]


def simhash(text: str, bits: int = 64) -> int:
    v = [0] * bits
    for sh in _shingles(text):
        h = int.from_bytes(hashlib.blake2b(sh.encode(), digest_size=8).digest(), "big")
        for i in range(bits):
            v[i] += 1 if (h >> i) & 1 else -1
    out = 0
    for i in range(bits):
        if v[i] > 0:
            out |= 1 << i
    return out


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def _ts(s: str) -> datetime | None:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def cluster_items(items, hamming_max: int, window_hours: int):
    """Assign origin_cluster_id; the earliest item in each cluster is the original."""
    ordered = sorted(items, key=lambda it: (_ts(it.posted_at) is None, _ts(it.posted_at) or datetime.min))
    reps = []  # (signature, cluster_id, timestamp)
    window = window_hours * 3600
    for it in ordered:
        sig = simhash(it.text_norm or it.text_raw)
        ts = _ts(it.posted_at)
        match = None
        if ts is not None:
            for h, cid, rts in reps:
                if hamming(sig, h) <= hamming_max and abs((ts - rts).total_seconds()) <= window:
                    match = cid
                    break
        if match:
            it.origin_cluster_id = match
            it.is_original = False
        else:
            it.origin_cluster_id = it.id
            it.is_original = it.forwarded_from is None
            if ts is not None:
                reps.append((sig, it.id, ts))
    return ordered
