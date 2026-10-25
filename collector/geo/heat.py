"""Per-cell "heat": importance computed from nearby cities, decaying with distance.

Dense, central places come out hot on their own; margins stay cold. This is the weight that
coverage is measured against, so a quiet hot cell is a real gap while a quiet cold cell is fine.
"""
import json
import math
from functools import lru_cache
from pathlib import Path

from collector.config import CONFIG
from collector.geo.grid import all_cells, center_of, haversine_km

_CITIES = json.loads((Path(__file__).parent / "cities.json").read_text(encoding="utf-8"))


def cell_weight(center: tuple) -> float:
    """Sum of each city's weight attenuated by a Gaussian in distance (sigma = heat_sigma_km)."""
    sigma = CONFIG.heat_sigma_km
    total = 0.0
    for city in _CITIES:
        d = haversine_km(center, (city["lat"], city["lon"]))
        total += city["weight"] * math.exp(-(d * d) / (2 * sigma * sigma))
    return total


@lru_cache(maxsize=1)
def build_heat() -> dict:
    return {rc: cell_weight(center_of(rc)) for rc in all_cells()}
