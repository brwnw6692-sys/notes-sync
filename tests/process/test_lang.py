from collector.process.lang import detect_lang


def test_arabic_text_is_ar():
    assert detect_lang("قصف في دمشق الليلة") == "ar"


def test_persian_is_grouped_as_ar():
    assert detect_lang("حمله به تهران") == "ar"


def test_hebrew_text_is_he():
    assert detect_lang("תקיפה בעזה הלילה") == "he"


def test_latin_text_is_en():
    assert detect_lang("breaking news from the north") == "en"


def test_empty_or_symbols_is_unknown():
    assert detect_lang("123 !!! ---") == ""
