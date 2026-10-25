"""Coverage measured on the grid: how many independent sources sit in each cell, versus its heat.

This is how the system knows, by itself, how densely it covers the Middle East and where the gaps are.
"""
from collector.config import CONFIG
from collector.geo.grid import cell_of
from collector.geo.heat import build_heat


def grid_coverage(items) -> dict:
    """cell -> number of independent sources (distinct origin clusters) reporting from it."""
    by_cell = {}
    for it in items:
        if not it.get("is_original"):
            continue
        if it.get("lat") is None or it.get("lon") is None:
            continue
        rc = cell_of(it["lat"], it["lon"])
        if rc is None:
            continue
        by_cell.setdefault(rc, set()).add(it["origin_cluster_id"])
    return {rc: len(clusters) for rc, clusters in by_cell.items()}


def _hot_cells() -> dict:
    return {rc: w for rc, w in build_heat().items() if w >= CONFIG.coverage_hot_weight}


def blind_cells(coverage: dict) -> set:
    """Hot cells (worth watching) that currently have no independent coverage."""
    return {rc for rc in _hot_cells() if coverage.get(rc, 0) == 0}


def coverage_summary(coverage: dict) -> dict:
    """A self-assessment: what weighted share of the hot Middle East we actually see."""
    hot = _hot_cells()
    total_w = sum(hot.values())
    covered_w = sum(w for rc, w in hot.items() if coverage.get(rc, 0) > 0)
    return {
        "hot_cells": len(hot),
        "covered_hot_cells": sum(1 for rc in hot if coverage.get(rc, 0) > 0),
        "coverage_pct": round(100 * covered_w / total_w) if total_w else 0,
    }
