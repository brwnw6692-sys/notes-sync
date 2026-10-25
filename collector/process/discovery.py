"""Auto-discovery: the network grows itself by finding channels referenced in forwards and links."""
import re

# Public channel handle: letters/digits/underscore, 5-32 chars (Telegram's rule).
_HANDLE = r"[A-Za-z]\w{4,31}"
_TME = re.compile(r"t\.me/(" + _HANDLE + r")", re.IGNORECASE)
_MENTION = re.compile(r"@(" + _HANDLE + r")")
# t.me/s (web preview), joinchat and +invite links are not public channel handles.
_RESERVED = {"s", "joinchat", "addstickers", "proxy", "iv", "share"}


def _clean(handle: str) -> str:
    return handle.lstrip("@").lower()


def extract_candidates(items, known) -> set:
    """Channel handles referenced by these items that we don't already follow."""
    known_lc = {_clean(k) for k in known}
    found = set()
    for it in items:
        if it.forwarded_from:
            found.add(_clean(it.forwarded_from))
        text = it.text_raw or ""
        for m in _TME.findall(text):
            found.add(m.lower())
        for m in _MENTION.findall(text):
            found.add(m.lower())
    return {h for h in found if h and h not in _RESERVED and h not in known_lc}
