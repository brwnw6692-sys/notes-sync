from collector.process.stats import coverage_score, expected_coverage, is_blind_spot


def _it(region, cluster, source, original=True):
    return {"region": region, "origin_cluster_id": cluster, "source_id": source, "is_original": original}


def test_coverage_counts_independent_sources_not_copies():
    items = [
        _it("r1", "c1", "a"),
        _it("r1", "c1", "b", original=False),   # copy of a's message: not independent
        _it("r1", "c2", "c"),
    ]
    assert coverage_score(items, "r1") == 2


def test_source_counted_once_even_with_many_originals():
    items = [_it("r1", "c1", "a"), _it("r1", "c2", "a"), _it("r1", "c3", "a")]
    assert coverage_score(items, "r1") == 1


def test_other_regions_ignored():
    assert coverage_score([_it("r2", "c1", "a")], "r1") == 0


def test_expected_coverage_scales_with_population_with_floor_of_one():
    assert expected_coverage(population=1_000, per_capita=1 / 100_000) == 1
    assert expected_coverage(population=500_000, per_capita=1 / 100_000) == 5


def test_blind_spot_when_below_expected():
    assert is_blind_spot(coverage=1, population=500_000, per_capita=1 / 100_000)
    assert not is_blind_spot(coverage=5, population=500_000, per_capita=1 / 100_000)
