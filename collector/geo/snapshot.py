"""The map snapshot: a compact, encrypted view the browser decrypts and draws.

It carries only geometry and numbers (cell centers, levels, counts, heat, coverage) — never a place
name or a source name — so even decrypted it reveals a heat picture, not who we watch.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from collector.config import CONFIG
from collector.geo.adaptive import cell_at, center_at
from collector.geo.grid import center_of, in_bounds
from collector.geo.grid_coverage import blind_cells, coverage_summary, grid_coverage
from collector.geo.heat import build_heat, cell_weight
from collector.store.crypto import decrypt, encrypt

_MAP = "map.bin"


def locate_rows(items) -> list:
    """Rows for the map from stored items. Items missing coords are re-located with the
    current gazetteer, so improving the gazetteer heals older messages on the next run."""
    from collector.geo.gazetteer import default_gazetteer
    gaz = default_gazetteer()
    rows = []
    for it in items:
        lat, lon = it.get("lat"), it.get("lon")
        if lat is None or lon is None:
            loc = gaz.primary_location(it.get("text_raw", "") or "")
            if loc is not None:
                lat, lon = loc
        rows.append({"lat": lat, "lon": lon,
                     "origin_cluster_id": it.get("origin_cluster_id"),
                     "is_original": it.get("is_original", True),
                     "posted_at": it.get("posted_at", "")})
    return rows


def _age_hours(posted_at, now):
    """Hours between a message's timestamp and now; None if it can't be parsed."""
    try:
        t = datetime.fromisoformat((posted_at or "").replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    n = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
    return (n - t).total_seconds() / 3600


def build_snapshot(items, now: datetime) -> dict:
    heat = build_heat()
    coverage = grid_coverage(items)

    # Bin located messages at city scale; count independent sources (distinct origin clusters),
    # and separately those from the recent window, so the map can show what is hot *now*.
    level = CONFIG.active_display_level
    recent_h = CONFIG.recent_activity_hours
    buckets = {}
    for it in items:
        lat, lon = it.get("lat"), it.get("lon")
        if lat is None or lon is None or not in_bounds(lat, lon):
            continue
        cid = it.get("origin_cluster_id") if it.get("is_original") else None
        b = buckets.setdefault(cell_at(lat, lon, level), {"all": set(), "recent": set()})
        b["all"].add(cid)
        age = _age_hours(it.get("posted_at"), now)
        if age is not None and 0 <= age <= recent_h:
            b["recent"].add(cid)

    def _n(clusters):
        return len([c for c in clusters if c is not None]) or len(clusters)

    active = []
    for rc, b in buckets.items():
        clat, clon = center_at(rc)
        active.append({
            "lat": round(clat, 4), "lon": round(clon, 4), "level": level,
            "count": _n(b["all"]), "recent": _n(b["recent"]) if b["recent"] else 0,
            "heat": round(cell_weight((clat, clon)), 3),
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
