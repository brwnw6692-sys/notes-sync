from collector.process.rhythm import build_profile, is_active_hour


def _posts(hours, per_hour, days=10):
    return [f"2026-10-{d:02d}T{h:02d}:{m:02d}:00+00:00"
            for d in range(1, days + 1) for h in hours for m in range(per_hour)]


def test_too_few_posts_gives_no_profile():
    assert build_profile(_posts([9], 1, days=3)) is None


def test_profile_has_24_shares_summing_to_one():
    prof = build_profile(_posts([8, 9, 10], 3))
    assert len(prof) == 24
    assert abs(sum(prof) - 1.0) < 1e-9


def test_posting_hours_are_active_and_night_is_not():
    prof = build_profile(_posts([8, 9, 10], 3))
    assert is_active_hour(prof, 9)
    assert not is_active_hour(prof, 3)


def test_smoothing_bridges_a_single_quiet_hour_between_busy_ones():
    prof = build_profile(_posts([8, 10], 3))  # nothing at 9, busy at 8 and 10
    assert is_active_hour(prof, 9)


def test_profile_wraps_around_midnight():
    prof = build_profile(_posts([23, 1], 3))
    assert is_active_hour(prof, 0)


def test_unknown_profile_is_never_active():
    assert not is_active_hour(None, 9)


def test_bad_timestamps_are_skipped():
    prof = build_profile(_posts([9], 6) + ["", "garbage"])
    assert prof is not None and is_active_hour(prof, 9)
