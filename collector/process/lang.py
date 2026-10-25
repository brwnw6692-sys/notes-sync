"""A cheap, offline language guess by dominant script — enough to tell Arabic/Persian from Hebrew or Latin.

Vetting only needs "is this Arab/Persian-world reporting", so we group all Arabic-script text as "ar"
(Persian shares the script) rather than attempting true ar-vs-fa detection.
"""

_RANGES = {
    "ar": ((0x0600, 0x06FF), (0x0750, 0x077F), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)),
    "he": ((0x0590, 0x05FF),),
    "en": ((0x0041, 0x005A), (0x0061, 0x007A)),
}


def detect_lang(text: str) -> str:
    counts = {k: 0 for k in _RANGES}
    for ch in text or "":
        o = ord(ch)
        for lang, ranges in _RANGES.items():
            if any(lo <= o <= hi for lo, hi in ranges):
                counts[lang] += 1
                break
    best = max(counts, key=counts.get)
    return best if counts[best] else ""
