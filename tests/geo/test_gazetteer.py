from collector.geo.gazetteer import Gazetteer

FIX = [
    {"id": "gaza", "names": ["غزة", "غزه"], "lat": 31.50, "lon": 34.47, "population": 590000},
    {"id": "khan_yunis", "names": ["خان يونس", "خانيونس"], "lat": 31.34, "lon": 34.30, "population": 200000},
    {"id": "beirut", "names": ["بيروت"], "lat": 33.89, "lon": 35.50, "population": 360000},
    {"id": "nasr", "names": ["النصر"], "lat": 30.0, "lon": 31.0, "population": 5000},
]


def _g():
    return Gazetteer(FIX)


def test_finds_a_place_and_returns_coords():
    hits = _g().tag_places("انفجار كبير في خان يونس الليلة")
    assert len(hits) == 1
    assert hits[0]["id"] == "khan_yunis"
    assert hits[0]["lat"] == 31.34 and hits[0]["lon"] == 34.30


def test_matches_spelling_variant_via_normalization():
    # "خانيونس" (no space) should match the "خان يونس" entry through normalization
    assert _g().tag_places("قصف خانيونس")[0]["id"] == "khan_yunis"


def test_finds_multiple_distinct_places():
    ids = {h["id"] for h in _g().tag_places("من غزة الى بيروت")}
    assert ids == {"gaza", "beirut"}


def test_same_place_mentioned_twice_is_deduped():
    hits = _g().tag_places("غزة غزة غزة")
    assert len(hits) == 1


def test_no_place_returns_empty():
    assert _g().tag_places("اجتماع اقتصادي اليوم") == []


def test_matches_name_with_an_attached_prefix():
    # Prepositions/article attach to the word in Arabic/Hebrew, so the boundary match
    # must still fire: و+بيروت and ب+غزة.
    assert _g().tag_places("انفجار وبيروت الليلة")[0]["id"] == "beirut"
    assert _g().tag_places("قصف بغزة")[0]["id"] == "gaza"


def test_does_not_match_inside_a_larger_word():
    # "النصر" as a standalone place must not fire inside "الانتصار"
    assert _g().tag_places("تحقق الانتصار الكبير") == []


def test_primary_location_picks_highest_population():
    g = _g()
    loc = g.primary_location("من غزة الصغيرة ومن بيروت")
    # Beirut (360k) < Gaza (590k) -> Gaza wins
    assert loc == (31.50, 34.47)


def test_primary_location_none_when_no_place():
    assert _g().primary_location("لا يوجد مكان هنا") is None
