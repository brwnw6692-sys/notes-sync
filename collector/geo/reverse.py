"""Reverse the gazetteer: name the most prominent place inside a grid cell.

This turns a blind spot into something we can act on — a place name to search channels for. We return
the name in both Arabic and Hebrew when the place has them, so one blind cell finds both the Arab and
the Israeli channels reporting from there (Israel is a lens, not an exception).
"""


def _script_name(names, lo, hi):
    for n in names:
        if any(lo <= c <= hi for c in n):
            return n
    return None


def _arabic(names):
    return _script_name(names, "؀", "ۿ")


def _hebrew(names):
    return _script_name(names, "֐", "׿")


def queries_in_cell(entries, lat: float, lon: float, half: float) -> list:
    """Arabic and/or Hebrew name(s) of the most populous named place within ±half degrees; [] if none.
    A place with only a Latin transliteration is skipped — it makes a useless Telegram query."""
    best, best_pop = None, -1
    for e in entries:
        if abs(e["lat"] - lat) <= half and abs(e["lon"] - lon) <= half:
            ar, he = _arabic(e["names"]), _hebrew(e["names"])
            if (ar or he) and e.get("population", 0) > best_pop:
                best, best_pop = (ar, he), e.get("population", 0)
    return [q for q in best if q] if best else []
