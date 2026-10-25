"""Pipeline entry point. Live fetching and storage wiring come in the next plan."""
from collector.config import CONFIG
from collector.geo.gazetteer import default_gazetteer
from collector.process.normalize import normalize_text
from collector.process.origin import cluster_items


def process_items(items):
    gaz = default_gazetteer()
    for it in items:
        it.text_norm = normalize_text(it.text_raw)
        places = gaz.tag_places(it.text_raw)
        it.tags = {**it.tags, "places": places}
        loc = gaz.primary_location(it.text_raw)
        if loc is not None:
            it.lat, it.lon = loc
    return cluster_items(items, CONFIG.simhash_hamming_max, CONFIG.simhash_window_hours)
