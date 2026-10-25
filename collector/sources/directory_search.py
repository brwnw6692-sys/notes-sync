"""Blind-spot discovery via a public Telegram search site (lyzem): a place name in, candidate handles out.

Pure: URL in / HTML -> handles. The actual GET lives at the live edge, like the Telegram adapter.
"""
import re
from urllib.parse import quote

_HANDLE = re.compile(r"t\.me/([A-Za-z]\w{4,31})", re.IGNORECASE)


def _is_spam(hl: str) -> bool:
    """A long handle that is almost all consonants is keyboard-mash, not a real channel."""
    if len(hl) <= 16:
        return False
    vowels = sum(c in "aeiou" for c in hl)
    return vowels / len(hl) < 0.22


def search_url(query: str) -> str:
    return f"https://lyzem.com/search?q={quote(query)}&type=channels"


def parse_results(html: str, limit: int = 15) -> list:
    """Candidate handles from a lyzem channel-search page, best-effort de-noised; vetting is the real filter."""
    out, seen = [], set()
    for h in _HANDLE.findall(html or ""):
        hl = h.lower()
        if hl in seen:
            continue
        seen.add(hl)
        if "lyzem" in hl or hl.endswith("bot") or _is_spam(hl):
            continue
        out.append(hl)
        if len(out) >= limit:
            break
    return out
