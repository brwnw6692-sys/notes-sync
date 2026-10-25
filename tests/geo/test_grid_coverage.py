from collector.geo.grid_coverage import grid_coverage, blind_cells, coverage_summary


def _item(lat, lon, cluster, original=True):
    return {"lat": lat, "lon": lon, "origin_cluster_id": cluster, "is_original": original}


def test_coverage_counts_independent_sources_per_cell():
    items = [
        _item(31.50, 34.47, "c1"),               # Gaza
        _item(31.51, 34.46, "c1", original=False),  # copy, same cell
        _item(31.52, 34.45, "c2"),               # independent, same cell
        _item(33.89, 35.50, "c3"),               # Beirut, different cell
    ]
    cov = grid_coverage(items)
    from collector.geo.grid import cell_of
    assert cov[cell_of(31.50, 34.47)] == 2
    assert cov[cell_of(33.89, 35.50)] == 1


def test_items_outside_the_grid_are_ignored():
    assert grid_coverage([_item(60.0, 10.0, "c1")]) == {}


def test_a_hot_cell_with_no_coverage_is_blind_a_cold_one_is_not():
    blind = blind_cells(coverage={})  # nothing covered anywhere
    from collector.geo.grid import cell_of
    assert cell_of(35.69, 51.39) in blind      # Tehran: hot, uncovered -> blind
    assert cell_of(27.0, 55.0) not in blind    # empty desert: cold -> not blind


def test_covering_a_hot_cell_removes_it_from_blind():
    tehran = (35.69, 51.39)
    cov = grid_coverage([_item(*tehran, "c1"), _item(35.70, 51.40, "c2")])
    from collector.geo.grid import cell_of
    assert cell_of(*tehran) not in blind_cells(cov)


def test_summary_reports_coverage_as_weighted_fraction_of_hot_cells():
    s = coverage_summary(coverage={})
    assert s["hot_cells"] > 0
    assert s["covered_hot_cells"] == 0
    assert s["coverage_pct"] == 0
