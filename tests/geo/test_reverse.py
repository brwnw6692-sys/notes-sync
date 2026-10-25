from collector.geo.reverse import queries_in_cell

ENTRIES = [
    {"id": "a", "names": ["دمشق", "Damascus"], "lat": 33.5, "lon": 36.3, "population": 1500000},
    {"id": "b", "names": ["داريا", "Darayya"], "lat": 33.45, "lon": 36.23, "population": 80000},
    {"id": "il", "names": ["ראשון לציון", "Rishon LeTsiyyon"], "lat": 31.96, "lon": 34.80, "population": 250000},
    {"id": "bs", "names": ["بئر السبع", "באר שבע", "Beersheba"], "lat": 31.25, "lon": 34.79, "population": 200000},
]


def test_returns_the_most_populous_place_name():
    assert queries_in_cell(ENTRIES, 33.5, 36.3, half=0.25) == ["دمشق"]


def test_hebrew_only_place_is_queried_in_hebrew():
    # Rishon has no Arabic name — we must still query it, in Hebrew (Israel is in).
    assert queries_in_cell(ENTRIES, 31.96, 34.80, half=0.25) == ["ראשון לציון"]


def test_bilingual_place_yields_both_scripts():
    out = queries_in_cell(ENTRIES, 31.25, 34.79, half=0.25)
    assert "بئر السبع" in out and "באר שבע" in out
    assert "Beersheba" not in out          # never the Latin transliteration


def test_empty_when_no_named_place_in_cell():
    assert queries_in_cell(ENTRIES, 20.0, 20.0, half=0.25) == []
