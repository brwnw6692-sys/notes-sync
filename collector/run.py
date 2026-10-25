"""Pipeline entry point. Live fetching and storage wiring come in the next plan."""
from collector.config import CONFIG
from collector.process.normalize import normalize_text
from collector.process.origin import cluster_items


def process_items(items):
    for it in items:
        it.text_norm = normalize_text(it.text_raw)
    return cluster_items(items, CONFIG.simhash_hamming_max, CONFIG.simhash_window_hours)
