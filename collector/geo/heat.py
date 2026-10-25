"""Per-cell importance = how many people live there.

Population-based, from the gazetteer, so the whole region is in scope uniformly — everywhere there
are people, not a handful of conflict cities. A quiet populated cell is a real gap; empty desert and
sea stay cold. log1p keeps a megacity and a town both "hot" without one drowning the other.
"""
import math
from functools import lru_cache

from collector.geo.gazetteer import gazetteer_entries
from collector.geo.grid import all_cells, cell_of, center_of


@lru_cache(maxsize=1)
def _cell_population() -> dict:
    pop: dict = {}
    for e in gazetteer_entries():
        rc = cell_of(e["lat"], e["lon"])
        if rc is not None:
            pop[rc] = pop.get(rc, 0) + e.get("population", 0)
    return pop


def cell_weight(center: tuple) -> float:
    """Importance of the grid cell containing this point: log of its total population."""
    rc = cell_of(center[0], center[1])
    if rc is None:
        return 0.0
    return math.log1p(_cell_population().get(rc, 0))


@lru_cache(maxsize=1)
def build_heat() -> dict:
    return {rc: cell_weight(center_of(rc)) for rc in all_cells()}
