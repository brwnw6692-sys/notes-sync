from collector.process.affiliation import classify_affiliation, dominant_affiliation


def test_detects_actor_markers():
    assert classify_affiliation("بيان صادر عن كتائب القسام") == "hamas"
    assert classify_affiliation("عناصر من الحشد الشعبي في الانبار") == "pmf"
    assert classify_affiliation("قوات قسد تسيطر على") == "sdf"
    assert classify_affiliation('הודעת צה"ל על תקיפה') == "israeli_mil"


def test_no_marker_is_empty():
    assert classify_affiliation("قصف في دمشق الليلة") == ""
    assert classify_affiliation("") == ""


def test_dominant_needs_a_clear_majority():
    assert dominant_affiliation({"hamas": 8, "pij": 1}) == "hamas"      # clear
    assert dominant_affiliation({"hamas": 3, "pij": 3}) == ""           # split -> unknown
    assert dominant_affiliation({"hamas": 2}) == ""                     # too few samples
