from collector.core.contract import CollectResult
from collector.core.health import classify, abnormal_silence


def test_structure_broken_is_never_quiet():
    r = CollectResult(fetch_ok=True, structure_ok=False)
    assert classify(r) == "broken"


def test_fetch_ok_no_items_is_quiet():
    assert classify(CollectResult(fetch_ok=True, structure_ok=True)) == "quiet"


def test_fetch_ok_with_items_is_ok():
    assert classify(CollectResult(fetch_ok=True, structure_ok=True, items=["x"])) == "ok"


def test_429_is_limited_even_though_fetch_failed():
    assert classify(CollectResult(fetch_ok=False, http_status=429)) == "limited"


def test_partial_is_limited():
    r = CollectResult(fetch_ok=True, structure_ok=True, error_kind="partial")
    assert classify(r) == "limited"


def test_server_error_is_broken():
    assert classify(CollectResult(fetch_ok=False, http_status=503)) == "broken"


def test_single_404_is_broken_not_dead():
    assert classify(CollectResult(fetch_ok=False, http_status=404), prior_not_found=0) == "broken"


def test_third_consecutive_404_is_dead():
    assert classify(CollectResult(fetch_ok=False, http_status=404), prior_not_found=2) == "dead"


def test_abnormal_silence_triggers_past_factor():
    assert abnormal_silence(median_gap_sec=3600, silent_sec=5 * 3600)


def test_silence_below_floor_is_not_abnormal():
    assert not abnormal_silence(median_gap_sec=60, silent_sec=2 * 3600)


def test_source_without_history_is_never_abnormal():
    assert not abnormal_silence(median_gap_sec=0, silent_sec=48 * 3600)
