"""Arabic/Persian normalization for matching. The original text is always kept separately."""
import re
import unicodedata

_DIACRITICS = re.compile(r"[ً-ْٰـ]")  # harakat, superscript alef, tatweel

# Everything collapses to one canonical (Arabic) form so spelling variants match.
_MAP = {
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ى": "ي", "ی": "ي",   # alef maqsura, Persian yeh -> Arabic yeh
    "ک": "ك",             # Persian kaf -> Arabic kaf
    "ة": "ه",             # ta marbuta -> ha (matching only)
}

_DIGITS = {ord(c): str(i) for i, c in enumerate("٠١٢٣٤٥٦٧٨٩")}
_DIGITS.update({ord(c): str(i) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹")})


def normalize_digits(s: str) -> str:
    return s.translate(_DIGITS)


def normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = _DIACRITICS.sub("", s)
    s = "".join(_MAP.get(ch, ch) for ch in s)
    s = normalize_digits(s)
    return re.sub(r"\s+", " ", s).strip()
