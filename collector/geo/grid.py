"""A fixed lat/lon grid over the Middle East. Each cell is the unit of coverage measurement."""
import math

from collector.config import CONFIG

_ROWS = round((CONFIG.grid_lat_max - CONFIG.grid_lat_min) / CONFIG.grid_cell_deg)
_COLS = round((CONFIG.grid_lon_max - CONFIG.grid_lon_min) / CONFIG.grid_cell_deg)


def in_bounds(lat: float, lon: float) -> bool:
    return (CONFIG.grid_lat_min <= lat < CONFIG.grid_lat_max
            and CONFIG.grid_lon_min <= lon < CONFIG.grid_lon_max)


def cell_of(lat: float, lon: float):
    """(row, col) for a coordinate, or None if outside the grid."""
    if not in_bounds(lat, lon):
        return None
    row = int((lat - CONFIG.grid_lat_min) / CONFIG.grid_cell_deg)
    col = int((lon - CONFIG.grid_lon_min) / CONFIG.grid_cell_deg)
    return (row, col)


def center_of(rc) -> tuple:
    row, col = rc
    lat = CONFIG.grid_lat_min + (row + 0.5) * CONFIG.grid_cell_deg
    lon = CONFIG.grid_lon_min + (col + 0.5) * CONFIG.grid_cell_deg
    return (lat, lon)


def cell_id(rc) -> str:
    """Opaque, stable id. Carries no place name, so it is safe in any stored or logged form."""
    row, col = rc
    return f"c{row:02d}{col:02d}"


def all_cells():
    for row in range(_ROWS):
        for col in range(_COLS):
            yield (row, col)


def haversine_km(a: tuple, b: tuple) -> float:
    lat1, lon1 = a
    lat2, lon2 = b
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(h)))
