from collector.geo.grid import cell_of, center_of
from collector.geo.heat import build_heat, cell_weight


def test_a_cell_on_a_major_city_is_hotter_than_an_empty_desert_cell():
    tehran = cell_of(35.69, 51.39)
    empty = cell_of(27.0, 55.0)  # open desert / gulf, far from any seed city
    assert cell_weight(center_of(tehran)) > cell_weight(center_of(empty))


def test_heat_decays_with_distance_from_a_city():
    near = cell_weight((33.89, 35.50))   # on Beirut
    far = cell_weight((33.89, 37.50))    # ~185 km east
    assert near > far


def test_build_heat_returns_a_weight_for_every_cell():
    heat = build_heat()
    from collector.geo.grid import all_cells
    assert set(heat) == {rc for rc in all_cells()}
    assert all(w >= 0 for w in heat.values())


def test_some_cells_are_hot_and_many_are_cold():
    heat = build_heat()
    from collector.config import CONFIG
    hot = [w for w in heat.values() if w >= CONFIG.coverage_hot_weight]
    assert 0 < len(hot) < len(heat)  # hot core exists, but most of the box is cold
