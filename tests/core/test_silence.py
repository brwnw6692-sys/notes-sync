from datetime import datetime, timezone

from collector.core.health import expected_posts, silence_signal
from collector.process.rhythm import build_profile


def _t(day, hour):
    return datetime(2026, 10, day, hour, 0, tzinfo=timezone.utc)


def _day_channel_profile():
    # Posts only between 08:00 and 17:59 UTC, 3 per hour, for 10 days.
    ts = [f"2026-10-{d:02d}T{h:02d}:{m:02d}:00+00:00"
          for d in range(1, 11) for h in range(8, 18) for m in range(3)]
    return build_profile(ts)


PROFILE = _day_channel_profile()
PER_DAY = 30


def test_night_silence_of_daytime_channel_is_not_abnormal():
    # 22:00 -> 06:00: almost nothing expected
    assert expected_posts(PROFILE, PER_DAY, _t(20, 22), _t(21, 6)) < 1
    assert not silence_signal(PROFILE, PER_DAY, 0, _t(20, 22), _t(21, 6))


def test_daytime_silence_of_daytime_channel_is_abnormal():
    # 09:00 -> 13:00: about 12 posts expected, none arrived
    assert expected_posts(PROFILE, PER_DAY, _t(20, 9), _t(20, 13)) > 8
    assert silence_signal(PROFILE, PER_DAY, 0, _t(20, 9), _t(20, 13))


def test_short_silence_below_floor_is_never_abnormal():
    assert not silence_signal(PROFILE, PER_DAY, 0, _t(20, 10), _t(20, 12))


def test_low_volume_channel_does_not_trigger():
    assert not silence_signal(PROFILE, 2, 0, _t(20, 9), _t(20, 13))


def test_partial_hours_are_counted_proportionally():
    start = datetime(2026, 10, 20, 9, 30, tzinfo=timezone.utc)
    end = datetime(2026, 10, 20, 10, 0, tzinfo=timezone.utc)
    full = expected_posts(PROFILE, PER_DAY, _t(20, 9), _t(20, 10))
    assert abs(expected_posts(PROFILE, PER_DAY, start, end) - full / 2) < 1e-9


def test_non_utc_times_use_the_correct_utc_hour():
    from datetime import timedelta
    il = timezone(timedelta(hours=3))  # 12:00 local = 09:00 UTC
    local = expected_posts(PROFILE, PER_DAY, datetime(2026, 10, 20, 12, tzinfo=il),
                           datetime(2026, 10, 20, 16, tzinfo=il))
    assert abs(local - expected_posts(PROFILE, PER_DAY, _t(20, 9), _t(20, 13))) < 1e-9


def test_without_profile_falls_back_to_median_gap_rule():
    # median gap 1h, silent 5h -> abnormal under the old rule
    assert silence_signal(None, PER_DAY, 3600, _t(20, 1), _t(20, 6))
    assert not silence_signal(None, PER_DAY, 3600, _t(20, 1), _t(20, 3))
