from collector.config import CONFIG
from collector.geo.adaptive import (adaptive_cells, cell_at, cell_id, center_at,
                                   level_deg, parent_of)


def _pt(lat, lon):
    return {"lat": lat, "lon": lon}


def test_level_deg_divides_by_factor_each_level():
    assert level_deg(0) == CONFIG.grid_cell_deg
    assert abs(level_deg(1) - CONFIG.grid_cell_deg / CONFIG.adaptive_factor) < 1e-12
    assert level_deg(2) < level_deg(1)


def test_deeper_levels_reach_village_scale():
    # max level cell size should be well under ~1 km (0.01 deg ~ 1.1 km)
    assert level_deg(CONFIG.adaptive_max_level) < 0.01


def test_cell_center_maps_back_to_same_cell_at_its_level():
    c = cell_at(31.50, 34.47, level=2)
    lat, lon = center_at(c)
    assert cell_at(lat, lon, level=2) == c


def test_a_deep_cell_nests_inside_its_parent():
    c = cell_at(33.89, 35.50, level=3)
    p = parent_of(c)
    assert p[0] == 2
    # the deep cell's center falls inside the parent cell
    assert cell_at(*center_at(c), level=2) == p


def test_sparse_area_stays_coarse():
    cells = adaptive_cells([_pt(31.5, 34.47), _pt(33.89, 35.50)],
                           split_threshold=5)
    assert all(c["level"] == 0 for c in cells)
    assert len(cells) == 2


def test_dense_cluster_refines_to_a_deep_cell():
    # 20 messages from essentially one spot -> refine down to the deepest level
    pts = [_pt(31.500 + i * 0.0001, 34.470) for i in range(20)]
    cells = adaptive_cells(pts, split_threshold=5)
    assert max(c["level"] for c in cells) == CONFIG.adaptive_max_level


def test_counts_are_preserved_across_refinement():
    pts = [_pt(31.500, 34.470) for _ in range(12)] + [_pt(33.89, 35.50)]
    cells = adaptive_cells(pts, split_threshold=5)
    assert sum(c["count"] for c in cells) == 13


def test_items_without_coords_are_ignored():
    cells = adaptive_cells([{"lat": None, "lon": None}, _pt(31.5, 34.47)], split_threshold=5)
    assert len(cells) == 1 and cells[0]["count"] == 1


def test_two_separated_clusters_do_not_over_refine_each_other():
    cluster_a = [_pt(31.500, 34.470) for _ in range(12)]
    far_single = [_pt(35.69, 51.39)]
    cells = adaptive_cells(cluster_a + far_single, split_threshold=5)
    deep = [c for c in cells if c["level"] == CONFIG.adaptive_max_level]
    shallow = [c for c in cells if c["level"] == 0 and c["count"] == 1]
    assert deep and shallow  # Tehran stays coarse while Gaza refines
