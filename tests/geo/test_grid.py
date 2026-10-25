from collector.geo.grid import cell_of, cell_id, center_of, all_cells, in_bounds
from collector.config import CONFIG


def test_a_point_inside_bounds_gets_a_cell():
    # Gaza City ~ 31.5N, 34.47E is inside the Middle East box
    rc = cell_of(31.5, 34.47)
    assert rc is not None
    assert in_bounds(31.5, 34.47)


def test_point_outside_bounds_is_none():
    assert cell_of(60.0, 10.0) is None   # northern Europe
    assert not in_bounds(60.0, 10.0)


def test_center_of_a_cell_maps_back_to_the_same_cell():
    for rc in list(all_cells())[:50]:
        lat, lon = center_of(rc)
        assert cell_of(lat, lon) == rc


def test_cell_id_is_stable_and_opaque():
    rc = cell_of(33.89, 35.50)  # Beirut
    assert cell_id(rc) == cell_id(rc)
    assert cell_id(rc).startswith("c")


def test_grid_covers_the_declared_bounds():
    cells = list(all_cells())
    lat_span = CONFIG.grid_lat_max - CONFIG.grid_lat_min
    lon_span = CONFIG.grid_lon_max - CONFIG.grid_lon_min
    expected = round(lat_span / CONFIG.grid_cell_deg) * round(lon_span / CONFIG.grid_cell_deg)
    assert len(cells) == expected


def test_two_distant_cities_fall_in_different_cells():
    assert cell_of(31.5, 34.47) != cell_of(35.7, 51.4)  # Gaza vs Tehran
