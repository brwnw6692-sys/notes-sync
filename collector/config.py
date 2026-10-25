"""All tunable parameters live here. TAG: RETUNE = needs calibration on real data."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    run_interval_min: int = 10
    telegram_req_budget: int = 300          # RETUNE
    run_time_budget_sec: int = 360          # RETUNE
    domain_delay_sec: tuple = (0.3, 1.0)
    hot_every_runs: int = 1
    quiet_every_min: int = 60
    red_duration_hours: int = 6
    gap_fill_max_pages: int = 5
    simhash_hamming_max: int = 3            # RETUNE
    simhash_window_hours: int = 6
    phash_recycle_after_hours: int = 48
    phash_retention_days: int = 365
    hot_tier_min_originality: float = 0.3   # RETUNE
    silence_factor: int = 4                 # RETUNE
    silence_floor_hours: int = 3
    hot_items_retention_days: int = 7
    vet_min_arabic_persian: float = 0.6     # RETUNE
    vet_min_place_mentions: float = 0.2     # RETUNE
    vet_min_original: float = 0.3           # RETUNE
    vet_min_posts_per_day: float = 1.0
    discovery_daily_cap: int = 20
    discovery_blindspot_reserved: int = 5
    retire_after_irrelevant_days: int = 14
    dead_after_consecutive_fails: int = 3


CONFIG = Config()
