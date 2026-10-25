"""Reverse the gazetteer: name the most prominent place inside a grid cell.

This is what turns a blind spot (a cell with activity but no coverage) into something we can act on —
an Arabic place name to search for channels that report from there.
"""


def _arabic_name(names):
    """An Arabic-script name, or None — a Latin transliteration makes a useless Telegram query."""
    for n in names:
        if any("؀" <= c <= "ۿ" for c in n):
            return n
    return None


def place_in_cell(entries, lat: float, lon: float, half: float) -> str:
    """Arabic name of the most populous Arabic-named place within ±half degrees of (lat, lon); '' if none.
    Places with no Arabic name are skipped, so the query always reads as an Arab-world place."""
    best_name, best_pop = "", -1
    for e in entries:
        if abs(e["lat"] - lat) <= half and abs(e["lon"] - lon) <= half:
            name = _arabic_name(e["names"])
            if name and e.get("population", 0) > best_pop:
                best_name, best_pop = name, e.get("population", 0)
    return best_name
