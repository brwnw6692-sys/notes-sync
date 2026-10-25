import pytest

from collector.core.safe_log import format_run_summary, scan_output_for_leaks


def test_detects_source_name_in_output():
    assert scan_output_for_leaks("run ok: fetched chan_secret", ["chan_secret"]) == ["chan_secret"]


def test_detection_ignores_case():
    assert scan_output_for_leaks("Fetched CHAN_Secret", ["chan_secret"]) == ["chan_secret"]


def test_clean_output_passes():
    assert scan_output_for_leaks("run ok: 12 sources, 3 failed", ["chan_secret"]) == []


def test_empty_terms_are_ignored():
    assert scan_output_for_leaks("anything", ["", None]) == []


def test_summary_contains_only_numbers():
    line = format_run_summary({"ok": 10, "quiet": 3, "broken": 1})
    assert line == "run: broken=1 ok=10 quiet=3"


def test_summary_rejects_non_numeric_values():
    with pytest.raises(TypeError):
        format_run_summary({"ok": "chan_secret"})


def test_summary_rejects_unknown_keys():
    with pytest.raises(ValueError):
        format_run_summary({"chan_secret": 1})
