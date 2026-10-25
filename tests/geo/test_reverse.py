from collector.geo.reverse import place_in_cell

ENTRIES = [
    {"id": "a", "names": ["دمشق", "Damascus"], "lat": 33.5, "lon": 36.3, "population": 1500000},
    {"id": "b", "names": ["داريا", "Darayya"], "lat": 33.45, "lon": 36.23, "population": 80000},
    {"id": "c", "names": ["بغداد"], "lat": 33.3, "lon": 44.4, "population": 6000000},
]


def test_picks_the_most_populous_place_in_the_cell():
    # cell around Damascus: both a and b fall inside, a is bigger
    assert place_in_cell(ENTRIES, 33.5, 36.3, half=0.25) == "دمشق"


def test_prefers_an_arabic_name_over_latin():
    one = [{"id": "a", "names": ["Damascus", "دمشق"], "lat": 33.5, "lon": 36.3, "population": 1}]
    assert place_in_cell(one, 33.5, 36.3, half=0.25) == "دمشق"


def test_empty_when_no_place_in_cell():
    assert place_in_cell(ENTRIES, 20.0, 20.0, half=0.25) == ""


def test_skips_places_with_no_arabic_name():
    # a Latin-only entry must not become a query
    latin = [{"id": "x", "names": ["Rishon LeTsiyyon"], "lat": 31.96, "lon": 34.8, "population": 200000}]
    assert place_in_cell(latin, 31.96, 34.8, half=0.25) == ""
