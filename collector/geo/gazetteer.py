"""Place tagging: turn place names in a message into points on the map.

Backed by a gazetteer (seed list bundled; a full GeoNames-built one can replace it). Matching is on
normalized Arabic/Persian text with word boundaries, so a name never fires inside a larger word.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

from collector.process.normalize import normalize_text

_MIN_NAME_CHARS = 3
_SEED = Path(__file__).parent / "gazetteer_seed.json"


class Gazetteer:
    def __init__(self, entries):
        self._by_id = {}
        self._patterns = []  # (compiled_regex, entry_id)
        for e in entries:
            self._by_id[e["id"]] = e
            for name in e["names"]:
                norm = normalize_text(name)
                if len(norm) < _MIN_NAME_CHARS:
                    continue
                # (?<!\w) / (?!\w) keep a name from matching inside a longer word.
                pat = re.compile(r"(?<!\w)" + re.escape(norm) + r"(?!\w)")
                self._patterns.append((pat, e["id"]))

    def tag_places(self, text: str) -> list:
        norm = normalize_text(text)
        found = {}
        for pat, eid in self._patterns:
            if eid not in found and pat.search(norm):
                e = self._by_id[eid]
                found[eid] = {"id": eid, "lat": e["lat"], "lon": e["lon"]}
        return list(found.values())

    def primary_location(self, text: str):
        """One representative coordinate for the message: the most populous place mentioned."""
        hits = self.tag_places(text)
        if not hits:
            return None
        best = max(hits, key=lambda h: self._by_id[h["id"]].get("population", 0))
        return (best["lat"], best["lon"])


@lru_cache(maxsize=1)
def default_gazetteer() -> Gazetteer:
    return Gazetteer(json.loads(_SEED.read_text(encoding="utf-8")))
