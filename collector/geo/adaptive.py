"""Adaptive resolution: coarse everywhere, fine only where activity is dense.

A uniform village-scale grid over the Middle East would be millions of cells. Instead a cell
refines into finer sub-cells only when enough messages land in it, so the number of fine cells
tracks activity, not area. Cell ids are opaque (no place names) and nest exactly across levels.
"""
from collector.config import CONFIG
from collector.geo.grid import in_bounds

_LAT0 = CONFIG.grid_lat_min
_LON0 = CONFIG.grid_lon_min


def level_deg(level: int) -> float:
    return CONFIG.grid_cell_deg / (CONFIG.adaptive_factor ** level)


def cell_at(lat: float, lon: float, level: int):
    size = level_deg(level)
    row = int((lat - _LAT0) / size)
    col = int((lon - _LON0) / size)
    return (level, row, col)


def center_at(cell) -> tuple:
    level, row, col = cell
    size = level_deg(level)
    return (_LAT0 + (row + 0.5) * size, _LON0 + (col + 0.5) * size)


def parent_of(cell):
    level, row, col = cell
    if level == 0:
        return cell
    f = CONFIG.adaptive_factor
    return (level - 1, row // f, col // f)


def cell_id(cell) -> str:
    level, row, col = cell
    return f"L{level}r{row}c{col}"


def adaptive_cells(items, split_threshold: int = CONFIG.adaptive_split_threshold,
                   max_level: int = CONFIG.adaptive_max_level) -> list:
    """Partition located items into mixed-level cells; dense spots end up at a deeper level."""
    located = [(it["lat"], it["lon"]) for it in items
               if it.get("lat") is not None and it.get("lon") is not None and in_bounds(it["lat"], it["lon"])]

    def refine(points, level):
        buckets = {}
        for lat, lon in points:
            buckets.setdefault(cell_at(lat, lon, level), []).append((lat, lon))
        out = []
        for cell, pts in buckets.items():
            if len(pts) >= split_threshold and level < max_level:
                out.extend(refine(pts, level + 1))
            else:
                lat, lon = center_at(cell)
                out.append({"id": cell_id(cell), "level": level, "lat": lat, "lon": lon, "count": len(pts)})
        return out

    return refine(located, 0)
