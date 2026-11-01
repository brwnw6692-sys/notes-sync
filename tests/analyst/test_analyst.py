from datetime import datetime, timezone, timedelta
from collector.analyst import build_digest, analyst_prompt, parse_assessment

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


def _it(cid, src, text, hours_ago, lat=33.5, lon=36.3):
    return {"lat": lat, "lon": lon, "source_id": src, "posted_at": (NOW - timedelta(hours=hours_ago)).isoformat(),
            "text_raw": text}


def test_digest_includes_recent_located_items_with_tags():
    items = [_it("c1", "s_ar", "قصف في دمشق", 3), _it("c2", "s_he", "תקיפה בגבול", 10)]
    d = build_digest(items, NOW, lens_of={"s_ar": "ar", "s_he": "he"},
                     affiliation_of={"s_ar": "hezbollah"})
    assert "دمشق" in d and "ar/hezbollah" in d
    assert "he" in d


def test_digest_drops_old_and_unlocated():
    items = [_it("c1", "s", "ישן מדי", 500), {"source_id": "s", "text_raw": "no coords", "posted_at": NOW.isoformat()}]
    assert build_digest(items, NOW) == ""


def test_prompt_demands_grounding_and_json():
    p = analyst_prompt("- 1h ago ...", NOW)
    assert "OBSERVED" in p and "INFERRED" in p and "insufficient data" in p and "JSON" in p


def test_parse_handles_fenced_json():
    out = parse_assessment('```json\n{"actors":[{"actor":"Iran"}],"summary":"x"}\n```')
    assert out["actors"][0]["actor"] == "Iran" and out["summary"] == "x"


def test_parse_falls_back_on_garbage():
    out = parse_assessment("sorry, no json here")
    assert out["actors"] == [] and "raw" in out
