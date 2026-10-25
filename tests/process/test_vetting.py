from collector.process.vetting import vet_candidate, rank_candidates


def _sample(lang="ar", places=1, original=True):
    return {"lang": lang, "place_hits": places, "is_original": original}


def _many(n, **kw):
    return [_sample(**kw) for _ in range(n)]


def test_too_few_samples_is_undecided():
    assert vet_candidate(_many(2), days_seen=1) == "pending"


def test_good_candidate_is_promoted():
    # arabic, mentions places, mostly original, active enough
    assert vet_candidate(_many(10), days_seen=3) == "promote"


def test_wrong_language_is_rejected():
    assert vet_candidate(_many(10, lang="en"), days_seen=3) == "reject"


def test_no_place_mentions_is_rejected():
    assert vet_candidate(_many(10, places=0), days_seen=3) == "reject"


def test_pure_reposter_is_rejected():
    assert vet_candidate(_many(10, original=False), days_seen=3) == "reject"


def test_blind_spot_candidates_are_vetted_first():
    cands = [
        {"handle": "a", "regions": {"covered"}},
        {"handle": "b", "regions": {"blind_1"}},
        {"handle": "c", "regions": {"covered"}},
    ]
    ranked = rank_candidates(cands, blind_regions={"blind_1"}, cap=2)
    assert ranked[0]["handle"] == "b"
    assert len(ranked) == 2


def test_rank_respects_cap():
    cands = [{"handle": str(i), "regions": set()} for i in range(30)]
    assert len(rank_candidates(cands, blind_regions=set(), cap=20)) == 20
