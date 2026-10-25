from collector.process.normalize import normalize_text, normalize_digits


def test_unifies_alef_and_strips_diacritics_and_tatweel():
    assert normalize_text("أحـــمَد") == "احمد"


def test_diacritic_variant_of_place_matches_plain():
    assert normalize_text("خانْ يونُس") == normalize_text("خان يونس")


def test_persian_and_arabic_yeh_kaf_match():
    assert normalize_text("کرمانشاهی") == normalize_text("كرمانشاهي")


def test_alef_maqsura_and_ta_marbuta_unified():
    assert normalize_text("مستشفى غزة") == normalize_text("مستشفي غزه")


def test_arabic_and_persian_digits_to_latin():
    assert normalize_digits("٣٤٥") == "345"
    assert normalize_digits("۱۲۳") == "123"


def test_collapses_whitespace():
    assert normalize_text("  خان   يونس \n") == "خان يونس"
