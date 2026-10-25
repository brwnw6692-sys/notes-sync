"""Coverage per region: how many independent sources actually see it (spec 5.6)."""


def coverage_score(items, region: str) -> int:
    """Distinct sources that originated at least one message about the region. Copies don't count."""
    return len({it["source_id"] for it in items
                if it["region"] == region and it.get("is_original")})


def expected_coverage(population: int, per_capita: float) -> int:
    return max(1, int(population * per_capita))


def is_blind_spot(coverage: int, population: int, per_capita: float) -> bool:
    return coverage < expected_coverage(population, per_capita)
