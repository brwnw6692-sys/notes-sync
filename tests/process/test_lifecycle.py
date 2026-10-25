from collector.process.lifecycle import next_status, lifecycle_stats


def _src(status, **kw):
    base = {"status": status, "irrelevant_streak_days": 0, "vet": None, "recent_relevant": False}
    base.update(kw)
    return base


def test_candidate_that_passed_vetting_is_promoted_to_active():
    s = _src("candidate", vet="promote")
    assert next_status(s)["status"] == "active"


def test_candidate_that_failed_vetting_is_retired():
    assert next_status(_src("candidate", vet="reject"))["status"] == "retired"


def test_pending_candidate_stays_candidate():
    assert next_status(_src("candidate", vet="pending"))["status"] == "candidate"


def test_dead_active_source_is_retired():
    assert next_status(_src("active", health="dead"))["status"] == "retired"


def test_active_source_irrelevant_too_long_is_retired():
    assert next_status(_src("active", irrelevant_streak_days=14))["status"] == "retired"


def test_active_source_still_relevant_stays_active():
    out = next_status(_src("active", irrelevant_streak_days=5, health="ok"))
    assert out["status"] == "active"


def test_retired_source_with_fresh_relevant_content_revives():
    assert next_status(_src("retired", recent_relevant=True))["status"] == "active"


def test_retired_source_without_content_stays_retired():
    assert next_status(_src("retired", recent_relevant=False))["status"] == "retired"


def test_stats_count_each_transition():
    before = [_src("candidate", vet="promote"), _src("active", health="dead"),
              _src("retired", recent_relevant=True), _src("active", health="ok")]
    stats = lifecycle_stats(before)
    assert stats == {"promoted": 1, "retired": 1, "revived": 1, "unchanged": 1}
