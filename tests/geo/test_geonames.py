from collector.geo.build_gazetteer import parse_line, build_entries

# geonameid, name, asciiname, alternatenames, lat, lon, fclass, fcode, cc, ... population at col 14
GAZA = "\t".join(["281133", "Gaza", "Gaza", "غزة,غزه,Gaza City", "31.5", "34.47",
                  "P", "PPLA", "PS"] + [""] * 5 + ["590481"] + [""] * 4)
MOUNTAIN = "\t".join(["999", "Some Peak", "Some Peak", "", "33.0", "36.0",
                      "T", "MT", "SY"] + [""] * 5 + ["0"] + [""] * 4)
TINY = "\t".join(["1000", "Hamlet", "Hamlet", "قرية", "32.0", "35.0",
                  "P", "PPL", "LB"] + [""] * 5 + ["12"] + [""] * 4)


def test_parse_extracts_names_coords_and_population():
    e = parse_line(GAZA)
    assert e["id"] == "gn281133"
    assert "غزة" in e["names"] and "Gaza" in e["names"]
    assert e["lat"] == 31.5 and e["lon"] == 34.47 and e["population"] == 590481


def test_non_populated_feature_is_skipped():
    assert parse_line(MOUNTAIN) is None


def test_build_filters_by_minimum_population():
    entries = build_entries([GAZA, TINY, MOUNTAIN], min_population=100)
    ids = {e["id"] for e in entries}
    assert "gn281133" in ids        # Gaza kept
    assert "gn1000" not in ids       # 12-person hamlet dropped at this threshold


def test_build_keeps_villages_when_threshold_is_low():
    entries = build_entries([TINY], min_population=0)
    assert len(entries) == 1 and "قرية" in entries[0]["names"]


def test_malformed_line_is_skipped():
    assert parse_line("too\tfew\tcols") is None
