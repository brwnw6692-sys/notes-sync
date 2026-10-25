from datetime import datetime, timedelta, timezone

from collector.core.canary import canary_failing, system_sight

NOW = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)


def _c(state, hours_since_post):
    return {"state": state, "last_post_at": (NOW - timedelta(hours=hours_since_post)).isoformat()}


def test_ok_canary_is_not_failing():
    assert not canary_failing(_c("ok", 0.5), NOW)


def test_quiet_but_recent_canary_is_not_failing():
    assert not canary_failing(_c("quiet", 1), NOW)


def test_canary_silent_too_long_is_failing():
    assert canary_failing(_c("quiet", 3), NOW)


def test_broken_or_limited_canary_is_failing():
    assert canary_failing(_c("broken", 0.1), NOW)
    assert canary_failing(_c("limited", 0.1), NOW)


def test_canary_without_any_post_is_failing():
    assert canary_failing({"state": "quiet", "last_post_at": ""}, NOW)


def test_all_healthy_means_healthy():
    r = system_sight([_c("ok", 0.2), _c("ok", 0.5), _c("quiet", 1)], NOW)
    assert r == {"sight": "healthy", "suppress_silence_signals": False, "failing": 0, "total": 3}


def test_minority_failing_is_degraded_and_signals_kept():
    r = system_sight([_c("ok", 0.2), _c("ok", 0.5), _c("broken", 0.1)], NOW)
    assert r["sight"] == "degraded" and r["suppress_silence_signals"] is False


def test_half_or_more_failing_is_blind_and_silence_suppressed():
    r = system_sight([_c("ok", 0.2), _c("broken", 0.1)], NOW)
    assert r["sight"] == "blind" and r["suppress_silence_signals"] is True


def test_no_canaries_configured_is_unknown_and_conservative():
    r = system_sight([], NOW)
    assert r["sight"] == "unknown" and r["suppress_silence_signals"] is True
