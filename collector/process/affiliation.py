"""A weak, honest signal of a source's orientation: which actor's language dominates its posts.

A news channel mentions every side, so a single marker proves nothing. We tally markers across many
samples and only commit an affiliation when one actor clearly dominates — otherwise it stays unknown.
This is an orientation hint, never a certainty, and the live layer refines it over time.
"""
from collector.process.normalize import normalize_text

# Distinctive actor markers (normalized Arabic unless noted). Deliberately narrow to reduce noise.
_MARKERS = {
    "hamas": ["كتائب القسام", "القسام", "حماس"],
    "pij": ["سرايا القدس", "الجهاد الاسلامي"],
    "hezbollah": ["حزب الله", "المقاومة الاسلامية في لبنان"],
    "pmf": ["الحشد الشعبي"],
    "sdf": ["قسد", "قوات سوريا الديمقراطية"],
    "houthi": ["انصار الله", "الحوثي"],
    "irgc": ["الحرس الثوري"],
    "syrian_army": ["الجيش العربي السوري"],
    "syrian_opposition": ["الجيش الوطني السوري"],
    "isis": ["داعش", "تنظيم الدولة"],
    "israeli_mil": ['צה"ל', "צבא ההגנה לישראל"],   # Hebrew
}
_NORM = {a: [normalize_text(m) for m in ms] for a, ms in _MARKERS.items()}


def classify_affiliation(text: str) -> str:
    """The actor whose marker appears in this text, or '' — first match wins, longest markers first."""
    norm = normalize_text(text or "")
    best = ""
    for actor, markers in _NORM.items():
        for m in markers:
            if m and m in norm:
                return actor
    return best


def dominant_affiliation(tally: dict, min_share: float = 0.6, min_count: int = 3) -> str:
    """Commit to an affiliation only when one actor clearly dominates the tally; else '' (unknown)."""
    total = sum(tally.values())
    if total < min_count:
        return ""
    actor, n = max(tally.items(), key=lambda kv: kv[1])
    return actor if n / total >= min_share else ""
