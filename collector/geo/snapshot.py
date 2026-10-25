"""The map snapshot: a compact, encrypted view the browser decrypts and draws.

It carries only geometry and numbers (cell centers, levels, counts, heat, coverage) — never a place
name or a source name — so even decrypted it reveals a heat picture, not who we watch.
"""
import json
from datetime import datetime
from pathlib import Path

from collector.geo.adaptive import adaptive_cells
from collector.geo.grid import center_of
from collector.geo.grid_coverage import blind_cells, coverage_summary, grid_coverage
from collector.geo.heat import build_heat, cell_weight
from collector.store.crypto import decrypt, encrypt

_MAP = "map.bin"


def build_snapshot(items, now: datetime) -> dict:
    heat = build_heat()
    coverage = grid_coverage(items)

    active = []
    for cell in adaptive_cells(items):
        active.append({
            "lat": round(cell["lat"], 4), "lon": round(cell["lon"], 4),
            "level": cell["level"], "count": cell["count"],
            "heat": round(cell_weight((cell["lat"], cell["lon"])), 3),
        })

    blind = []
    for rc in blind_cells(coverage):
        lat, lon = center_of(rc)
        blind.append({"lat": round(lat, 4), "lon": round(lon, 4), "heat": round(heat[rc], 3)})

    summary = coverage_summary(coverage)
    return {
        "generated_at": now.isoformat(),
        "coverage_pct": summary["coverage_pct"],
        "hot_cells": summary["hot_cells"],
        "covered_hot_cells": summary["covered_hot_cells"],
        "active": active,
        "blind": blind,
    }


def save_snapshot(snapshot: dict, key: bytes, root: Path) -> None:
    path = Path(root) / _MAP
    path.write_bytes(encrypt(json.dumps(snapshot, ensure_ascii=False).encode(), key))


def load_snapshot(key: bytes, root: Path) -> dict:
    return json.loads(decrypt((Path(root) / _MAP).read_bytes(), key))
