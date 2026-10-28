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
    # Measured on 64-bit char-4-gram SimHash: small edits = 4-8, unrelated texts ~= 32.
    simhash_hamming_max: int = 12           # RETUNE
    simhash_window_hours: int = 6
    phash_recycle_after_hours: int = 48
    phash_retention_days: int = 365
    hot_tier_min_originality: float = 0.3   # RETUNE
    silence_factor: int = 4                 # RETUNE
    silence_floor_hours: int = 3
    # Rhythm-aware silence: zero posts when >= this many were expected. Poisson P(0 | 4) ~= 1.8%.
    silence_min_expected_posts: float = 4.0  # RETUNE
    hot_items_retention_days: int = 7
    vet_min_relevant_lang: float = 0.6      # share in a Middle East language (ar/fa/he); RETUNE
    vet_min_place_mentions: float = 0.2     # RETUNE
    vet_min_original: float = 0.3           # RETUNE
    vet_min_posts_per_day: float = 1.0
    discovery_daily_cap: int = 20
    discovery_blindspot_reserved: int = 5
    discovery_per_run: int = 40             # candidate pages actively sampled each run
    discovery_max_pending: int = 500        # pause blind-spot search while the backlog is this deep
    discovery_sample_keep: int = 12         # sample messages retained per candidate
    discovery_searches_per_run: int = 2     # blind-spot directory searches each run
    discovery_default_region: str = "arab_world"
    retire_after_irrelevant_days: int = 14
    dead_after_consecutive_fails: int = 3
    canary_max_silence_hours: float = 2.0   # RETUNE
    canary_blind_fraction: float = 0.5      # RETUNE
    rhythm_min_posts: int = 50              # RETUNE
    quarantine_max_per_source: int = 3
    quarantine_max_total: int = 50
    # Coverage grid over the Middle East (degrees). Box spans Gaza/Sinai up to Iran/Caucasus.
    grid_lat_min: float = 12.0
    grid_lat_max: float = 42.5             # includes all of Turkey (Black Sea coast)
    grid_lon_min: float = 25.0             # includes western Turkey (Istanbul, Izmir, the Aegean)
    grid_lon_max: float = 64.0
    grid_cell_deg: float = 0.5             # RETUNE
    heat_sigma_km: float = 60.0            # city heat falloff radius; RETUNE
    coverage_hot_weight: float = 6.0       # ~log1p(400): any populated cell is in scope; RETUNE
    # Adaptive resolution: refine a cell into sub-cells only where activity is dense.
    adaptive_factor: int = 5               # each level divides a cell into factor x factor
    adaptive_max_level: int = 3            # 0.5 -> 0.1 -> 0.02 -> 0.004 deg (~440 m, village)
    adaptive_split_threshold: int = 8      # items in a cell before it refines; RETUNE
    # Located messages carry a precise city coordinate, so draw active cells fine (city scale,
    # ~2 km at level 2) rather than binning them into coarse 55 km cells.
    active_display_level: int = 2          # RETUNE
    recent_activity_hours: int = 48        # window for "what is happening now" vs the 7-day backdrop
    rhythm_active_ratio: float = 1.0        # active = share >= ratio x uniform (1/24); RETUNE


CONFIG = Config()
