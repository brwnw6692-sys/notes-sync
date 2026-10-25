"""Actions logs are public. Only fixed keys and numbers may ever be printed."""

ALLOWED_KEYS = frozenset({
    "ok", "quiet", "limited", "broken", "dead",
    "items", "gaps", "gaps_filled", "duration_sec", "requests",
})


def format_run_summary(counts: dict) -> str:
    for key, value in counts.items():
        if key not in ALLOWED_KEYS:
            raise ValueError("summary key not allowed")
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError("summary values must be numbers")
    return "run: " + " ".join(f"{k}={counts[k]}" for k in sorted(counts))


def scan_output_for_leaks(output: str, secret_terms) -> list:
    low = output.lower()
    return [t for t in secret_terms if t and t.lower() in low]
