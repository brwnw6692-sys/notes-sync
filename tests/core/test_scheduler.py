from collector.core.scheduler import plan_run


def _s(id_, tier="quiet", region="x", status="active"):
    return {"id": id_, "tier": tier, "region": region, "status": status}


def _ids(sources):
    return [s["id"] for s in sources]


def test_hot_sources_due_every_run():
    sel, _ = plan_run([_s("a", "hot")], run_index=7, minutes=10, red_regions=set(), budget=10)
    assert _ids(sel) == ["a"]


def test_each_quiet_source_due_exactly_once_per_hour_and_spread_out():
    srcs = [_s(f"q{i}") for i in range(60)]
    per_run = []
    seen = []
    for run in range(6):  # 6 runs x 10 min = 1 hour
        sel, _ = plan_run(srcs, run_index=run, minutes=10, red_regions=set(), budget=1000)
        per_run.append(len(sel))
        seen += _ids(sel)
    assert sorted(seen) == sorted(_ids(srcs))      # every source once, none twice
    assert max(per_run) < 60                         # not all in the same run


def test_red_region_forces_all_its_sources():
    srcs = [_s("b", region="r_red"), _s("c", region="r_other")]
    sel, _ = plan_run(srcs, run_index=1, minutes=10, red_regions={"r_red"}, budget=10)
    assert "b" in _ids(sel)


def test_inactive_sources_never_scheduled():
    sel, _ = plan_run([_s("a", "hot", status="retired")], run_index=0, minutes=10, red_regions=set(), budget=10)
    assert sel == []


def test_budget_caps_selection_with_red_first_then_hot_and_reports_overflow():
    srcs = [_s("h1", "hot"), _s("h2", "hot"), _s("r1", region="r_red")]
    sel, overflow = plan_run(srcs, run_index=1, minutes=10, red_regions={"r_red"}, budget=2)
    assert _ids(sel) == ["r1", "h1"]
    assert overflow == ["h2"]


def test_quiet_source_in_its_active_hours_is_due_every_run():
    srcs = [_s("q1")]
    for run in range(6):
        sel, _ = plan_run(srcs, run_index=run, minutes=10, red_regions=set(), budget=10, active_now={"q1"})
        assert _ids(sel) == ["q1"]


def test_active_now_ranks_after_red_and_hot_before_regular_quiet():
    srcs = [_s("q_active"), _s("h1", "hot"), _s("r1", region="r_red")]
    sel, overflow = plan_run(srcs, run_index=0, minutes=10, red_regions={"r_red"}, budget=2,
                             active_now={"q_active"})
    assert _ids(sel) == ["r1", "h1"]
    assert overflow == ["q_active"]


def test_backlog_goes_first_next_run():
    srcs = [_s("h1", "hot"), _s("h2", "hot")]
    sel, _ = plan_run(srcs, run_index=2, minutes=10, red_regions=set(), budget=1, backlog=["h2"])
    assert _ids(sel) == ["h2"]
